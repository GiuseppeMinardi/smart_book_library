from fastapi import FastAPI

from agents import get_agent
from agents.output_models import AuthorInfo

app = FastAPI()


@app.get("/author-info")
async def get_author_info(author_name: str) -> AuthorInfo:
    # 1. Await the run to get the AgentRunResult object
    # 2. Return the .output attribute which contains the actual AuthorInfo object
    author_info_model = get_agent("author_info")
    result = await author_info_model.run(author_name)
    return result.output


@app.get("/book-description")
async def get_book_description(book_title: str) -> str:
    # Extract .output to get the raw string
    book_description_model = get_agent("book_description")
    result = await book_description_model.run(book_title)
    return result.output


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