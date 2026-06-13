from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AuthEvent:
    timestamp: datetime
    host: str
    process: str
    username: str
    source_ip: str
    outcome: str
    auth_method: str
    raw: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> "AuthEvent":
        return AuthEvent(
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            host=payload["host"],
            process=payload["process"],
            username=payload["username"],
            source_ip=payload["source_ip"],
            outcome=payload["outcome"],
            auth_method=payload.get("auth_method", "unknown"),
            raw=payload.get("raw", ""),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class Alert:
    timestamp: datetime
    alert_type: str
    severity: str
    username: str
    source_ip: str
    reason: str
    evidence: dict[str, Any]

    @property
    def alert_id(self) -> str:
        basis = f"{self.timestamp.isoformat()}:{self.alert_type}:{self.username}:{self.source_ip}:{self.reason}"
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        payload["alert_id"] = self.alert_id
        return payload
