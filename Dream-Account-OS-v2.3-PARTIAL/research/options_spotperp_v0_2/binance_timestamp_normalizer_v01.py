#!/usr/bin/env python3
"""Technical compatibility helper for Binance public-data timestamps.

Scientific rules are untouched. This helper only normalizes provider timestamp
units to milliseconds and fails closed on any unsupported magnitude.
"""
from __future__ import annotations

import datetime as dt

UTC = dt.timezone.utc


def to_milliseconds(value: int | str) -> int:
    x = int(value)
    # Legacy/public archives commonly encode milliseconds (~1.7e12).
    if 1_000_000_000_000 <= x < 10_000_000_000_000:
        return x
    # Newer spot archives may encode microseconds (~1.7e15).
    if 1_000_000_000_000_000 <= x < 10_000_000_000_000_000:
        if x % 1000 != 0:
            # Preserve floor-to-ms semantics only when the provider value is an
            # exact microsecond timestamp; sub-ms precision is irrelevant to 1d bars.
            return x // 1000
        return x // 1000
    raise RuntimeError(f"FAIL-CLOSED: unsupported Binance timestamp magnitude: {x}")


def to_utc_datetime(value: int | str) -> dt.datetime:
    ms = to_milliseconds(value)
    return dt.datetime.fromtimestamp(ms / 1000.0, tz=UTC)


def self_test() -> None:
    assert to_utc_datetime(1733011200000).date().isoformat() == "2024-12-01"
    assert to_utc_datetime(1735689600000000).date().isoformat() == "2025-01-01"
    try:
        to_milliseconds(1735689600)
    except RuntimeError:
        pass
    else:
        raise AssertionError("seconds-scale timestamp must fail closed")
    print("BINANCE_TIMESTAMP_NORMALIZER_SELF_TEST_PASS")


if __name__ == "__main__":
    self_test()
