from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Protocol

from .embeddings import EmbeddingModel
from .models import Chunk, SearchResult


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have equal dimensionality")
    denom_left = math.sqrt(sum(v * v for v in left))
    denom_right = math.sqrt(sum(v * v for v in right))
    if denom_left == 0 or denom_right == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (denom_left * denom_right)


class VectorStore(Protocol):
    def reset(self) -> None: ...
    def add_chunks(self, chunks: list[Chunk]) -> None: ...
    def search(self, query: str, top_k: int = 4) -> list[SearchResult]: ...


class JsonVectorStore:
    """Simple persistent vector store stored as JSON files.

    It is intentionally transparent for review. For large document collections, use the
    ChromaVectorStore adapter below.
    """

    def __init__(self, persist_dir: str | Path, embedding_model: EmbeddingModel) -> None:
        self.persist_dir = Path(persist_dir)
        self.embedding_model = embedding_model
        self.index_file = self.persist_dir / "index.json"
        self._chunks: list[Chunk] = []
        self._embeddings: list[list[float]] = []
        self._load_if_present()

    def _load_if_present(self) -> None:
        if not self.index_file.exists():
            return
        payload = json.loads(self.index_file.read_text(encoding="utf-8"))
        self._chunks = [Chunk.from_dict(item) for item in payload.get("chunks", [])]
        self._embeddings = [list(map(float, row)) for row in payload.get("embeddings", [])]

    def _persist(self) -> None:
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "embedding_model": self.embedding_model.name,
            "chunks": [chunk.to_dict() for chunk in self._chunks],
            "embeddings": self._embeddings,
        }
        self.index_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def reset(self) -> None:
        if self.persist_dir.exists():
            shutil.rmtree(self.persist_dir)
        self._chunks = []
        self._embeddings = []

    def add_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])
        self._chunks.extend(chunks)
        self._embeddings.extend(embeddings)
        self._persist()

    def search(self, query: str, top_k: int = 4) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if not self._chunks:
            return []
        query_embedding = self.embedding_model.embed([query])[0]
        scored = [
            SearchResult(chunk=chunk, score=cosine_similarity(query_embedding, embedding))
            for chunk, embedding in zip(self._chunks, self._embeddings)
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]


class ChromaVectorStore:
    """Optional ChromaDB vector store adapter.

    ChromaDB is not required for the default demo path, but this adapter matches the
    target architecture when the optional dependency is installed.
    """

    def __init__(self, persist_dir: str | Path, embedding_model: EmbeddingModel, collection_name: str = "documents") -> None:
        try:
            import chromadb  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError("ChromaDB is not installed. Install with: pip install -e '.[full]'" ) from exc
        self.persist_dir = Path(persist_dir)
        self.embedding_model = embedding_model
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(collection_name)

    def reset(self) -> None:  # pragma: no cover - optional dependency path
        try:
            self.client.delete_collection(self.collection.name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(self.collection.name)

    def add_chunks(self, chunks: list[Chunk]) -> None:  # pragma: no cover - optional dependency path
        if not chunks:
            return
        embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])
        self.collection.add(
            ids=[chunk.citation() for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[{"source": chunk.source, "chunk_id": chunk.chunk_id, **chunk.metadata} for chunk in chunks],
        )

    def search(self, query: str, top_k: int = 4) -> list[SearchResult]:  # pragma: no cover - optional dependency path
        results = self.collection.query(query_embeddings=self.embedding_model.embed([query]), n_results=top_k)
        output: list[SearchResult] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0] or [0.0] * len(ids)
        for citation, text, metadata, distance in zip(ids, docs, metadatas, distances):
            source = metadata.get("source", "unknown")
            chunk_id = metadata.get("chunk_id", citation.split("#")[-1])
            chunk = Chunk(chunk_id=chunk_id, source=source, text=text, start_word=0, end_word=0, metadata=dict(metadata))
            output.append(SearchResult(chunk=chunk, score=1.0 / (1.0 + float(distance))))
        return output


def build_vector_store(backend: str, persist_dir: str | Path, embedding_model: EmbeddingModel) -> VectorStore:
    normalized = backend.lower().strip()
    if normalized in {"json", "local", "portable"}:
        return JsonVectorStore(persist_dir, embedding_model)
    if normalized == "chroma":
        return ChromaVectorStore(persist_dir, embedding_model)
    if normalized == "auto":
        try:
            return ChromaVectorStore(persist_dir, embedding_model)
        except RuntimeError:
            return JsonVectorStore(persist_dir, embedding_model)
    raise ValueError(f"Unknown vector store backend: {backend}")
