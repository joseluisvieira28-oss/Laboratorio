#!/usr/bin/env python3
"""
ONCHAIN-CAPFLOW-001 V0.1A — data audit only.

Verifies hashes, source coverage and holdout isolation. Does not calculate
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
WARMUP_START = dt.datetime(2020, 1, 1, tzinfo=UTC)
DISCOVERY_END = dt.datetime(2025, 1, 1, tzinfo=UTC)
HOLDOUT_START = DISCOVERY_END
PROTOCOL_SHA256 = "1c6c66b7188694bcc2d62cb83ee050a023fba7f97388bc87933ed668d3392b65"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_iso_time(value: str) -> dt.datetime:
    text = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_coinmetrics_pages(paths: list[Path]) -> dict[str, list[tuple[dt.datetime, float]]]:
    out: dict[str, list[tuple[dt.datetime, float]]] = {"usdt": [], "usdc": []}
    if not paths:
        raise ValueError("no Coin Metrics stablecoin pages found")
    for path in paths:
        obj = json.loads(path.read_text(encoding="utf-8"))
        data = obj.get("data")
        if not isinstance(data, list):
            raise ValueError(f"{path}: missing data[]")
        for row in data:
            if not isinstance(row, dict):
                continue
            asset = str(row.get("asset", "")).lower()
            if asset not in out:
                continue
            t_raw = row.get("time")
            v_raw = row.get("SplyCur")
            if not isinstance(t_raw, str) or v_raw is None:
                continue
            try:
                value = float(v_raw)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(value) or value <= 0:
                continue
            out[asset].append((parse_iso_time(t_raw), value))
    return {k: sorted(v) for k, v in out.items()}


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
    gate_path = root / "data_gate_status.json"
    report_path = root / "data_audit_report.json"

    checks: list[dict[str, Any]] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
    except Exception as e:
        report = {
            "lab_id": "ONCHAIN-CAPFLOW-001",
            "version": "V0.1A",
            "status": "BLOCKED",
            "error": str(e),
            "checks": [],
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print("BLOCKED: manifest or data-source gate unreadable")
        return 2

    add_check(checks, "data_source_gate_pass", gate.get("status") == "PASS", gate)
    add_check(checks, "protocol_hash_match", manifest.get("protocol_sha256") == PROTOCOL_SHA256, manifest.get("protocol_sha256"))
    add_check(checks, "manifest_holdout_not_accessed", manifest.get("holdout_accessed") is False, manifest.get("holdout_accessed"))
    add_check(checks, "manifest_2026_not_accessed", manifest.get("locked_2026_accessed") is False, manifest.get("locked_2026_accessed"))

    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        entries = []
        add_check(checks, "manifest_entries_list", False, "entries is not a list")

    for entry in entries:
        path = root / entry["relative_path"]
        exists = path.exists()
        add_check(checks, f"exists:{entry['name']}", exists, str(path))
        if exists:
            actual = sha256_file(path)
            add_check(checks, f"sha256:{entry['name']}", actual == entry.get("sha256"), actual)

    cm_pages = sorted((root / "raw/coinmetrics").glob("stablecoin_supply_page_*.json"))
    try:
        stable = parse_coinmetrics_pages(cm_pages)
        for asset in ("usdt", "usdc"):
            series = stable[asset]
            if not series:
                raise ValueError(f"{asset}: no usable SplyCur records")
            times = [t for t, _ in series]
            add_check(checks, f"{asset}_no_duplicate_dates", duplicates(times) == 0, duplicates(times))
            add_check(checks, f"{asset}_starts_by_2020", min(times) <= WARMUP_START + dt.timedelta(days=2), min(times).isoformat())
            add_check(checks, f"{asset}_covers_through_2024", max(times) >= DISCOVERY_END - dt.timedelta(days=2), max(times).isoformat())
            add_check(checks, f"{asset}_no_2025_plus", max(times) < HOLDOUT_START, max(times).isoformat())
            add_check(checks, f"{asset}_daily_gap_le_2d", max_gap_days(times) <= 2.01, max_gap_days(times))
            add_check(checks, f"{asset}_positive_supply", all(v > 0 and math.isfinite(v) for _, v in series), len(series))
    except Exception as e:
        add_check(checks, "coinmetrics_parse", False, str(e))

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
        "version": "V0.1A",
        "protocol_sha256": PROTOCOL_SHA256,
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
