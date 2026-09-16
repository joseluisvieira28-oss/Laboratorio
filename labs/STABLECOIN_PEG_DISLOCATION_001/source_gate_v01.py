#!/usr/bin/env python3
"""Outcome-blind Source/Data Gate for STABLECOIN-PEG-DISLOCATION-001.

This program MUST NOT compute or emit prices, peg deviations, returns, signal counts,
forward convergence, PnL, extrema, thresholds, or any other economic outcome.
"""
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

LAB_ID = "STABLECOIN-PEG-DISLOCATION-001"
SOURCE_GATE_ID = "SPD-USDCUSDT-SOURCE-001"
SYMBOL = "USDCUSDT"
INTERVAL = "1m"
START = dt.date(2021, 1, 1)
END = dt.date(2024, 12, 31)
EXPECTED_DAYS = 1461
BASE = f"https://data.binance.vision/data/spot/daily/klines/{SYMBOL}/{INTERVAL}"
PROBE_DATES = [
    dt.date(2021, 1, 15), dt.date(2021, 7, 15),
    dt.date(2022, 1, 15), dt.date(2022, 7, 15),
    dt.date(2023, 1, 15), dt.date(2023, 7, 15),
    dt.date(2024, 1, 15), dt.date(2024, 7, 15),
]
EXPECTED_COLS = 12
MIN_PROBE_ROWS = 1000
OUT = Path("stablecoin_peg_source_gate_artifact")
OUT.mkdir(parents=True, exist_ok=True)
UA = "CryptoLab-SourceGate/1.0 (+research-only)"
CHECKSUM_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def daterange(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        yield cur
        cur += dt.timedelta(days=1)


def urls_for(day: dt.date):
    ds = day.isoformat()
    fn = f"{SYMBOL}-{INTERVAL}-{ds}.zip"
    zurl = f"{BASE}/{fn}"
    return fn, zurl, zurl + ".CHECKSUM"


def open_url(req: urllib.request.Request, timeout: int = 25):
    return urllib.request.urlopen(req, timeout=timeout)


def zip_reachable(url: str):
    # HEAD is outcome-blind and avoids downloading the archive body.
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with open_url(req) as r:
            return int(getattr(r, "status", 200)), "HEAD"
    except urllib.error.HTTPError as e:
        if e.code not in (403, 405):
            return e.code, "HEAD"
    except Exception:
        pass

    # Transport-only fallback. Do not read the response body.
    req = urllib.request.Request(
        url, method="GET", headers={"User-Agent": UA, "Range": "bytes=0-0"}
    )
    try:
        with open_url(req) as r:
            return int(getattr(r, "status", 200)), "GET_RANGE"
    except urllib.error.HTTPError as e:
        return e.code, "GET_RANGE"
    except Exception:
        return None, "GET_RANGE"


def fetch_checksum(url: str, expected_filename: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with open_url(req) as r:
            status = int(getattr(r, "status", 200))
            text = r.read(4096).decode("utf-8", "replace").strip()
    except urllib.error.HTTPError as e:
        return {"status": e.code, "valid": False, "sha256": None, "error": f"HTTP_{e.code}"}
    except Exception as e:
        return {"status": None, "valid": False, "sha256": None, "error": type(e).__name__}

    tokens = text.split()
    sha = tokens[0] if len(tokens) >= 1 else None
    named = tokens[-1].lstrip("*") if len(tokens) >= 2 else None
    valid = bool(status == 200 and sha and CHECKSUM_RE.match(sha) and named == expected_filename)
    return {
        "status": status,
        "valid": valid,
        "sha256": sha.lower() if valid else None,
        "error": None if valid else "INVALID_CHECKSUM_FORMAT_OR_FILENAME",
    }


def check_day(day: dt.date):
    if day.year >= 2025:
        raise RuntimeError("Protected-period firewall violation")
    fn, zurl, curl = urls_for(day)
    zstatus, method = zip_reachable(zurl)
    c = fetch_checksum(curl, fn)
    return {
        "date": day.isoformat(),
        "zip_status": zstatus,
        "zip_reachable": zstatus in (200, 206),
        "zip_probe_method": method,
        "checksum_status": c["status"],
        "checksum_valid": c["valid"],
        "checksum_sha256": c["sha256"],
        "checksum_error": c["error"],
    }


def download_bytes(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with open_url(req, timeout=60) as r:
        status = int(getattr(r, "status", 200))
        if status != 200:
            raise RuntimeError(f"Unexpected HTTP status {status}")
        return r.read()


def probe_archive(day: dt.date, official_sha: str):
    if day.year >= 2025:
        raise RuntimeError("Protected-period firewall violation")
    fn, zurl, _ = urls_for(day)
    raw = download_bytes(zurl)
    got_sha = hashlib.sha256(raw).hexdigest()
    checksum_match = got_sha.lower() == official_sha.lower()

    expected_csv = fn[:-4] + ".csv"
    with zipfile.ZipFile(io.BytesIO(raw), "r") as zf:
        bad_member = zf.testzip()
        names = zf.namelist()
        if expected_csv not in names:
            raise RuntimeError(f"Expected CSV missing: {expected_csv}")
        with zf.open(expected_csv, "r") as fb:
            text = io.TextIOWrapper(fb, encoding="utf-8", newline="")
            reader = csv.reader(text)
            timestamps = []
            schema_ok = True
            skipped_header = False
            for row in reader:
                if not row:
                    continue
                if not timestamps:
                    try:
                        int(row[0])
                    except ValueError:
                        skipped_header = True
                        continue
                if len(row) != EXPECTED_COLS:
                    schema_ok = False
                    break
                # IMPORTANT: only timestamp is parsed. OHLC/volume fields are never read semantically.
                try:
                    ts = int(row[0])
                except ValueError:
                    schema_ok = False
                    break
                timestamps.append(ts)

    unique_count = len(set(timestamps))
    duplicate_count = len(timestamps) - unique_count
    day_start_ms = int(dt.datetime.combine(day, dt.time.min, tzinfo=dt.timezone.utc).timestamp() * 1000)
    next_day_ms = day_start_ms + 86_400_000
    timestamps_in_day = all(day_start_ms <= ts < next_day_ms for ts in timestamps)
    ascending = all(a < b for a, b in zip(timestamps, timestamps[1:]))
    enough_rows = len(timestamps) >= MIN_PROBE_ROWS
    valid = all([
        checksum_match,
        bad_member is None,
        schema_ok,
        duplicate_count == 0,
        timestamps_in_day,
        ascending,
        enough_rows,
    ])
    return {
        "date": day.isoformat(),
        "zip_sha256": got_sha,
        "official_checksum_match": checksum_match,
        "zip_integrity_pass": bad_member is None,
        "csv_member": expected_csv,
        "header_skipped": skipped_header,
        "expected_columns": EXPECTED_COLS,
        "schema_pass": schema_ok,
        "row_count": len(timestamps),
        "minimum_probe_rows": MIN_PROBE_ROWS,
        "minimum_rows_pass": enough_rows,
        "unique_open_timestamps": unique_count,
        "duplicate_open_timestamps": duplicate_count,
        "timestamps_in_requested_utc_date": timestamps_in_day,
        "timestamps_strictly_ascending": ascending,
        "first_open_timestamp_ms": timestamps[0] if timestamps else None,
        "last_open_timestamp_ms": timestamps[-1] if timestamps else None,
        "valid": valid,
        "price_values_emitted": False,
    }


def dump(name: str, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p


def main():
    days = list(daterange(START, END))
    if len(days) != EXPECTED_DAYS:
        raise RuntimeError(f"Calendar invariant failed: {len(days)} != {EXPECTED_DAYS}")
    if any(d.year >= 2025 for d in days):
        raise RuntimeError("Protected-period firewall violated by calendar")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as ex:
        futs = {ex.submit(check_day, d): d for d in days}
        for fut in concurrent.futures.as_completed(futs):
            d = futs[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({
                    "date": d.isoformat(),
                    "zip_status": None,
                    "zip_reachable": False,
                    "zip_probe_method": None,
                    "checksum_status": None,
                    "checksum_valid": False,
                    "checksum_sha256": None,
                    "checksum_error": type(e).__name__,
                })
    results.sort(key=lambda x: x["date"])

    zip_ok = sum(bool(r["zip_reachable"]) for r in results)
    checksum_ok = sum(bool(r["checksum_valid"]) for r in results)
    missing_dates = [r["date"] for r in results if not (r["zip_reachable"] and r["checksum_valid"])]

    probes = []
    preprobe_ok = zip_ok == EXPECTED_DAYS and checksum_ok == EXPECTED_DAYS
    technical_probe_error = None
    if preprobe_ok:
        by_date = {r["date"]: r for r in results}
        try:
            for day in PROBE_DATES:
                official_sha = by_date[day.isoformat()]["checksum_sha256"]
                probes.append(probe_archive(day, official_sha))
        except Exception as e:
            technical_probe_error = f"{type(e).__name__}: {e}"

    probe_ok = len(probes) == len(PROBE_DATES) and all(p["valid"] for p in probes)
    if not preprobe_ok:
        classification = "SOURCE_DATA_INCOMPLETE"
    elif technical_probe_error is not None:
        classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    elif not probe_ok:
        classification = "DATA_FAILURE"
    else:
        classification = "SOURCE_DATA_PASS"

    manifest = {
        "lab_id": LAB_ID,
        "source_gate_id": SOURCE_GATE_ID,
        "source": "Binance Data Vision daily spot klines",
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "window_start": START.isoformat(),
        "window_end": END.isoformat(),
        "days": results,
        "access_2025": False,
        "access_2026": False,
        "economic_outcomes_opened": False,
    }
    manifest_path = dump("source_manifest.json", manifest)
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    dump("probe_metadata.json", {
        "probe_dates": [d.isoformat() for d in PROBE_DATES],
        "probes": probes,
        "technical_probe_error": technical_probe_error,
        "price_values_emitted": False,
    })
    receipt = {
        "lab_id": LAB_ID,
        "source_gate_id": SOURCE_GATE_ID,
        "classification": classification,
        "expected_calendar_days": EXPECTED_DAYS,
        "zip_reachable_days": zip_ok,
        "checksum_valid_days": checksum_ok,
        "missing_or_invalid_days_count": len(missing_dates),
        "missing_or_invalid_dates": missing_dates,
        "probe_dates_expected": len(PROBE_DATES),
        "probe_dates_completed": len(probes),
        "probe_dates_valid": sum(bool(p.get("valid")) for p in probes),
        "source_manifest_sha256": manifest_sha,
        "access_2025": False,
        "access_2026": False,
        "economic_outcomes_opened": False,
        "peg_deviation_computed": False,
        "returns_computed": False,
        "forward_convergence_computed": False,
        "pnl_computed": False,
        "signal_counts_computed": False,
        "extrema_computed": False,
        "live_trading": False,
        "exchange_mutation": False,
        "technical_probe_error": technical_probe_error,
    }
    dump("source_gate_receipt.json", receipt)

    print(json.dumps({
        "classification": classification,
        "days": EXPECTED_DAYS,
        "zip_reachable": zip_ok,
        "checksums_valid": checksum_ok,
        "probes_valid": receipt["probe_dates_valid"],
        "access_2025": False,
        "access_2026": False,
        "economic_outcomes_opened": False,
    }, sort_keys=True))

    return 0 if classification == "SOURCE_DATA_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
