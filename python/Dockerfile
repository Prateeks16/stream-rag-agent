# Python query/serving side of the Stream RAG Agent.
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install the package.
COPY pyproject.toml ./
COPY strag ./strag
RUN pip install --no-cache-dir .

# The config is mounted/copied from the repo root at runtime; point the loader
# at it and the service defaults (override with env vars as needed).
ENV STRAG_CONFIG=/config/configs.yml \
    STRAG_HOST=0.0.0.0 \
    STRAG_PORT=8000

EXPOSE 8000

CMD ["strag-service"]
