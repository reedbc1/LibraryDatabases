from functools import lru_cache

from flask import Flask, render_template, request

from hybrid_search import HybridSearcher

app = Flask(__name__)


@lru_cache(maxsize=1)
def get_searcher():
    return HybridSearcher()


def serialize_results(results):
    records = []

    for row in results.to_dict(orient="records"):
        records.append(
            {
                "rank": row["rank"],
                "title": row.get("title", "Untitled"),
                "description": row.get("description", ""),
                "resource_type": row.get("type", ""),
                "link": row.get("link", ""),
                "hybrid_score": f"{row.get('hybrid_score', 0.0):.4f}",
                "semantic_score": f"{row.get('semantic_score', 0.0):.4f}",
                "keyword_score": f"{row.get('keyword_score', 0.0):.4f}",
            }
        )

    return records


@app.get("/")
def index():
    query = request.args.get("query", "").strip()
    results = []
    error = None

    if query:
        try:
            results_df = get_searcher().search(query=query)
            results = serialize_results(results_df)
        except Exception as exc:
            error = str(exc)

    return render_template(
        "index.html",
        query=query,
        results=results,
        result_count=len(results),
        error=error,
    )


if __name__ == "__main__":
    app.run(debug=True)
