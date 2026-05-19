import asyncio
import inspect
import os
from typing import Any

import httpx

from api.db import (
    get_author_by_name,
    get_author_embedding,
    get_book_by_isbn,
    get_db_connection,
    save_author_embedding,
    save_author_record,
    save_book_embedding,
    save_book_record,
)
from api.google_books import get_book_info_from_isbn
from api.models.isbn import ISBN


class ExternalServiceError(Exception):
    """Base exception for external service failures."""


class AgenticServiceError(ExternalServiceError):
    """Raised when the agentic service cannot fulfill a request."""


AGENTIC_API_URL = os.getenv("AGENTIC_API_URL", "http://agentic_calls:8000")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "nomic-embed-text")


async def _fetch_from_agentic(endpoint: str, params: dict[str, str]) -> Any:
    url = f"{AGENTIC_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            response = exc.response
            status = response.status_code if response is not None else "unknown"
            body = response.text if response is not None else str(exc)
            raise AgenticServiceError(
                f"Agentic service returned {status} for {endpoint}: {body}"
            ) from exc
        except httpx.RequestError as exc:
            raise AgenticServiceError(
                f"Agentic service request failed for {endpoint}: {exc}"
            ) from exc


async def get_book_description_from_agentic(book_title: str) -> str:
    return await _fetch_from_agentic("book-description", {"book_title": book_title})


async def get_author_info_from_agentic(author_name: str) -> dict[str, Any]:
    return await _fetch_from_agentic("author-info", {"author_name": author_name})


async def get_embedding_from_agentic(
    text: str, model_name: str = EMBEDDING_MODEL_NAME
) -> list[float]:
    return await _fetch_from_agentic(
        "embedding", {"text": text, "model_name": model_name}
    )


async def dispatch_book(isbn: ISBN) -> dict[str, Any]:
    existing_book = await asyncio.to_thread(get_book_by_isbn, isbn)
    if existing_book is not None:
        return existing_book

    maybe_awaitable = get_book_info_from_isbn(isbn, flatten_response=True)
    if inspect.isawaitable(maybe_awaitable):
        google_book = await maybe_awaitable
    else:
        google_book = maybe_awaitable

    if not google_book.description:
        if not google_book.title:
            raise ValueError("Book title is required to generate a description")
        google_book.description = await get_book_description_from_agentic(
            google_book.title
        )

    saved_book = None
    embedding_source = google_book.description or google_book.title
    book_embedding = None
    if embedding_source:
        book_embedding = await get_embedding_from_agentic(embedding_source)

    authors = google_book.authors or []
    author_enrichment: list[dict[str, Any]] = []
    for author_name in authors:
        if not author_name:
            continue

        author = await asyncio.to_thread(get_author_by_name, author_name)
        author_info = None
        author_embedding = None

        if author is None or not author.get("bio"):
            author_info = await get_author_info_from_agentic(author_name)
            bio_text = author_info.get("biography")
            if bio_text:
                author_embedding = await get_embedding_from_agentic(bio_text)
        else:
            embedding_exists = await asyncio.to_thread(
                get_author_embedding, author["id"], EMBEDDING_MODEL_NAME
            )
            if embedding_exists is None and author.get("bio"):
                author_embedding = await get_embedding_from_agentic(author["bio"])

        author_enrichment.append(
            {
                "name": author_name,
                "author_info": author_info,
                "author_embedding": author_embedding,
            }
        )

    with get_db_connection() as conn:
        try:
            saved_book = save_book_record(google_book, conn=conn)
            if book_embedding is not None:
                save_book_embedding(saved_book["id"], book_embedding, conn=conn)

            for author_entry in author_enrichment:
                author_info = author_entry["author_info"]
                author_name = author_entry["name"]
                if author_info is not None:
                    author = save_author_record(author_info, conn=conn)
                else:
                    author = get_author_by_name(author_name, conn=conn)
                    if author is None:
                        author = save_author_record({"name": author_name}, conn=conn)

                if author_entry["author_embedding"] is not None:
                    save_author_embedding(
                        author["id"], author_entry["author_embedding"], conn=conn
                    )

            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return saved_book
