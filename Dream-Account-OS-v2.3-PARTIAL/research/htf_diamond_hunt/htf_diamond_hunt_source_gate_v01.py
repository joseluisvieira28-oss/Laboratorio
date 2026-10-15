from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sys
import time
import urllib.request
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator

CAMPAIGN_ID = "HTF-DIAMOND-HUNT-001"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
YEARS = (2021, 2022)
MONTHS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
INTERVAL = "1m"
MINUTE_MS = 60_000
BAR15_MS = 15 * MINUTE_MS
START_MS = 1609459200000  # 2021-01-01T00:00:00Z
END_MS = 1672531200000    # 2023-01-01T00:00:00Z, exclusive
BASE_URL = "https://data.binance.vision/data/spot/monthly/klines"
UA = "HTF-DIAMOND-HUNT-001 research source gate/1.0"

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "local_data" / "htf_diamond_hunt_source_v01"
CANON = OUT / "canonical_15m"
RAW_META = OUT / "raw_meta"
RECEIPT = OUT / "HTF_DIAMOND_HUNT_001_SOURCE_GATE_V0.1.json"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_hash(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def get(url: str, retries: int = 4) -> bytes:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                if r.status != 200:
                    raise RuntimeError(f"HTTP {r.status}: {url}")
                return r.read()
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {url}: {last}")


def parse_checksum(text: bytes, expected_name: str) -> str:
    line = text.decode("utf-8", errors="strict").strip().splitlines()[0].strip()
    parts = line.replace("*", " ").split()
    if not parts or len(parts[0]) != 64:
        raise ValueError(f"invalid CHECKSUM payload for {expected_name}: {line[:200]}")
    value = parts[0].lower()
    if len(parts) > 1 and expected_name not in " ".join(parts[1:]):
        raise ValueError(f"CHECKSUM filename mismatch for {expected_name}: {line[:200]}")
    return value


def iter_zip_rows(zip_bytes: bytes, expected_csv: str) -> Iterator[tuple[int, float, float, float, float, float]]:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if expected_csv not in names:
            if len(names) == 1 and names[0].endswith(".csv"):
                member = names[0]
            else:
                raise ValueError(f"CSV member mismatch: expected={expected_csv} names={names[:5]}")
        else:
            member = expected_csv
        with zf.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            for row in reader:
                if not row:
                    continue
                try:
                    t = int(row[0])
                except ValueError:
                    # tolerate a provider header; never treat it as market data
                    if row[0].strip().lower() in {"open_time", "open time"}:
                        continue
                    raise
                if len(row) < 6:
                    raise ValueError(f"schema row has {len(row)} columns")
                yield t, float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])


@dataclass
class SymbolAudit:
    symbol: str
    monthly_archive_count: int = 0
    provider_checksum_verified_count: int = 0
    raw_row_count: int = 0
    duplicate_timestamp_count: int = 0
    non_monotonic_timestamp_count: int = 0
    out_of_window_row_count: int = 0
    complete_15m_count: int = 0
    incomplete_15m_bucket_count: int = 0
    detected_minute_gap_count: int = 0
    canonical_csv_sha256: str = ""
    first_raw_open_time: int | None = None
    last_raw_open_time: int | None = None


def aggregate_symbol(symbol: str, month_payloads: list[tuple[str, bytes]]) -> SymbolAudit:
    audit = SymbolAudit(symbol=symbol)
    CANON.mkdir(parents=True, exist_ok=True)
    out_path = CANON / f"{symbol}_15m.csv"
    h = hashlib.sha256()
    prev_t: int | None = None
    current_bucket: int | None = None
    bucket_rows: list[tuple[int, float, float, float, float, float]] = []

    def emit(writer: csv.writer) -> None:
        nonlocal bucket_rows, current_bucket
        if current_bucket is None or not bucket_rows:
            return
        expected = [current_bucket + i * MINUTE_MS for i in range(15)]
        observed = [r[0] for r in bucket_rows]
        if len(bucket_rows) == 15 and observed == expected:
            o = bucket_rows[0][1]
            hi = max(r[2] for r in bucket_rows)
            lo = min(r[3] for r in bucket_rows)
            c = bucket_rows[-1][4]
            v = sum(r[5] for r in bucket_rows)
            line = [current_bucket, repr(o), repr(hi), repr(lo), repr(c), repr(v), 15]
            sio = io.StringIO(newline="")
            csv.writer(sio, lineterminator="\n").writerow(line)
            b = sio.getvalue().encode("utf-8")
            writer.writerow(line)
            h.update(b)
            audit.complete_15m_count += 1
        else:
            audit.incomplete_15m_bucket_count += 1
        bucket_rows = []

    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        header = ["open_time", "open", "high", "low", "close", "volume", "minute_count"]
        writer.writerow(header)
        h.update((",".join(header) + "\n").encode("utf-8"))
        for ym, zip_bytes in month_payloads:
            expected_csv = f"{symbol}-{INTERVAL}-{ym}.csv"
            for row in iter_zip_rows(zip_bytes, expected_csv):
                t = row[0]
                audit.raw_row_count += 1
                if audit.first_raw_open_time is None:
                    audit.first_raw_open_time = t
                audit.last_raw_open_time = t
                if not (START_MS <= t < END_MS):
                    audit.out_of_window_row_count += 1
                    continue
                if prev_t is not None:
                    if t == prev_t:
                        audit.duplicate_timestamp_count += 1
                    elif t < prev_t:
                        audit.non_monotonic_timestamp_count += 1
                    elif t > prev_t + MINUTE_MS:
                        audit.detected_minute_gap_count += 1
                prev_t = t
                bucket = (t // BAR15_MS) * BAR15_MS
                if current_bucket is None:
                    current_bucket = bucket
                if bucket != current_bucket:
                    emit(writer)
                    current_bucket = bucket
                bucket_rows.append(row)
        emit(writer)
    audit.canonical_csv_sha256 = h.hexdigest()
    return audit


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW_META.mkdir(parents=True, exist_ok=True)
    CANON.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    audits: dict[str, dict[str, object]] = {}
    try:
        for symbol in SYMBOLS:
            payloads: list[tuple[str, bytes]] = []
            for ym in MONTHS:
                name = f"{symbol}-{INTERVAL}-{ym}.zip"
                url = f"{BASE_URL}/{symbol}/{INTERVAL}/{name}"
                c_url = url + ".CHECKSUM"
                z = get(url)
                checksum_bytes = get(c_url)
                provider_sha = parse_checksum(checksum_bytes, name)
                local_sha = sha256_bytes(z)
                if provider_sha != local_sha:
                    raise ValueError(f"provider checksum mismatch:{symbol}:{ym}:{provider_sha}!={local_sha}")
                rec = {
                    "symbol": symbol,
                    "month": ym,
                    "archive_name": name,
                    "archive_url": url,
                    "checksum_url": c_url,
                    "byte_count": len(z),
                    "provider_sha256": provider_sha,
                    "local_sha256": local_sha,
                }
                records.append(rec)
                payloads.append((ym, z))
                print(f"{symbol} {ym} checksum=PASS bytes={len(z)}", flush=True)
            audit = aggregate_symbol(symbol, payloads)
            audit.monthly_archive_count = len(payloads)
            audit.provider_checksum_verified_count = len(payloads)
            audits[symbol] = asdict(audit)
            (RAW_META / f"{symbol}_SOURCE_META.json").write_text(
                json.dumps([r for r in records if r["symbol"] == symbol], indent=2, sort_keys=True),
                encoding="utf-8",
            )
            if audit.duplicate_timestamp_count or audit.non_monotonic_timestamp_count or audit.out_of_window_row_count:
                raise ValueError(f"integrity failure:{symbol}:{asdict(audit)}")
            if audit.complete_15m_count < 60_000:
                raise ValueError(f"unexpectedly low complete 15m count:{symbol}:{audit.complete_15m_count}")

        if len(records) != 144:
            raise ValueError(f"archive count mismatch:{len(records)}")
        if sum(int(v["provider_checksum_verified_count"]) for v in audits.values()) != 144:
            raise ValueError("checksum verified count mismatch")
        source_preimage = {
            "campaign_id": CAMPAIGN_ID,
            "provider": "Binance public data",
            "market": "Spot",
            "raw_interval": INTERVAL,
            "allowed_years": list(YEARS),
            "records": sorted(records, key=lambda r: (str(r["symbol"]), str(r["month"]))),
            "symbol_audits": audits,
        }
        fp = canonical_hash(source_preimage)
        receipt = {
            "status": "SOURCE_DATA_PASS",
            **source_preimage,
            "monthly_archive_count": len(records),
            "provider_checksum_verified_count": 144,
            "source_fingerprint": fp,
            "outcome_evaluation_performed": False,
            "market_return_calculation_performed": False,
            "signal_calculation_performed": False,
            "access_2023_performed": False,
            "access_2024_performed": False,
            "access_2025_performed": False,
            "access_2026_performed": False,
            "live_trading": False,
            "exchange_mutation": False,
        }
        RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({
            "status": receipt["status"],
            "monthly_archive_count": receipt["monthly_archive_count"],
            "provider_checksum_verified_count": receipt["provider_checksum_verified_count"],
            "source_fingerprint": fp,
            "complete_15m_count_by_symbol": {s: audits[s]["complete_15m_count"] for s in SYMBOLS},
            "incomplete_15m_buckets_by_symbol": {s: audits[s]["incomplete_15m_bucket_count"] for s in SYMBOLS},
            "minute_gap_count_by_symbol": {s: audits[s]["detected_minute_gap_count"] for s in SYMBOLS},
            "outcome_evaluation_performed": False,
        }, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        receipt = {
            "status": "BLOCKED_PRE_OUTCOME_SOURCE_GATE",
            "reason": f"{type(exc).__name__}: {exc}",
            "campaign_id": CAMPAIGN_ID,
            "outcome_evaluation_performed": False,
            "market_return_calculation_performed": False,
            "signal_calculation_performed": False,
            "access_2023_performed": False,
            "access_2024_performed": False,
            "access_2025_performed": False,
            "access_2026_performed": False,
            "live_trading": False,
            "exchange_mutation": False,
        }
        RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(receipt, indent=2, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
