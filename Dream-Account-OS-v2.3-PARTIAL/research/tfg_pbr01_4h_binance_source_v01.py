#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

LAB_ID = "TFG-PBR01-4H-XVENUE-BINANCE-001"
AUTHORITY_COMMIT = "6703e683f59d5d5c322f119895d6d3e89a88857f"
BASE_URL = "https://data.binance.vision/data/spot/monthly/klines"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
INTERVAL = "15m"
START_MONTH = "2023-02"
END_MONTH = "2024-12"
FIFTEEN_MIN_MS = 15 * 60 * 1000


def months(start: str, end: str) -> list[str]:
    cur = datetime.strptime(start, "%Y-%m")
    finish = datetime.strptime(end, "%Y-%m")
    out: list[str] = []
    while cur <= finish:
        out.append(cur.strftime("%Y-%m"))
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)
    return out


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "crypto-lab-research/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def parse_checksum(raw: bytes, filename: str) -> str:
    text = raw.decode("utf-8").strip()
    parts = text.split()
    if not parts or len(parts[0]) != 64:
        raise RuntimeError(f"invalid checksum payload for {filename}")
    if len(parts) > 1 and Path(parts[-1].lstrip("*")).name != filename:
        raise RuntimeError(f"checksum filename mismatch for {filename}")
    return parts[0].lower()


def validate_archive(data: bytes, symbol: str, month: str) -> dict:
    expected_prefix = datetime.strptime(month + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)
    month_start_ms = int(expected_prefix.timestamp() * 1000)
    if expected_prefix.month == 12:
        nxt = expected_prefix.replace(year=expected_prefix.year + 1, month=1)
    else:
        nxt = expected_prefix.replace(month=expected_prefix.month + 1)
    month_end_ms = int(nxt.timestamp() * 1000)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        members = [n for n in zf.namelist() if not n.endswith("/")]
        if len(members) != 1:
            raise RuntimeError(f"archive member count !=1 {symbol} {month}")
        with zf.open(members[0]) as fh:
            reader = csv.reader(io.TextIOWrapper(fh, encoding="utf-8"))
            count = completed_count = incomplete_count = 0
            incomplete_examples: list[dict] = []
            first = last = prev = None
            for row in reader:
                if not row:
                    continue
                if len(row) < 7:
                    raise RuntimeError(f"short kline row {symbol} {month}")
                try:
                    ts = int(row[0])
                    close_ts = int(row[6])
                    o, h, l, c, v = map(float, row[1:6])
                except Exception as exc:
                    raise RuntimeError(f"invalid kline row {symbol} {month}: {exc}") from exc
                if not (month_start_ms <= ts < month_end_ms):
                    raise RuntimeError(f"timestamp outside month {symbol} {month}: {ts}")
                if ts % FIFTEEN_MIN_MS != 0:
                    raise RuntimeError(f"unaligned 15m open_time {symbol} {month}: {ts}")
                if min(o, h, l, c) <= 0 or v < 0 or h < max(o, c, l) or l > min(o, c, h):
                    raise RuntimeError(f"OHLCV failure {symbol} {month}: {ts}")
                if prev is not None and ts <= prev:
                    raise RuntimeError(f"non-increasing timestamp {symbol} {month}: {ts}")
                expected_close = ts + FIFTEEN_MIN_MS - 1
                if close_ts != expected_close:
                    incomplete_count += 1
                    if len(incomplete_examples) < 10:
                        incomplete_examples.append({
                            "open_time_ms": ts,
                            "raw_close_time_ms": close_ts,
                            "expected_close_time_ms": expected_close,
                        })
                else:
                    completed_count += 1
                first = ts if first is None else first
                last = ts
                prev = ts
                count += 1
            if count == 0:
                raise RuntimeError(f"empty archive {symbol} {month}")
    return {
        "row_count": count,
        "completed_15m_row_count": completed_count,
        "ineligible_incomplete_15m_rows": incomplete_count,
        "incomplete_row_examples": incomplete_examples,
        "first_open_time_ms": first,
        "last_open_time_ms": last,
    }


def run(output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    raw_dir = output / "raw"
    raw_dir.mkdir(exist_ok=True)
    entries: list[dict] = []
    errors: list[str] = []
    accessed_years: set[int] = set()
    for symbol in SYMBOLS:
        for month in months(START_MONTH, END_MONTH):
            year = int(month[:4])
            if year >= 2025:
                raise RuntimeError("hard firewall: attempted protected year")
            accessed_years.add(year)
            filename = f"{symbol}-{INTERVAL}-{month}.zip"
            url = f"{BASE_URL}/{symbol}/{INTERVAL}/{filename}"
            checksum_url = url + ".CHECKSUM"
            try:
                data = get(url)
                checksum_raw = get(checksum_url)
                expected = parse_checksum(checksum_raw, filename)
                actual = sha256_bytes(data)
                if actual != expected:
                    raise RuntimeError(f"sha256 mismatch expected={expected} actual={actual}")
                meta = validate_archive(data, symbol, month)
                path = raw_dir / filename
                path.write_bytes(data)
                entries.append({
                    "symbol": symbol,
                    "month": month,
                    "file": filename,
                    "source_url": url,
                    "checksum_url": checksum_url,
                    "sha256": actual,
                    **meta,
                })
                print("SOURCE_OK", symbol, month, meta["row_count"], "INELIGIBLE_INCOMPLETE=", meta["ineligible_incomplete_15m_rows"])
            except (urllib.error.URLError, RuntimeError, zipfile.BadZipFile, OSError) as exc:
                errors.append(f"{symbol}:{month}:{type(exc).__name__}:{exc}")
                print("SOURCE_FAIL", errors[-1])
    required = len(SYMBOLS) * len(months(START_MONTH, END_MONTH))
    by_symbol = {s: sum(1 for e in entries if e["symbol"] == s) for s in SYMBOLS}
    incomplete_by_symbol = {s: sum(int(e["ineligible_incomplete_15m_rows"]) for e in entries if e["symbol"] == s) for s in SYMBOLS}
    status = "SOURCE_AUDIT_PASS" if not errors and len(entries) == required and all(n == 23 for n in by_symbol.values()) else "SOURCE_OR_DATA_BLOCKED"
    manifest = {
        "lab_id": LAB_ID,
        "stage": "BINANCE_XVENUE_SOURCE_GATE",
        "status": status,
        "authority_commit": AUTHORITY_COMMIT,
        "technical_remediation": "DROP_NONSTANDARD_CLOSE_TIME_ROWS_AS_INELIGIBLE_INCOMPLETE_15M_PER_FROZEN_GAP_RULE",
        "provider": "BINANCE_DATA_VISION_PUBLIC_ARCHIVES",
        "venue": "BINANCE_SPOT",
        "interval": INTERVAL,
        "symbols": list(SYMBOLS),
        "start_month": START_MONTH,
        "end_month": END_MONTH,
        "required_archive_count": required,
        "accepted_archive_count": len(entries),
        "accepted_months_by_symbol": by_symbol,
        "ineligible_incomplete_15m_rows_by_symbol": incomplete_by_symbol,
        "accessed_years": sorted(accessed_years),
        "year_2025_accessed": False,
        "year_2026_accessed": False,
        "outcomes_computed": False,
        "signals_computed": False,
        "pnl_computed": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "errors": errors,
        "archives": entries,
    }
    (output / "TFG_PBR01_4H_BINANCE_XVENUE_SOURCE_MANIFEST_V0.1.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print("SOURCE_GATE_STATUS=", status)
    print("ACCEPTED_ARCHIVES=", len(entries), "/", required)
    print("INELIGIBLE_INCOMPLETE_BY_SYMBOL=", incomplete_by_symbol)
    print("2025_ACCESSED=false")
    print("2026_ACCESSED=false")
    return 0 if status == "SOURCE_AUDIT_PASS" else 4


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    raise SystemExit(run(Path(args.output)))
