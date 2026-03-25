import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Make sure OPENAI_API_KEY is set in environment
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError('OPENAI_API_KEY environment variable is required')
client = OpenAI(api_key=api_key)

INPUT_CSV = 'subscription_resources.csv'
OUTPUT_CSV = 'subscription_resources_embeddings.csv'
EMBEDDING_MODEL = 'text-embedding-3-small'  # or text-embedding-3-large


def build_input_text(row):
    title = str(row.get('title', '')).strip()
    description = str(row.get('description', '')).strip()
    return f"{title}. {description}" if description else title


def generate_embedding(text):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        encoding_format='float',
    )
    return response.data[0].embedding


def main():
    df = pd.read_csv(INPUT_CSV)
    df = df.dropna(subset=['title', 'description'])

    df['input_text'] = df.apply(build_input_text, axis=1)

    embeddings = []

    for input_text in df['input_text']:
        embeddings.append(generate_embedding(input_text))

    df['embedding'] = embeddings

    # Store embeddings as JSON string (list of floats) for easy retrieval
    df['embedding'] = df['embedding'].apply(json.dumps)
    df.to_csv(OUTPUT_CSV, index=False)

    print(f'Wrote {len(df)} embeddings to {OUTPUT_CSV}')


if __name__ == '__main__':
    main()
