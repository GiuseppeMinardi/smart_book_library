import os
from typing import Any

from psycopg import connect
from psycopg.rows import dict_row

from api.models.google_responses import GoogleBookSlimResponse


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "admin")
    password = os.getenv("DB_PASSWORD", "secretpassword")
    database = os.getenv("DB_NAME", "appdb")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def get_db_connection():
    return connect(get_database_url(), autocommit=False, row_factory=dict_row)


def get_book_by_isbn(isbn: str) -> dict[str, Any] | None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, publisher, published_date, description,
                       page_count, print_type, language, info_link,
                       small_thumbnail, isbn
                FROM books
                WHERE isbn = %s
                """,
                (isbn,),
            )
            book = cur.fetchone()
            if book is None:
                return None

            book_id = book["id"]

            cur.execute(
                """
                SELECT a.name
                FROM authors a
                JOIN book_authors ba ON a.id = ba.author_id
                WHERE ba.book_id = %s
                ORDER BY a.name
                """,
                (book_id,),
            )
            book["authors"] = [row["name"] for row in cur.fetchall()]

            cur.execute(
                """
                SELECT c.name
                FROM categories c
                JOIN book_categories bc ON c.id = bc.category_id
                WHERE bc.book_id = %s
                ORDER BY c.name
                """,
                (book_id,),
            )
            book["categories"] = [row["name"] for row in cur.fetchall()]

            return book


def _insert_or_get_author_id(cur, name: str) -> int:
    cur.execute(
        """
        INSERT INTO authors (name)
        VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name,),
    )
    return cur.fetchone()["id"]


def _insert_or_get_category_id(cur, name: str) -> int:
    cur.execute(
        """
        INSERT INTO categories (name)
        VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name,),
    )
    return cur.fetchone()["id"]


def get_author_by_name(name: str, conn=None) -> dict[str, Any] | None:
    if conn is None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, birth_date, death_date, nationality, sex, bio, author_link
                    FROM authors
                    WHERE name = %s
                    """,
                    (name,),
                )
                return cur.fetchone()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, name, birth_date, death_date, nationality, sex, bio, author_link
            FROM authors
            WHERE name = %s
            """,
            (name,),
        )
        return cur.fetchone()


def save_author_record(author_info: dict[str, Any], conn=None) -> dict[str, Any]:
    if not author_info.get("name"):
        raise ValueError("Author name is required")

    if conn is None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO authors (
                        name, birth_date, death_date, nationality, sex, bio, author_link
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        birth_date = COALESCE(EXCLUDED.birth_date, authors.birth_date),
                        death_date = COALESCE(EXCLUDED.death_date, authors.death_date),
                        nationality = COALESCE(EXCLUDED.nationality, authors.nationality),
                        sex = COALESCE(EXCLUDED.sex, authors.sex),
                        bio = COALESCE(EXCLUDED.bio, authors.bio),
                        author_link = COALESCE(EXCLUDED.author_link, authors.author_link)
                    RETURNING id, name, birth_date, death_date, nationality, sex, bio, author_link
                    """,
                    (
                        author_info.get("name"),
                        author_info.get("birth_date"),
                        author_info.get("death_date"),
                        author_info.get("nationality"),
                        author_info.get("sex"),
                        author_info.get("biography"),
                        author_info.get("url"),
                    ),
                )
                author_row = cur.fetchone()
                conn.commit()
                return {
                    "id": author_row["id"],
                    "name": author_row["name"],
                    "birth_date": author_row["birth_date"],
                    "death_date": author_row["death_date"],
                    "nationality": author_row["nationality"],
                    "sex": author_row["sex"],
                    "bio": author_row["bio"],
                    "author_link": author_row["author_link"],
                }
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO authors (
                name, birth_date, death_date, nationality, sex, bio, author_link
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                birth_date = COALESCE(EXCLUDED.birth_date, authors.birth_date),
                death_date = COALESCE(EXCLUDED.death_date, authors.death_date),
                nationality = COALESCE(EXCLUDED.nationality, authors.nationality),
                sex = COALESCE(EXCLUDED.sex, authors.sex),
                bio = COALESCE(EXCLUDED.bio, authors.bio),
                author_link = COALESCE(EXCLUDED.author_link, authors.author_link)
            RETURNING id, name, birth_date, death_date, nationality, sex, bio, author_link
            """,
            (
                author_info.get("name"),
                author_info.get("birth_date"),
                author_info.get("death_date"),
                author_info.get("nationality"),
                author_info.get("sex"),
                author_info.get("biography"),
                author_info.get("url"),
            ),
        )
        author_row = cur.fetchone()
        return {
            "id": author_row["id"],
            "name": author_row["name"],
            "birth_date": author_row["birth_date"],
            "death_date": author_row["death_date"],
            "nationality": author_row["nationality"],
            "sex": author_row["sex"],
            "bio": author_row["bio"],
            "author_link": author_row["author_link"],
        }


def get_author_embedding(
    author_id: int, model_name: str, conn=None
) -> dict[str, Any] | None:
    if conn is None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT author_id, model_name
                    FROM author_embeddings
                    WHERE author_id = %s AND model_name = %s
                    """,
                    (author_id, model_name),
                )
                return cur.fetchone()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT author_id, model_name
            FROM author_embeddings
            WHERE author_id = %s AND model_name = %s
            """,
            (author_id, model_name),
        )
        return cur.fetchone()


def save_book_embedding(
    book_id: int,
    embedding: list[float],
    model_name: str = "nomic-embed-text",
    conn=None,
) -> None:
    if conn is None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO book_embeddings (book_id, model_name, vector)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (book_id, model_name) DO UPDATE SET
                        vector = EXCLUDED.vector,
                        created_at = CURRENT_TIMESTAMP
                    """,
                    (book_id, model_name, embedding),
                )
            conn.commit()
        return

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO book_embeddings (book_id, model_name, vector)
            VALUES (%s, %s, %s)
            ON CONFLICT (book_id, model_name) DO UPDATE SET
                vector = EXCLUDED.vector,
                created_at = CURRENT_TIMESTAMP
            """,
            (book_id, model_name, embedding),
        )


def save_author_embedding(
    author_id: int,
    embedding: list[float],
    model_name: str = "nomic-embed-text",
    conn=None,
) -> None:
    if conn is None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO author_embeddings (author_id, model_name, vector)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (author_id, model_name) DO UPDATE SET
                        vector = EXCLUDED.vector,
                        created_at = CURRENT_TIMESTAMP
                    """,
                    (author_id, model_name, embedding),
                )
            conn.commit()
        return

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO author_embeddings (author_id, model_name, vector)
            VALUES (%s, %s, %s)
            ON CONFLICT (author_id, model_name) DO UPDATE SET
                vector = EXCLUDED.vector,
                created_at = CURRENT_TIMESTAMP
            """,
            (author_id, model_name, embedding),
        )


def save_book_record(book: GoogleBookSlimResponse, conn=None) -> dict[str, Any]:
    authors = book.authors or []
    categories = book.categories or []

    unique_authors: list[str] = []
    seen_authors: set[str] = set()
    for author in authors:
        if author and author not in seen_authors:
            unique_authors.append(author)
            seen_authors.add(author)

    unique_categories: list[str] = []
    seen_categories: set[str] = set()
    for category in categories:
        if category and category not in seen_categories:
            unique_categories.append(category)
            seen_categories.add(category)

    if conn is None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                book_row = _save_book_record(cur, book)
            conn.commit()
            return book_row

    with conn.cursor() as cur:
        return _save_book_record(cur, book)


def _save_book_record(cur, book: GoogleBookSlimResponse) -> dict[str, Any]:
    authors = book.authors or []
    categories = book.categories or []

    unique_authors: list[str] = []
    seen_authors: set[str] = set()
    for author in authors:
        if author and author not in seen_authors:
            unique_authors.append(author)
            seen_authors.add(author)

    unique_categories: list[str] = []
    seen_categories: set[str] = set()
    for category in categories:
        if category and category not in seen_categories:
            unique_categories.append(category)
            seen_categories.add(category)

    cur.execute(
        """
        INSERT INTO books (
            title, publisher, published_date, description,
            page_count, print_type, language, info_link,
            small_thumbnail, isbn
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (isbn) DO UPDATE SET
            title = EXCLUDED.title,
            publisher = EXCLUDED.publisher,
            published_date = EXCLUDED.published_date,
            description = EXCLUDED.description,
            page_count = EXCLUDED.page_count,
            print_type = EXCLUDED.print_type,
            language = EXCLUDED.language,
            info_link = EXCLUDED.info_link,
            small_thumbnail = EXCLUDED.small_thumbnail
        RETURNING id, title, publisher, published_date,
                  description, page_count, print_type,
                  language, info_link, small_thumbnail, isbn
        """,
        (
            book.title,
            book.publisher,
            book.published_date,
            book.description,
            book.page_count,
            book.print_type,
            book.language,
            book.info_link,
            book.small_thumbnail,
            book.isbn,
        ),
    )
    book_row = cur.fetchone()
    book_id = book_row["id"]

    for author_name in unique_authors:
        author_id = _insert_or_get_author_id(cur, author_name)
        cur.execute(
            """
            INSERT INTO book_authors (book_id, author_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (book_id, author_id),
        )

    for category_name in unique_categories:
        category_id = _insert_or_get_category_id(cur, category_name)
        cur.execute(
            """
            INSERT INTO book_categories (book_id, category_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (book_id, category_id),
        )

    return {
        "id": book_id,
        "title": book_row["title"],
        "publisher": book_row["publisher"],
        "published_date": book_row["published_date"],
        "description": book_row["description"],
        "page_count": book_row["page_count"],
        "print_type": book_row["print_type"],
        "language": book_row["language"],
        "info_link": book_row["info_link"],
        "small_thumbnail": book_row["small_thumbnail"],
        "isbn": book_row["isbn"],
        "authors": unique_authors,
        "categories": unique_categories,
    }
