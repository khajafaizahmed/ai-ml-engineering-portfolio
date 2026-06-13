from __future__ import annotations

FEATURE_NAMES = [
    "account_age_days",
    "failed_login_count",
    "transaction_amount",
    "device_trust_score",
]


def ordered_features(payload: dict[str, float]) -> list[float]:
    """Return feature values in the exact order expected by the model."""
    missing = [name for name in FEATURE_NAMES if name not in payload]
    if missing:
        raise KeyError(f"Missing required feature(s): {', '.join(missing)}")
    return [float(payload[name]) for name in FEATURE_NAMES]


def validate_feature_names(names: list[str]) -> None:
    if list(names) != FEATURE_NAMES:
        raise ValueError(f"Model expects {names}, but service expects {FEATURE_NAMES}")
