#!/usr/bin/env python3
"""Prospective implementation corrections for OPTIONS-SPOTPERP-001 source audit.

1) Deribit option contracts expire at 08:00 UTC. The canonical instrument name
   encodes the expiry date but not the hour. The original source_audit.py treated
   that date as 00:00 UTC, which can misclassify trades near the frozen 30/120-DTE
   boundaries.
2) Raw JSON pages are stored as gzip. The original gzip writer used the current
   compression timestamp, so identical response bodies could receive different
   compressed-byte SHA256 values across runs. This wrapper uses mtime=0 and no
   stored filename, making gzip bytes deterministic for identical raw response bytes.

These corrections change no hypothesis, source, date range, moneyness bucket,
coverage threshold, outcome, cost, or holdout rule. No skew, return, or PnL is
introduced here.
"""
from __future__ import annotations

import datetime as dt
import gzip
import math
from pathlib import Path

import source_audit as base


def parse_instrument(name: str) -> tuple[dt.datetime, float, str]:
    parts = name.split("-")
    if len(parts) != 4 or parts[0] != "BTC" or parts[3] not in {"C", "P"}:
        raise ValueError(f"unexpected instrument name: {name}")
    expiry = dt.datetime.strptime(parts[1].upper(), "%d%b%y").replace(
        hour=8, minute=0, second=0, microsecond=0, tzinfo=base.UTC
    )
    strike = float(parts[2])
    if not math.isfinite(strike) or strike <= 0:
        raise ValueError(f"invalid strike: {name}")
    return expiry, strike, parts[3]


def write_gz(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            compresslevel=6,
            fileobj=raw,
            mtime=0,
        ) as gz:
            gz.write(body)


# Patch only implementation details used by source_audit.py.
base.parse_instrument = parse_instrument
base.write_gz = write_gz


if __name__ == "__main__":
    raise SystemExit(base.main())
