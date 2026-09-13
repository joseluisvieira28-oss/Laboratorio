#!/usr/bin/env python3
"""Outcome-blind yearly acquisition shard for OPTIONS-SPOTPERP-001 V0.1.

FALLBACK INFRASTRUCTURE ONLY. This does not change any scientific rule and is not
a source verdict by itself. It partitions the already-frozen 2021-04-01 through
2024-12-31 Deribit source window into non-overlapping calendar-year acquisition
shards, uses the already-proven count=10,000 and monthly top-level windows, and
preserves every raw response plus request bounds/hash.

Each shard is intentionally expected to fail the global >=500-day coverage rule
when evaluated alone. That per-shard scientific status is ignored; only complete
raw acquisition + protected-period flags are eligible for the later global merge.
NO skew, signal, forward return or PnL is computed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

import source_audit as raw

UTC = dt.timezone.utc
OFFICIAL_HISTORY_MAX_COUNT = 10_000
ALLOWED_YEARS = (2021, 2022, 2023, 2024)
GLOBAL_START = dt.datetime(2021, 4, 1, tzinfo=UTC)
GLOBAL_END_EXCLUSIVE = dt.datetime(2025, 1, 1, tzinfo=UTC)


def monthly_windows() -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    cur = raw.START
    while cur < raw.END_EXCLUSIVE:
        if cur.month == 12:
            nxt = dt.datetime(cur.year + 1, 1, 1, tzinfo=UTC)
        else:
            nxt = dt.datetime(cur.year, cur.month + 1, 1, tzinfo=UTC)
        nxt = min(nxt, raw.END_EXCLUSIVE)
        out.append((int(cur.timestamp() * 1000), int(nxt.timestamp() * 1000) - 1))
        cur = nxt
    return out


def main() -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--year", type=int, required=True)
    args, rest = ap.parse_known_args()
    if args.year not in ALLOWED_YEARS:
        raise SystemExit(f"year must be one of {ALLOWED_YEARS}")

    start = max(GLOBAL_START, dt.datetime(args.year, 1, 1, tzinfo=UTC))
    end = min(GLOBAL_END_EXCLUSIVE, dt.datetime(args.year + 1, 1, 1, tzinfo=UTC))
    if not (GLOBAL_START <= start < end <= GLOBAL_END_EXCLUSIVE):
        raise SystemExit("FAIL-CLOSED shard outside frozen window")

    raw.START = start
    raw.END_EXCLUSIVE = end
    # HOLDOUT_START_MS stays at 2025-01-01 and continues to hard-block 2025+.
    raw.COUNT = OFFICIAL_HISTORY_MAX_COUNT
    raw.daily_windows = monthly_windows

    # Let the frozen source_audit parser consume only its own remaining args.
    sys.argv = [sys.argv[0], *rest]
    print(f"YEAR_SHARD={args.year} START={start.isoformat()} END_EXCLUSIVE={end.isoformat()}")
    print("SOURCE ACQUISITION ONLY / NO OUTCOMES / 2025+ FAIL-CLOSED")
    return raw.main()


if __name__ == "__main__":
    raise SystemExit(main())
