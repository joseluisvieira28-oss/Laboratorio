"""Strict no-lookahead helpers for MRCR V0.1.

The caller supplies anchor and decision times. This module does not choose them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import re
from typing import Callable, Iterable, Sequence, TypeVar


T = TypeVar("T")

_RFC3339_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})T"
    r"(?P<time>\d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<fraction>\d{1,9}))?"
    r"(?P<tz>Z|[+-]\d{2}:\d{2})$"
)


@dataclass(frozen=True)
class TimedObservation:
    timestamp_ns: int
    payload: object


def epoch_ms_to_ns(value: int | str) -> int:
    ms = int(value)
    if ms < 0:
        raise ValueError("epoch milliseconds must be >= 0")
    return ms * 1_000_000


def rfc3339_to_ns(value: str) -> int:
    text = value.strip()
    match = _RFC3339_RE.fullmatch(text)
    if not match:
        raise ValueError("timestamp must be strict RFC3339 with timezone")

    date_part = match.group("date")
    time_part = match.group("time")
    fraction = (match.group("fraction") or "").ljust(9, "0")
    fractional_ns = int(fraction) if fraction else 0

    base = datetime.strptime(
        f"{date_part}T{time_part}",
        "%Y-%m-%dT%H:%M:%S",
    )

    tz_text = match.group("tz")
    if tz_text == "Z":
        tz = timezone.utc
    else:
        sign = 1 if tz_text[0] == "+" else -1
        hours = int(tz_text[1:3])
        minutes = int(tz_text[4:6])
        if hours > 23 or minutes > 59:
            raise ValueError("invalid RFC3339 timezone offset")
        tz = timezone(sign * timedelta(hours=hours, minutes=minutes))

    aware = base.replace(tzinfo=tz).astimezone(timezone.utc)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = aware - epoch
    whole_seconds = delta.days * 86_400 + delta.seconds
    return whole_seconds * 1_000_000_000 + fractional_ns


def bounded_window(
    rows: Iterable[T],
    *,
    timestamp_ns: Callable[[T], int],
    anchor_ns: int,
    decision_ns: int,
) -> tuple[T, ...]:
    if decision_ns < anchor_ns:
        raise ValueError("decision must be >= anchor")
    out = []
    for row in rows:
        ts = int(timestamp_ns(row))
        if anchor_ns <= ts <= decision_ns:
            out.append(row)
    out.sort(key=lambda row: int(timestamp_ns(row)))
    return tuple(out)


def latest_at_or_before(
    rows: Sequence[T],
    *,
    timestamp_ns: Callable[[T], int],
    decision_ns: int,
) -> T | None:
    eligible = [row for row in rows if int(timestamp_ns(row)) <= decision_ns]
    if not eligible:
        return None
    return max(eligible, key=lambda row: int(timestamp_ns(row)))


def assert_no_future(
    rows: Iterable[T],
    *,
    timestamp_ns: Callable[[T], int],
    decision_ns: int,
) -> None:
    future = [int(timestamp_ns(row)) for row in rows if int(timestamp_ns(row)) > decision_ns]
    if future:
        raise ValueError(
            f"future observations present beyond decision boundary: min_future={min(future)}"
        )


def raw_sha256(raw: bytes) -> str:
    if not isinstance(raw, (bytes, bytearray)):
        raise TypeError("raw must be bytes")
    return sha256(bytes(raw)).hexdigest()
