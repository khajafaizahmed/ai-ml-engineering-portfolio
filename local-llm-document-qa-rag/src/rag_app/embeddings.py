from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


class EmbeddingModel(ABC):
    """Minimal embedding interface used by vector stores."""

    name: str

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class HashingEmbeddingModel(EmbeddingModel):
    """Deterministic bag-of-words hashing encoder.

    This is not as semantically rich as sentence-transformers, but it is dependency-light,
    reproducible, and good enough for testing retrieval and the rest of the RAG stack.
    """

    name = "hashing-384"

    def __init__(self, dimensions: int = 384) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class SentenceTransformerEmbeddingModel(EmbeddingModel):
    """Optional sentence-transformer embedding adapter."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError(
                "sentence-transformers is not installed. Install optional dependencies with: pip install -e '.[full]'"
            ) from exc
        self.model_name = model_name
        self.name = model_name
        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover - optional dependency path
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, row)) for row in vectors]


def build_embedding_model(kind: str = "hashing", model_name: str | None = None) -> EmbeddingModel:
    normalized = kind.lower().strip()
    if normalized in {"hash", "hashing", "local"}:
        return HashingEmbeddingModel()
    if normalized in {"sentence-transformer", "sentence_transformer", "sbert"}:
        return SentenceTransformerEmbeddingModel(model_name or "sentence-transformers/all-MiniLM-L6-v2")
    raise ValueError(f"Unknown embedding kind: {kind}")
