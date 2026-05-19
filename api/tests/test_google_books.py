import asyncio

import pytest

from api import google_books


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        return self._json_data


def test_get_book_info_from_isbn_raises_without_api_key(monkeypatch):
    monkeypatch.setattr(google_books, "_GOOGLE_BOOKS_API_KEY", None)

    with pytest.raises(ValueError, match="Google Books API key is required"):
        asyncio.run(google_books.get_book_info_from_isbn(isbn="9780306406157"))


def test_get_book_info_from_isbn_raises_for_non_200_response(monkeypatch):
    monkeypatch.setattr(google_books, "_GOOGLE_BOOKS_API_KEY", "fake-key")

    def fake_get(url, *args, **kwargs):
        return FakeResponse(404, {"error": {"message": "Not found"}}, text="Not found")

    monkeypatch.setattr(google_books.requests, "get", fake_get)

    with pytest.raises(
        google_books.GoogleBooksServiceError,
        match="Failed to fetch book info from Google Books API",
    ):
        asyncio.run(google_books.get_book_info_from_isbn(isbn="9780306406157"))


def test_get_book_info_from_isbn_returns_full_response(monkeypatch):
    monkeypatch.setattr(google_books, "_GOOGLE_BOOKS_API_KEY", "fake-key")

    expected_json = {
        "kind": "books#volumes",
        "totalItems": 1,
        "items": [
            {
                "kind": "books#volume",
                "id": "OXb0AAAACAAJ",
                "etag": "abc123",
                "selfLink": "https://www.googleapis.com/books/v1/volumes/OXb0AAAACAAJ",
                "volumeInfo": {"title": "Example Book"},
            }
        ],
    }

    def fake_get(url, *args, **kwargs):
        assert "q=isbn:9780306406157" in url
        assert "key=fake-key" in url
        return FakeResponse(200, expected_json, text=str(expected_json))

    monkeypatch.setattr(google_books.requests, "get", fake_get)

    result = asyncio.run(
        google_books.get_book_info_from_isbn(
            isbn="9780306406157",
            flatten_response=False,
            google_books_api_url="https://example.com",
            google_books_api_key="fake-key",
        )
    )

    assert result.kind == "books#volume"
    assert result.volume_info.title == "Example Book"


def test_get_book_info_from_isbn_returns_slim_response(monkeypatch):
    monkeypatch.setattr(google_books, "_GOOGLE_BOOKS_API_KEY", "fake-key")

    expected_json = {
        "kind": "books#volumes",
        "totalItems": 1,
        "items": [
            {
                "kind": "books#volume",
                "id": "OXb0AAAACAAJ",
                "etag": "abc123",
                "selfLink": "https://www.googleapis.com/books/v1/volumes/OXb0AAAACAAJ",
                "volumeInfo": {
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
                    "imageLinks": {"smallThumbnail": "https://example.com/thumb.jpg"},
                },
            }
        ],
    }

    def fake_get(url, *args, **kwargs):
        return FakeResponse(200, expected_json, text=str(expected_json))

    monkeypatch.setattr(google_books.requests, "get", fake_get)

    result = asyncio.run(
        google_books.get_book_info_from_isbn(
            isbn="9780306406157",
            flatten_response=True,
            google_books_api_url="https://example.com",
            google_books_api_key="fake-key",
        )
    )

    assert result.title == "Example Book"
    assert result.authors == ["Jane Doe"]
    assert result.isbn == "9780306406157"


def test_get_book_info_from_isbn_raises_when_items_is_empty(monkeypatch):
    monkeypatch.setattr(google_books, "_GOOGLE_BOOKS_API_KEY", "fake-key")

    expected_json = {
        "kind": "books#volumes",
        "totalItems": 0,
        "items": [],
    }

    def fake_get(url, *args, **kwargs):
        return FakeResponse(200, expected_json, text=str(expected_json))

    monkeypatch.setattr(google_books.requests, "get", fake_get)

    with pytest.raises(ValueError, match="No books found for the provided ISBN"):
        asyncio.run(
            google_books.get_book_info_from_isbn(
                isbn="9780306406157",
                flatten_response=True,
                google_books_api_url="https://example.com",
                google_books_api_key="fake-key",
            )
        )
