from __future__ import annotations

import argparse
import json
from prometheus_client import start_http_server

from .detector import DetectionEngine
from .models import AuthEvent
from .prometheus_metrics import ALERTS_EMITTED, EVENTS_PROCESSED, LAST_EVENT_TIMESTAMP


def build_consumer(bootstrap_servers: str, topic: str):
    try:
        from kafka import KafkaConsumer  # type: ignore
    except Exception as exc:  # pragma: no cover - optional runtime dependency path
        raise RuntimeError("kafka-python is required for streaming mode. Install requirements.txt first.") from exc
    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="security-detector",
    )


def build_producer(bootstrap_servers: str):
    try:
        from kafka import KafkaProducer  # type: ignore
    except Exception as exc:  # pragma: no cover - optional runtime dependency path
        raise RuntimeError("kafka-python is required for streaming mode. Install requirements.txt first.") from exc
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda key: key.encode("utf-8") if key else None,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Consume auth events and emit security alerts")
    parser.add_argument("--input-topic", default="auth-logs")
    parser.add_argument("--alert-topic", default="security-alerts")
    parser.add_argument("--bootstrap-servers", default="localhost:9092")
    parser.add_argument("--metrics-port", type=int, default=9000)
    args = parser.parse_args(argv)

    start_http_server(args.metrics_port)
    consumer = build_consumer(args.bootstrap_servers, args.input_topic)
    producer = build_producer(args.bootstrap_servers)
    engine = DetectionEngine()
    print(f"detector listening to {args.input_topic}; metrics on :{args.metrics_port}")

    for message in consumer:
        event = AuthEvent.from_dict(message.value)
        EVENTS_PROCESSED.labels(outcome=event.outcome).inc()
        LAST_EVENT_TIMESTAMP.set(event.timestamp.timestamp())
        for alert in engine.process(event):
            ALERTS_EMITTED.labels(alert_type=alert.alert_type, severity=alert.severity).inc()
            producer.send(args.alert_topic, key=alert.username, value=alert.to_dict())
            producer.flush()
            print(json.dumps(alert.to_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
