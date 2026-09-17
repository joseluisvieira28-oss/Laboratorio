#!/usr/bin/env python3
"""ORDERBOOK-RESILIENCE-001 source-only schema/cadence probe.

Does not read or retain depth/notional economic values.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import statistics
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

LAB_ID = "ORDERBOOK-RESILIENCE-001"
DATES = ["2023-01-01", "2023-06-15", "2024-01-15", "2024-12-15"]
BASE = "https://data.binance.vision/data/futures/um/daily/bookDepth/BTCUSDT"
EXPECTED_HEADER = ["timestamp", "percentage", "depth", "notional"]


def parse_ts(v: str) -> int:
    s = v.strip()
    if s.isdigit():
        x = int(s)
        return x if x > 10_000_000_000 else x * 1000
    # Binance bookDepth historically uses e.g. 2023-01-01 00:00:00
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def probe_date(day: str) -> dict:
    url = f"{BASE}/BTCUSDT-bookDepth-{day}.zip"
    r = requests.get(url, timeout=60, headers={"User-Agent": f"{LAB_ID}/source-probe-v0.1"})
    status = r.status_code
    if status != 200:
        return {"date": day, "url": url, "status": status, "ok": False, "failure": f"HTTP_{status}"}
    raw = r.content
    sha = hashlib.sha256(raw).hexdigest()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = zf.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected archive members for {day}: {names}")
        with zf.open(names[0], "r") as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8-sig", newline="")
            reader = csv.reader(text)
            header = next(reader)
            timestamps = []
            pct_labels = set()
            rows = 0
            for row in reader:
                if not row:
                    continue
                if len(row) != len(header):
                    raise RuntimeError(f"ragged row on {day}")
                rows += 1
                # Only structural fields timestamp and percentage are opened.
                timestamps.append(parse_ts(row[0]))
                pct_labels.add(row[1].strip())
                # row[2] depth and row[3] notional are intentionally never parsed.
    unique_ts = sorted(set(timestamps))
    if len(unique_ts) < 2:
        raise RuntimeError(f"insufficient snapshot timestamps on {day}")
    diffs = [b - a for a, b in zip(unique_ts, unique_ts[1:]) if b >= a]
    median_ms = statistics.median(diffs)
    p95_ms = sorted(diffs)[max(0, min(len(diffs)-1, int(0.95 * (len(diffs)-1))))]
    rows_per_snapshot = rows / len(unique_ts)
    return {
        "date": day,
        "url": url,
        "status": status,
        "ok": True,
        "archive_bytes": len(raw),
        "archive_sha256": sha,
        "member": names[0],
        "header": header,
        "row_count": rows,
        "unique_snapshot_count": len(unique_ts),
        "percentage_labels": sorted(pct_labels),
        "rows_per_snapshot": rows_per_snapshot,
        "median_snapshot_interval_ms": median_ms,
        "p95_snapshot_interval_ms": p95_ms,
        "first_timestamp_ms": unique_ts[0],
        "last_timestamp_ms": unique_ts[-1],
        "depth_values_opened": False,
        "notional_values_opened": False,
    }


def main() -> int:
    probes = []
    failure = None
    try:
        probes = [probe_date(d) for d in DATES]
        if not all(p.get("ok") for p in probes):
            classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        elif any(p.get("header") != EXPECTED_HEADER for p in probes):
            classification = "PROVENANCE_FAILURE"
        else:
            temporal_ok = all(
                float(p["median_snapshot_interval_ms"]) <= 5_000 and
                float(p["p95_snapshot_interval_ms"]) <= 10_000
                for p in probes
            )
            # Percentage-band schema is structurally aggregated, not reconstructable near-touch L2.
            pct_band_semantics = all(len(p.get("percentage_labels") or []) > 0 for p in probes)
            if not temporal_ok:
                classification = "SOURCE_TEMPORAL_RESOLUTION_FAIL"
            elif pct_band_semantics:
                classification = "SOURCE_SEMANTICS_TOO_COARSE_FOR_TRUE_REFILL"
            else:
                classification = "SOURCE_SCHEMA_PASS"
    except Exception as exc:
        classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:500]}"

    receipt = {
        "lab_id": LAB_ID,
        "phase": "SOURCE_SCHEMA_ONLY_OUTCOME_BLIND",
        "classification": classification,
        "probe_dates": DATES,
        "probes": probes,
        "failure": failure,
        "safety": {
            "depth_values_opened": False,
            "notional_values_opened": False,
            "price_series_opened": False,
            "returns_opened": False,
            "future_impact_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    out = Path("source_probe_output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "ORDERBOOK_RESILIENCE_001_SOURCE_SCHEMA_RECEIPT_V0_1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "lab_id": LAB_ID,
        "classification": classification,
        "probe_files_ok": sum(1 for p in probes if p.get("ok")),
        "median_intervals_ms": [p.get("median_snapshot_interval_ms") for p in probes if p.get("ok")],
        "schema_headers": [p.get("header") for p in probes if p.get("ok")],
        "economic_values_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    # A scientific source inadequacy is a completed probe, not an infrastructure crash.
    return 0 if classification in {
        "SOURCE_SCHEMA_PASS", "SOURCE_TEMPORAL_RESOLUTION_FAIL",
        "SOURCE_SEMANTICS_TOO_COARSE_FOR_TRUE_REFILL"
    } else 2

if __name__ == "__main__":
    sys.exit(main())
