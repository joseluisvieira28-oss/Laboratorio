#!/usr/bin/env python3
"""Build the protected trade-derived expiry-intensity source series.

Reads ONLY immutable Deribit BTC option-trade raw pages from the prior
OPTIONS-SPOTPERP-001 source artifact plus its source-gate receipts.

No BTC price data, no returns, no PnL, no 2025/2026.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

UTC = dt.timezone.utc
LAB_ID = "OPTIONS-EXPIRY-REVERSAL-001"
MVE_ID = "OER-BTC-EXPIRY-INTENSITY-30M-001"
SOURCE_RUN_ID = 34774293327
SOURCE_GATE_RUN_ID = 34784590423
SOURCE_START = dt.datetime(2021, 4, 1, tzinfo=UTC)
SOURCE_END_EXCLUSIVE = dt.datetime(2025, 1, 1, tzinfo=UTC)
SIGNAL_START = dt.date(2021, 5, 2)
SIGNAL_END = dt.date(2024, 12, 31)
TRAILING_DAYS = 30

MIN_EVALUABLE_DAYS = 800
MIN_HIGH_TOTAL = 150
MIN_HIGH_BY_YEAR = {2021: 15, 2022: 30, 2023: 30, 2024: 30}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def locate_unique(root: Path, filename: str) -> Path:
    matches = [p for p in root.rglob(filename) if p.is_file()]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {filename} under {root}, found {len(matches)}")
    return matches[0]


def locate_deribit_raw(root: Path) -> Path:
    # Deliberately match only a directory whose basename is exactly 'raw'.
    # Never traverse raw_binance_btcusdt_1d or any other price directory.
    candidates = []
    for p in root.rglob("raw"):
        if p.is_dir() and any(p.glob("*.json.gz")):
            candidates.append(p)
    if len(candidates) != 1:
        raise RuntimeError(f"expected exactly one Deribit raw directory under {root}, found {len(candidates)}")
    return candidates[0]


def parse_expiry_date(name: str) -> dt.date:
    parts = name.split("-")
    if len(parts) != 4 or parts[0] != "BTC" or parts[3] not in {"C", "P"}:
        raise ValueError(name)
    expiry = dt.datetime.strptime(parts[1].upper(), "%d%b%y").date()
    strike = float(parts[2])
    if not math.isfinite(strike) or strike <= 0:
        raise ValueError(name)
    return expiry


def settlement_source_date(ts: dt.datetime) -> dt.date | None:
    """Map a trade to the settlement date whose source window contains it.

    Window for settlement d: [d-1 08:00, d 07:30). Trades in [07:30,08:00)
    are intentionally excluded from the source classifier.
    """
    tod = ts.timetz().replace(tzinfo=None)
    if tod < dt.time(7, 30):
        return ts.date()
    if tod >= dt.time(8, 0):
        return ts.date() + dt.timedelta(days=1)
    return None


def iter_trades(raw_dir: Path):
    pages = sorted(raw_dir.glob("*.json.gz"))
    if not pages:
        raise RuntimeError("no immutable Deribit raw pages found")
    for page in pages:
        with gzip.open(page, "rb") as f:
            obj = json.loads(f.read().decode("utf-8"))
        result = obj.get("result")
        trades = result.get("trades") if isinstance(result, dict) else None
        if not isinstance(trades, list):
            raise RuntimeError(f"invalid Deribit raw page schema: {page.name}")
        for row in trades:
            if isinstance(row, dict):
                yield row


def date_range(start: dt.date, end: dt.date):
    d = start
    while d <= end:
        yield d
        d += dt.timedelta(days=1)


def main() -> int:
    source_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source_artifact")
    gate_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("source_gate_artifact")
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("artifacts/options_expiry_reversal_source_v01")
    out.mkdir(parents=True, exist_ok=True)

    raw_dir = locate_deribit_raw(source_root)
    manifest_path = locate_unique(source_root, "source_manifest.json")
    report_path = locate_unique(source_root, "source_audit_report.json")
    gate_manifest_path = locate_unique(gate_root, "source_manifest.json")
    gate_report_path = locate_unique(gate_root, "source_audit_report.json")
    gate_receipt_path = locate_unique(gate_root, "source_gate_calendar_day_reconciled_receipt.json")
    protocol_path = Path("labs/OPTIONS_EXPIRY_REVERSAL_001/FROZEN_PRE_SOURCE_PROTOCOL_V0.1.md")
    if not protocol_path.exists():
        raise RuntimeError(f"missing frozen protocol: {protocol_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    gate = json.loads(gate_receipt_path.read_text(encoding="utf-8"))

    if manifest.get("source_fetch_complete") is not True or manifest.get("probe_mode") is not False:
        raise RuntimeError("prior immutable source corpus is not a complete full source acquisition")
    if manifest.get("holdout_accessed") is not False or manifest.get("locked_2026_accessed") is not False:
        raise RuntimeError("prior immutable source corpus violated protected-period flags")
    if report.get("outcome_metrics_computed") is not False:
        raise RuntimeError("prior source report unexpectedly contains outcomes")
    audit = report.get("audit") or {}
    if audit.get("forward_returns_computed") is not False or audit.get("pnl_computed") is not False:
        raise RuntimeError("prior source report unexpectedly contains return/PnL outcomes")
    if gate.get("status") != "SOURCE_AUDIT_PASS":
        raise RuntimeError(f"prior latest-code source gate is not PASS: {gate.get('status')}")
    if gate.get("holdout_2025_accessed") is not False or gate.get("year_2026_accessed") is not False:
        raise RuntimeError("prior latest-code source gate violated protected-period flags")
    if sha256_file(manifest_path) != sha256_file(gate_manifest_path):
        raise RuntimeError("raw artifact source_manifest does not match final source-gate copy")
    if sha256_file(report_path) != sha256_file(gate_report_path):
        raise RuntimeError("raw artifact source_audit_report does not match final source-gate copy")

    total_volume: dict[dt.date, float] = defaultdict(float)
    expiring_volume: dict[dt.date, float] = defaultdict(float)
    total_rows = 0
    used_rows = 0
    excluded_settlement_window = 0
    outside_signal_support = 0
    parse_failures = 0
    invalid_amount = 0
    timestamp_violations = 0
    max_timestamp_ms = 0

    for row in iter_trades(raw_dir):
        total_rows += 1
        try:
            ts_ms = int(row["timestamp"])
            ts = dt.datetime.fromtimestamp(ts_ms / 1000, tz=UTC)
        except Exception:
            timestamp_violations += 1
            continue
        max_timestamp_ms = max(max_timestamp_ms, ts_ms)
        if ts < SOURCE_START or ts >= SOURCE_END_EXCLUSIVE:
            timestamp_violations += 1
            continue
        try:
            expiry_date = parse_expiry_date(str(row.get("instrument_name", "")))
        except Exception:
            parse_failures += 1
            continue
        try:
            amount = float(row["amount"])
            if not math.isfinite(amount) or amount <= 0:
                raise ValueError
        except Exception:
            invalid_amount += 1
            continue

        d = settlement_source_date(ts)
        if d is None:
            excluded_settlement_window += 1
            continue
        if d < dt.date(2021, 4, 1) or d > SIGNAL_END:
            outside_signal_support += 1
            continue
        used_rows += 1
        total_volume[d] += amount
        if expiry_date == d:
            expiring_volume[d] += amount

    if timestamp_violations or parse_failures or invalid_amount:
        classification = "DATA_FAILURE"
    else:
        classification = "SOURCE_DATASET_PASS"

    base_start = dt.date(2021, 4, 2)
    base_rows: dict[dt.date, dict[str, Any]] = {}
    for d in date_range(base_start, SIGNAL_END):
        tv = float(total_volume.get(d, 0.0))
        ev = float(expiring_volume.get(d, 0.0))
        if ev > tv + 1e-12:
            classification = "DATA_FAILURE"
        share = ev / tv if tv > 0 else 0.0
        base_rows[d] = {"date": d, "total": tv, "expiring": ev, "share": share}

    rows: list[dict[str, Any]] = []
    high_by_year = defaultdict(int)
    for d in date_range(SIGNAL_START, SIGNAL_END):
        prior_dates = [d - dt.timedelta(days=i) for i in range(TRAILING_DAYS, 0, -1)]
        if any(x not in base_rows for x in prior_dates) or d not in base_rows:
            classification = "DATA_FAILURE"
            continue
        trailing = [base_rows[x]["share"] for x in prior_dates]
        med = float(statistics.median(trailing))
        cur = base_rows[d]
        high = int(cur["share"] > med)
        high_by_year[d.year] += high
        rows.append({
            "date": d.isoformat(),
            "total_option_volume_btc": cur["total"],
            "expiring_option_volume_btc": cur["expiring"],
            "expiry_activity_share": cur["share"],
            "trailing_30d_median_share": med,
            "high_expiry_pressure": high,
        })

    high_total = sum(int(r["high_expiry_pressure"]) for r in rows)
    sample_pass = (
        len(rows) >= MIN_EVALUABLE_DAYS
        and high_total >= MIN_HIGH_TOTAL
        and all(high_by_year.get(y, 0) >= n for y, n in MIN_HIGH_BY_YEAR.items())
    )
    if classification == "SOURCE_DATASET_PASS" and not sample_pass:
        classification = "INSUFFICIENT_SAMPLE"

    csv_path = out / "BTC_EXPIRY_INTENSITY_SOURCE_20210502_20241231.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "date", "total_option_volume_btc", "expiring_option_volume_btc",
            "expiry_activity_share", "trailing_30d_median_share", "high_expiry_pressure"
        ])
        w.writeheader()
        w.writerows(rows)

    receipt = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "classification": classification,
        "source_run_id": SOURCE_RUN_ID,
        "source_gate_run_id": SOURCE_GATE_RUN_ID,
        "source_artifact_name": "options-spotperp-001-monthly-raw-34774293327-1",
        "known_source_artifact_zip_sha256": "bcccd53db114221c948feaff5a8691f0710b7045e7dcac441c250c09eb443cda",
        "resolved_deribit_raw_dir_relative": str(raw_dir.relative_to(source_root)),
        "source_manifest_sha256": sha256_file(manifest_path),
        "source_report_sha256": sha256_file(report_path),
        "prior_source_gate_receipt_sha256": sha256_file(gate_receipt_path),
        "protocol_sha256": sha256_file(protocol_path),
        "source_csv_sha256": sha256_file(csv_path),
        "protected_signal_start": SIGNAL_START.isoformat(),
        "protected_signal_end": SIGNAL_END.isoformat(),
        "trailing_days": TRAILING_DAYS,
        "source_window": "[d-1 08:00:00 UTC, d 07:30:00 UTC)",
        "evaluable_days": len(rows),
        "high_pressure_days": high_total,
        "high_pressure_days_by_year": {str(y): high_by_year.get(y, 0) for y in sorted(MIN_HIGH_BY_YEAR)},
        "sample_thresholds": {
            "min_evaluable_days": MIN_EVALUABLE_DAYS,
            "min_high_total": MIN_HIGH_TOTAL,
            "min_high_by_year": {str(k): v for k, v in MIN_HIGH_BY_YEAR.items()},
        },
        "sample_pass": sample_pass,
        "raw_trade_rows_seen": total_rows,
        "raw_trade_rows_used_in_source_windows": used_rows,
        "excluded_0730_0800_rows": excluded_settlement_window,
        "outside_signal_support_rows": outside_signal_support,
        "instrument_parse_failures": parse_failures,
        "invalid_amount_rows": invalid_amount,
        "timestamp_violations": timestamp_violations,
        "max_raw_timestamp_ms": max_timestamp_ms,
        "btc_market_data_accessed": False,
        "btc_returns_computed": False,
        "pnl_computed": False,
        "open_interest_accessed": False,
        "gamma_exposure_computed": False,
        "access_2025": False,
        "access_2026": False,
        "live_trading": False,
        "exchange_mutation": False,
    }
    receipt_path = out / "SOURCE_DATASET_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
