# Real-Time Security Log Detection Pipeline

This is a complete implementation of a real-time security log detection pipeline. It parses SSH authentication logs, detects brute-force and anomalous sign-in patterns, can run as an offline demo, and includes a Kafka/Redpanda + Prometheus + Grafana Docker Compose stack for streaming mode.

## What is implemented

- SSH authentication log parser for common OpenSSH `Failed password`, `Accepted password`, and `Accepted publickey` events.
- Detection engine for brute-force velocity, new-device sign-ins, and successful-login velocity across multiple IP addresses.
- Offline demo that reads a log file and writes JSONL alerts without Kafka.
- Kafka producer and consumer for real-time streaming mode.
- Prometheus metrics for processed events and emitted alerts.
- Grafana dashboard provisioning for event and alert trends.
- Synthetic/sample SSH auth logs and unit tests.

## Quick start without Kafka

```bash
cd real-time-security-log-detection-pipeline
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m security_pipeline.offline_demo --input data/sample_auth.log --output alerts.jsonl
python -m unittest discover -s tests
```

The offline demo is the fastest way to understand the detection logic. It produces alerts like:

```json
{"alert_type":"BRUTE_FORCE","severity":"HIGH","username":"root","source_ip":"203.0.113.10"}
```

## Streaming mode with Docker Compose

```bash
docker compose up --build
```

Services:

- Redpanda Kafka-compatible broker on `localhost:9092`
- Producer that replays `data/sample_auth.log` into the `auth-logs` topic
- Detector that consumes `auth-logs` and produces `security-alerts`
- Prometheus on `http://localhost:9090`
- Grafana on `http://localhost:3000` with username `admin` and password `admin`

## Use real SSH logs

You can run the offline demo against a real log file:

```bash
python -m security_pipeline.offline_demo --input /var/log/auth.log --output alerts.jsonl
```

For production use, redact usernames and IP addresses before sharing logs externally. The parser and detector do not require privileged access as long as the log file is readable.

## Main files

```text
src/security_pipeline/log_parser.py       OpenSSH auth log parser
src/security_pipeline/detector.py         rule engine and sliding-window state
src/security_pipeline/offline_demo.py     no-Kafka demo runner
src/security_pipeline/producer.py         Kafka producer for log events
src/security_pipeline/consumer.py         Kafka consumer and alert producer
monitoring/                              Prometheus and Grafana configuration
data/sample_auth.log                     sample log file with expected detections
```
