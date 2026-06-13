# ML Model Deployment Pipeline with CI/CD and Monitoring

This is a complete implementation of an ML model deployment pipeline with CI/CD and monitoring. It trains a small PyTorch tabular classifier, deploys it behind a FastAPI prediction service, exposes Prometheus metrics, includes Grafana dashboards, and demonstrates a model version rollback path.

## What is implemented

- PyTorch model definition, synthetic training data, and reproducible training script.
- Versioned model artifacts in `models/` with an active-model registry.
- FastAPI service with health, prediction, model info, metrics, and rollback endpoints.
- Prediction latency, throughput, class distribution, active model version, and drift metrics through Prometheus.
- Dockerfile and Docker Compose stack for API + Prometheus + Grafana.
- GitHub Actions workflow with dependency install, tests, model sanity check, and Docker build.
- Unit tests for feature ordering, registry rollback, and API predictions.

## Quick start

```bash
cd ml-model-deployment-pipeline
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
uvicorn ml_service.app:app --reload --port 8080
```

The repository already includes small `v1` and `v2` model artifacts so the API can start immediately. To regenerate them:

```bash
python -m ml_service.train --model-dir models --versions v1 v2 --epochs 5
```

## Try a prediction

```bash
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{
    "account_age_days": 45,
    "failed_login_count": 7,
    "transaction_amount": 420.0,
    "device_trust_score": 0.22
  }'
```

Response fields include the risk probability, binary label, active model version, and drift score.

## Monitoring stack

```bash
docker compose up --build
```

Then open:

- API: `http://localhost:8080/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` with username `admin` and password `admin`

The dashboard is provisioned from `monitoring/grafana/dashboards/ml_service_dashboard.json`.

## Rollback endpoint

The registry keeps a deployment history. To roll back from the current active model to the previous version:

```bash
curl -X POST http://localhost:8080/admin/rollback
```

The API reloads the newly active model and updates the active-version metric.

## Main files

```text
src/ml_service/train.py       trains and saves versioned PyTorch models
src/ml_service/model.py       neural network and predictor wrapper
src/ml_service/registry.py    active model registry and rollback logic
src/ml_service/app.py         FastAPI service
src/ml_service/monitoring.py  Prometheus metrics and drift monitor
.github/workflows/ci.yml      CI/CD pipeline skeleton
monitoring/                   Prometheus and Grafana configuration
```
