# Local LLM Document Q&A System with Retrieval-Augmented Generation

This is a complete, runnable reference implementation of a local LLM document Q&A system with retrieval-augmented generation. It indexes local technical documents, retrieves the most relevant chunks for a question, and produces an answer with source citations. It supports an Ollama-backed local LLM when available and includes a deterministic extractive fallback so the project works immediately on a fresh machine.

## What is implemented

- Local document ingestion for Markdown, text, and optional PDF files.
- Chunking with overlap and stable source identifiers.
- Embeddings through a deterministic local hashing encoder by default, with an optional sentence-transformer adapter.
- Persistent vector store in JSON by default, with a ChromaDB adapter available when ChromaDB is installed.
- Local answer generation through Ollama when available, with an extractive fallback that always returns citations.
- CLI commands, FastAPI service, sample documents, and an evaluation harness.
- Tests for chunking, retrieval, answer citation behavior, and evaluation metrics.

## Quick start

```bash
cd local-llm-document-qa-rag
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

python -m rag_app.cli ingest --docs data/docs --store .rag_store
python -m rag_app.cli ask --question "How does the system avoid hallucinations?" --store .rag_store
python -m rag_app.evaluate --docs data/docs --store .rag_store --eval-file data/eval/questions.jsonl
python -m unittest discover -s tests
```

The commands above run without Ollama, ChromaDB, or sentence-transformers. They use the built-in hashing embeddings and the extractive answerer.

## Optional full local LLM mode

Install the optional dependencies and run Ollama locally:

```bash
pip install -e ".[full,dev]"
ollama pull llama3.1:8b
ollama serve
python -m rag_app.cli ingest --docs data/docs --store .rag_store --embedding sentence-transformer --store-backend chroma
python -m rag_app.cli ask --question "What does the RAG pipeline store in ChromaDB?" --store .rag_store --llm ollama --model llama3.1:8b
```

If Ollama is unavailable, the application automatically falls back to a deterministic extractive answer. This makes automated testing and local review reliable.

## API server

```bash
uvicorn rag_app.api:app --reload --port 8000
```

Example request:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"How are answers grounded?","top_k":4}'
```

## Evaluation harness

The evaluator reads JSONL records such as:

```json
{"question":"How are answers grounded?","expected_sources":["rag_architecture.md"],"expected_keywords":["citations","retrieved"]}
```

It reports:

- `retrieval_relevance`: whether expected sources appear in the top-k retrieved contexts.
- `answer_keyword_coverage`: expected keyword coverage in the generated answer.
- `approx_hallucination_rate`: a lightweight lexical estimate of unsupported answer sentences.

This is intentionally transparent rather than mathematically perfect; it is meant to compare chunking, retrieval, and reranking choices during development.

## Main files

```text
src/rag_app/chunker.py        document chunking
src/rag_app/embeddings.py     hashing and optional sentence-transformer embeddings
src/rag_app/vector_store.py   JSON vector store and optional Chroma adapter
src/rag_app/llm.py            Ollama client and extractive fallback
src/rag_app/pipeline.py       ingestion and question-answering orchestration
src/rag_app/evaluate.py       evaluation harness
src/rag_app/api.py            FastAPI API
```
