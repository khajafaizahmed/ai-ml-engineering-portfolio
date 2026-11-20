from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .pipeline import RAGPipeline

STORE_DIR = os.getenv("RAG_STORE_DIR", ".rag_store")
DOC_DIR = os.getenv("RAG_DOC_DIR", "data/docs")

app = FastAPI(title="Local RAG Document Q&A", version="0.1.0")
pipeline = RAGPipeline(store_dir=STORE_DIR)


class IngestRequest(BaseModel):
    docs_path: str = Field(default=DOC_DIR)
    chunk_size: int = Field(default=180, ge=50, le=2000)
    overlap: int = Field(default=40, ge=0, le=500)
    reset: bool = True


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=4, ge=1, le=12)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def resolve_docs_path(requested: str) -> Path:
    """Only allow ingesting from inside RAG_DOC_DIR, so the API can't be used to read arbitrary files."""
    root = Path(DOC_DIR).resolve()
    candidate = Path(requested)
    target = (candidate if candidate.is_absolute() else Path.cwd() / candidate).resolve()
    if target != root and root not in target.parents:
        raise HTTPException(status_code=400, detail=f"docs_path must be inside {DOC_DIR}")
    if not target.exists():
        raise HTTPException(status_code=404, detail="docs_path not found")
    return target


@app.post("/ingest")
def ingest(request: IngestRequest) -> dict[str, int]:
    docs_path = resolve_docs_path(request.docs_path)
    return pipeline.ingest(docs_path, chunk_size=request.chunk_size, overlap=request.overlap, reset=request.reset)


@app.post("/ask")
def ask(request: AskRequest) -> dict[str, object]:
    answer = pipeline.ask(request.question, top_k=request.top_k)
    payload = asdict(answer)
    payload["contexts"] = [
        {
            "source": item.chunk.source,
            "chunk_id": item.chunk.chunk_id,
            "citation": item.chunk.citation(),
            "score": item.score,
            "text": item.chunk.text,
        }
        for item in answer.contexts
    ]
    return payload
