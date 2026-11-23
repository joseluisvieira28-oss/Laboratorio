#!/usr/bin/env python3
"""BINANCE-DIAMANTE-001: bounded, public Spot archive source gate. No trading.
Source-only: never computes or emits market returns, entry signals, or PnL.
"""
from __future__ import annotations

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

DAY = dt.date(2026, 11, 12)
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
HOST = "https://data.binance.vision"
MAX_ZIP_BYTES = 4_000_000
MAX_CSV_BYTES = 15_000_000
OUT = Path("binance001-evidence")

def url_for(symbol: str, day: dt.date) -> str:
    if symbol not in SYMBOLS:
        raise ValueError("symbol not authorized")
    name = f"{symbol}-1m-{day.isoformat()}.zip"
    return f"{HOST}/data/spot/daily/klines/{symbol}/1m/{name}"

def public_get(url: str, cap: int) -> bytes:
    if not url.startswith(HOST + "/data/spot/daily/klines/"):
        raise ValueError("public archive only; URL denied")
    req = urllib.request.Request(url, headers={
        "User-Agent": "BinanceDiamante001-source-gate/0.1 (research-only)"
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        if response.status != 200:
            raise ValueError(f"unexpected HTTP {response.status}")
        blob = response.read(cap + 1)
    if not blob or len(blob) > cap:
        raise ValueError("empty or oversized public response")
    return blob

def official_checksum(checksum: bytes, expected_name: str) -> str:
    line = checksum.decode("ascii").strip()
    m = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?([^\s/\\]+)", line)
    if not m or m.group(2) != expected_name:
        raise ValueError("missing/incorrect official checksum line")
    return m.group(1).lower()

def verify_archive(archive: bytes, checksum: bytes, symbol: str, day: dt.date) -> dict:
    expected_name = f"{symbol}-1m-{day.isoformat()}.zip"
    declared = official_checksum(checksum, expected_name)
    actual = hashlib.sha256(archive).hexdigest()
    if declared != actual:
        raise ValueError("OFFICIAL_SHA256_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        entries = zf.infolist()
        csv_name = expected_name[:-4] + ".csv"
        if len(entries) != 1 or entries[0].filename != csv_name:
            raise ValueError("unexpected zip member/name")
        if entries[0].file_size > MAX_CSV_BYTES:
            raise ValueError("CSV extraction cap exceeded")
        with zf.open(entries[0]) as zdata:
            content = zdata.read(MAX_CSV_BYTES + 1)
        if len(content) > MAX_CSV_BYTES:
            raise ValueError("uncompressed CSV exceeds cap")
    rows = csv.reader(io.StringIO(content.decode("utf-8-sig")))
    first = int(dt.datetime.combine(day, dt.time(), tzinfo=dt.timezone.utc).timestamp() * 1_000_000)
    seen = 0
    for row in rows:
        if seen == 0 and row and row[0].lower().strip().replace(" ", "_") in ("open_time", "open_timestamp"):
            continue
        if len(row) != 12:
            raise ValueError("unexpected Spot kline column count")
        open_stamp = int(row[0])
        if open_stamp != first + seen * 60_000_000:
            raise ValueError("gap/duplicate/out-of-day/incorrect timestamp unit")
        o, h, l, c = (float(row[i]) for i in (1, 2, 3, 4))
        qty, quote, taker_base, taker_quote = (float(row[i]) for i in (5, 7, 9, 10))
        trades = int(row[8])
        vals = (o, h, l, c, qty, quote, taker_base, taker_quote)
        if not all(-1e300 < v < 1e300 for v in vals):
            raise ValueError("non-finite numeric value")
        if l <= 0 or l > min(o, c) or h < max(o, c) or h < l:
            raise ValueError("invalid OHLC")
        if min(qty, quote, taker_base, taker_quote, trades) < 0:
            raise ValueError("negative volume/trade count")
        seen += 1
        if seen > 1440:
            raise ValueError("more than 1440 rows")
    if seen != 1440:
        raise ValueError(f"incomplete UTC day: {seen}/1440 1m rows")
    return {
        "status": "SOURCE_PASS", "symbol": symbol, "day_utc": day.isoformat(),
        "rows": seen, "raw_zip_sha256": actual, "official_checksum_sha256": declared,
        "csv_sha256": hashlib.sha256(content).hexdigest(),
        "archive_bytes": len(archive), "first_open_us": first,
        "last_open_us": first + 1439 * 60_000_000,
        "market_outcomes_examined": False, "signals_generated": False,
        "economic_edge_claimed": False
    }

def run() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT / "raw"
    raw_dir.mkdir(exist_ok=True)
    report = {
        "study": "BINANCE-DIAMANTE-001", "stage": "SOURCE_GATE_ONLY",
        "day_utc": DAY.isoformat(), "symbols": {}, "no_api_keys": True,
        "no_private_endpoints": True, "no_orders": True, "no_trades": True,
        "no_pnl": True, "no_paper_trades": True,
        "strategy_armed": False, "status": "SOURCE_BLOCKED"
    }
    for symbol in SYMBOLS:
        base = url_for(symbol, DAY)
        name = base.rsplit("/", 1)[-1]
        try:
            archive = public_get(base, MAX_ZIP_BYTES)
            checksum = public_get(base + ".CHECKSUM", 1_024)
            record = verify_archive(archive, checksum, symbol, DAY)
            (raw_dir / name).write_bytes(archive)
            (raw_dir / (name + ".CHECKSUM")).write_bytes(checksum)
            record["official_zip_url"] = base
            record["official_checksum_url"] = base + ".CHECKSUM"
            report["symbols"][symbol] = record
        except (ValueError, UnicodeError, zipfile.BadZipFile, OSError, urllib.error.URLError) as exc:
            report["symbols"][symbol] = {
                "status": "SOURCE_BLOCKED", "error_type": type(exc).__name__,
                "error": str(exc)[:240], "official_zip_url": base
            }
    if (len(report["symbols"]) == len(SYMBOLS) and
            all(r["status"] == "SOURCE_PASS" for r in report["symbols"].values())):
        report["status"] = "SOURCE_PASS_ONLY_NO_ECONOMIC_INFERENCE"
    manifest = OUT / "manifest.json"
    manifest.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "manifest.sha256").write_text(
        hashlib.sha256(manifest.read_bytes()).hexdigest() + "  manifest.json\n", encoding="ascii")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"].startswith("SOURCE_PASS") else 2

if __name__ == "__main__":
    sys.exit(run())
