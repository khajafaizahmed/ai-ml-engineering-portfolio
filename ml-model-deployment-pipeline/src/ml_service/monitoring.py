from __future__ import annotations

import math
from collections import deque
from statistics import mean

from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNT = Counter(
    "ml_service_requests_total",
    "Total HTTP requests handled by endpoint.",
    ["endpoint", "method", "status"],
)

PREDICTION_COUNT = Counter(
    "ml_service_predictions_total",
    "Total predictions by model version and predicted label.",
    ["model_version", "label"],
)

PREDICTION_LATENCY = Histogram(
    "ml_service_prediction_latency_seconds",
    "Prediction latency in seconds.",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

DRIFT_SCORE = Gauge(
    "ml_service_prediction_drift_score",
    "Mean absolute z-score drift between recent features and training reference statistics.",
)

ACTIVE_MODEL = Gauge(
    "ml_service_active_model_info",
    "Active model version exposed as an info-style gauge.",
    ["model_version"],
)


class DriftMonitor:
    """Tracks recent feature means and compares them to training statistics."""

    def __init__(self, window_size: int = 200) -> None:
        self.window: deque[list[float]] = deque(maxlen=window_size)

    def update(self, features: list[float], reference_mean: list[float], reference_std: list[float]) -> float:
        self.window.append(features)
        current_mean = [mean(values) for values in zip(*self.window)]
        z_scores: list[float] = []
        for current, ref_mean, ref_std in zip(current_mean, reference_mean, reference_std):
            denom = ref_std if abs(ref_std) > 1e-6 else 1.0
            z_scores.append(abs((current - ref_mean) / denom))
        score = float(sum(z_scores) / len(z_scores)) if z_scores else 0.0
        if math.isfinite(score):
            DRIFT_SCORE.set(score)
        return score


def set_active_model_metric(version: str, known_versions: list[str]) -> None:
    for candidate in known_versions:
        ACTIVE_MODEL.labels(model_version=candidate).set(1.0 if candidate == version else 0.0)
