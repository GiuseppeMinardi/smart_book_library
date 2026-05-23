import urllib.parse

from fastapi import FastAPI, HTTPException

from agents import get_agent
from agents.embeddings import generate_embedding
from agents.output_models import AuthorInfo

app = FastAPI()


def _normalize_query_value(value: str) -> str:
    if "%" in value or "+" in value:
        try:
            return urllib.parse.unquote_plus(value)
        except Exception:
            return value
    return value


async def _run_agent_safely(agent_name: str, argument: str):
    agent = get_agent(agent_name)
    try:
        return await agent.run(argument)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Agent '{agent_name}' failed for input '{argument}': {exc}",
        ) from exc


@app.get("/author-info")
async def get_author_info(author_name: str) -> AuthorInfo:
    normalized_name = _normalize_query_value(author_name)
    result = await _run_agent_safely("author_info", normalized_name)
    return result.output


@app.get("/book-description")
async def get_book_description(book_title: str) -> str:
    normalized_title = _normalize_query_value(book_title)
    result = await _run_agent_safely("book_description", normalized_title)
    return result.output


@app.get("/embedding")
async def get_embedding(text: str, model_name: str = "nomic-embed-text") -> list[float]:
    normalized_text = _normalize_query_value(text)
    embedding = await generate_embedding(normalized_text, model_name)
    return embedding

@app.get("/")
async def root():

    return {
        "message": "Welcome to the Agents API!",
    }

@app.get("/health")
async def health_check() -> dict[str, str]:
    # FIX: Use the async '.run()' method and await it
    health_agent = get_agent("health")
    result = await health_agent.run("How's the system health?")
    response: str = result.output

    return {"status": response}