#!/usr/bin/env python3
"""LL-0017 positioning-ratio source schema probe V0.1.

Outcome-blind source gate. It verifies provider bytes/checksums, CSV schema,
row/timestamp structure and cadence only. It never converts or summarizes
positioning-ratio values, prices, returns or PnL.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import requests

LAB_ID = "LL-0017-POSITIONING-RATIO-001"
MVE_ID = "LL17-BTCUSDT-METRICS-SCHEMA-001"
BASE = "https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"
DATES = ["2021-01-15", "2022-06-15", "2023-06-15", "2024-12-15"]
SYMBOL = "BTCUSDT"
TIMEOUT = (15, 120)

EXPECTED_FIELDS = {
    "top_trader_account_ratio": "count_toptrader_long_short_ratio",
    "top_trader_position_ratio": "sum_toptrader_long_short_ratio",
    "global_account_ratio": "count_long_short_ratio",
}

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def get(url: str) -> requests.Response:
    if "2025" in url or "2026" in url:
        raise RuntimeError("protected-period URL rejected")
    r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": f"{LAB_ID}/source-schema-v0.1"})
    return r

def parse_checksum(text: str) -> str:
    m = re.search(r"\b([0-9a-fA-F]{64})\b", text)
    if not m:
        raise ValueError("provider checksum SHA256 not found")
    return m.group(1).lower()

def parse_timestamp(raw: str) -> int:
    s = raw.strip()
    if re.fullmatch(r"\d+", s):
        n = int(s)
        # milliseconds/microseconds/nanoseconds normalization
        if n > 10**17:
            return n // 10**9
        if n > 10**14:
            return n // 10**6
        if n > 10**11:
            return n // 1000
        return n
    s2 = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s2)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())

def utc_day(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

def main() -> int:
    outdir = Path("ll0017_source_output")
    outdir.mkdir(parents=True, exist_ok=True)
    receipt_path = outdir / "LL0017_POSITIONING_RATIO_SOURCE_SCHEMA_RECEIPT_V0_1.json"

    receipts = []
    failure_class = None
    failure = None
    common_header = None

    try:
        for day in DATES:
            zip_name = f"{SYMBOL}-metrics-{day}.zip"
            zip_url = f"{BASE}/{zip_name}"
            checksum_url = zip_url + ".CHECKSUM"

            zr = get(zip_url)
            cr = get(checksum_url)
            if zr.status_code != 200 or cr.status_code != 200:
                failure_class = "SOURCE_ACCESS_BLOCKED"
                raise RuntimeError(f"{day}: zip={zr.status_code}, checksum={cr.status_code}")

            zbytes = zr.content
            checksum_text = cr.text
            provider_sha = parse_checksum(checksum_text)
            actual_sha = sha256_bytes(zbytes)
            if provider_sha != actual_sha:
                failure_class = "SOURCE_CHECKSUM_FAILURE"
                raise RuntimeError(f"{day}: provider checksum mismatch")

            with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
                members = [x for x in zf.namelist() if not x.endswith("/")]
                if len(members) != 1 or not members[0].lower().endswith(".csv"):
                    failure_class = "SOURCE_SCHEMA_INADEQUATE"
                    raise RuntimeError(f"{day}: expected exactly one CSV member, got {members}")
                raw = zf.read(members[0])

            text = raw.decode("utf-8-sig")
            reader = csv.reader(io.StringIO(text))
            try:
                header = next(reader)
            except StopIteration:
                failure_class = "SOURCE_SCHEMA_INADEQUATE"
                raise RuntimeError(f"{day}: empty CSV")

            header = [x.strip() for x in header]
            lower = [x.lower() for x in header]
            if common_header is None:
                common_header = header
            elif header != common_header:
                failure_class = "PROVENANCE_FAILURE"
                raise RuntimeError(f"{day}: header differs from prior probes")

            semantic = {k: (v in lower) for k, v in EXPECTED_FIELDS.items()}
            if not all(semantic.values()):
                failure_class = "SOURCE_SCHEMA_INADEQUATE"
                raise RuntimeError(f"{day}: missing required positioning fields; header={header}")

            # Timestamp field identity: exact provider header only.
            ts_candidates = [x for x in ("create_time", "timestamp", "time") if x in lower]
            if len(ts_candidates) != 1:
                failure_class = "SOURCE_SCHEMA_INADEQUATE"
                raise RuntimeError(f"{day}: ambiguous/missing timestamp field; header={header}")
            ts_idx = lower.index(ts_candidates[0])

            timestamps = []
            row_count = 0
            for row in reader:
                if not row:
                    continue
                if len(row) != len(header):
                    failure_class = "PROVENANCE_FAILURE"
                    raise RuntimeError(f"{day}: malformed row width")
                # Deliberately parse ONLY timestamp. All metric fields remain opaque strings.
                timestamps.append(parse_timestamp(row[ts_idx]))
                row_count += 1

            unique = sorted(set(timestamps))
            duplicates = row_count - len(unique)
            if row_count < 200 or len(unique) < 200:
                failure_class = "SOURCE_TEMPORAL_COVERAGE_INADEQUATE"
                raise RuntimeError(f"{day}: insufficient timestamps rows={row_count}, unique={len(unique)}")
            if duplicates != 0:
                failure_class = "PROVENANCE_FAILURE"
                raise RuntimeError(f"{day}: duplicate timestamps={duplicates}")
            outside = [x for x in unique if utc_day(x) != day]
            if outside:
                failure_class = "PROVENANCE_FAILURE"
                raise RuntimeError(f"{day}: timestamp outside requested UTC day")
            diffs = [b-a for a,b in zip(unique, unique[1:])]
            med = median(diffs) if diffs else None
            p95 = sorted(diffs)[max(0, min(len(diffs)-1, int(0.95*(len(diffs)-1))))] if diffs else None
            max_gap = max(diffs) if diffs else None
            if med is None or med > 600:
                failure_class = "SOURCE_TEMPORAL_COVERAGE_INADEQUATE"
                raise RuntimeError(f"{day}: median interval {med} exceeds 600s")

            receipts.append({
                "date": day,
                "zip_url": zip_url,
                "checksum_url": checksum_url,
                "provider_sha256": provider_sha,
                "archive_sha256": actual_sha,
                "archive_bytes": len(zbytes),
                "csv_member": members[0],
                "csv_header": header,
                "positioning_field_presence": semantic,
                "timestamp_field": ts_candidates[0],
                "row_count": row_count,
                "unique_timestamp_count": len(unique),
                "duplicate_timestamp_count": duplicates,
                "median_interval_seconds": med,
                "p95_interval_seconds": p95,
                "max_gap_seconds": max_gap,
                "first_timestamp_utc": datetime.fromtimestamp(unique[0], tz=timezone.utc).isoformat(),
                "last_timestamp_utc": datetime.fromtimestamp(unique[-1], tz=timezone.utc).isoformat(),
            })

        classification = "SOURCE_SCHEMA_PASS"
    except requests.RequestException as exc:
        classification = failure_class or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:1000]}"
    except Exception as exc:
        classification = failure_class or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:1500]}"

    receipt = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "phase": "SOURCE_SCHEMA_ONLY_OUTCOME_BLIND",
        "classification": classification,
        "failure": failure,
        "frozen_probe_dates": DATES,
        "symbol": SYMBOL,
        "source": BASE,
        "expected_positioning_fields": EXPECTED_FIELDS,
        "probe_results": receipts,
        "common_header": common_header,
        "safety": {
            "ratio_numeric_values_parsed": False,
            "ratio_numeric_values_persisted": False,
            "open_interest_values_parsed": False,
            "taker_values_parsed": False,
            "prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "2025_accessed": False,
            "2026_accessed": False,
            "authenticated_exchange_access": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": classification,
        "failure": failure,
        "probe_count": len(receipts),
        "header": common_header,
        "ratio_values_parsed": False,
        "prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if classification == "SOURCE_SCHEMA_PASS" else 2

if __name__ == "__main__":
    sys.exit(main())
