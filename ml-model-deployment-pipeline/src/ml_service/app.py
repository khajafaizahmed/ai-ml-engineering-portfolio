from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .features import FEATURE_NAMES
from .model import Predictor
from .monitoring import DRIFT_SCORE, PREDICTION_COUNT, PREDICTION_LATENCY, REQUEST_COUNT, DriftMonitor, set_active_model_metric
from .registry import ModelRegistry
from .schemas import ModelInfoResponse, PredictionRequest, PredictionResponse, RollbackResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(os.getenv("MODEL_DIR", PROJECT_ROOT / "models"))

app = FastAPI(title="PyTorch Model Deployment Service", version="0.1.0")
registry = ModelRegistry(MODEL_DIR)
predictor = Predictor()
drift_monitor = DriftMonitor(window_size=200)


def load_active_model() -> None:
    record = registry.active_record()
    predictor.load(record["path"])
    set_active_model_metric(predictor.version, registry.available_versions())


load_active_model()


@app.get("/health")
def health() -> dict[str, str]:
    REQUEST_COUNT.labels(endpoint="/health", method="GET", status="200").inc()
    return {"status": "ok", "model_version": predictor.version}


@app.get("/model/info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    REQUEST_COUNT.labels(endpoint="/model/info", method="GET", status="200").inc()
    record = registry.active_record()
    return ModelInfoResponse(
        active_version=predictor.version,
        available_versions=registry.available_versions(),
        feature_names=FEATURE_NAMES,
        threshold=predictor.threshold,
        model_path=record["path"],
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    start = time.perf_counter()
    try:
        features = request.vector()
        probability, label = predictor.predict(features)
        drift_score = drift_monitor.update(features, predictor.reference_mean, predictor.reference_std)
        PREDICTION_COUNT.labels(model_version=predictor.version, label=str(label)).inc()
        REQUEST_COUNT.labels(endpoint="/predict", method="POST", status="200").inc()
        return PredictionResponse(
            model_version=predictor.version,
            probability=probability,
            label=label,
            threshold=predictor.threshold,
            drift_score=drift_score,
        )
    except Exception as exc:
        REQUEST_COUNT.labels(endpoint="/predict", method="POST", status="500").inc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        PREDICTION_LATENCY.observe(time.perf_counter() - start)


@app.post("/admin/rollback", response_model=RollbackResponse)
def rollback() -> RollbackResponse:
    try:
        version = registry.rollback()
        load_active_model()
        DRIFT_SCORE.set(0.0)
        REQUEST_COUNT.labels(endpoint="/admin/rollback", method="POST", status="200").inc()
        return RollbackResponse(active_version=version, message=f"Rolled back to {version}")
    except RuntimeError as exc:
        REQUEST_COUNT.labels(endpoint="/admin/rollback", method="POST", status="409").inc()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/metrics")
def metrics() -> Response:
    REQUEST_COUNT.labels(endpoint="/metrics", method="GET", status="200").inc()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
