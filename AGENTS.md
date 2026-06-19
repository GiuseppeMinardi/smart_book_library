# AI Agent Instructions for smart_book_library

## Purpose
This repository implements a small Python microservices example with three primary components:
- `api/`: FastAPI service for book ingestion, Google Books lookup, and pgvector similarity queries
- `agents/`: FastAPI service for LLM-backed agent workflows, local Ollama model serving, and embeddings
- `frontend/`: Streamlit dashboard that visualizes books and authors using PostgreSQL data

The root also includes a Docker Compose setup that starts the services, database, Ollama, and Phoenix telemetry.

## Key facts for code changes
- Each service is isolated in its folder and has its own `pyproject.toml` and `.env`.
- The `api` service depends on the `agents` service for embeddings and agent workflows.
- The `frontend` service reads the same PostgreSQL database as the `api` service.
- The root `main.py` is a utility for bulk ISBN ingestion and is not part of the service runtime.

## Recommended commands
- Start the full stack:
  - `docker compose up --build`
- API development:
  - `cd api`
  - `python -m venv .venv`
  - `.venv\Scripts\activate`
  - `pip install -e .`
  - `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- Agents development:
  - `cd agents`
  - `python -m venv .venv`
  - `.venv\Scripts\activate`
  - `pip install -e .`
  - `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- Frontend development:
  - `cd frontend`
  - `python -m venv .venv`
  - `.venv\Scripts\activate`
  - `pip install -e .`
  - `streamlit run main.py --server.port 8501`
- Tests:
  - `cd api && pytest`

## Important files and directories
- `docker-compose.yml`: orchestrates `books_db`, `db_api`, `agentic_calls`, `frontend`, `ollama`, and `phoenix`
- `db/init.sql`: initializes the PostgreSQL database schema
- `api/main.py`: REST entrypoints for book ingestion and similarity
- `api/db.py`: database connection and query utilities
- `agents/main.py`: agent endpoint router and workflow integration
- `agents/prompts/`: agent prompt templates used by the agents service
- `frontend/main.py`: Streamlit app and dashboard logic
- `frontend/sql/`: SQL queries used by the frontend dashboard

## Service-specific behavior
- `api` uses PostgreSQL with `pgvector` and exposes endpoints like `POST /books/ingest`, `POST /vector-similarity`, and `POST /retrieve-book`.
- `agents` is a lightweight agent service backed by local Ollama model hosting and exposes endpoints like `GET /author-info`, `GET /book-description`, and `GET /embedding`.
- `frontend` renders the UI with Streamlit and depends on the database and optional agent API.

## Notes for agents
- Do not introduce a new cross-service dependency unless it is clearly required by a feature.
- Use the per-service `.env` files and `docker-compose.yml` service names when reasoning about runtime configuration.
- Prefer modifying existing prompt templates in `agents/prompts/` for agent behavior changes rather than hard-coding text in Python.
- Keep new backend logic within the service boundaries: API changes in `api/`, agent workflow changes in `agents/`, UI changes in `frontend/`.
- When diagnosing issues, check Docker Compose logs for `db_api`, `agentic_calls`, `frontend`, `ollama`, and `phoenix`.

## Additional references
- `README.md`: high-level repository overview and quickstart instructions
- `api/README.md`, `agents/README.md`, `frontend/README.md`: service-specific documentation
