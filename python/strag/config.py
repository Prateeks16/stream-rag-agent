"""Configuration loading for the Python side.

Reads the same ``configs/configs.yml`` file used by the Go agent so both stacks
stay in sync. Selected values can be overridden with environment variables,
which is convenient inside containers where hostnames differ from ``localhost``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class KafkaTopicConfig:
    name: str
    context: str = ""
    window_duration_seconds: int = 60
    window_max_messages: int = 100


@dataclass
class KafkaConfig:
    brokers: list[str] = field(default_factory=lambda: ["localhost:9092"])
    consumer_group_id: str = "rag_agent_group"
    topics: list[KafkaTopicConfig] = field(default_factory=list)


@dataclass
class OllamaConfig:
    url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    llm_model: str = "llama3"


@dataclass
class ElasticsearchConfig:
    addresses: list[str] = field(default_factory=lambda: ["http://localhost:9200"])
    index_name: str = "rag_embeddings"


@dataclass
class AppConfig:
    kafka: KafkaConfig
    ollama: OllamaConfig
    elasticsearch: ElasticsearchConfig


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def find_config_path(explicit: str | None = None) -> Path:
    """Locate ``configs/configs.yml``.

    Order of precedence: an explicit path, then ``$STRAG_CONFIG``, then a walk up
    the directory tree starting from both the current working directory and this
    file's location.
    """

    if explicit:
        return Path(explicit).expanduser()

    env = os.environ.get("STRAG_CONFIG")
    if env:
        return Path(env).expanduser()

    seen: set[Path] = set()
    for base in (Path.cwd(), Path(__file__).resolve().parent):
        current = base
        for _ in range(6):
            candidate = current / "configs" / "configs.yml"
            if candidate not in seen:
                seen.add(candidate)
                if candidate.is_file():
                    return candidate
            if current.parent == current:
                break
            current = current.parent

    raise FileNotFoundError(
        "could not locate configs/configs.yml; pass a path or set STRAG_CONFIG"
    )


def load_config(path: str | None = None) -> AppConfig:
    """Load and parse the YAML config, applying environment overrides."""

    config_path = find_config_path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    kafka_raw = raw.get("kafka", {}) or {}
    topics = [
        KafkaTopicConfig(
            name=topic["name"],
            context=topic.get("context", ""),
            window_duration_seconds=int(topic.get("window_duration_seconds", 60)),
            window_max_messages=int(topic.get("window_max_messages", 100)),
        )
        for topic in kafka_raw.get("topics", []) or []
    ]
    kafka = KafkaConfig(
        brokers=list(kafka_raw.get("brokers", ["localhost:9092"])),
        consumer_group_id=kafka_raw.get("consumer_group_id", "rag_agent_group"),
        topics=topics,
    )

    ollama_raw = raw.get("ollama", {}) or {}
    ollama = OllamaConfig(
        url=ollama_raw.get("url", "http://localhost:11434"),
        embedding_model=ollama_raw.get("embedding_model", "nomic-embed-text"),
        llm_model=ollama_raw.get("llm_model", "llama3"),
    )

    es_raw = raw.get("elasticsearch", {}) or {}
    elasticsearch = ElasticsearchConfig(
        addresses=list(es_raw.get("addresses", ["http://localhost:9200"])),
        index_name=es_raw.get("index_name", "rag_embeddings"),
    )

    # Environment overrides (handy for Docker / alternate deployments).
    if env := os.environ.get("KAFKA_BROKERS"):
        kafka.brokers = _split_csv(env)
    if env := os.environ.get("OLLAMA_URL"):
        ollama.url = env
    if env := os.environ.get("OLLAMA_EMBEDDING_MODEL"):
        ollama.embedding_model = env
    if env := os.environ.get("OLLAMA_LLM_MODEL"):
        ollama.llm_model = env
    if env := os.environ.get("ELASTICSEARCH_ADDRESSES"):
        elasticsearch.addresses = _split_csv(env)
    if env := os.environ.get("ELASTICSEARCH_INDEX"):
        elasticsearch.index_name = env

    return AppConfig(kafka=kafka, ollama=ollama, elasticsearch=elasticsearch)
