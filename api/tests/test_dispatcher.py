from fastapi.testclient import TestClient

from api.dispatcher import AgenticServiceError
from api.models.google_responses import GoogleBookSlimResponse
from main import app


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self

    def execute(self, *args, **kwargs):
        return None

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def commit(self):
        return None

    def rollback(self):
        return None


client = TestClient(app)


def test_ingest_new_book(monkeypatch):
    monkeypatch.setattr("api.dispatcher.get_book_by_isbn", lambda isbn: None)

    fake_book = GoogleBookSlimResponse.model_validate(
        {
            "kind": "books#volume",
            "title": "Example Book",
            "authors": ["Jane Doe"],
            "publisher": "Example Publisher",
            "publishedDate": "2025-01-01",
            "description": "A test book.",
            "pageCount": 123,
            "categories": ["Fiction"],
            "printType": "BOOK",
            "language": "en",
            "infoLink": "https://example.com/book",
            "smallThumbnail": "https://example.com/thumb.jpg",
            "isbn": "9780306406157",
        }
    )

    monkeypatch.setattr("api.dispatcher.get_book_info_from_isbn", lambda isbn, flatten_response=True: fake_book)
    monkeypatch.setattr("api.dispatcher.get_db_connection", lambda: FakeConnection())
    monkeypatch.setattr(
        "api.dispatcher.save_book_record",
        lambda book, conn=None: {
            "id": 1,
            "title": book.title,
            "publisher": book.publisher,
            "published_date": book.published_date,
            "description": book.description,
            "page_count": book.page_count,
            "print_type": book.print_type,
            "language": book.language,
            "info_link": book.info_link,
            "small_thumbnail": book.small_thumbnail,
            "isbn": book.isbn,
            "authors": book.authors or [],
            "categories": book.categories or [],
        },
    )

    async def fake_embedding(text, model_name="nomic-embed-text"):
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr("api.dispatcher.get_embedding_from_agentic", fake_embedding)
    monkeypatch.setattr(
        "api.dispatcher.save_book_embedding", lambda book_id, embedding, conn=None: None
    )
    monkeypatch.setattr("api.dispatcher.get_author_by_name", lambda name: None)

    async def fake_author_info(author_name):
        return {
            "name": author_name,
            "birth_date": None,
            "death_date": None,
            "nationality": None,
            "sex": None,
            "biography": "Generated author biography.",
            "url": None,
        }

    monkeypatch.setattr("api.dispatcher.get_author_info_from_agentic", fake_author_info)
    monkeypatch.setattr(
        "api.dispatcher.save_author_record",
        lambda author_info, conn=None: {
            "id": 1,
            "name": author_info["name"],
            "bio": author_info.get("biography"),
        },
    )
    monkeypatch.setattr(
        "api.dispatcher.get_author_embedding",
        lambda author_id, model_name, conn=None: None,
    )
    monkeypatch.setattr(
        "api.dispatcher.save_author_embedding",
        lambda author_id, embedding, conn=None: None,
    )

    response = client.post("/books/ingest", json={"isbn": "9780306406157"})
    assert response.status_code == 200
    assert response.json()["isbn"] == "9780306406157"
    assert response.json()["title"] == "Example Book"
    assert response.json()["authors"] == ["Jane Doe"]


def test_ingest_returns_502_for_agentic_failure(monkeypatch):
    monkeypatch.setattr("api.dispatcher.get_book_by_isbn", lambda isbn: None)

    fake_book = GoogleBookSlimResponse.model_validate(
        {
            "kind": "books#volume",
            "title": "Example Book",
            "authors": ["Jane Doe"],
            "publisher": "Example Publisher",
            "publishedDate": "2025-01-01",
            "description": None,
            "pageCount": 123,
            "categories": ["Fiction"],
            "printType": "BOOK",
            "language": "en",
            "infoLink": "https://example.com/book",
            "smallThumbnail": "https://example.com/thumb.jpg",
            "isbn": "9780306406157",
        }
    )

    monkeypatch.setattr(
        "api.dispatcher.get_book_info_from_isbn",
        lambda isbn, flatten_response=True: fake_book,
    )

    async def fail_description(book_title):
        raise AgenticServiceError("Agentic description service failed")

    monkeypatch.setattr(
        "api.dispatcher.get_book_description_from_agentic",
        fail_description,
    )

    response = client.post("/books/ingest", json={"isbn": "9780306406157"})
    assert response.status_code == 502
    assert "Agentic description service failed" in response.json()["detail"]


def test_ingest_new_book_generates_description_and_author(monkeypatch):
    monkeypatch.setattr("api.dispatcher.get_book_by_isbn", lambda isbn: None)

    fake_book = GoogleBookSlimResponse.model_validate(
        {
            "kind": "books#volume",
            "title": "Example Book",
            "authors": ["Jane Doe"],
            "publisher": "Example Publisher",
            "publishedDate": "2025-01-01",
            "description": None,
            "pageCount": 123,
            "categories": ["Fiction"],
            "printType": "BOOK",
            "language": "en",
            "infoLink": "https://example.com/book",
            "smallThumbnail": "https://example.com/thumb.jpg",
            "isbn": "9780306406157",
        }
    )

    monkeypatch.setattr(
        "api.dispatcher.get_book_info_from_isbn",
        lambda isbn, flatten_response=True: fake_book,
    )
    monkeypatch.setattr("api.dispatcher.get_db_connection", lambda: FakeConnection())

    async def fake_description(title):
        return "Generated description from LLM."

    async def fake_embedding(text, model_name="nomic-embed-text"):
        return [0.1, 0.2, 0.3]

    async def fake_author_info(author_name):
        return {
            "name": author_name,
            "birth_date": None,
            "death_date": None,
            "nationality": None,
            "sex": None,
            "biography": "Generated biography for the author.",
            "url": None,
        }

    monkeypatch.setattr(
        "api.dispatcher.get_book_description_from_agentic", fake_description
    )
    monkeypatch.setattr("api.dispatcher.get_embedding_from_agentic", fake_embedding)
    monkeypatch.setattr("api.dispatcher.get_author_info_from_agentic", fake_author_info)
    monkeypatch.setattr(
        "api.dispatcher.save_book_record",
        lambda book, conn=None: {
            "id": 1,
            "title": book.title,
            "publisher": book.publisher,
            "published_date": book.published_date,
            "description": book.description,
            "page_count": book.page_count,
            "print_type": book.print_type,
            "language": book.language,
            "info_link": book.info_link,
            "small_thumbnail": book.small_thumbnail,
            "isbn": book.isbn,
            "authors": book.authors or [],
            "categories": book.categories or [],
        },
    )
    monkeypatch.setattr("api.dispatcher.get_author_by_name", lambda name: None)
    monkeypatch.setattr(
        "api.dispatcher.save_author_record",
        lambda author_info, conn=None: {
            "id": 2,
            "name": author_info["name"],
            "bio": author_info.get("biography"),
        },
    )
    monkeypatch.setattr(
        "api.dispatcher.get_author_embedding",
        lambda author_id, model_name, conn=None: None,
    )
    monkeypatch.setattr(
        "api.dispatcher.save_book_embedding", lambda book_id, embedding, conn=None: None
    )
    monkeypatch.setattr(
        "api.dispatcher.save_author_embedding",
        lambda author_id, embedding, conn=None: None,
    )

    response = client.post("/books/ingest", json={"isbn": "9780306406157"})
    assert response.status_code == 200
    assert response.json()["description"] == "Generated description from LLM."
    assert response.json()["authors"] == ["Jane Doe"]


def test_ingest_existing_book_returns_cached_record(monkeypatch):
    existing_book = {
        "id": 1,
        "title": "Cached Book",
        "publisher": "Cached Publisher",
        "published_date": "2024-01-01",
        "description": "Already stored.",
        "page_count": 200,
        "print_type": "BOOK",
        "language": "en",
        "info_link": "https://example.com/cached",
        "small_thumbnail": "https://example.com/cached.jpg",
        "isbn": "9780306406157",
        "authors": ["Cached Author"],
        "categories": ["Cached Category"],
    }

    monkeypatch.setattr("api.dispatcher.get_book_by_isbn", lambda isbn: existing_book)

    def fail_fetch(*args, **kwargs):
        raise AssertionError("Google Books should not be called for cached ISBN")

    monkeypatch.setattr("api.dispatcher.get_book_info_from_isbn", fail_fetch)

    response = client.post("/books/ingest", json={"isbn": "9780306406157"})
    assert response.status_code == 200
    assert response.json() == existing_book
