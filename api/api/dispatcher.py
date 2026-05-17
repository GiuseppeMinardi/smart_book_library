import asyncio
import inspect
from typing import Any

from api.db import get_book_by_isbn, save_book_record
from api.google_books import get_book_info_from_isbn
from api.models.isbn import ISBN


async def dispatch_book(isbn: ISBN) -> dict[str, Any]:
    existing_book = await asyncio.to_thread(get_book_by_isbn, isbn)
    if existing_book is not None:
        return existing_book

    # Support fetchers that may be sync (tests) or async (real implementation)
    maybe_awaitable = get_book_info_from_isbn(isbn, flatten_response=True)
    if inspect.isawaitable(maybe_awaitable):
        google_book = await maybe_awaitable
    else:
        google_book = maybe_awaitable

    # TODO: if description is missing, enrich book metadata using an LLM.
    # TODO: add author enrichment via LLM when stored author details are incomplete.
    saved_book = await asyncio.to_thread(save_book_record, google_book)
    return saved_book
