FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

COPY pyproject.toml uv.lock /app/
COPY api /app/api
COPY main.py /app/

RUN python -m pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
