from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque

from .models import Alert, AuthEvent


@dataclass(frozen=True)
class DetectionConfig:
    brute_force_threshold: int = 5
    brute_force_window_seconds: int = 300
    new_device_enabled: bool = True
    velocity_window_seconds: int = 600
    velocity_distinct_ip_threshold: int = 3
    alert_cooldown_seconds: int = 300


class DetectionEngine:
    """Stateful streaming detector using sliding windows."""

    def __init__(self, config: DetectionConfig | None = None) -> None:
        self.config = config or DetectionConfig()
        self.failures: dict[tuple[str, str], Deque[datetime]] = defaultdict(deque)
        self.known_success_ips: dict[str, set[str]] = defaultdict(set)
        self.success_windows: dict[str, Deque[tuple[datetime, str]]] = defaultdict(deque)
        self.recent_alerts: dict[tuple[str, str, str], datetime] = {}

    def process(self, event: AuthEvent) -> list[Alert]:
        alerts: list[Alert] = []
        if event.outcome in {"failed", "invalid_user"}:
            alert = self._detect_brute_force(event)
            if alert:
                alerts.append(alert)
        elif event.outcome == "accepted":
            new_device_alert = self._detect_new_device(event)
            if new_device_alert:
                alerts.append(new_device_alert)
            velocity_alert = self._detect_success_velocity(event)
            if velocity_alert:
                alerts.append(velocity_alert)
        return alerts

    def _detect_brute_force(self, event: AuthEvent) -> Alert | None:
        key = (event.username, event.source_ip)
        window = self.failures[key]
        window.append(event.timestamp)
        self._purge_old(window, event.timestamp, self.config.brute_force_window_seconds)
        if len(window) < self.config.brute_force_threshold:
            return None
        return self._emit_once(
            event=event,
            alert_type="BRUTE_FORCE",
            severity="HIGH",
            reason=(
                f"{len(window)} failed SSH authentication events for user '{event.username}' "
                f"from {event.source_ip} within {self.config.brute_force_window_seconds} seconds"
            ),
            evidence={"failed_count": len(window), "window_seconds": self.config.brute_force_window_seconds},
        )

    def _detect_new_device(self, event: AuthEvent) -> Alert | None:
        if not self.config.new_device_enabled:
            return None
        known_ips = self.known_success_ips[event.username]
        is_new_device = bool(known_ips) and event.source_ip not in known_ips
        known_ips.add(event.source_ip)
        if not is_new_device:
            return None
        return self._emit_once(
            event=event,
            alert_type="NEW_DEVICE_LOGIN",
            severity="MEDIUM",
            reason=f"Successful login for user '{event.username}' from a new source IP {event.source_ip}",
            evidence={"known_ip_count_before_event": len(known_ips) - 1, "auth_method": event.auth_method},
        )

    def _detect_success_velocity(self, event: AuthEvent) -> Alert | None:
        window = self.success_windows[event.username]
        window.append((event.timestamp, event.source_ip))
        cutoff = event.timestamp - timedelta(seconds=self.config.velocity_window_seconds)
        while window and window[0][0] < cutoff:
            window.popleft()
        distinct_ips = sorted({ip for _, ip in window})
        if len(distinct_ips) < self.config.velocity_distinct_ip_threshold:
            return None
        return self._emit_once(
            event=event,
            alert_type="SUCCESS_VELOCITY",
            severity="MEDIUM",
            reason=(
                f"User '{event.username}' had successful logins from {len(distinct_ips)} distinct IPs "
                f"within {self.config.velocity_window_seconds} seconds"
            ),
            evidence={"distinct_ips": distinct_ips, "window_seconds": self.config.velocity_window_seconds},
        )

    def _emit_once(self, event: AuthEvent, alert_type: str, severity: str, reason: str, evidence: dict[str, object]) -> Alert | None:
        dedupe_key = (alert_type, event.username, event.source_ip)
        last_seen = self.recent_alerts.get(dedupe_key)
        if last_seen is not None:
            cooldown = timedelta(seconds=self.config.alert_cooldown_seconds)
            if event.timestamp - last_seen < cooldown:
                return None
        self.recent_alerts[dedupe_key] = event.timestamp
        return Alert(
            timestamp=event.timestamp,
            alert_type=alert_type,
            severity=severity,
            username=event.username,
            source_ip=event.source_ip,
            reason=reason,
            evidence=evidence,
        )

    @staticmethod
    def _purge_old(window: Deque[datetime], current: datetime, max_age_seconds: int) -> None:
        cutoff = current - timedelta(seconds=max_age_seconds)
        while window and window[0] < cutoff:
            window.popleft()
