from __future__ import annotations

from pathlib import Path

from .chunker import chunk_documents
from .document_loader import load_documents
from .embeddings import build_embedding_model
from .llm import AnswerGenerator
from .models import Answer
from .vector_store import VectorStore, build_vector_store


class RAGPipeline:
    """End-to-end local RAG orchestration."""

    def __init__(
        self,
        store_dir: str | Path = ".rag_store",
        embedding: str = "hashing",
        store_backend: str = "json",
        llm_provider: str = "auto",
        llm_model: str = "llama3.1:8b",
        ollama_base_url: str = "http://localhost:11434",
    ) -> None:
        self.embedding_model = build_embedding_model(embedding)
        self.vector_store: VectorStore = build_vector_store(store_backend, store_dir, self.embedding_model)
        self.answer_generator = AnswerGenerator(provider=llm_provider, model=llm_model, base_url=ollama_base_url)

    def ingest(self, docs_path: str | Path, chunk_size: int = 180, overlap: int = 40, reset: bool = True) -> dict[str, int]:
        documents = load_documents(docs_path)
        chunks = chunk_documents(documents, chunk_size=chunk_size, overlap=overlap)
        if reset:
            self.vector_store.reset()
        self.vector_store.add_chunks(chunks)
        return {"documents": len(documents), "chunks": len(chunks)}

    def ask(self, question: str, top_k: int = 4) -> Answer:
        contexts = self.vector_store.search(question, top_k=top_k)
        generated = self.answer_generator.generate(question, contexts)
        citations = [result.chunk.citation() for result in contexts]
        return Answer(
            question=question,
            answer=generated.text,
            citations=citations,
            contexts=contexts,
            used_llm=generated.provider,
        )
