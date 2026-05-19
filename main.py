import argparse
import asyncio
import os
from typing import Any

import httpx


async def ingest_isbn(api_url: str, isbn: str, client: httpx.AsyncClient) -> dict[str, Any]:
    url = api_url.rstrip("/") + "/books/ingest"
    response = await client.post(url, json={"isbn": isbn})
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to ingest ISBN {isbn}: {response.status_code} {response.text}"
        )
    return response.json()


async def ingest_isbns(api_url: str, isbns: list[str]) -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [ingest_isbn(api_url, isbn, client) for isbn in isbns]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for isbn, result in zip(isbns, results):
        if isinstance(result, Exception):
            print(f"ISBN {isbn}: ERROR -> {result}")
        else:
            print(f"ISBN {isbn}: SUCCESS")
            print(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest ISBNs into the smart book library API asynchronously."
    )
    parser.add_argument(
        "isbn",
        nargs="+",
        help="One or more ISBN values to ingest.",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_URL", "http://localhost:8000"),
        help="Base URL of the API service (default: http://localhost:8000).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(ingest_isbns(args.api_url, args.isbn))


if __name__ == "__main__":
    main()
