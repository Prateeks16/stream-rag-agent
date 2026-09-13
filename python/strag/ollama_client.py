"""Async Ollama client.

Mirrors the request/response contract used by the Go ``embedding`` and ``llm``
packages: ``POST /api/embeddings`` and ``POST /api/generate``.
"""

from __future__ import annotations

import httpx

from .config import OllamaConfig


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        cfg: OllamaConfig,
        embed_timeout: float = 30.0,
        generate_timeout: float = 120.0,
    ) -> None:
        self._url = cfg.url.rstrip("/")
        self._embedding_model = cfg.embedding_model
        self._llm_model = cfg.llm_model
        self._embed_timeout = embed_timeout
        self._generate_timeout = generate_timeout

    async def embed(self, text: str) -> list[float]:
        """Return the embedding vector for ``text``."""
        payload = {"model": self._embedding_model, "prompt": text}
        async with httpx.AsyncClient(timeout=self._embed_timeout) as client:
            resp = await client.post(f"{self._url}/api/embeddings", json=payload)
        if resp.status_code != httpx.codes.OK:
            raise OllamaError(
                f"ollama embeddings API returned {resp.status_code}: {resp.text}"
            )
        embedding = resp.json().get("embedding")
        if not embedding:
            raise OllamaError("ollama embeddings API returned an empty embedding")
        return embedding

    async def generate(self, prompt: str) -> str:
        """Return a non-streamed completion for ``prompt``."""
        payload = {"model": self._llm_model, "prompt": prompt, "stream": False}
        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            resp = await client.post(f"{self._url}/api/generate", json=payload)
        if resp.status_code != httpx.codes.OK:
            raise OllamaError(
                f"ollama generate API returned {resp.status_code}: {resp.text}"
            )
        return resp.json().get("response", "")
