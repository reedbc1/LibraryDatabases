import html

import streamlit as st

from hybrid_search import HybridSearcher


st.set_page_config(
    page_title="Library Database Search",
    page_icon="📚",
    layout="wide",
)


@st.cache_resource(show_spinner=False)
def get_searcher():
    return HybridSearcher()


def inject_styles():
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(255, 219, 169, 0.7), transparent 30%),
                    radial-gradient(circle at right 15%, rgba(136, 194, 175, 0.45), transparent 25%),
                    linear-gradient(180deg, #f9f3e8 0%, #f5efe4 48%, #efe5d5 100%);
            }

            .block-container {
                padding-top: 2.5rem;
                padding-bottom: 3rem;
                max-width: 1120px;
            }

            .hero-shell {
                padding: 2rem;
                border: 1px solid rgba(92, 73, 46, 0.14);
                border-radius: 28px;
                background: rgba(255, 252, 246, 0.88);
                box-shadow: 0 22px 60px rgba(76, 58, 32, 0.12);
                backdrop-filter: blur(12px);
            }

            .eyebrow {
                margin: 0 0 0.75rem 0;
                font-size: 0.8rem;
                letter-spacing: 0.18em;
                text-transform: uppercase;
                color: #0e5a47;
                font-weight: 700;
            }

            .hero-title {
                margin: 0;
                max-width: 11ch;
                font-size: clamp(2.7rem, 5vw, 4.4rem);
                line-height: 0.95;
                color: #1e1a16;
                font-family: Georgia, "Times New Roman", serif;
                font-weight: 700;
            }

            .hero-lede {
                max-width: 700px;
                margin: 1rem 0 0 0;
                font-size: 1rem;
                line-height: 1.7;
                color: #66584a;
            }

            .message {
                margin-top: 1rem;
                padding: 0.95rem 1rem;
                border-radius: 16px;
                font-size: 0.95rem;
                border: 1px solid transparent;
            }

            .message-neutral {
                background: rgba(255, 255, 255, 0.55);
                color: #66584a;
            }

            .message-success {
                background: #d7efe6;
                color: #093a2f;
            }

            .message-error {
                background: #f5d6d1;
                color: #7a1d16;
            }

            .result-card {
                padding: 1.35rem;
                border: 1px solid rgba(92, 73, 46, 0.14);
                border-radius: 24px;
                background: rgba(255, 252, 246, 0.92);
                box-shadow: 0 22px 60px rgba(76, 58, 32, 0.12);
                height: 100%;
            }

            .card-topline {
                display: flex;
                align-items: center;
                gap: 0.6rem;
                flex-wrap: wrap;
                margin-bottom: 0.8rem;
            }

            .rank {
                font-size: 0.9rem;
                font-weight: 700;
                color: #0e5a47;
            }

            .pill {
                display: inline-block;
                padding: 0.35rem 0.65rem;
                border-radius: 999px;
                background: rgba(14, 90, 71, 0.09);
                color: #093a2f;
                font-size: 0.82rem;
                font-weight: 600;
            }

            .result-title {
                margin: 0;
                color: #1e1a16;
                font-size: 1.18rem;
                line-height: 1.2;
            }

            .result-description {
                margin: 0.8rem 0 1rem 0;
                color: #66584a;
                line-height: 1.65;
                min-height: 5.2rem;
            }

            .score-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.6rem;
                margin-bottom: 1rem;
            }

            .score-box {
                padding: 0.8rem;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.74);
            }

            .score-label {
                display: block;
                margin-bottom: 0.35rem;
                font-size: 0.78rem;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: #66584a;
            }

            .score-value {
                font-weight: 700;
                color: #1e1a16;
            }

            .result-link {
                display: inline-block;
                padding: 0.65rem 0.95rem;
                border-radius: 999px;
                background: #ffffff;
                color: #093a2f;
                text-decoration: none;
                font-weight: 700;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_message(message, variant):
    st.markdown(
        f'<div class="message message-{variant}">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def render_result_card(result):
    description = html.escape(result.get("description") or "")
    resource_type = html.escape(result.get("type") or "")
    title = html.escape(result.get("title") or "Untitled")
    link = html.escape(result.get("link") or "")

    st.markdown(
        f"""
        <article class="result-card">
            <div class="card-topline">
                <span class="rank">#{result["rank"]}</span>
                {f'<span class="pill">{resource_type}</span>' if resource_type else ''}
            </div>
            <h3 class="result-title">{title}</h3>
            <p class="result-description">{description}</p>
            <div class="score-grid">
                <div class="score-box">
                    <span class="score-label">Hybrid</span>
                    <span class="score-value">{result["hybrid_score"]:.4f}</span>
                </div>
                <div class="score-box">
                    <span class="score-label">Semantic</span>
                    <span class="score-value">{result["semantic_score"]:.4f}</span>
                </div>
                <div class="score-box">
                    <span class="score-label">Keyword</span>
                    <span class="score-value">{result["keyword_score"]:.4f}</span>
                </div>
            </div>
            {f'<a class="result-link" href="{link}" target="_blank">Open database</a>' if link else ''}
        </article>
        """,
        unsafe_allow_html=True,
    )


def main():
    inject_styles()

    st.markdown(
        """
        <section class="hero-shell">
            <p class="eyebrow">Proof of Concept</p>
            <h1 class="hero-title">Hybrid search for subscription databases</h1>
            <p class="hero-lede">
                Enter a query to rank every database using semantic similarity from FAISS plus BM25 keyword matching.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.form("search_form", clear_on_submit=False):
        query = st.text_input(
            "Search query",
            placeholder="Try: cookbooks, legal forms, business research",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Search", use_container_width=False)

    results = None
    error = None

    if submitted and query.strip():
        with st.spinner("Ranking databases..."):
            try:
                results = get_searcher().search(query=query.strip())
            except Exception as exc:
                error = str(exc)
    elif submitted:
        error = "A non-empty query is required."

    if error:
        render_message(error, "error")
    elif results is not None:
        render_message(
            f"Showing {len(results)} ranked results for “{query.strip()}”.",
            "success",
        )
    else:
        render_message(
            "Submit a query to rank all databases from most relevant to least relevant.",
            "neutral",
        )

    if results is not None and not results.empty:
        columns = st.columns(2, gap="large")
        for index, record in enumerate(results.to_dict(orient="records")):
            with columns[index % 2]:
                render_result_card(record)


main()
