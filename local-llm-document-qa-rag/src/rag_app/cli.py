from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .pipeline import RAGPipeline


def build_common_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--store", default=".rag_store", help="Persistent vector store directory")
    parser.add_argument("--embedding", default="hashing", choices=["hashing", "sentence-transformer"], help="Embedding backend")
    parser.add_argument("--store-backend", default="json", choices=["json", "chroma", "auto"], help="Vector store backend")
    parser.add_argument("--llm", default="auto", choices=["auto", "ollama", "extractive"], help="Answer generator")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model name")
    return parser


def ingest_main(argv: list[str] | None = None) -> None:
    parser = build_common_parser("Ingest documents into the local RAG store")
    parser.add_argument("--docs", default="data/docs", help="Document directory or file")
    parser.add_argument("--chunk-size", type=int, default=180)
    parser.add_argument("--overlap", type=int, default=40)
    args = parser.parse_args(argv)

    pipeline = RAGPipeline(store_dir=args.store, embedding=args.embedding, store_backend=args.store_backend, llm_provider=args.llm, llm_model=args.model)
    summary = pipeline.ingest(args.docs, chunk_size=args.chunk_size, overlap=args.overlap)
    print(json.dumps(summary, indent=2))


def ask_main(argv: list[str] | None = None) -> None:
    parser = build_common_parser("Ask a question against the local RAG store")
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args(argv)

    pipeline = RAGPipeline(store_dir=args.store, embedding=args.embedding, store_backend=args.store_backend, llm_provider=args.llm, llm_model=args.model)
    answer = pipeline.ask(args.question, top_k=args.top_k)
    payload = asdict(answer)
    payload["contexts"] = [
        {"source": item.chunk.source, "chunk_id": item.chunk.chunk_id, "score": item.score, "text": item.chunk.text[:500]}
        for item in answer.contexts
    ]
    print(json.dumps(payload, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Local RAG utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("ingest")
    subparsers.add_parser("ask")
    known, remaining = parser.parse_known_args(argv)
    if known.command == "ingest":
        ingest_main(remaining)
    elif known.command == "ask":
        ask_main(remaining)


if __name__ == "__main__":
    main()
