"""Python side of the Stream RAG Agent.

The Go agent handles high-throughput streaming ingestion (Kafka -> windowing ->
embeddings -> Elasticsearch). This package provides the query/serving side in
Python: a FastAPI RAG service, a multi-topic Kafka producer, and a CLI client.

Both languages share the same ``configs/configs.yml``, the same Elasticsearch
index, and the same Ollama endpoints, so they are fully interoperable.
"""

__version__ = "0.1.0"
