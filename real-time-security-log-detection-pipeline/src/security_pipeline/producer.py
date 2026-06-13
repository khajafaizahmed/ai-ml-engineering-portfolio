from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .log_parser import parse_line


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
    parser = argparse.ArgumentParser(description="Replay auth logs into Kafka")
    parser.add_argument("--input", default="data/sample_auth.log")
    parser.add_argument("--topic", default="auth-logs")
    parser.add_argument("--bootstrap-servers", default="localhost:9092")
    parser.add_argument("--delay", type=float, default=0.25)
    args = parser.parse_args(argv)

    producer = build_producer(args.bootstrap_servers)
    sent = 0
    for line in Path(args.input).read_text(encoding="utf-8", errors="replace").splitlines():
        event = parse_line(line)
        if event is None:
            continue
        producer.send(args.topic, key=event.username, value=event.to_dict())
        producer.flush()
        sent += 1
        print(f"sent event {sent}: {event.username} {event.outcome} {event.source_ip}")
        time.sleep(args.delay)
    print(f"sent {sent} events to topic {args.topic}")


if __name__ == "__main__":
    main()
