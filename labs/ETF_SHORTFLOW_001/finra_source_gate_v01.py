#!/usr/bin/env python3
"""ETF-SHORTFLOW-001 outcome-blind FINRA Source/Data Gate V0.1.

This script is intentionally prohibited from opening BTC prices, returns, PnL,
2025 data, or 2026 data. It verifies only the frozen 2024 FINRA source route,
schema, IBIT coverage, and provenance.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

LAB_ID = "ETF-SHORTFLOW-001"
MVE_ID = "ESF-IBIT-SHORTVOL-5D-001"
SYMBOL = "IBIT"
START = date(2024, 1, 11)
END = date(2024, 12, 31)
URL_TMPL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{yyyymmdd}.txt"
EXPECTED_HEADER = [
    "Date",
    "Symbol",
    "ShortVolume",
    "ShortExemptVolume",
    "TotalVolume",
    "Market",
]
HOLIDAYS = {
    date(2024, 1, 15),
    date(2024, 2, 19),
    date(2024, 3, 29),
    date(2024, 5, 27),
    date(2024, 6, 19),
    date(2024, 7, 4),
    date(2024, 9, 2),
    date(2024, 11, 28),
    date(2024, 12, 25),
}
EXPECTED_FILE_COUNT = 245
MIN_IBIT_ROWS = 240
OUT = Path("artifacts/etf_shortflow_source_gate_v01")
PROTOCOL = Path("labs/ETF_SHORTFLOW_001/PRE_DISCOVERY_PROTOCOL_V0.1.md")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return os.environ.get("GITHUB_SHA")


def expected_dates() -> list[date]:
    if START.year != 2024 or END.year != 2024:
        raise RuntimeError("PROTECTED_PERIOD_FIREWALL_BREACH")
    out: list[date] = []
    d = START
    while d <= END:
        if d.weekday() < 5 and d not in HOLIDAYS:
            out.append(d)
        d += timedelta(days=1)
    if len(out) != EXPECTED_FILE_COUNT:
        raise RuntimeError(
            f"EXPECTED_CALENDAR_MISMATCH:{len(out)}!={EXPECTED_FILE_COUNT}"
        )
    return out


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 ETF-SHORTFLOW-001 research-only source-audit"
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP_{resp.status}")
        return resp.read()


def dec(value: str, field: str, d: date) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"NON_NUMERIC_{field}_{d.isoformat()}:{value}") from exc


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "FINRA_SOURCE_MANIFEST_2024.jsonl"
    rows_path = OUT / "FINRA_IBIT_SOURCE_ROWS_2024.csv"
    receipt_path = OUT / "SOURCE_GATE_RECEIPT.json"

    access_errors: list[str] = []
    data_errors: list[str] = []
    manifest: list[dict] = []
    ibit_rows: list[dict] = []

    if not PROTOCOL.exists():
        data_errors.append("FROZEN_PROTOCOL_FILE_MISSING")
        protocol_sha = None
    else:
        protocol_sha = sha256_file(PROTOCOL)

    dates = expected_dates()

    for idx, d in enumerate(dates, start=1):
        ymd = d.strftime("%Y%m%d")
        url = URL_TMPL.format(yyyymmdd=ymd)
        entry = {
            "date": d.isoformat(),
            "url": url,
            "http_status": None,
            "bytes": None,
            "sha256": None,
            "header_ok": False,
            "ibit_row_count": 0,
        }
        try:
            raw = fetch(url)
            entry["http_status"] = 200
            entry["bytes"] = len(raw)
            entry["sha256"] = sha256_bytes(raw)

            text = raw.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text), delimiter="|")
            header = reader.fieldnames or []
            if header != EXPECTED_HEADER:
                data_errors.append(
                    f"HEADER_MISMATCH_{d.isoformat()}:{header!r}"
                )
                manifest.append(entry)
                continue
            entry["header_ok"] = True

            matches = []
            for row in reader:
                if row.get("Symbol") == SYMBOL:
                    matches.append(row)
            entry["ibit_row_count"] = len(matches)

            if len(matches) > 1:
                data_errors.append(f"DUPLICATE_IBIT_ROW_{d.isoformat()}")
                manifest.append(entry)
                continue
            if len(matches) == 0:
                manifest.append(entry)
                continue

            row = matches[0]
            if row["Date"] != ymd:
                data_errors.append(
                    f"ROW_DATE_MISMATCH_{d.isoformat()}:{row['Date']}"
                )
                manifest.append(entry)
                continue

            short = dec(row["ShortVolume"], "ShortVolume", d)
            exempt = dec(row["ShortExemptVolume"], "ShortExemptVolume", d)
            total = dec(row["TotalVolume"], "TotalVolume", d)

            if short < 0:
                data_errors.append(f"NEGATIVE_SHORT_{d.isoformat()}")
            if exempt < 0:
                data_errors.append(f"NEGATIVE_EXEMPT_{d.isoformat()}")
            if total <= 0:
                data_errors.append(f"NONPOSITIVE_TOTAL_{d.isoformat()}")
            if exempt > short:
                data_errors.append(f"EXEMPT_GT_SHORT_{d.isoformat()}")

            ibit_rows.append(
                {
                    "Date": row["Date"],
                    "Symbol": row["Symbol"],
                    "ShortVolume": row["ShortVolume"],
                    "ShortExemptVolume": row["ShortExemptVolume"],
                    "TotalVolume": row["TotalVolume"],
                    "Market": row["Market"],
                    "source_url": url,
                    "source_sha256": entry["sha256"],
                }
            )
        except urllib.error.HTTPError as exc:
            entry["http_status"] = exc.code
            access_errors.append(f"HTTP_{exc.code}_{d.isoformat()}")
        except urllib.error.URLError as exc:
            access_errors.append(f"URL_ERROR_{d.isoformat()}:{exc.reason}")
        except Exception as exc:
            data_errors.append(f"PARSE_OR_VALIDATION_{d.isoformat()}:{type(exc).__name__}:{exc}")

        manifest.append(entry)
        if idx % 25 == 0:
            print(f"source gate progress: {idx}/{len(dates)}", flush=True)
        time.sleep(0.02)

    with manifest_path.open("w", encoding="utf-8") as f:
        for item in manifest:
            f.write(json.dumps(item, sort_keys=True) + "\n")

    with rows_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Date",
                "Symbol",
                "ShortVolume",
                "ShortExemptVolume",
                "TotalVolume",
                "Market",
                "source_url",
                "source_sha256",
            ],
        )
        writer.writeheader()
        writer.writerows(ibit_rows)

    valid_files = sum(
        1
        for x in manifest
        if x["http_status"] == 200 and x["header_ok"] is True
    )

    if valid_files != EXPECTED_FILE_COUNT:
        data_errors.append(
            f"FILE_COVERAGE_FAIL:{valid_files}/{EXPECTED_FILE_COUNT}"
        )
    if len(ibit_rows) < MIN_IBIT_ROWS:
        data_errors.append(f"IBIT_COVERAGE_FAIL:{len(ibit_rows)}/{EXPECTED_FILE_COUNT}")

    source_dates_after_2024 = [
        x["Date"] for x in ibit_rows if int(x["Date"][0:4]) > 2024
    ]
    if source_dates_after_2024:
        data_errors.append("PROTECTED_PERIOD_SOURCE_BREACH")

    if access_errors:
        classification = "SOURCE_ACCESS_BLOCKED"
    elif data_errors:
        classification = "DATA_FAILURE"
    else:
        classification = "SOURCE_DATA_PASS"

    receipt = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "classification": classification,
        "git_head": git_head(),
        "frozen_protocol_sha256": protocol_sha,
        "source": "FINRA Consolidated NMS Daily Short Sale Volume",
        "symbol": SYMBOL,
        "window_start": START.isoformat(),
        "window_end": END.isoformat(),
        "expected_source_dates": EXPECTED_FILE_COUNT,
        "valid_source_files": valid_files,
        "ibit_rows": len(ibit_rows),
        "minimum_ibit_rows_required": MIN_IBIT_ROWS,
        "access_2025": False,
        "access_2026": False,
        "btc_market_data_accessed": False,
        "signal_computed": False,
        "returns_computed": False,
        "pnl_computed": False,
        "access_errors": access_errors,
        "data_errors": data_errors,
        "manifest_sha256": sha256_file(manifest_path),
        "ibit_rows_sha256": sha256_file(rows_path),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if classification == "SOURCE_DATA_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
