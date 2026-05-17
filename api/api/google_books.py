import asyncio
import os

import requests

from .logger import logger
from .models import ISBN, GoogleBookSlimResponse, GoogleBooksResponse

_GOOGLE_BOOKS_API_URL = os.getenv(
    "GOOGLE_BOOKS_API_URL", "https://www.googleapis.com/books/v1/volumes"
)
_GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")


async def get_book_info_from_isbn(
    isbn: ISBN,
    flatten_response: bool = False,
    google_books_api_url: str | None = None,
    google_books_api_key: str | None = None,
) -> GoogleBooksResponse | GoogleBookSlimResponse:
    if google_books_api_url is None:
        google_books_api_url = _GOOGLE_BOOKS_API_URL
    if google_books_api_key is None:
        if _GOOGLE_BOOKS_API_KEY is not None:
            google_books_api_key = _GOOGLE_BOOKS_API_KEY
        else:
            raise ValueError("Google Books API key is required but not provided")

    get_book_url = (
        f"{google_books_api_url}?q=isbn:{str(isbn)}&key={google_books_api_key}"
    )

    logger.debug(
        f"Fetching book info from Google Books API for ISBN {isbn} using URL: {get_book_url}"
    )
    response: requests.Response = await asyncio.to_thread(requests.get, get_book_url)
    logger.debug(
        f"Received response from Google Books API for ISBN {isbn}: {response.status_code} - {response.text[:200]}..."
    )  # Log status code and first 200 chars of response text

    if response.status_code != 200:
        logger.error(
            f"Failed to fetch book info from Google Books API: {response.status_code} - {response.text}"
        )
        raise ValueError(
            f"Failed to fetch book info from Google Books API: {response.status_code} - {response.text}"
        )

    response_json = response.json()
    if isinstance(response_json, dict) and response_json.get("items") is not None:
        if not response_json["items"]:
            raise ValueError("No books found for the provided ISBN")
        response_json = response_json["items"][0]

    full_response = GoogleBooksResponse.model_validate(response_json)

    if flatten_response:
        logger.debug(f"Flattening Google Books API response for ISBN {isbn}")
        slim_response = {
            "kind": full_response.kind,
            "title": full_response.volume_info.title,
            "authors": full_response.volume_info.authors,
            "publisher": full_response.volume_info.publisher,
            "publishedDate": full_response.volume_info.published_date,
            "description": full_response.volume_info.description,
            "pageCount": full_response.volume_info.page_count,
            "categories": full_response.volume_info.categories,
            "printType": full_response.volume_info.print_type,
            "language": full_response.volume_info.language,
            "infoLink": full_response.volume_info.info_link,
            "smallThumbnail": (
                full_response.volume_info.image_links.small_thumbnail
                if full_response.volume_info.image_links
                else None
            ),
            "isbn": isbn,
        }

        return GoogleBookSlimResponse.model_validate(slim_response)
    else:
        logger.debug(f"Returning full Google Books API response for ISBN {isbn}")
        return full_response
