import json
from pathlib import Path

import pytest

from ml_service.registry import ModelRegistry


def test_registry_rollback_moves_to_previous_version(tmp_path: Path):
    registry_payload = {
        "active_version": "v2",
        "deployment_history": ["v1", "v2"],
        "models": {"v1": {"file": "model_v1.pt"}, "v2": {"file": "model_v2.pt"}},
    }
    (tmp_path / "registry.json").write_text(json.dumps(registry_payload), encoding="utf-8")
    registry = ModelRegistry(tmp_path)
    assert registry.rollback() == "v1"
    assert registry.active_version() == "v1"


def test_registry_rollback_rejects_missing_previous_version(tmp_path: Path):
    registry_payload = {
        "active_version": "v1",
        "deployment_history": ["v1"],
        "models": {"v1": {"file": "model_v1.pt"}},
    }
    (tmp_path / "registry.json").write_text(json.dumps(registry_payload), encoding="utf-8")
    registry = ModelRegistry(tmp_path)
    with pytest.raises(RuntimeError):
        registry.rollback()
