#!/usr/bin/env bash
set -euo pipefail
python -m security_pipeline.offline_demo --input data/sample_auth.log --output alerts.jsonl
cat alerts.jsonl
