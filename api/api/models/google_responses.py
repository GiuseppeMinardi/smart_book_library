from typing import List, Optional

from pydantic import BaseModel, Field


class IndustryIdentifier(BaseModel):
    type: str = Field(
        ..., description="Type of industry identifier (e.g., ISBN_13, ISBN_10)."
    )
    identifier: str = Field(
        ..., description="The identifier value associated with the type."
    )


class ImageLinks(BaseModel):
    small_thumbnail: Optional[str] = Field(
        None,
        alias="smallThumbnail",
        description="URL for the small thumbnail image of the book cover.",
    )
    thumbnail: Optional[str] = Field(
        None,
        alias="thumbnail",
        description="URL for the standard thumbnail image of the book cover.",
    )


class VolumeInfo(BaseModel):
    title: str = Field(..., description="The title of the book.")
    authors: Optional[List[str]] = Field(
        None, description="List of authors of the book."
    )
    publisher: Optional[str] = Field(None, description="The publisher of the book.")
    published_date: Optional[str] = Field(
        None,
        alias="publishedDate",
        description="Date of publication (ISO 8601 format).",
    )
    description: Optional[str] = Field(
        None, description="Summary or description of the book."
    )
    industry_identifiers: Optional[List[IndustryIdentifier]] = Field(
        None,
        alias="industryIdentifiers",
        description="Industry standard identifiers like ISBN.",
    )
    page_count: Optional[int] = Field(
        None, alias="pageCount", description="Total number of pages in the book."
    )
    print_type: Optional[str] = Field(
        None,
        alias="printType",
        description="Type of printed material (e.g., BOOK, MAGAZINE).",
    )
    categories: Optional[List[str]] = Field(
        None, description="Book categories or genres."
    )
    maturity_rating: Optional[str] = Field(
        None,
        alias="maturityRating",
        description="Book maturity rating (e.g., NOT_MATURE).",
    )
    content_version: Optional[str] = Field(
        None, alias="contentVersion", description="Content version tag for the book."
    )
    image_links: Optional[ImageLinks] = Field(
        None, alias="imageLinks", description="Links to cover images."
    )
    language: Optional[str] = Field(
        None, description="Language code of the book (ISO 639-1)."
    )
    info_link: Optional[str] = Field(
        None, alias="infoLink", description="URL for additional book information."
    )


class GoogleBooksResponse(BaseModel):
    kind: str = Field(..., description="The resource type (usually 'books#volume').")
    id_: str = Field(
        ..., alias="id", description="Unique identifier for the book volume."
    )
    etag: str = Field(..., description="ETag of the item for version control.")
    self_link: str = Field(
        ..., alias="selfLink", description="API link for the item resource."
    )
    volume_info: VolumeInfo = Field(
        ...,
        alias="volumeInfo",
        description="Metadata and descriptive info about the volume.",
    )


class GoogleBookSlimResponse(BaseModel):
    """A slimmed-down representation of a Google Books API response.

    This class provides a subset of fields from the full Google Books API response,
    focusing on key metadata about a book.

    Attributes
    ----------
    kind : Optional[str]
        The resource type (e.g., 'books#volume').
    title : Optional[str]
        The title of the book.
    authors : Optional[list[str]]
        List of authors of the book.
    publisher : Optional[str]
        The publisher of the book.
    published_date : Optional[str]
        Date of publication (ISO 8601 format).
    description : Optional[str]
        Summary or description of the book.
    page_count : Optional[str]
        Total number of pages in the book.
    categories : Optional[list[str]]
        Book categories or genres.
    print_type : Optional[str]
        Type of printed material (e.g., BOOK, MAGAZINE).
    language : Optional[str]
        Language code of the book (ISO 639-1).
    info_link : Optional[str]
        URL for additional book information.
    small_thumbnail : Optional[str]
        URL for the small thumbnail image of the book cover.
    """

    kind: Optional[str] = Field(
        alias="kind", description="The resource type (e.g., 'books#volume')."
    )
    title: Optional[str] = Field(alias="title", description="The title of the book.")
    authors: Optional[list[str]] = Field(
        alias="authors", description="List of authors of the book."
    )
    publisher: Optional[str] = Field(
        alias="publisher", description="The publisher of the book."
    )
    published_date: Optional[str] = Field(
        alias="publishedDate", description="Date of publication (ISO 8601 format)."
    )
    description: Optional[str] = Field(
        alias="description", description="Summary or description of the book."
    )
    page_count: Optional[int] = Field(
        alias="pageCount", description="Total number of pages in the book."
    )
    categories: Optional[list[str]] = Field(
        alias="categories", description="Book categories or genres."
    )
    print_type: Optional[str] = Field(
        alias="printType",
        description="Type of printed material (e.g., BOOK, MAGAZINE).",
    )
    language: Optional[str] = Field(
        alias="language", description="Language code of the book (ISO 639-1)."
    )
    info_link: Optional[str] = Field(
        alias="infoLink", description="URL for additional book information."
    )
    small_thumbnail: Optional[str] = Field(
        alias="smallThumbnail",
        description="URL for the small thumbnail image of the book cover.",
    )
    isbn: str = Field(description="ISBN identifier for the book.")
