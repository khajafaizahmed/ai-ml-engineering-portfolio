from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any

from .pipeline import RAGPipeline


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def lexical_hallucination_rate(answer: str, context_text: str) -> float:
    """Approximate unsupported sentence rate using content-word overlap.

    A sentence is treated as supported when at least 30% of its content words appear
    in the retrieved context. This simple metric is meant for comparing pipeline
    versions, not for certifying factuality.
    """
    context_terms = set(re.findall(r"[a-z][a-z0-9_\-]+", context_text.lower()))
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
    if not sentences:
        return 0.0
    unsupported = 0
    for sentence in sentences:
        terms = [term for term in re.findall(r"[a-z][a-z0-9_\-]+", sentence.lower()) if len(term) > 3]
        if not terms:
            continue
        overlap = sum(1 for term in terms if term in context_terms) / len(terms)
        if overlap < 0.30:
            unsupported += 1
    return unsupported / len(sentences)


def evaluate_record(pipeline: RAGPipeline, record: dict[str, Any], top_k: int) -> dict[str, Any]:
    answer = pipeline.ask(record["question"], top_k=top_k)
    retrieved_sources = [result.chunk.source for result in answer.contexts]
    expected_sources = record.get("expected_sources", [])
    source_hits = [expected in retrieved_sources for expected in expected_sources]
    retrieval_relevance = sum(source_hits) / len(expected_sources) if expected_sources else 1.0

    answer_lower = answer.answer.lower()
    expected_keywords = [str(item).lower() for item in record.get("expected_keywords", [])]
    keyword_hits = [keyword in answer_lower for keyword in expected_keywords]
    keyword_coverage = sum(keyword_hits) / len(expected_keywords) if expected_keywords else 1.0
    context_text = "\n".join(result.chunk.text for result in answer.contexts)

    return {
        "question": record["question"],
        "retrieved_sources": retrieved_sources,
        "retrieval_relevance": retrieval_relevance,
        "answer_keyword_coverage": keyword_coverage,
        "approx_hallucination_rate": lexical_hallucination_rate(answer.answer, context_text),
        "used_llm": answer.used_llm,
        "answer": answer.answer,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate local RAG retrieval and grounded answer quality")
    parser.add_argument("--docs", default="data/docs")
    parser.add_argument("--store", default=".rag_store")
    parser.add_argument("--eval-file", default="data/eval/questions.jsonl")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--embedding", default="hashing", choices=["hashing", "sentence-transformer"])
    parser.add_argument("--store-backend", default="json", choices=["json", "chroma", "auto"])
    parser.add_argument("--output", default="", help="Optional path for JSON report")
    args = parser.parse_args(argv)

    pipeline = RAGPipeline(store_dir=args.store, embedding=args.embedding, store_backend=args.store_backend)
    pipeline.ingest(args.docs, reset=True)
    records = read_jsonl(args.eval_file)
    results = [evaluate_record(pipeline, record, args.top_k) for record in records]
    summary = {
        "records": len(results),
        "mean_retrieval_relevance": mean(item["retrieval_relevance"] for item in results) if results else 0.0,
        "mean_answer_keyword_coverage": mean(item["answer_keyword_coverage"] for item in results) if results else 0.0,
        "mean_approx_hallucination_rate": mean(item["approx_hallucination_rate"] for item in results) if results else 0.0,
        "results": results,
    }
    text = json.dumps(summary, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
