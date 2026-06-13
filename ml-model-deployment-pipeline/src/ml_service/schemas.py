from __future__ import annotations

from pydantic import BaseModel, Field

from .features import FEATURE_NAMES, ordered_features


class PredictionRequest(BaseModel):
    account_age_days: float = Field(..., ge=0, le=36500, description="Age of the account in days")
    failed_login_count: float = Field(..., ge=0, le=1000, description="Failed logins in the recent monitoring window")
    transaction_amount: float = Field(..., ge=0, le=1_000_000, description="Amount or value of the event")
    device_trust_score: float = Field(..., ge=0, le=1, description="Trust score for the device, where 1 is trusted")

    def vector(self) -> list[float]:
        return ordered_features({name: getattr(self, name) for name in FEATURE_NAMES})


class PredictionResponse(BaseModel):
    model_version: str
    probability: float
    label: int
    threshold: float
    drift_score: float


class ModelInfoResponse(BaseModel):
    active_version: str
    available_versions: list[str]
    feature_names: list[str]
    threshold: float
    model_path: str


class RollbackResponse(BaseModel):
    active_version: str
    message: str
