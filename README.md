# Streaming RAG Agent

Streaming Retrieval-Augmented Generation (RAG) agent — a **polyglot (Go + Python)** project. It consumes real-time data from Kafka topics, processes it in configurable windows, converts the window content into embeddings using Ollama, and stores these embeddings (along with the original text) in Elasticsearch for near real-time and historical context retrieval by Large Language Models (LLMs).

## Architecture

The two languages split the workload along their strengths and interoperate through shared infrastructure:

| Side | Responsibility | Entry points |
| --- | --- | --- |
| **Go** (`cmd/`, `internal/`) | High-throughput streaming **ingestion**: Kafka consume → windowing → embeddings → Elasticsearch, plus a RAG query API on **:8080** | `cmd/agent`, `cmd/producer` |
| **Python** (`python/`) | ML/**query serving**: a FastAPI RAG service on **:8000**, a multi-topic Kafka producer, and a CLI client | `strag-service`, `strag-producer`, `strag-query` |

Both read the same [`configs/configs.yml`](configs/configs.yml), the same Elasticsearch index (`rag_embeddings`, 768-dim `dense_vector` kNN), and the same Ollama endpoints — so windows written by the Go agent are queryable from the Python service and vice versa. See [`python/README.md`](python/README.md) for the Python side.

## Features

* **Kafka Integration:** Consumes messages from multiple Kafka topics.
* **Configurable Windows:** Messages are grouped into time-based or message-count-based windows.
* **Contextualization:** Converts raw JSON Kafka messages into human-readable, contextualized text for embedding.
* **Ollama Integration:** Uses a local Ollama instance for generating text embeddings and LLM responses.
* **Elasticsearch Storage:** Persists embedded window data in Elasticsearch for efficient vector search and filtering.
* **Graceful Shutdown:** Ensures all open windows are processed before the agent stops.

---

## Getting Started

### Prerequisites

* **Go** (1.21 or higher) — for the ingestion agent
* **Python** (3.10 or higher) — for the query service (see [`python/README.md`](python/README.md))
* **Kafka** (running and accessible)
* **Ollama** (running locally, with `nomic-embed-text` and `llama3` models pulled (or what if you want))
* **Elasticsearch** (running and accessible)

> A `docker-compose.yml` is provided that brings up the infrastructure (Zookeeper, Kafka, Elasticsearch, Kibana): `docker compose up -d`. Ollama and the Go/Python apps run on the host.

### Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/onurbaran/stream-rag-agent.git]
    cd stream-rag-agent
    ```

2.  **Initialize Go Module:**
    ```bash
    go mod tidy
    ```

3.  **Configure:**
    Edit the `configs/configs.yml` file to match your Kafka, Ollama, and Elasticsearch settings.

    ```yaml
    # Example snippet from configs/configs.yml
    kafka:
      brokers:
        - localhost:9092
      # ... other kafka configs
    ollama:
      url: http://localhost:11434
      embedding_model: nomic-embed-text
      llm_model: llama3 # Updated to llama3
    elasticsearch:
      addresses:
        - http://localhost:9200
      index_name: rag_embeddings
    ```

4.  **Run Ollama and pull models:**
    Ensure Ollama is running and you have pulled the necessary models:

    ```bash
    ollama pull nomic-embed-text
    ollama pull llama3
    ```

---

## Running the Agent (Go)

```bash
go run ./cmd/agent
```

You can also build the binaries:

```bash
go build -o bin/agent ./cmd/agent
go build -o bin/producer ./cmd/producer
```

## Running the Python query service

```bash
cd python
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Unix: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

strag-service                       # RAG query API on http://localhost:8000
strag-producer --topic all --rate 10  # feed both Kafka topics
strag-query "Are there any transactions in EUR?"
```

Full details in [`python/README.md`](python/README.md).

## API Usage Examples

Once the agent is running, you can send queries to its API endpoint. The agent will retrieve relevant context from Elasticsearch and augment the LLM's response.

The API endpoint is `http://localhost:8080/query`. You should always include a `--max-time` parameter to ensure `curl` waits long enough for the LLM to generate a response, especially with larger models like Llama3. A value of `90` seconds or more is recommended.

### Example 1: Querying for a specific account ID

```bash
curl -X POST -H "Content-Type: application/json" -d '{"prompt": "Get data matching account_id: ACC-0833"}' --max-time 90 http://localhost:8080/query
```

Response 
```bash
{"answer":"Here are the transactions for account_id ACC-0833: ..."}
```
Another example 
```bash
curl -X POST -H "Content-Type: application/json" -d '{"prompt": "Are there any transactions made in Euro (EUR)?"}' --max-time 90 http://localhost:8080/query
```
Response
```bash
{"answer":"Yes, I found transactions in Euro (EUR) including: ..."}
```

## Deploy the frontend on Vercel

The dependency-free query console lives in [`frontend/`](frontend/). In Vercel,
create a project from this repository and set **Root Directory** to `frontend`.
Deploy it as a static site, then enter the public URL of the Go API in the
frontend's **Agent endpoint** field. The Go API allows browser requests by
default; set `STRAG_ALLOWED_ORIGIN` to the Vercel origin to restrict access in
production.