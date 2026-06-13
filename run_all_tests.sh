#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

printf '\n[1/3] Local RAG tests\n'
cd "$ROOT/local-llm-document-qa-rag"
PYTHONPATH=src python -m unittest discover -s tests

printf '\n[2/3] ML deployment tests\n'
cd "$ROOT/ml-model-deployment-pipeline"
PYTHONPATH=src python -m pytest -q

printf '\n[3/3] Security pipeline tests\n'
cd "$ROOT/real-time-security-log-detection-pipeline"
PYTHONPATH=src python -m unittest discover -s tests

printf '\nAll project tests completed.\n'
