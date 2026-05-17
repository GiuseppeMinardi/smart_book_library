FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

COPY pyproject.toml uv.lock /app/
RUN python -m pip install --no-cache-dir .

COPY agents /app/agents
COPY main.py /app/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
