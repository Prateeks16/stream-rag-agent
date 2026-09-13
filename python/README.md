# Stream RAG Agent — Python side

This package is the **query / serving** half of the project. The Go agent handles
high-throughput streaming ingestion (Kafka → windowing → embeddings →
Elasticsearch); this Python code provides:

- **`strag-service`** — a FastAPI RAG query service (`POST /query`, `GET /health`),
  a Python peer of the Go API. Listens on **:8000** so it can run next to the Go
  API on :8080.
- **`strag-producer`** — a Kafka producer that can emit **both**
  `financial_transactions` and `sensor_data` (the Go producer only emits the
  former).
- **`strag-query`** — a CLI client that works against either the Python (:8000)
  or Go (:8080) endpoint.

Everything reads the same [`configs/configs.yml`](../configs/configs.yml) and
talks to the same Elasticsearch index and Ollama instance as the Go side, so the
two stacks are fully interoperable — documents written by Go are queried by
Python and vice versa.

## Install

```bash
cd python
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Unix: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .           # exposes the strag-* commands
```

## Run

Start the infrastructure and Ollama first (see the root README), then:

```bash
# RAG query service on http://localhost:8000
strag-service

# Feed data (both topics, ~10 msg/s)
strag-producer --topic all --rate 10

# Ask a question (defaults to the Python service on :8000)
strag-query "Are there any transactions in EUR?"

# Or query the Go API instead
strag-query --url http://localhost:8080/query "Get data for account_id ACC-0833"
```

## Configuration & environment overrides

The config file is located via, in order: an explicit path, `$STRAG_CONFIG`,
then a walk up the directory tree looking for `configs/configs.yml`.

These environment variables override the file (useful in containers):

| Variable | Overrides |
| --- | --- |
| `KAFKA_BROKERS` | `kafka.brokers` (comma-separated) |
| `OLLAMA_URL` | `ollama.url` |
| `OLLAMA_EMBEDDING_MODEL` | `ollama.embedding_model` |
| `OLLAMA_LLM_MODEL` | `ollama.llm_model` |
| `ELASTICSEARCH_ADDRESSES` | `elasticsearch.addresses` (comma-separated) |
| `ELASTICSEARCH_INDEX` | `elasticsearch.index_name` |
| `STRAG_HOST` / `STRAG_PORT` | service bind address (default `0.0.0.0:8000`) |

## Docker

```bash
docker build -t strag-agent-py ./python
docker run --rm -p 8000:8000 \
  -v "$(pwd)/configs:/config:ro" \
  -e ELASTICSEARCH_ADDRESSES=http://host.docker.internal:9200 \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  strag-agent-py
```

## Layout

```
python/
  strag/
    config.py         # loads configs/configs.yml (+ env overrides)
    ollama_client.py  # /api/embeddings and /api/generate
    es_client.py      # same index/mapping/kNN as the Go vectordb package
    rag.py            # build_rag_prompt + RagPipeline
    service.py        # FastAPI app (strag-service)
    producer.py       # multi-topic Kafka producer (strag-producer)
    client.py         # CLI query client (strag-query)
  pyproject.toml
  requirements.txt
  Dockerfile
```
