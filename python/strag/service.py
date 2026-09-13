"""FastAPI RAG query service (the Python peer of the Go ``/query`` API).

Run with either of:

    strag-service
    uvicorn strag.service:app --port 8000

Listens on port 8000 by default so it can run alongside the Go API on 8080.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from .config import AppConfig, load_config
from .es_client import EsClient
from .ollama_client import OllamaClient, OllamaError
from .rag import RagPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("strag.service")


class QueryRequest(BaseModel):
    prompt: str


class QueryResponse(BaseModel):
    answer: str = ""
    error: str | None = None


def create_app(config_path: str | None = None) -> FastAPI:
    cfg: AppConfig = load_config(config_path)
    ollama = OllamaClient(cfg.ollama)
    es = EsClient(cfg.elasticsearch)
    pipeline = RagPipeline(ollama, es)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        # Best-effort: don't crash if Elasticsearch isn't up yet. The Go agent
        # also creates the index, so a missing one is recoverable.
        try:
            await es.ensure_index()
        except Exception as exc:  # noqa: BLE001 - startup should be resilient
            logger.warning("Could not ensure Elasticsearch index at startup: %s", exc)
        yield
        es.close()

    app = FastAPI(
        title="Stream RAG Agent - Python Query Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/query", response_model=QueryResponse)
    async def query(req: QueryRequest) -> QueryResponse:
        prompt = req.prompt.strip()
        if not prompt:
            return QueryResponse(error="Prompt cannot be empty")

        logger.info("Received query: %s", prompt)
        try:
            result = await pipeline.query(prompt)
        except OllamaError as exc:
            logger.error("Ollama error: %s", exc)
            return QueryResponse(error="Failed to generate a response from the LLM")
        except Exception as exc:  # noqa: BLE001
            logger.error("Query failed: %s", exc)
            return QueryResponse(error="Failed to process query")

        logger.info(
            "Answered query using %d context window(s)", len(result.context_windows)
        )
        return QueryResponse(answer=result.answer)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    host = os.environ.get("STRAG_HOST", "0.0.0.0")
    port = int(os.environ.get("STRAG_PORT", "8000"))
    uvicorn.run("strag.service:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
