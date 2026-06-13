from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Document:
    """A complete source document loaded from disk."""

    source: str
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class Chunk:
    """A retrievable document chunk with a stable citation id."""

    chunk_id: str
    source: str
    text: str
    start_word: int
    end_word: int
    metadata: dict[str, Any]

    def citation(self) -> str:
        return f"{self.source}#{self.chunk_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Chunk":
        return Chunk(
            chunk_id=str(data["chunk_id"]),
            source=str(data["source"]),
            text=str(data["text"]),
            start_word=int(data["start_word"]),
            end_word=int(data["end_word"]),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class SearchResult:
    """A chunk plus its vector similarity score."""

    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Answer:
    """A generated answer and the contexts used to produce it."""

    question: str
    answer: str
    citations: list[str]
    contexts: list[SearchResult]
    used_llm: str
