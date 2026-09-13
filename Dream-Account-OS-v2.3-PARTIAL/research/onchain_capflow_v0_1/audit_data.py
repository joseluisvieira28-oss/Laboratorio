#!/usr/bin/env python3
"""
ONCHAIN-CAPFLOW-001 V0.1 — data audit only.

This script verifies raw hashes and source coverage. It does not calculate
forward returns, PnL, win rate, Sharpe, or any other outcome metric.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import zipfile
from pathlib import Path
from typing import Any

UTC = dt.timezone.utc
HOLDOUT_START = dt.datetime(2025, 1, 1, tzinfo=UTC)
WARMUP_START = dt.datetime(2020, 1, 1, tzinfo=UTC)
DISCOVERY_END = dt.datetime(2025, 1, 1, tzinfo=UTC)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pegged_usd(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        v = value.get("peggedUSD")
        if isinstance(v, (int, float)):
            return float(v)
    return None


def parse_stablecoin(path: Path) -> list[tuple[dt.datetime, float]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    tokens = obj.get("tokens")
    if not isinstance(tokens, list):
        raise ValueError(f"{path}: missing tokens[]")
    out: list[tuple[dt.datetime, float]] = []
    for row in tokens:
        if not isinstance(row, dict):
            continue
        ts = row.get("date")
        circ = pegged_usd(row.get("circulating"))
        if not isinstance(ts, (int, float)) or circ is None or not math.isfinite(circ):
            continue
        t = dt.datetime.fromtimestamp(float(ts), tz=UTC)
        out.append((t, circ))
    if not out:
        raise ValueError(f"{path}: no usable circulating history")
    return sorted(out)


def parse_binance_zip(path: Path) -> list[tuple[dt.datetime, float]]:
    rows: list[tuple[dt.datetime, float]] = []
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if len(names) != 1:
            raise ValueError(f"{path}: expected one CSV member, got {len(names)}")
        with zf.open(names[0]) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            for row in reader:
                if not row:
                    continue
                try:
                    open_ms = int(row[0])
                    open_px = float(row[1])
                except (ValueError, IndexError):
                    if row[0].lower().startswith("open"):
                        continue
                    raise
                t = dt.datetime.fromtimestamp(open_ms / 1000.0, tz=UTC)
                rows.append((t, open_px))
    return rows


def duplicates(times: list[dt.datetime]) -> int:
    return len(times) - len(set(times))


def max_gap_days(times: list[dt.datetime]) -> float:
    uniq = sorted(set(times))
    if len(uniq) < 2:
        return float("inf")
    return max((b - a).total_seconds() / 86400.0 for a, b in zip(uniq, uniq[1:]))


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"name": name, "pass": bool(passed), "detail": detail})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data", help="data directory created by acquire_data.py")
    args = parser.parse_args()
    root = Path(args.data).resolve()
    manifest_path = root / "raw_manifest.json"
    report_path = root / "data_audit_report.json"

    checks: list[dict[str, Any]] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        report = {"lab_id": "ONCHAIN-CAPFLOW-001", "status": "BLOCKED", "error": str(e), "checks": []}
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print("BLOCKED: manifest unreadable")
        return 2

    add_check(checks, "manifest_holdout_not_accessed", manifest.get("holdout_accessed") is False, manifest.get("holdout_accessed"))
    add_check(checks, "manifest_2026_not_accessed", manifest.get("locked_2026_accessed") is False, manifest.get("locked_2026_accessed"))

    for entry in manifest.get("entries", []):
        path = root / entry["relative_path"]
        exists = path.exists()
        add_check(checks, f"exists:{entry['name']}", exists, str(path))
        if exists:
            actual = sha256_file(path)
            add_check(checks, f"sha256:{entry['name']}", actual == entry.get("sha256"), actual)

    for name in ("usdt", "usdc"):
        path = root / f"raw/defillama/{name}.json"
        try:
            series = parse_stablecoin(path)
            times = [t for t, _ in series]
            add_check(checks, f"{name}_no_duplicate_dates", duplicates(times) == 0, duplicates(times))
            add_check(checks, f"{name}_starts_by_2020", min(times) <= WARMUP_START, min(times).isoformat())
            add_check(checks, f"{name}_covers_through_2024", max(times) >= DISCOVERY_END - dt.timedelta(days=1), max(times).isoformat())
            add_check(checks, f"{name}_no_2025_plus", max(times) < HOLDOUT_START, max(times).isoformat())
            add_check(checks, f"{name}_max_gap_le_2d", max_gap_days(times) <= 2.0, max_gap_days(times))
        except Exception as e:
            add_check(checks, f"{name}_parse", False, str(e))

    for symbol in ("BTCUSDT", "ETHUSDT"):
        all_rows: list[tuple[dt.datetime, float]] = []
        symbol_dir = root / f"raw/binance/{symbol}"
        try:
            files = sorted(symbol_dir.glob(f"{symbol}-1d-*.zip"))
            add_check(checks, f"{symbol}_archive_count_60", len(files) == 60, len(files))
            for path in files:
                all_rows.extend(parse_binance_zip(path))
            times = [t for t, _ in all_rows]
            add_check(checks, f"{symbol}_no_duplicate_opens", duplicates(times) == 0, duplicates(times))
            add_check(checks, f"{symbol}_starts_2020", min(times) <= WARMUP_START, min(times).isoformat())
            add_check(checks, f"{symbol}_covers_2024", max(times) >= DISCOVERY_END - dt.timedelta(days=1), max(times).isoformat())
            add_check(checks, f"{symbol}_no_2025_plus", max(times) < HOLDOUT_START, max(times).isoformat())
            add_check(checks, f"{symbol}_daily_continuity", max_gap_days(times) <= 1.01, max_gap_days(times))
            add_check(checks, f"{symbol}_positive_prices", all(px > 0 and math.isfinite(px) for _, px in all_rows), len(all_rows))
        except Exception as e:
            add_check(checks, f"{symbol}_parse", False, str(e))

    status = "PASS" if checks and all(c["pass"] for c in checks) else "BLOCKED"
    report = {
        "lab_id": "ONCHAIN-CAPFLOW-001",
        "version": "V0.1",
        "stage": "DATA_AUDIT_ONLY",
        "status": status,
        "outcome_metrics_computed": False,
        "holdout_accessed": False,
        "locked_2026_accessed": False,
        "checks": checks,
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"{status}: wrote {report_path}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
