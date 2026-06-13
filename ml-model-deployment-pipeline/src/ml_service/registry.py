from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ModelRegistry:
    """File-backed model registry for active version and rollback state."""

    def __init__(self, model_dir: str | Path) -> None:
        self.model_dir = Path(model_dir)
        self.registry_path = self.model_dir / "registry.json"
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Missing model registry: {self.registry_path}")

    def load(self) -> dict[str, Any]:
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def save(self, registry: dict[str, Any]) -> None:
        self.registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    def active_version(self) -> str:
        return str(self.load()["active_version"])

    def available_versions(self) -> list[str]:
        return sorted(self.load()["models"].keys())

    def active_record(self) -> dict[str, Any]:
        registry = self.load()
        version = registry["active_version"]
        record = dict(registry["models"][version])
        record["version"] = version
        record["path"] = str(self.model_dir / record["file"])
        return record

    def set_active_version(self, version: str) -> None:
        registry = self.load()
        if version not in registry["models"]:
            raise KeyError(f"Unknown model version: {version}")
        registry["active_version"] = version
        history = registry.setdefault("deployment_history", [])
        if not history or history[-1] != version:
            history.append(version)
        self.save(registry)

    def rollback(self) -> str:
        registry = self.load()
        history = list(registry.get("deployment_history", []))
        active = registry["active_version"]
        if not history:
            raise RuntimeError("No deployment history is available for rollback")
        while history and history[-1] == active:
            history.pop()
        if not history:
            raise RuntimeError("No previous model version is available for rollback")
        previous = history[-1]
        registry["active_version"] = previous
        history.append(previous)
        registry["deployment_history"] = history
        self.save(registry)
        return previous
