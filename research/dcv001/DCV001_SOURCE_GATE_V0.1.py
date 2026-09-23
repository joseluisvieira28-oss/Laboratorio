#!/usr/bin/env python3
"""DCV-001 source-only gate.

Outcome firewall:
- validates only transport, published checksums, ZIP/CSV schema and timestamps;
- never emits funding/OI/price values, returns, PnL or directional outcomes;
- never requests 2025/2026 data.
"""

from __future__ import annotations

import calendar
import csv
import hashlib
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

BASE = "https://data.binance.vision/data/futures/um"
SYMBOL = "BTCUSDT"
PROTECTED_START_MS = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
PROBES = (
    ("2021-06-15", "2021-06"),
    ("2022-06-15", "2022-06"),
    ("2023-06-15", "2023-06"),
    ("2024-06-15", "2024-06"),
)
METRICS_REQUIRED = {
    "create_time",
    "symbol",
    "sum_open_interest",
    "sum_open_interest_value",
    "count_toptrader_long_short_ratio",
    "sum_toptrader_long_short_ratio",
    "count_long_short_ratio",
    "sum_taker_long_short_vol_ratio",
}
FUNDING_TIME_ALIASES = ("calc_time", "fundingTime", "funding_time")
FUNDING_RATE_ALIASES = ("last_funding_rate", "fundingRate", "funding_rate")
USER_AGENT = "Crypto-Lab-DCV001-SourceGate/0.1"
OUT = Path("dcv001_source_gate_receipt.json")


class GateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Downloaded:
    url: str
    data: bytes
    sha256: str
    published_sha256: str


def _request(url: str, attempts: int = 4) -> bytes:
    last: Exception | None = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as response:
                if response.status != 200:
                    raise GateError(f"HTTP_{response.status}:{url}")
                return response.read()
        except Exception as exc:  # fail closed after bounded retry
            last = exc
            if i + 1 < attempts:
                time.sleep(1.5 * (i + 1))
    raise GateError(f"DOWNLOAD_FAILED:{url}:{type(last).__name__}:{last}")


def _published_checksum(url: str) -> str:
    raw = _request(url + ".CHECKSUM").decode("utf-8", "replace").strip()
    m = re.search(r"(?i)\b([0-9a-f]{64})\b", raw)
    if not m:
        raise GateError(f"CHECKSUM_PARSE_FAILED:{url}")
    return m.group(1).lower()


def download_verified(url: str) -> Downloaded:
    published = _published_checksum(url)
    data = _request(url)
    actual = hashlib.sha256(data).hexdigest()
    if actual != published:
        raise GateError(f"CHECKSUM_MISMATCH:{url}:{actual}:{published}")
    return Downloaded(url=url, data=data, sha256=actual, published_sha256=published)


def _one_csv(z: Downloaded) -> tuple[str, bytes]:
    try:
        with zipfile.ZipFile(io.BytesIO(z.data), "r") as archive:
            bad = archive.testzip()
            if bad is not None:
                raise GateError(f"ZIP_CRC_FAIL:{z.url}:{bad}")
            names = [n for n in archive.namelist() if not n.endswith("/") and n.lower().endswith(".csv")]
            if len(names) != 1:
                raise GateError(f"ZIP_CSV_COUNT_NOT_ONE:{z.url}:{len(names)}")
            return names[0], archive.read(names[0])
    except zipfile.BadZipFile as exc:
        raise GateError(f"BAD_ZIP:{z.url}:{exc}") from exc


def _decode_csv(data: bytes) -> list[list[str]]:
    text = data.decode("utf-8-sig", "strict")
    return [row for row in csv.reader(io.StringIO(text)) if row and any(cell.strip() for cell in row)]


def _to_ms(value: str) -> int:
    v = value.strip()
    if not v:
        raise GateError("EMPTY_TIMESTAMP")
    try:
        x = float(v)
        if x > 1e14:
            return int(x / 1000.0)
        if x > 1e11:
            return int(x)
        if x > 1e9:
            return int(x * 1000.0)
    except ValueError:
        pass

    iso = v.replace("Z", "+00:00")
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _assert_pre2025(ts: Iterable[int], label: str) -> None:
    bad = [x for x in ts if x >= PROTECTED_START_MS]
    if bad:
        raise GateError(f"PROTECTED_TIMESTAMP:{label}:{_iso(min(bad))}")


def _no_dupes(ts: list[int], label: str) -> None:
    if len(set(ts)) != len(ts):
        raise GateError(f"DUPLICATE_TIMESTAMP:{label}:{len(ts)-len(set(ts))}")


def parse_metrics(z: Downloaded, day: str) -> dict:
    name, raw = _one_csv(z)
    rows = _decode_csv(raw)
    if len(rows) < 2:
        raise GateError(f"METRICS_EMPTY:{z.url}")
    header = [x.strip() for x in rows[0]]
    missing = sorted(METRICS_REQUIRED.difference(header))
    if missing:
        raise GateError(f"METRICS_SCHEMA_MISSING:{z.url}:{','.join(missing)}")
    idx = header.index("create_time")
    symbol_idx = header.index("symbol")
    body = rows[1:]
    if not body:
        raise GateError(f"METRICS_NO_BODY:{z.url}")
    timestamps = [_to_ms(r[idx]) for r in body if len(r) > max(idx, symbol_idx)]
    if len(timestamps) != len(body):
        raise GateError(f"METRICS_ROW_WIDTH:{z.url}")
    if any(r[symbol_idx].strip() != SYMBOL for r in body):
        raise GateError(f"METRICS_SYMBOL_MISMATCH:{z.url}")
    _assert_pre2025(timestamps, "metrics")
    _no_dupes(timestamps, "metrics")
    requested = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    lo = int(requested.timestamp() * 1000)
    hi = lo + 86_400_000
    if min(timestamps) < lo or max(timestamps) >= hi:
        raise GateError(f"METRICS_TIMESTAMP_OUTSIDE_DAY:{z.url}:{_iso(min(timestamps))}:{_iso(max(timestamps))}")
    return {
        "dataset": "metrics",
        "object": name,
        "url": z.url,
        "sha256": z.sha256,
        "checksum_verified": True,
        "row_count": len(body),
        "first_timestamp_utc": _iso(min(timestamps)),
        "last_timestamp_utc": _iso(max(timestamps)),
        "required_schema_present": True,
        "duplicate_timestamp_count": 0,
        "economic_values_reported": False,
    }


def _find_alias(header: list[str], aliases: tuple[str, ...], kind: str, url: str) -> int:
    for a in aliases:
        if a in header:
            return header.index(a)
    raise GateError(f"FUNDING_{kind}_COLUMN_MISSING:{url}:{','.join(header)}")


def parse_funding(z: Downloaded, month: str) -> dict:
    name, raw = _one_csv(z)
    rows = _decode_csv(raw)
    if len(rows) < 2:
        raise GateError(f"FUNDING_EMPTY:{z.url}")
    header = [x.strip() for x in rows[0]]
    time_idx = _find_alias(header, FUNDING_TIME_ALIASES, "TIME", z.url)
    _find_alias(header, FUNDING_RATE_ALIASES, "RATE", z.url)
    body = rows[1:]
    timestamps = [_to_ms(r[time_idx]) for r in body if len(r) > time_idx]
    if len(timestamps) != len(body):
        raise GateError(f"FUNDING_ROW_WIDTH:{z.url}")
    _assert_pre2025(timestamps, "funding")
    _no_dupes(timestamps, "funding")
    y, m = (int(x) for x in month.split("-"))
    lo = int(datetime(y, m, 1, tzinfo=timezone.utc).timestamp() * 1000)
    if m == 12:
        next_dt = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_dt = datetime(y, m + 1, 1, tzinfo=timezone.utc)
    hi = int(next_dt.timestamp() * 1000)
    if min(timestamps) < lo or max(timestamps) >= hi:
        raise GateError(f"FUNDING_TIMESTAMP_OUTSIDE_MONTH:{z.url}:{_iso(min(timestamps))}:{_iso(max(timestamps))}")
    return {
        "dataset": "fundingRate",
        "object": name,
        "url": z.url,
        "sha256": z.sha256,
        "checksum_verified": True,
        "row_count": len(body),
        "first_timestamp_utc": _iso(min(timestamps)),
        "last_timestamp_utc": _iso(max(timestamps)),
        "required_schema_present": True,
        "duplicate_timestamp_count": 0,
        "economic_values_reported": False,
    }


def parse_mark_1h(z: Downloaded, month: str) -> dict:
    name, raw = _one_csv(z)
    rows = _decode_csv(raw)
    if not rows:
        raise GateError(f"MARK_EMPTY:{z.url}")

    # Binance kline archives may be headerless or have a header in newer exports.
    body = rows
    try:
        _to_ms(rows[0][0])
    except Exception:
        body = rows[1:]

    if not body or any(len(r) < 6 for r in body):
        raise GateError(f"MARK_SCHEMA_INVALID:{z.url}")
    timestamps = [_to_ms(r[0]) for r in body]
    _assert_pre2025(timestamps, "markPriceKlines")
    _no_dupes(timestamps, "markPriceKlines")

    y, m = (int(x) for x in month.split("-"))
    lo_dt = datetime(y, m, 1, tzinfo=timezone.utc)
    if m == 12:
        hi_dt = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
    else:
        hi_dt = datetime(y, m + 1, 1, tzinfo=timezone.utc)
    lo = int(lo_dt.timestamp() * 1000)
    hi = int(hi_dt.timestamp() * 1000)
    if min(timestamps) < lo or max(timestamps) >= hi:
        raise GateError(f"MARK_TIMESTAMP_OUTSIDE_MONTH:{z.url}:{_iso(min(timestamps))}:{_iso(max(timestamps))}")

    expected = calendar.monthrange(y, m)[1] * 24
    coverage = len(timestamps) / expected
    if coverage < 0.99:
        raise GateError(f"MARK_1H_COVERAGE_LT_99PCT:{z.url}:{len(timestamps)}/{expected}")

    return {
        "dataset": "markPriceKlines_1h",
        "object": name,
        "url": z.url,
        "sha256": z.sha256,
        "checksum_verified": True,
        "row_count": len(body),
        "expected_hour_count": expected,
        "timestamp_coverage_fraction": coverage,
        "first_timestamp_utc": _iso(min(timestamps)),
        "last_timestamp_utc": _iso(max(timestamps)),
        "required_schema_present": True,
        "duplicate_timestamp_count": 0,
        "economic_values_reported": False,
    }


def urls(day: str, month: str) -> tuple[str, str, str]:
    metrics = f"{BASE}/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{day}.zip"
    funding = f"{BASE}/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{month}.zip"
    mark = f"{BASE}/monthly/markPriceKlines/{SYMBOL}/1h/{SYMBOL}-1h-{month}.zip"
    return metrics, funding, mark


def main() -> int:
    receipt = {
        "lab_id": "DCV-001",
        "gate": "SOURCE_GATE_V0.1",
        "classification": "SOURCE_GATE_RUNNING",
        "outcome_values_opened": False,
        "economic_values_reported": False,
        "protected_2025_accessed": False,
        "protected_2026_accessed": False,
        "live_trading": False,
        "exchange_mutation": False,
        "objects": [],
        "errors": [],
    }

    try:
        for day, month in PROBES:
            m_url, f_url, p_url = urls(day, month)
            receipt["objects"].append(parse_metrics(download_verified(m_url), day))
            receipt["objects"].append(parse_funding(download_verified(f_url), month))
            receipt["objects"].append(parse_mark_1h(download_verified(p_url), month))

        if len(receipt["objects"]) != len(PROBES) * 3:
            raise GateError("OBJECT_COUNT_MISMATCH")

        receipt["classification"] = "SOURCE_DATA_PASS"
        receipt["fixed_probe_count"] = len(PROBES)
        receipt["verified_object_count"] = len(receipt["objects"])
        receipt["verified_checksum_count"] = len(receipt["objects"])
        status = 0
    except Exception as exc:
        receipt["classification"] = "SOURCE_GATE_FAIL_CLOSED"
        receipt["errors"].append(f"{type(exc).__name__}:{exc}")
        status = 1

    receipt["receipt_sha256"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "lab_id": receipt["lab_id"],
        "classification": receipt["classification"],
        "verified_object_count": receipt.get("verified_object_count", 0),
        "errors": receipt["errors"],
        "outcome_values_opened": False,
        "economic_values_reported": False,
        "protected_2025_accessed": False,
        "protected_2026_accessed": False,
        "receipt_sha256": receipt["receipt_sha256"],
    }, sort_keys=True))
    return status


if __name__ == "__main__":
    sys.exit(main())
