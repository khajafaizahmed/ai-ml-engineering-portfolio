from __future__ import annotations

import re
from datetime import datetime

from .models import AuthEvent

SYSLOG_RE = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+(?P<process>[A-Za-z0-9_./-]+)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.*)$"
)

FAILED_RE = re.compile(
    r"Failed (?P<method>\S+) for (?:(?P<invalid>invalid user)\s+)?(?P<user>\S+) "
    r"from (?P<ip>(?:\d{1,3}\.){3}\d{1,3}) port (?P<port>\d+)"
)

ACCEPTED_RE = re.compile(
    r"Accepted (?P<method>\S+) for (?P<user>\S+) from (?P<ip>(?:\d{1,3}\.){3}\d{1,3}) port (?P<port>\d+)"
)

INVALID_USER_RE = re.compile(
    r"Invalid user (?P<user>\S+) from (?P<ip>(?:\d{1,3}\.){3}\d{1,3}) port (?P<port>\d+)"
)


def parse_syslog_timestamp(month: str, day: str, time_text: str, year: int | None = None) -> datetime:
    year = year or datetime.now().year
    return datetime.strptime(f"{year} {month} {int(day):02d} {time_text}", "%Y %b %d %H:%M:%S")


def parse_line(line: str, year: int | None = None) -> AuthEvent | None:
    """Parse a single OpenSSH authentication log line.

    Unsupported lines return None so callers can stream mixed auth.log files safely.
    """
    match = SYSLOG_RE.match(line.strip())
    if not match:
        return None

    message = match.group("message")
    timestamp = parse_syslog_timestamp(match.group("month"), match.group("day"), match.group("time"), year=year)
    host = match.group("host")
    process = match.group("process")

    failed = FAILED_RE.search(message)
    if failed:
        return AuthEvent(
            timestamp=timestamp,
            host=host,
            process=process,
            username=failed.group("user"),
            source_ip=failed.group("ip"),
            outcome="failed",
            auth_method=failed.group("method"),
            raw=line.rstrip("\n"),
            metadata={"port": int(failed.group("port")), "invalid_user": bool(failed.group("invalid"))},
        )

    accepted = ACCEPTED_RE.search(message)
    if accepted:
        return AuthEvent(
            timestamp=timestamp,
            host=host,
            process=process,
            username=accepted.group("user"),
            source_ip=accepted.group("ip"),
            outcome="accepted",
            auth_method=accepted.group("method"),
            raw=line.rstrip("\n"),
            metadata={"port": int(accepted.group("port"))},
        )

    invalid = INVALID_USER_RE.search(message)
    if invalid:
        return AuthEvent(
            timestamp=timestamp,
            host=host,
            process=process,
            username=invalid.group("user"),
            source_ip=invalid.group("ip"),
            outcome="invalid_user",
            auth_method="unknown",
            raw=line.rstrip("\n"),
            metadata={"port": int(invalid.group("port"))},
        )

    return None
