# AI/ML Engineering Portfolio

![CI](https://github.com/khajafaizahmed/ai-ml-engineering-portfolio/actions/workflows/ci.yml/badge.svg)

A collection of production-oriented Python projects covering retrieval-augmented generation, machine learning model serving, and security event detection. The repository emphasizes tested code, reproducible local execution, CI, containerized services, and monitoring assets.

## Projects

| Project | Focus | Highlights |
|---|---|---|
| `local-llm-document-qa-rag` | Retrieval-augmented document question answering | Document loading, chunking, embeddings, vector search, citation-aware answers, CLI/API, evaluation tests |
| `ml-model-deployment-pipeline` | ML model training and serving | PyTorch model, FastAPI service, model registry, rollback support, Prometheus metrics, Grafana dashboard |
| `real-time-security-log-detection-pipeline` | Security log parsing and detection | SSH auth-log parser, sliding-window detection rules, offline demo, streaming components, monitoring dashboard |

## Repository Structure

```text
.github/workflows/ci.yml
docs/project-overview.pdf
local-llm-document-qa-rag/
ml-model-deployment-pipeline/
real-time-security-log-detection-pipeline/
run_all_tests.ps1
run_all_tests.sh
```

## Run All Tests

Windows PowerShell:

```powershell
.\run_all_tests.ps1
```

Linux/macOS:

```bash
./run_all_tests.sh
```

GitHub Actions also runs the test suites for all three projects on push and pull request.

## Local Review

Each project has its own README with setup and usage details.

```bash
cd local-llm-document-qa-rag
pip install -e ".[dev]"
python -m unittest discover -s tests
```

```bash
cd ml-model-deployment-pipeline
pip install -e ".[dev]"
python -m pytest -q
```

```bash
cd real-time-security-log-detection-pipeline
pip install -e ".[dev]"
python -m unittest discover -s tests
python -m security_pipeline.offline_demo --input data/sample_auth.log --output alerts.jsonl
```

## Architecture Notes

A high-level architecture and implementation overview is available here:

```text
docs/project-overview.pdf
```

## Scope

These projects are intentionally compact enough to run locally while still demonstrating production-style engineering patterns: package structure, tests, CI, container files, service APIs, monitoring configuration, model/version management, and reproducible sample data.
