import argparse

from hybrid_search import EMBEDDING_MODEL, INPUT_CSV, HybridSearcher, format_results


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run hybrid semantic + keyword search over resource embeddings."
    )
    parser.add_argument("query", nargs="+", help="The user query to search for.")
    parser.add_argument("--csv-path", default=INPUT_CSV, help="Path to the embeddings CSV file.")
    parser.add_argument(
        "--model",
        default=EMBEDDING_MODEL,
        help="Embedding model used to encode the query.",
    )
    parser.add_argument(
        "--semantic-weight",
        type=float,
        default=0.65,
        help="Weight assigned to the semantic FAISS score.",
    )
    parser.add_argument(
        "--keyword-weight",
        type=float,
        default=0.35,
        help="Weight assigned to the BM25 keyword score.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Optional number of results to print. Defaults to all rows.",
    )
    parser.add_argument(
        "--show-input-text",
        action="store_true",
        help="Include the full input_text field in the printed results.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    query = " ".join(args.query).strip()

    searcher = HybridSearcher(csv_path=args.csv_path, embedding_model=args.model)
    results = searcher.search(
        query=query,
        semantic_weight=args.semantic_weight,
        keyword_weight=args.keyword_weight,
        top_k=args.top_k,
    )
    print(format_results(results, show_input_text=args.show_input_text))


if __name__ == "__main__":
    main()
