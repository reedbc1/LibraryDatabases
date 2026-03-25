import importlib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

INPUT_CSV = "subscription_resources_embeddings.csv"
EMBEDDING_MODEL = "text-embedding-3-small"
TOKEN_PATTERN = re.compile(r"\b\w+\b")


def load_faiss_library():
    current_dir = Path(__file__).resolve().parent
    original_sys_path = list(sys.path)

    try:
        sys.path = [
            path for path in sys.path
            if Path(path or ".").resolve() != current_dir
        ]
        return importlib.import_module("faiss")
    except ModuleNotFoundError as exc:
        raise ImportError(
            "The FAISS package is required. Install `faiss-cpu` before running this script."
        ) from exc
    finally:
        sys.path = original_sys_path


faiss = load_faiss_library()


def tokenize(text):
    return TOKEN_PATTERN.findall(str(text).lower())


def normalize_scores(scores):
    if len(scores) == 0:
        return scores

    min_score = float(np.min(scores))
    max_score = float(np.max(scores))

    if max_score - min_score < 1e-12:
        return np.zeros_like(scores, dtype=np.float32)

    return ((scores - min_score) / (max_score - min_score)).astype(np.float32)


class BM25Index:
    def __init__(self, corpus_tokens, k1=1.5, b=0.75):
        self.corpus_tokens = corpus_tokens
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus_tokens)
        self.doc_lengths = np.array([len(doc) for doc in corpus_tokens], dtype=np.float32)
        self.avg_doc_length = float(self.doc_lengths.mean()) if self.corpus_size else 0.0
        self.term_frequencies = []
        self.idf = {}

        document_frequencies = {}

        for doc in corpus_tokens:
            frequencies = {}
            for token in doc:
                frequencies[token] = frequencies.get(token, 0) + 1

            self.term_frequencies.append(frequencies)

            for token in frequencies:
                document_frequencies[token] = document_frequencies.get(token, 0) + 1

        for token, frequency in document_frequencies.items():
            self.idf[token] = np.log(1 + (self.corpus_size - frequency + 0.5) / (frequency + 0.5))

    def get_scores(self, query_tokens):
        scores = np.zeros(self.corpus_size, dtype=np.float32)
        if not query_tokens or self.corpus_size == 0:
            return scores

        length_denominator_base = self.k1 * (1 - self.b)

        for index, term_frequencies in enumerate(self.term_frequencies):
            doc_length = self.doc_lengths[index]
            length_denominator = length_denominator_base

            if self.avg_doc_length:
                length_denominator += self.k1 * self.b * (doc_length / self.avg_doc_length)

            score = 0.0
            for token in query_tokens:
                term_frequency = term_frequencies.get(token)
                if not term_frequency:
                    continue

                idf = self.idf.get(token, 0.0)
                numerator = term_frequency * (self.k1 + 1)
                denominator = term_frequency + length_denominator
                score += idf * (numerator / denominator)

            scores[index] = score

        return scores


class HybridSearcher:
    def __init__(self, csv_path=INPUT_CSV, embedding_model=EMBEDDING_MODEL):
        self.csv_path = csv_path
        self.embedding_model = embedding_model
        self.df, self.embedding_matrix = self._load_dataset(csv_path)
        self.index = self._build_faiss_index(self.embedding_matrix)
        self.bm25 = BM25Index([tokenize(text) for text in self.df["input_text"]])
        self.client = self._build_openai_client()

    def _load_dataset(self, csv_path):
        df = pd.read_csv(csv_path)
        required_columns = {"embedding", "input_text"}
        missing_columns = required_columns.difference(df.columns)

        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing required columns in {csv_path}: {missing}")

        parsed_rows = []
        parsed_embeddings = []
        expected_dimension = None

        for _, row in df.iterrows():
            raw_embedding = row.get("embedding")
            if pd.isna(raw_embedding):
                continue

            embedding = np.asarray(json.loads(raw_embedding), dtype=np.float32)
            if embedding.ndim != 1:
                raise ValueError("Each embedding must be a one-dimensional vector.")

            if expected_dimension is None:
                expected_dimension = embedding.shape[0]
            elif embedding.shape[0] != expected_dimension:
                raise ValueError("All embeddings must have the same dimension.")

            parsed_rows.append(row.to_dict())
            parsed_embeddings.append(embedding)

        if not parsed_embeddings:
            raise ValueError(f"No embeddings were loaded from {csv_path}.")

        cleaned_df = pd.DataFrame(parsed_rows).reset_index(drop=True)
        embedding_matrix = np.vstack(parsed_embeddings).astype(np.float32)
        return cleaned_df, embedding_matrix

    def _build_faiss_index(self, embedding_matrix):
        normalized_embeddings = embedding_matrix.copy()
        faiss.normalize_L2(normalized_embeddings)

        index = faiss.IndexFlatIP(normalized_embeddings.shape[1])
        index.add(normalized_embeddings)
        return index

    def _build_openai_client(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        return OpenAI(api_key=api_key)

    def embed_query(self, query):
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=query,
            encoding_format="float",
        )
        return np.asarray(response.data[0].embedding, dtype=np.float32)

    def search(self, query, semantic_weight=0.65, keyword_weight=0.35, top_k=None):
        if not query or not query.strip():
            raise ValueError("A non-empty query is required.")

        total_weight = semantic_weight + keyword_weight
        if total_weight <= 0:
            raise ValueError("semantic_weight and keyword_weight must sum to a positive value.")

        semantic_weight /= total_weight
        keyword_weight /= total_weight

        query_embedding = self.embed_query(query).reshape(1, -1)
        faiss.normalize_L2(query_embedding)

        semantic_scores = np.zeros(len(self.df), dtype=np.float32)
        distances, indices = self.index.search(query_embedding, len(self.df))
        semantic_scores[indices[0]] = distances[0]

        keyword_scores = self.bm25.get_scores(tokenize(query))
        normalized_semantic_scores = normalize_scores(semantic_scores)
        normalized_keyword_scores = normalize_scores(keyword_scores)

        hybrid_scores = (
            semantic_weight * normalized_semantic_scores
            + keyword_weight * normalized_keyword_scores
        )

        results = self.df.copy()
        results["semantic_score"] = semantic_scores
        results["keyword_score"] = keyword_scores
        results["hybrid_score"] = hybrid_scores

        ordered = results.sort_values(
            by=["hybrid_score", "semantic_score", "keyword_score"],
            ascending=[False, False, False],
        ).reset_index(drop=True)

        if top_k is not None:
            ordered = ordered.head(top_k).copy()

        ordered.insert(0, "rank", np.arange(1, len(ordered) + 1))
        return ordered


def format_results(results, show_input_text=False):
    display_columns = ["rank", "hybrid_score", "semantic_score", "keyword_score"]

    for column in ["title", "type", "link"]:
        if column in results.columns:
            display_columns.append(column)

    if show_input_text and "input_text" in results.columns:
        display_columns.append("input_text")

    display_df = results[display_columns].copy()

    for score_column in ["hybrid_score", "semantic_score", "keyword_score"]:
        display_df[score_column] = display_df[score_column].map(lambda value: f"{value:.4f}")

    return display_df.to_string(index=False)
