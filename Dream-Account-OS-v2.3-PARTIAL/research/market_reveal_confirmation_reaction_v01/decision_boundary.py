"""Strict no-lookahead helpers for MRCR V0.1.

The caller supplies anchor and decision times. This module does not choose them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable, Sequence, TypeVar, Callable


T = TypeVar("T")


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
    if not text:
        raise ValueError("timestamp is empty")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    utc = dt.astimezone(timezone.utc)
    return int(utc.timestamp() * 1_000_000_000)


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
