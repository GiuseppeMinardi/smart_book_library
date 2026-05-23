from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import psycopg
import streamlit as st
from psycopg.rows import dict_row

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("frontend")

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    logger.warning(
        "Warning: python-dotenv is not installed, environment variables will not be loaded from .env file."
    )
    pass


BASE_DIR = Path(__file__).resolve().parent
SQL_DIR = BASE_DIR / "sql"

def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "postgres"),
        row_factory=dict_row,
    )

def main():
    st.title("Smart Book Library")

    logger.info("Connecting to the database...")
    db_connection = get_db_connection()

    books_query = SQL_DIR.joinpath("get_books.sql").read_text()
    authors_query = SQL_DIR.joinpath("get_authors.sql").read_text()

    with db_connection.cursor() as cursor:
        logger.info("Executing SQL queries to fetch books and authors...")
        books = cursor.execute(books_query).fetchall()
        authors: list[dict] = cursor.execute(authors_query).fetchall()

    st.subheader("Books")
    books_df = pd.DataFrame(books).assign(
        years_past=lambda df: pd.Timestamp.now().year - df["publishing_year"]
    )

    number_of_books = books_df.isbn.nunique()
    avg_book_age = books_df.years_past.mean()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Number of Books", number_of_books)
    with col2:
        st.metric("Average Book Age", f"{avg_book_age:.2f} years")

    language_count = books_df["language"].value_counts().sort_values(ascending=False)
    fig = px.bar(
        data_frame=language_count,
        x=language_count.index,
        y=language_count.values,
        labels={"x": "Language", "y": "Count"},
        title="Books by Language",
    )
    st.plotly_chart(fig)

    st.dataframe(books_df)

    st.subheader("Authors")
    authors_df = pd.DataFrame(authors).assign(
        is_alive=lambda df: df["death_date"].isna(),
        number_of_books=lambda df: df["name"].map(
            books_df.explode("authors").groupby("authors").size()
        ),
    )

    percent_alive = authors_df.is_alive.value_counts(normalize=True).get(True, 0) * 100
    percent_male = authors_df["sex"].value_counts(normalize=True).get("M", 0) * 100
    # pretty visualizations
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Percentage of Living Authors", f"{percent_alive:.2f}%")
    with col2:
        st.metric("Percentage of Male Authors", f"{percent_male:.2f}%")
    with col3:
        st.metric("Total Authors", len(authors_df))

    # plotly bargraph of nationalities
    nationality_counts = (
        authors_df["nationality"].value_counts().sort_values(ascending=False)
    )
    fig = px.bar(
        data_frame=nationality_counts,
        x=nationality_counts.index,
        y=nationality_counts.values,
        labels={"x": "Nationality", "y": "Count"},
        title="Authors by Nationality",
    )
    st.plotly_chart(fig)

    st.dataframe(authors_df.sort_values("number_of_books", ascending=False))

    logger.info("Finished displaying data.")

if __name__ == "__main__":
    main()