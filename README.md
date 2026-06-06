# smart_book_library

Smart Book Library is a small reference project that demonstrates an opinionated architecture for
ingesting book metadata, generating embeddings / vector similarity searches, and exposing both
API and agent-backed endpoints together with a Streamlit frontend. The repository contains
three primary components: an API service, an Agents service, and a Streamlit frontend; a
PostgreSQL (pgvector) database is used for storage and vector search.

**This README** documents the repository layout, how to run the project (Docker Compose),
and common development tasks.

## Repository layout

- **api/**: FastAPI application exposing book ingest and vector-similarity endpoints. See [api/main.py](api/main.py).
- **agents/**: FastAPI agents service that runs small agent workflows (author info, book description, embeddings). See [agents/main.py](agents/main.py).
- **frontend/**: Streamlit dashboard visualizing books and authors. See [frontend/main.py](frontend/main.py).
- **db/**: Database initialization SQL and env templates used by the Docker Compose setup.
- **ollama/** and **phoenix/**: folders used by the docker-compose configuration for model hosting and telemetry (OLLAMA, Phoenix).
- **docker-compose.yml**: Orchestrates the services for local development.
- **main.py**: Small helper to bulk-ingest ISBNs via the API (root-level utility).

Quick overview of important endpoints

- API (default port `8000`):
  - `POST /books/ingest` — ingest book metadata by ISBN (returns stored book data). See [api/main.py](api/main.py).
  - `POST /vector-similarity` — run vector similarity queries against a vector table.
  - `POST /retrieve-book` — wrapper around Google Books lookup by ISBN.
- Agents (default port `8001`):
  - `GET /author-info?author_name=...` — returns author information via agent.
  - `GET /book-description?book_title=...` — agent-generated description.
  - `GET /embedding?text=...` — returns an embedding for given text. See [agents/main.py](agents/main.py).
- Frontend (Streamlit, default port `8501`) — interactive dashboard. See [frontend/main.py](frontend/main.py).

Quickstart (Docker Compose)

1. Install Docker and Docker Compose on your machine.
2. From the repository root run:

```bash
docker compose up --build
```

This will start the database (`pgvector` image), `db_api` (FastAPI), `agentic_calls` (agents service),
`frontend` (Streamlit), `ollama`, and `phoenix` containers as configured in `docker-compose.yml`.

Environment variables

- Each service may read an `.env` file inside its folder (see `api/.env`, `agents/.env`, `frontend/.env`, `db/.env`).
- Key environment variables used in the compose file:
  - `API_URL` / `AGENTIC_API_URL` — base URLs for services.
  - Database connection: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (used by the frontend and API).

Running locally without Docker (developer mode)

- Each subproject includes a `pyproject.toml`. Use a virtual environment and install dependencies per subproject.
- Example for the root ingest tool (requires Python >= 3.13):

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\\Scripts\\activate
pip install -r api/requirements.txt  # or install packages from the respective pyproject.toml
python main.py 9780143127550 --api-url http://localhost:8000
```

Example usage

- Ingest a book via the API:

```bash
curl -X POST http://localhost:8000/books/ingest -H "Content-Type: application/json" -d '{"isbn":"9780143127550"}'
```

- Query the agents embedding endpoint:

```bash
curl "http://localhost:8001/embedding?text=To+be+or+not+to+be"
```

Development notes

- The API uses FastAPI and Uvicorn (`uvicorn main:app --reload`) for hot reload during development. See `api/main.py`.
- The frontend is implemented with Streamlit; the compose file runs it with `streamlit run main.py` on port `8501`.
- The agents service exposes small agent-run endpoints for text/author workflows.

Troubleshooting

- If the Streamlit frontend fails to start, ensure the database container is healthy and reachable at the host/port configured in `frontend/.env` or the compose file.
- If embedding or agent calls error, check that `ollama` (model host) and `phoenix` (telemetry) services are running and reachable.

Next steps

- Add `api/requirements.txt`, `agents/requirements.txt`, and `frontend/requirements.txt` if you prefer `pip` installs (this repository currently uses `pyproject.toml`).
- Add example `.env.example` files in subfolders to document required environment variables.
