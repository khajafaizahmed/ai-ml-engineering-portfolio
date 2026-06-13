from __future__ import annotations

import argparse
import json
from pathlib import Path

from .detector import DetectionConfig, DetectionEngine
from .log_parser import parse_line


def run_offline(input_path: str | Path, output_path: str | Path, threshold: int = 5) -> dict[str, int]:
    engine = DetectionEngine(DetectionConfig(brute_force_threshold=threshold))
    events = 0
    alerts = 0
    output = Path(output_path)
    with Path(input_path).open("r", encoding="utf-8", errors="replace") as reader, output.open("w", encoding="utf-8") as writer:
        for line in reader:
            event = parse_line(line)
            if event is None:
                continue
            events += 1
            for alert in engine.process(event):
                alerts += 1
                writer.write(json.dumps(alert.to_dict(), sort_keys=True) + "\n")
    return {"events_processed": events, "alerts_emitted": alerts, "output": str(output)}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run security detection against a local auth.log file")
    parser.add_argument("--input", default="data/sample_auth.log")
    parser.add_argument("--output", default="alerts.jsonl")
    parser.add_argument("--brute-force-threshold", type=int, default=5)
    args = parser.parse_args(argv)
    summary = run_offline(args.input, args.output, threshold=args.brute_force_threshold)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
