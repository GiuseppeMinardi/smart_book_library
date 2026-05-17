from fastapi.testclient import TestClient

from api.models.google_responses import GoogleBookSlimResponse
from main import app

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
    monkeypatch.setattr(
        "api.dispatcher.save_book_record",
        lambda book: {
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

    response = client.post("/books/ingest", json={"isbn": "9780306406157"})
    assert response.status_code == 200
    assert response.json()["isbn"] == "9780306406157"
    assert response.json()["title"] == "Example Book"
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
