from __future__ import annotations

import logging
import math
import os
import time
from pathlib import Path

import httpx
import pandas as pd
import plotly.express as px
import psycopg
import streamlit as st
from psycopg.rows import dict_row

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("frontend")

BASE_DIR = Path(__file__).resolve().parent
SQL_DIR = BASE_DIR / "sql"


def load_sql(filename: str) -> str:
    path = SQL_DIR / filename
    return path.read_text(encoding="utf-8")


def get_db_connection() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "secretpassword"),
        dbname=os.getenv("DB_NAME", "appdb"),
        row_factory=dict_row,
        autocommit=True,
    )


@st.cache_data(show_spinner=False)
def run_query(sql_file: str) -> pd.DataFrame:
    query = load_sql(sql_file)
    logger.info("Starting SQL query: %s", sql_file)
    start = time.perf_counter()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
    duration = time.perf_counter() - start
    logger.info("SQL query completed: %s rows=%d duration=%.3fs", sql_file, len(rows), duration)
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def get_query_embedding(text: str, model_name: str = "nomic-embed-text") -> list[float]:
    api_url = os.getenv("AGENTIC_API_URL", "http://localhost:8001")
    url = f"{api_url.rstrip('/')}/embedding"
    logger.info("Requesting query embedding (text=%s chars, model=%s)", len(text), model_name)
    start = time.perf_counter()
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params={"text": text, "model_name": model_name})
        response.raise_for_status()
        embedding = response.json()
    duration = time.perf_counter() - start
    logger.info("Query embedding received: dims=%s duration=%.3fs", len(embedding) if isinstance(embedding, list) else "?", duration)
    if not isinstance(embedding, list):
        raise ValueError("Embedding endpoint returned unexpected payload")
    return embedding


def clean_vector(value: object) -> list[float]:
    if value is None:
        return []
    if isinstance(value, memoryview):
        return list(value)
    if isinstance(value, (list, tuple)):
        return [float(x) for x in value]
    return [float(x) for x in list(value)]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vector dimensions do not match")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_similarity_table(items: pd.DataFrame, vector_column: str, top_n: int) -> pd.DataFrame:
    logger.info("Building similarity matrix items=%d top_n=%d", len(items), top_n)
    labels = items["label"].tolist()
    vectors = [clean_vector(v) for v in items[vector_column].tolist()]
    if not vectors:
        logger.info("No vectors available to build similarity matrix")
        return pd.DataFrame()
    start = time.perf_counter()
    matrix = [
        [cosine_similarity(u, v) for v in vectors[:top_n]]
        for u in vectors[:top_n]
    ]
    duration = time.perf_counter() - start
    logger.info("Similarity matrix built duration=%.3fs", duration)
    return pd.DataFrame(matrix, index=labels[:top_n], columns=labels[:top_n])


def run_search(
    query: str,
    embeddings: pd.DataFrame,
    model_name: str,
    limit: int,
) -> pd.DataFrame:
    logger.info("Starting similarity search query_chars=%d model=%s limit=%d", len(query), model_name, limit)
    start = time.perf_counter()
    query_vector = get_query_embedding(query, model_name)
    rows = []
    for row in embeddings.itertuples(index=False):
        row_vector = clean_vector(row.vector)
        if len(row_vector) != len(query_vector):
            continue
        score = cosine_similarity(query_vector, row_vector)
        rows.append({"id": row[0], "label": row[1], "model_name": row.model_name, "score": score})
    result = pd.DataFrame(rows)
    duration = time.perf_counter() - start
    logger.info("Search completed candidates=%d results=%d duration=%.3fs", len(rows), len(result), duration)
    if result.empty:
        return result
    return result.sort_values("score", ascending=False).head(limit)


def render_overview(books_df: pd.DataFrame, authors_df: pd.DataFrame) -> None:
    st.header("Library Overview")
    left, right = st.columns(2)
    left.metric("Books in catalog", len(books_df))
    right.metric("Authors in catalog", len(authors_df))

    categories = books_df["categories"].apply(lambda value: value if isinstance(value, list) else [])
    category_counts = (
        pd.Series([category for categories_list in categories for category in categories_list], name="category")
        .value_counts()
        .reset_index(name="count")
        .rename(columns={"index": "category"})
    )

    publisher_counts = (
        books_df["publisher"].fillna("Unknown")
        .value_counts()
        .head(10)
        .reset_index(name="count")
        .rename(columns={"index": "publisher"})
    )

    nationality_counts = (
        authors_df["nationality"].fillna("Unknown")
        .value_counts()
        .head(10)
        .reset_index(name="count")
        .rename(columns={"index": "nationality"})
    )

    col1, col2 = st.columns(2)
    if not category_counts.empty:
        category_fig = px.bar(
            category_counts.head(10),
            x="count",
            y="category",
            orientation="h",
            title="Top Book Categories",
            labels={"count": "Number of books", "category": "Category"},
            color="count",
            color_continuous_scale="Blues",
        )
        category_fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=120, r=20, t=40, b=20))
        col1.plotly_chart(category_fig, use_container_width=True)
    else:
        col1.info("No category data available.")

    if not nationality_counts.empty:
        nationality_fig = px.bar(
            nationality_counts,
            x="count",
            y="nationality",
            orientation="h",
            title="Top Author Nationalities",
            labels={"count": "Number of authors", "nationality": "Nationality"},
            color="count",
            color_continuous_scale="Teal",
        )
        nationality_fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=120, r=20, t=40, b=20))
        col2.plotly_chart(nationality_fig, use_container_width=True)
    else:
        col2.info("No author nationality data available.")

    st.markdown("### Publisher distribution")
    if not publisher_counts.empty:
        publisher_fig = px.bar(
            publisher_counts,
            x="count",
            y="publisher",
            orientation="h",
            title="Top Publishers by Book Count",
            labels={"count": "Number of books", "publisher": "Publisher"},
            color="count",
            color_continuous_scale="Purples",
        )
        publisher_fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=120, r=20, t=40, b=20))
        st.plotly_chart(publisher_fig, use_container_width=True)
    else:
        st.info("No publisher distribution data available.")

    st.markdown("### Recent books")
    st.dataframe(books_df[["title", "authors", "categories", "isbn"]].head(10), use_container_width=True)
    st.markdown("### Authors")
    st.dataframe(authors_df[["name", "birth_date", "nationality", "books"]].head(10), use_container_width=True)


def render_embeddings_view(embeddings: pd.DataFrame, entity_name: str) -> None:
    st.header(f"{entity_name} Embeddings")
    if embeddings.empty:
        st.warning("No embeddings found for this entity.")
        return

    model_names = sorted(embeddings["model_name"].unique())
    selected_model = st.selectbox("Embedding model", model_names)
    filtered = embeddings[embeddings["model_name"] == selected_model].copy()
    if filtered.empty:
        st.warning("No embeddings are available for the selected model.")
        return

    filtered["label"] = filtered["title"].fillna(filtered["name"])
    max_items = min(len(filtered), 50)
    display_count = st.slider("Number of entries for matrix", 5, max_items, min(20, max_items))
    matrix_df = build_similarity_table(filtered, "vector", display_count)
    if matrix_df.empty:
        st.warning("Unable to build a similarity matrix from the selected embeddings.")
        return

    st.markdown(
        "These values represent cosine similarity between embedding vectors. High values indicate stronger semantic closeness."
    )

    fig = px.imshow(
        matrix_df,
        labels={"x": entity_name, "y": entity_name, "color": "Similarity"},
        x=matrix_df.columns,
        y=matrix_df.index,
        color_continuous_scale="Viridis",
        zmin=0,
        zmax=1,
        aspect="auto",
    )
    fig.update_layout(title=f"{entity_name} similarity heatmap", xaxis={"side": "top"}, margin=dict(l=40, r=40, t=50, b=40))
    fig.update_traces(hovertemplate="%{x}<br>%{y}<br>Similarity: %{z:.3f}")
    st.plotly_chart(fig, use_container_width=True)


def render_search_page(
    book_embeddings: pd.DataFrame,
    author_embeddings: pd.DataFrame,
    books_df: pd.DataFrame,
    authors_df: pd.DataFrame,
) -> None:
    st.header("Similarity Search")
    entity = st.radio("Search for", ["Books", "Authors"], horizontal=True)
    if entity == "Books":
        embeddings = book_embeddings
        data_df = books_df
        key_column = "book_id"
        label_column = "title"
    else:
        embeddings = author_embeddings
        data_df = authors_df
        key_column = "author_id"
        label_column = "name"

    if embeddings.empty:
        st.warning("No embeddings are stored yet. Ingest books/authors first.")
        return

    available_models = sorted(embeddings["model_name"].unique())
    selected_model = st.selectbox("Embedding model", available_models)
    query_text = st.text_input("Search text", help="Search books or authors by semantic similarity.")
    top_k = st.slider("Results", 1, 20, 5)

    if st.button("Run search"):
        filtered_embeddings = embeddings[embeddings["model_name"] == selected_model].copy()
        if filtered_embeddings.empty:
            st.warning("No stored embeddings match the selected model.")
            return
        if not query_text:
            st.info("Enter a search phrase to run a similarity search.")
            return

        results = run_search(query_text, filtered_embeddings, selected_model, top_k)
        if results.empty:
            st.warning("No matching embeddings were found for the selected model.")
            return

        merged = results.merge(
            data_df,
            left_on=["id"],
            right_on=[key_column],
            how="left",
        )
        merged = merged.assign(item_label=merged[label_column].fillna("Unknown"))
        score_fig = px.bar(
            merged.sort_values("score"),
            x="score",
            y="item_label",
            orientation="h",
            title=f"Top {entity} similarity scores",
            labels={"score": "Similarity", "item_label": entity[:-1]},
            color="score",
            color_continuous_scale="Viridis",
        )
        score_fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=140, r=20, t=50, b=20))
        st.plotly_chart(score_fig, use_container_width=True)

        st.markdown("### Top similar items")
        st.dataframe(
            merged[[label_column, "model_name", "score"]].rename(columns={label_column: entity[:-1]}),
            use_container_width=True,
        )
        st.markdown("#### Matching details")
        st.dataframe(merged.drop(columns=["vector"] if "vector" in merged.columns else []), use_container_width=True)


def render_sql_view() -> None:
    st.header("Raw SQL Queries")
    sql_files = sorted([f.name for f in SQL_DIR.glob("*.sql")])
    selected_file = st.selectbox("SQL file", sql_files)

    if selected_file:
        st.code(load_sql(selected_file), language="sql")
        if st.button("Run query"):
            df = run_query(selected_file)
            st.write(df)


def main() -> None:
    st.set_page_config(page_title="Smart Book Library Explorer", layout="wide")
    st.title("Smart Book Library Explorer")

    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Choose a page",
            ["Overview", "Embeddings", "Search", "SQL"],
        )
        st.markdown("---")
        st.markdown("### Connection settings")
        st.write(
            {
                "DB_HOST": os.getenv("DB_HOST", "localhost"),
                "DB_PORT": os.getenv("DB_PORT", "5432"),
                "DB_NAME": os.getenv("DB_NAME", "appdb"),
                "AGENTIC_API_URL": os.getenv("AGENTIC_API_URL", "http://localhost:8001"),
            }
        )

    logger.info("Starting page render: %s", page)
    page_start = time.perf_counter()
    books_df = run_query("get_books.sql")
    authors_df = run_query("get_authors.sql")
    book_embeddings = run_query("get_book_embeddings.sql")
    author_embeddings = run_query("get_author_embeddings.sql")
    logger.info("Loaded all frontend datasets in %.3fs", time.perf_counter() - page_start)

    if page == "Overview":
        render_overview(books_df, authors_df)
    elif page == "Embeddings":
        entity = st.selectbox("Visualize embeddings for", ["Books", "Authors"])
        render_embeddings_view(book_embeddings if entity == "Books" else author_embeddings, entity)
    elif page == "Search":
        render_search_page(book_embeddings, author_embeddings, books_df, authors_df)
    else:
        render_sql_view()


if __name__ == "__main__":
    main()
