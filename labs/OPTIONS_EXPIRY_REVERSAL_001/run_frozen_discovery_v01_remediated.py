#!/usr/bin/env python3
"""Pre-outcome technical remediation wrapper for OPTIONS-EXPIRY-REVERSAL-001.

Scientific logic remains in run_frozen_discovery_v01.py unchanged.
This wrapper replaces only BTC price acquisition with a deterministic same-source
fallback: official Binance Vision monthly BTCUSDT Spot 1m archive first, then
official daily BTCUSDT Spot 1m archive for any protected date missing one or more
of the four exact required minute opens. Both paths require official CHECKSUMs.

No interpolation. No alternative exchange. No date dropping. No 2025/2026.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import importlib.util
import io
import json
import math
import sys
import zipfile
from pathlib import Path

RUNNER_PATH = Path("labs/OPTIONS_EXPIRY_REVERSAL_001/run_frozen_discovery_v01.py")
REMEDIATION_PATH = Path("labs/OPTIONS_EXPIRY_REVERSAL_001/PRE_OUTCOME_TECHNICAL_REMEDIATION_001.md")
INITIAL_FAILED_RUN_ID = 34900018454
DAILY_BASE = "https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1m"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_original():
    spec = importlib.util.spec_from_file_location("oer_frozen_v01", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen original runner")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def acquire_prices_with_daily_fallback(mod, target_dates: set[dt.date], out: Path):
    prices: dict[dt.date, dict[str, float]] = {d: {} for d in target_dates}
    archives: list[dict] = []

    # 1) Original monthly path, unchanged in market/symbol/interval/timestamps.
    for y, m in mod.month_iter(mod.START_DATE, mod.END_DATE):
        if y >= 2025:
            raise RuntimeError("forbidden archive year")
        name = f"BTCUSDT-1m-{y:04d}-{m:02d}.zip"
        url = f"{mod.BASE}/{name}"
        checksum_url = url + ".CHECKSUM"
        checksum_raw = mod.http_get(checksum_url)
        expected = mod.parse_checksum(checksum_raw, name)
        blob = mod.http_get(url)
        actual = mod.sha256_bytes(blob)
        if actual != expected:
            raise RuntimeError(f"official Binance checksum mismatch {name}")
        z = zipfile.ZipFile(io.BytesIO(blob))
        names = z.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected Binance ZIP member count {name}: {names}")
        member = names[0]
        rows_seen = 0
        required_seen = 0
        with z.open(member, "r") as raw:
            txt = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            for row in csv.reader(txt):
                if not row:
                    continue
                if len(row) < 5:
                    raise RuntimeError(f"short Binance row in {name}")
                try:
                    open_ts = int(row[0])
                    open_px = float(row[1])
                except ValueError:
                    if rows_seen == 0:
                        continue
                    raise
                rows_seen += 1
                if open_ts >= 10**14:
                    raise RuntimeError(f"unexpected timestamp unit before 2025 in {name}: {open_ts}")
                ts = dt.datetime.fromtimestamp(open_ts / 1000, tz=mod.UTC)
                if ts.year != y or ts.month != m:
                    raise RuntimeError(f"timestamp outside archive month {name}: {ts.isoformat()}")
                d = ts.date()
                if d not in target_dates:
                    continue
                key = mod.TARGET_MINUTES.get((ts.hour, ts.minute))
                if key is None or ts.second != 0 or ts.microsecond != 0:
                    continue
                if key in prices[d]:
                    raise RuntimeError(f"duplicate exact minute {d} {key}")
                if not math.isfinite(open_px) or open_px <= 0:
                    raise RuntimeError(f"invalid open price {d} {key}")
                prices[d][key] = open_px
                required_seen += 1
        archives.append({
            "source_scope": "monthly",
            "name": name,
            "url": url,
            "checksum_url": checksum_url,
            "sha256": actual,
            "bytes": len(blob),
            "rows_seen": rows_seen,
            "required_points_seen": required_seen,
        })

    required_keys = set(mod.TARGET_MINUTES.values())
    missing_before = {
        d: sorted(required_keys - set(v))
        for d, v in prices.items()
        if len(v) != len(required_keys)
    }

    # 2) Same official source, daily granularity, only for missing exact points.
    for d in sorted(missing_before):
        if d.year >= 2025:
            raise RuntimeError("forbidden daily fallback year")
        name = f"BTCUSDT-1m-{d.isoformat()}.zip"
        url = f"{DAILY_BASE}/{name}"
        checksum_url = url + ".CHECKSUM"
        checksum_raw = mod.http_get(checksum_url)
        expected = mod.parse_checksum(checksum_raw, name)
        blob = mod.http_get(url)
        actual = mod.sha256_bytes(blob)
        if actual != expected:
            raise RuntimeError(f"official Binance daily checksum mismatch {name}")
        z = zipfile.ZipFile(io.BytesIO(blob))
        names = z.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected Binance daily ZIP member count {name}: {names}")
        member = names[0]
        rows_seen = 0
        filled = []
        with z.open(member, "r") as raw:
            txt = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            for row in csv.reader(txt):
                if not row:
                    continue
                if len(row) < 5:
                    raise RuntimeError(f"short Binance daily row in {name}")
                try:
                    open_ts = int(row[0])
                    open_px = float(row[1])
                except ValueError:
                    if rows_seen == 0:
                        continue
                    raise
                rows_seen += 1
                if open_ts >= 10**14:
                    raise RuntimeError(f"unexpected daily timestamp unit before 2025 in {name}: {open_ts}")
                ts = dt.datetime.fromtimestamp(open_ts / 1000, tz=mod.UTC)
                if ts.date() != d:
                    raise RuntimeError(f"timestamp outside daily archive date {name}: {ts.isoformat()}")
                key = mod.TARGET_MINUTES.get((ts.hour, ts.minute))
                if key is None or ts.second != 0 or ts.microsecond != 0:
                    continue
                if key not in missing_before[d]:
                    continue
                if key in prices[d]:
                    raise RuntimeError(f"daily fallback would overwrite existing exact minute {d} {key}")
                if not math.isfinite(open_px) or open_px <= 0:
                    raise RuntimeError(f"invalid daily fallback open price {d} {key}")
                prices[d][key] = open_px
                filled.append(key)
        archives.append({
            "source_scope": "daily_fallback",
            "date": d.isoformat(),
            "name": name,
            "url": url,
            "checksum_url": checksum_url,
            "sha256": actual,
            "bytes": len(blob),
            "rows_seen": rows_seen,
            "missing_before": missing_before[d],
            "filled_exact_points": sorted(filled),
        })

    missing_after = {
        d.isoformat(): sorted(required_keys - set(v))
        for d, v in prices.items()
        if len(v) != len(required_keys)
    }
    if missing_after:
        raise RuntimeError(
            "missing exact protected one-minute points after official daily fallback: "
            f"{list(missing_after.items())[:10]}"
        )

    archives.append({
        "technical_remediation": "BINANCE_DAILY_FALLBACK_V01",
        "initial_failed_run_id": INITIAL_FAILED_RUN_ID,
        "dates_requiring_daily_fallback": [d.isoformat() for d in sorted(missing_before)],
        "fallback_date_count": len(missing_before),
        "no_interpolation": True,
        "no_alternative_exchange": True,
        "no_date_dropping": True,
    })
    return prices, archives


def main() -> int:
    if not RUNNER_PATH.exists() or not REMEDIATION_PATH.exists():
        raise RuntimeError("frozen runner/remediation authority missing")
    mod = load_original()

    def patched(target_dates, out):
        return acquire_prices_with_daily_fallback(mod, target_dates, out)

    mod.acquire_prices = patched
    rc = int(mod.main())
    if rc != 0:
        return rc

    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("artifacts/options_expiry_reversal_discovery_v01")
    receipt_path = out / "DISCOVERY_RECEIPT.json"
    if not receipt_path.exists():
        raise RuntimeError("Discovery completed without receipt")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["technical_remediation"] = {
        "id": "BINANCE_DAILY_FALLBACK_V01",
        "authority_file": str(REMEDIATION_PATH),
        "authority_sha256": sha256_file(REMEDIATION_PATH),
        "initial_failed_run_id": INITIAL_FAILED_RUN_ID,
        "initial_failure_classification": "TECHNICAL_FAILURE_PREOUTCOME",
        "outcomes_computed_in_initial_failed_run": False,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("FINAL_REMEDIATED_DISCOVERY_RECEIPT")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
