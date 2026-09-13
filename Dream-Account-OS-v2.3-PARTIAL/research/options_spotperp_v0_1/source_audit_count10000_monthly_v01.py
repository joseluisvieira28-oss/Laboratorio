#!/usr/bin/env python3
"""
Outcome-blind infrastructure wrapper for OPTIONS-SPOTPERP-001.

Uses the exact same frozen Deribit acquisition/audit implementation as
source_audit_count10000_v01.py, changing ONLY the top-level retrieval windows
from daily to monthly. Recursive has_more splitting, trade parsing, hashes,
coverage diagnostics, 2025/2026 firewalls and all scientific rules are unchanged.

This wrapper is not itself scientific authority. It is accepted only if a
same-period equivalence test proves the exact same trade_id set as the daily
count=10000 acquisition.
"""
from __future__ import annotations

import datetime as dt
import source_audit_count10000_v01 as base

UTC = dt.timezone.utc


def monthly_windows() -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    cur = base.START
    while cur < base.END_EXCLUSIVE:
        if cur.month == 12:
            nxt = dt.datetime(cur.year + 1, 1, 1, tzinfo=UTC)
        else:
            nxt = dt.datetime(cur.year, cur.month + 1, 1, tzinfo=UTC)
        nxt = min(nxt, base.END_EXCLUSIVE)
        out.append((int(cur.timestamp() * 1000), int(nxt.timestamp() * 1000) - 1))
        cur = nxt
    return out


base.daily_windows = monthly_windows

if __name__ == "__main__":
    raise SystemExit(base.main())
