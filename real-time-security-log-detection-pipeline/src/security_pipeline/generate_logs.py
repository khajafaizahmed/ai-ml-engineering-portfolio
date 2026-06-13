from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path


def generate_sample_lines(start: datetime | None = None) -> list[str]:
    start = start or datetime(2026, 6, 12, 10, 0, 0)
    lines: list[str] = []

    def fmt(offset_seconds: int, message: str) -> str:
        ts = start + timedelta(seconds=offset_seconds)
        return f"{ts.strftime('%b')} {ts.day:2d} {ts.strftime('%H:%M:%S')} web01 sshd[1234]: {message}"

    for index in range(5):
        lines.append(fmt(index * 25, f"Failed password for root from 203.0.113.10 port {54000 + index} ssh2"))
    lines.append(fmt(180, "Accepted publickey for alice from 198.51.100.10 port 55000 ssh2"))
    lines.append(fmt(240, "Accepted publickey for alice from 198.51.100.44 port 55001 ssh2"))
    lines.append(fmt(300, "Accepted password for alice from 198.51.100.77 port 55002 ssh2"))
    lines.append(fmt(360, "Failed password for invalid user admin from 192.0.2.50 port 55100 ssh2"))
    return lines


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic SSH authentication logs")
    parser.add_argument("--output", default="data/sample_auth.log")
    args = parser.parse_args(argv)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(generate_sample_lines()) + "\n", encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
