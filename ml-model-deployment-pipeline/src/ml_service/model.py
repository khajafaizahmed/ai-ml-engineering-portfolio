from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn

from .features import FEATURE_NAMES, validate_feature_names


class RiskNet(nn.Module):
    """Small feed-forward classifier for tabular risk prediction."""

    def __init__(self, input_dim: int = len(FEATURE_NAMES), hidden_dim: int = 12) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features).squeeze(-1)


@dataclass
class ModelBundle:
    version: str
    model_path: Path
    model: RiskNet
    feature_names: list[str]
    reference_mean: list[float]
    reference_std: list[float]
    threshold: float


class Predictor:
    """Loads a versioned PyTorch checkpoint and serves predictions."""

    def __init__(self) -> None:
        self.bundle: ModelBundle | None = None

    @property
    def version(self) -> str:
        self._require_bundle()
        assert self.bundle is not None
        return self.bundle.version

    @property
    def threshold(self) -> float:
        self._require_bundle()
        assert self.bundle is not None
        return self.bundle.threshold

    @property
    def reference_mean(self) -> list[float]:
        self._require_bundle()
        assert self.bundle is not None
        return self.bundle.reference_mean

    @property
    def reference_std(self) -> list[float]:
        self._require_bundle()
        assert self.bundle is not None
        return self.bundle.reference_std

    def load(self, model_path: str | Path) -> ModelBundle:
        path = Path(model_path)
        checkpoint: dict[str, Any] = torch.load(path, map_location="cpu")
        feature_names = list(checkpoint["feature_names"])
        validate_feature_names(feature_names)
        model = RiskNet(input_dim=len(feature_names))
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()
        self.bundle = ModelBundle(
            version=str(checkpoint["version"]),
            model_path=path,
            model=model,
            feature_names=feature_names,
            reference_mean=[float(v) for v in checkpoint["reference_mean"]],
            reference_std=[float(v) for v in checkpoint["reference_std"]],
            threshold=float(checkpoint.get("threshold", 0.5)),
        )
        return self.bundle

    def predict_probability(self, features: list[float]) -> float:
        self._require_bundle()
        assert self.bundle is not None
        normalized = [
            (value - mean) / (std if abs(std) > 1e-6 else 1.0)
            for value, mean, std in zip(features, self.bundle.reference_mean, self.bundle.reference_std)
        ]
        with torch.no_grad():
            tensor = torch.tensor([normalized], dtype=torch.float32)
            logits = self.bundle.model(tensor)
            probability = torch.sigmoid(logits).item()
        return float(probability)

    def predict(self, features: list[float]) -> tuple[float, int]:
        probability = self.predict_probability(features)
        return probability, int(probability >= self.threshold)

    def _require_bundle(self) -> None:
        if self.bundle is None:
            raise RuntimeError("No model has been loaded")
