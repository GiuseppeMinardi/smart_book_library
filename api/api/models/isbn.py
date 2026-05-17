import re
from typing import Annotated

from pydantic import BeforeValidator


def validate_isbn(value: str | int) -> str:
    if not isinstance(value, (str, int)):
        raise ValueError("ISBN must be a string or an integer")
    
    # Convert to string and strip hyphens/spaces
    isbn_str = re.sub(pattern=r"[- ]", repl="", string=str(value)).upper()
    
    # Check absolute format requirements
    if not re.match(pattern=r"^(?:\d{9}[\dX]|\d{13})$", string=isbn_str):
        raise ValueError("ISBN must be 10 or 13 digits (optionally ending in 'X' for ISBN-10)")
    
    # Validate mathematical check digit
    if len(isbn_str) == 10:
        # ISBN-10 Check Digit Validation
        total = sum((10 - i) * (10 if char == 'X' else int(char)) for i, char in enumerate(iterable=isbn_str))
        if total % 11 != 0:
            raise ValueError("Invalid ISBN-10 check digit")
    else:
        # ISBN-13 Check Digit Validation
        total = sum(int(char) * (3 if i % 2 else 1) for i, char in enumerate(iterable=isbn_str))
        if total % 10 != 0:
            raise ValueError("Invalid ISBN-13 check digit")
            
    return isbn_str

# Define the reusable Pydantic Custom Type
ISBN = Annotated[str, BeforeValidator(validate_isbn)]