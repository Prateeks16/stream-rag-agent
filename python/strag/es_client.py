"""Elasticsearch access for the Python side.

Uses the same index name, mapping, and ``dense_vector`` kNN field as the Go
``vectordb`` package so documents written by the Go agent are queryable here and
vice versa. The synchronous official client is wrapped with ``asyncio.to_thread``
to keep the async service responsive without pulling in an async transport.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from elasticsearch import Elasticsearch

from .config import ElasticsearchConfig

logger = logging.getLogger(__name__)

# nomic-embed-text produces 768-dimensional vectors. Keep this in sync with the
# Go mapping in internal/vectordb/elasticsearch.go if you change the model.
EMBEDDING_DIMS = 768


def _index_mapping() -> dict[str, Any]:
    return {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "window_id": {"type": "keyword"},
                "topic": {"type": "keyword"},
                "partition": {"type": "integer"},
                "start_time": {"type": "date"},
                "end_time": {"type": "date"},
                "message_count": {"type": "integer"},
                "context_text": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": EMBEDDING_DIMS,
                    "index": True,
                    "similarity": "cosine",
                },
            }
        },
    }


class EsClient:
    def __init__(self, cfg: ElasticsearchConfig) -> None:
        self._client = Elasticsearch(hosts=list(cfg.addresses))
        self._index = cfg.index_name

    @property
    def index_name(self) -> str:
        return self._index

    # -- index bootstrap ---------------------------------------------------
    def _ensure_index_sync(self) -> None:
        if self._client.indices.exists(index=self._index):
            logger.info("Elasticsearch index '%s' already exists.", self._index)
            return
        self._client.indices.create(index=self._index, body=_index_mapping())
        logger.info("Elasticsearch index '%s' created.", self._index)

    async def ensure_index(self) -> None:
        await asyncio.to_thread(self._ensure_index_sync)

    # -- search ------------------------------------------------------------
    def _search_sync(self, embedding: list[float], k: int) -> list[dict[str, Any]]:
        resp = self._client.search(
            index=self._index,
            knn={
                "field": "embedding",
                "query_vector": embedding,
                "k": k,
                "num_candidates": 100,
            },
        )
        return [hit["_source"] for hit in resp.get("hits", {}).get("hits", [])]

    async def search_similar(
        self, embedding: list[float], k: int = 5
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._search_sync, embedding, k)

    # -- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        self._client.close()

    def ping(self) -> bool:
        try:
            return bool(self._client.ping())
        except Exception:  # pragma: no cover - network dependent
            return False
