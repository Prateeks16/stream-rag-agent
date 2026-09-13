"""RAG pipeline: embed the prompt, retrieve context, build the prompt, generate.

``build_rag_prompt`` intentionally mirrors ``buildRAGPrompt`` in the Go
``internal/api`` package so both services produce comparable answers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .es_client import EsClient
from .ollama_client import OllamaClient


def build_rag_prompt(user_prompt: str, context_windows: list[dict[str, Any]]) -> str:
    parts: list[str] = [
        "You are an AI assistant specialized in analyzing Kafka streaming data. ",
        "Use the provided data from Kafka topics to answer the user's question. ",
        "If the answer is not in the provided data, state that you don't have enough information. ",
        "Do NOT make up information.\n\n",
        "--- RELEVANT KAFKA DATA ---\n",
    ]

    if not context_windows:
        parts.append("No relevant Kafka data found.\n")
    else:
        for i, window in enumerate(context_windows, start=1):
            topic = window.get("topic", "unknown")
            window_id = window.get("window_id", "unknown")
            parts.append(f"--- Window {i} (Topic: {topic}, ID: {window_id}) ---\n")
            parts.append(window.get("context_text", ""))
            parts.append("\n\n")

    parts.append("--------------------------\n\n")
    parts.append("USER QUESTION: ")
    parts.append(user_prompt)
    parts.append("\n")
    return "".join(parts)


@dataclass
class RagResult:
    answer: str
    context_windows: list[dict[str, Any]]


class RagPipeline:
    def __init__(self, ollama: OllamaClient, es: EsClient, top_k: int = 5) -> None:
        self._ollama = ollama
        self._es = es
        self._top_k = top_k

    async def query(self, prompt: str) -> RagResult:
        query_embedding = await self._ollama.embed(prompt)
        windows = await self._es.search_similar(query_embedding, self._top_k)
        rag_prompt = build_rag_prompt(prompt, windows)
        answer = await self._ollama.generate(rag_prompt)
        return RagResult(answer=answer, context_windows=windows)
