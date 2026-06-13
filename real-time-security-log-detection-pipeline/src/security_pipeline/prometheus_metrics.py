from __future__ import annotations

from prometheus_client import Counter, Gauge

EVENTS_PROCESSED = Counter(
    "security_pipeline_events_processed_total",
    "Authentication events processed by outcome.",
    ["outcome"],
)

ALERTS_EMITTED = Counter(
    "security_pipeline_alerts_emitted_total",
    "Security alerts emitted by type and severity.",
    ["alert_type", "severity"],
)

LAST_EVENT_TIMESTAMP = Gauge(
    "security_pipeline_last_event_timestamp_seconds",
    "Unix timestamp of the last processed authentication event.",
)
