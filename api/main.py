import logging
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.dispatcher import ExternalServiceError, dispatch_book
from api.google_books import GoogleBooksServiceError, get_book_info_from_isbn
from api.models.isbn import ISBN


class BookIngestRequest(BaseModel):
    isbn: ISBN


class BookIngestResponse(BaseModel):
    id: int
    title: str
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    description: Optional[str] = None
    page_count: Optional[int] = None
    print_type: Optional[str] = None
    language: Optional[str] = None
    info_link: Optional[str] = None
    small_thumbnail: Optional[str] = None
    isbn: str
    authors: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)


app = FastAPI()
logger = logging.getLogger("api.startup")


@app.on_event("startup")
async def log_proxy_settings() -> None:
    proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"]
    configured_proxies = {key: os.getenv(key) for key in proxy_keys if os.getenv(key)}

    if configured_proxies:
        logger.info(
            "Proxy environment variables are configured for API container: %s",
            configured_proxies,
        )
    else:
        logger.info("No proxy environment variables are configured for API container.")


@app.exception_handler(ExternalServiceError)
async def external_service_exception_handler(
    request: Request, exc: ExternalServiceError
) -> JSONResponse:
    logger.error("External service failure: %s", exc)
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(GoogleBooksServiceError)
async def google_books_exception_handler(
    request: Request, exc: GoogleBooksServiceError
) -> JSONResponse:
    logger.error("Google Books service failure: %s", exc)
    return JSONResponse(status_code=502, content={"detail": str(exc)})

app.add_api_route("/retrieve-book", endpoint=get_book_info_from_isbn, methods=["POST"])


@app.post("/books/ingest", response_model=BookIngestResponse)
async def ingest_book_endpoint(request: BookIngestRequest):
    try:
        return await dispatch_book(request.isbn)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during book ingest")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


if __name__ == "__main__":
    pass
