from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from api.dispatcher import dispatch_book
from api.google_books import get_book_info_from_isbn
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

app.add_api_route("/retrieve-book", endpoint=get_book_info_from_isbn, methods=["POST"])


@app.post("/books/ingest", response_model=BookIngestResponse)
async def ingest_book_endpoint(request: BookIngestRequest):
    try:
        return await dispatch_book(request.isbn)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    pass
