import asyncio
import os

import httpx
import pytest

import api.dispatcher as dispatcher
from api.dispatcher import (
    get_author_info_from_agentic,
    get_book_description_from_agentic,
    get_embedding_from_agentic,
)

AGENTIC_API_URL = os.getenv("AGENTIC_API_URL", "http://127.0.0.1:8001")
dispatcher.AGENTIC_API_URL = AGENTIC_API_URL


def _is_agentic_service_healthy(url: str) -> bool:
    try:
        health_url = f"{url.rstrip('/')}/health"
        response = httpx.get(health_url, timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


SERVICE_AVAILABLE = _is_agentic_service_healthy(AGENTIC_API_URL)


@pytest.mark.skipif(
    not SERVICE_AVAILABLE,
    reason=(
        "Skipping integration test because the live AGENTIC_API_URL service is not reachable. "
        "Set AGENTIC_API_URL to the running agentic_calls container endpoint if needed."
    ),
)
def test_agentic_api_endpoints_live():
    description = asyncio.run(get_book_description_from_agentic("Pride and Prejudice"))
    assert isinstance(description, str)
    assert len(description.strip()) > 10

    author_info = asyncio.run(get_author_info_from_agentic("Jane Austen"))
    assert isinstance(author_info, dict)
    assert author_info.get("name") in {"Jane Austen", "Austen", "Jane Austen"} or author_info.get("biography")
    assert isinstance(author_info.get("biography"), str)
    assert len(author_info.get("biography", "").strip()) > 10

    embedding = asyncio.run(get_embedding_from_agentic("Testing embedding generation from live agentic service."))
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(value, (int, float)) for value in embedding)
