#!/usr/bin/env python3
"""
Outcome-blind infrastructure wrapper for OPTIONS-SPOTPERP-001.

Uses the exact same frozen Deribit acquisition/audit implementation as
source_audit.py, changing ONLY:
- technical page size from 1,000 to the official History API maximum 10,000; and
- top-level retrieval windows from daily to monthly.

Recursive has_more splitting, trade parsing, hashes, coverage diagnostics,
2025/2026 firewalls and all scientific rules are unchanged.

This wrapper is not itself scientific authority. It is accepted only if a
same-period equivalence test proves the exact same trade_id set as the daily
count=10,000 acquisition.
"""
from __future__ import annotations

import datetime as dt
import source_audit as raw

UTC = dt.timezone.utc
OFFICIAL_HISTORY_MAX_COUNT = 10_000


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
    # Infrastructure-only monkeypatches on the module that owns main().
    raw.COUNT = OFFICIAL_HISTORY_MAX_COUNT
    raw.daily_windows = monthly_windows
    return raw.main()


if __name__ == "__main__":
    raise SystemExit(main())
