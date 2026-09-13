#!/usr/bin/env python3
"""Prospective implementation correction for OPTIONS-SPOTPERP-001 source audit.

Deribit option contracts expire at 08:00 UTC. The canonical instrument name encodes
the expiry date but not the hour. The original source_audit.py interpreted that date
at 00:00 UTC, which can misclassify trades near the frozen 30/120-DTE boundaries.

This wrapper changes only expiry timestamp interpretation. It does not change the
hypothesis, sample, moneyness buckets, coverage threshold, source, or any outcome.
It computes no skew, return, or PnL beyond what source_audit.py already forbids.
"""
from __future__ import annotations

import datetime as dt
import math

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


# Patch only the time-of-expiry interpretation used by AuditAccumulator.consume().
base.parse_instrument = parse_instrument


if __name__ == "__main__":
    raise SystemExit(base.main())
