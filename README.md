# AI/ML Engineering Portfolio

[![CI](https://github.com/khajafaizahmed/ai-ml-engineering-portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/khajafaizahmed/ai-ml-engineering-portfolio/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

Three small, self-contained Python services that cover the parts of ML engineering that happen
*around* a model: retrieval and grounding, serving and rollback, and streaming detection with
monitoring. Each one runs locally with no API keys or external services, has tests that run in CI,
and ships with Docker and Prometheus/Grafana config for the "full" setup.

| Project | What it does | Stack |
|---|---|---|
| [**Local RAG Document Q&A**](local-llm-document-qa-rag/) | Indexes local documents and answers questions with source citations. Uses a local LLM (Ollama) when available, and a deterministic extractive answerer when not. Includes an evaluation harness. | FastAPI · Ollama · ChromaDB / JSON store · sentence-transformers |
| [**ML Model Deployment Pipeline**](ml-model-deployment-pipeline/) | Trains a PyTorch risk classifier, serves it behind FastAPI with a versioned model registry and one-call rollback, and exports latency, throughput and feature-drift metrics. | PyTorch · FastAPI · Prometheus · Grafana · Docker Compose |
| [**Real-Time Security Log Detection**](real-time-security-log-detection-pipeline/) | Parses OpenSSH auth logs and flags brute-force attempts, logins from new IPs, and logins from many IPs in a short window. Runs offline on a file or as a Kafka consumer. | Kafka (Redpanda) · Prometheus · Grafana · Docker Compose |

## Try one

Each project installs on its own. For example, the security pipeline needs nothing but Python:

```bash
cd real-time-security-log-detection-pipeline
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m security_pipeline.offline_demo --input data/sample_auth.log --output alerts.jsonl
# {"events_processed": 9, "alerts_emitted": 4, ...}
```

Every project README has a quick start, sample output, an API/CLI reference, and its known limitations.

## Run all the tests

```bash
./run_all_tests.sh        # Linux/macOS
.\run_all_tests.ps1       # Windows PowerShell
```

Both scripts expect each project's dependencies to be installed (`pip install -e ".[dev]"` in each folder).
GitHub Actions runs all three suites on every push and pull request ([`ci.yml`](.github/workflows/ci.yml)).

| Project | Tests |
|---|---|
| Local RAG Document Q&A | chunking, retrieval + citations, evaluation metrics, API ingest/ask and path restriction |
| ML Model Deployment Pipeline | feature ordering, registry rollback, prediction API, admin-token check |
| Real-Time Security Log Detection | log parsing, each detection rule, end-to-end offline demo |

## Design choices that apply to all three

- **Works without the heavy parts.** Each project has a dependency-light path (hashing embeddings, a JSON
  vector store, an offline log replay) so it runs and tests anywhere. The production-style components
  (Ollama, ChromaDB, Kafka, Grafana) plug in behind the same interfaces.
- **Observable by default.** The two services export Prometheus metrics and come with a provisioned Grafana dashboard.
- **Small, readable code.** Each `src/` package is a few hundred lines, split by responsibility
  (loading, indexing, serving, detecting) so it's easy to review.

## Repository layout

```text
.github/workflows/ci.yml                     tests for all three projects
docs/project-overview.pdf                    architecture and implementation notes (5 pages)
local-llm-document-qa-rag/                   project 1
ml-model-deployment-pipeline/                project 2
real-time-security-log-detection-pipeline/   project 3
run_all_tests.sh / run_all_tests.ps1         run every test suite
```

## Author

**Faiz Ahmed**: MS Computer Science, University of Washington Tacoma · [GitHub](https://github.com/khajafaizahmed)
