import pytest
from pydantic import BaseModel

from api.models.isbn import ISBN, validate_isbn


def test_validate_isbn_accepts_valid_isbn_13():
    assert validate_isbn("9780306406157") == "9780306406157"


def test_validate_isbn_accepts_valid_isbn_10_with_x():
    assert validate_isbn("0-306-40615-2") == "0306406152"


def test_validate_isbn_strips_hyphens_and_spaces():
    assert validate_isbn("978 0-306-40615 7") == "9780306406157"


def test_validate_isbn_rejects_invalid_type():
    with pytest.raises(ValueError, match="ISBN must be a string or an integer"):
        validate_isbn(["9780306406157"])


def test_validate_isbn_rejects_invalid_length():
    with pytest.raises(ValueError, match="ISBN must be 10 or 13 digits"):
        validate_isbn("1234")


def test_validate_isbn_rejects_invalid_check_digit():
    with pytest.raises(ValueError, match="Invalid ISBN-13 check digit"):
        validate_isbn("9780306406158")


def test_isbn_type_works_in_pydantic_model():
    class Book(BaseModel):
        isbn: ISBN

    book = Book(isbn="0-306-40615-2")
    assert book.isbn == "0306406152"
