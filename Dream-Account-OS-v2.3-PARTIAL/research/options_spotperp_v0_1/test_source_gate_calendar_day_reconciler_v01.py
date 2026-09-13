#!/usr/bin/env python3
"""Outcome-blind boundary tests for the canonical calendar-day source-gate reconciler."""

from __future__ import annotations

import gzip
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from source_gate_calendar_day_reconciler_v01 import canonical_calendar_day_coverage

UTC = timezone.utc


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trade(ts_ms: int, name: str, iv: float = 60.0, index: float = 100.0) -> dict:
    return {
        "timestamp": ts_ms,
        "trade_id": name + str(ts_ms),
        "instrument_name": name,
        "iv": iv,
        "index_price": index,
        "mark_price": 0.01,
        "direction": "buy",
        "amount": 1.0,
    }


def make_day_rows(day: datetime, expiry_code: str) -> list[dict]:
    # Noon is deliberate: the old fractional-midnight implementation would see
    # an expiry exactly 30 calendar dates ahead as only 29.5 elapsed days.
    ts_ms = int(day.timestamp() * 1000)
    rows = []
    for i, strike in enumerate((106, 108, 110, 112, 114)):
        rows.append(trade(ts_ms + i, f"BTC-{expiry_code}-{strike}-C"))
    for i, strike in enumerate((81, 84, 87, 90, 93)):
        rows.append(trade(ts_ms + 100 + i, f"BTC-{expiry_code}-{strike}-P"))
    return rows


def build_root(rows: list[dict]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="options_calendar_dte_test_"))
    raw = root / "raw"
    raw.mkdir(parents=True)
    page = raw / "response_000001.json.gz"
    payload = {"result": {"trades": rows, "has_more": False}}
    with gzip.open(page, "wb", compresslevel=6) as f:
        f.write(json.dumps(payload).encode("utf-8"))
    manifest = {
        "probe_mode": False,
        "source_fetch_complete": True,
        "holdout_accessed": False,
        "locked_2026_accessed": False,
        "raw_pages": [{"page": page.name, "sha256": sha256_file(page)}],
    }
    (root / "source_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


def check_exact_30_day_inclusive() -> None:
    day = datetime(2021, 4, 1, 12, 0, tzinfo=UTC)
    root = build_root(make_day_rows(day, "01MAY21"))
    out = canonical_calendar_day_coverage(root)
    assert out["valid_signal_coverage_days"] == 1, out
    assert out["eligible_trade_rows"] == 10, out


def check_exact_120_day_inclusive() -> None:
    day = datetime(2021, 4, 1, 12, 0, tzinfo=UTC)
    root = build_root(make_day_rows(day, "30JUL21"))  # 120 calendar days after Apr 1
    out = canonical_calendar_day_coverage(root)
    assert out["valid_signal_coverage_days"] == 1, out
    assert out["eligible_trade_rows"] == 10, out


def check_29_and_121_day_excluded() -> None:
    day = datetime(2021, 4, 1, 12, 0, tzinfo=UTC)
    for expiry in ("30APR21", "31JUL21"):
        root = build_root(make_day_rows(day, expiry))
        out = canonical_calendar_day_coverage(root)
        assert out["valid_signal_coverage_days"] == 0, (expiry, out)
        assert out["eligible_trade_rows"] == 0, (expiry, out)


def main() -> None:
    check_exact_30_day_inclusive()
    check_exact_120_day_inclusive()
    check_29_and_121_day_excluded()
    print("CALENDAR_DAY_DTE_BOUNDARY_TESTS_PASS")
    print("30/120 INCLUDED | 29/121 EXCLUDED")
    print("NO SKEW / NO SIGNALS / NO RETURNS / NO PNL")


if __name__ == "__main__":
    main()
