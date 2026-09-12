"""Public-market-data provenance shakedown for Cross-Venue Funding & Basis Lab V0.1.

This script is intentionally outcome-blind. It may retrieve realized funding records from
public Binance USD-M and Hyperliquid endpoints ONLY through 2025-12-31, but it MUST NOT
compute funding carry, rate averages, APR/APY, PnL, signal thresholds, rankings, or any
profitability statistic. Its outputs are limited to provenance, timestamps, interval
coverage, missingness diagnostics, and cryptographic fingerprints.

A PASS is a data-provenance result only. It does not authorize Discovery or trading.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
AUDIT_ID = "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_SHAKEDOWN_V01"
AUDIT_START_MS = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
AUDIT_END_MS = int(datetime(2025, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc).timestamp() * 1000)
LOCKED_2026_START_MS = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
BINANCE_BASE = "https://fapi.binance.com"
HYPERLIQUID_INFO = "https://api.hyperliquid.xyz/info"
BINANCE_SYMBOLS = ("BTCUSDT", "ETHUSDT")
HYPERLIQUID_COINS = ("BTC", "ETH")
USER_AGENT = "DreamAccountOS-Research-Provenance/0.1"


class ProvenanceFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class SeriesSpec:
    series_id: str
    venue: str
    instrument: str
    expected_max_gap_ms: int


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProvenanceFailure(message)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _request_json(req: urllib.request.Request, *, retries: int = 4) -> Any:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:  # pragma: no cover - exercised only on network failure
            last_error = exc
            time.sleep(min(2 ** attempt, 8))
    raise ProvenanceFailure(f"public endpoint request failed after {retries} attempts: {last_error}")


def fetch_binance_funding(symbol: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    _require(symbol in BINANCE_SYMBOLS, "symbol outside frozen scope")
    _require(end_ms < LOCKED_2026_START_MS, "locked 2026 access forbidden")
    records: list[dict[str, Any]] = []
    cursor = start_ms
    while cursor <= end_ms:
        params = urllib.parse.urlencode({
            "symbol": symbol,
            "startTime": cursor,
            "endTime": end_ms,
            "limit": 1000,
        })
        req = urllib.request.Request(
            f"{BINANCE_BASE}/fapi/v1/fundingRate?{params}",
            headers={"User-Agent": USER_AGENT},
            method="GET",
        )
        batch = _request_json(req)
        _require(isinstance(batch, list), "unexpected Binance response shape")
        if not batch:
            break
        for row in batch:
            ts = int(row["fundingTime"])
            _require(ts < LOCKED_2026_START_MS, "Binance response leaked locked 2026")
            if start_ms <= ts <= end_ms:
                records.append(dict(row))
        last_ts = int(batch[-1]["fundingTime"])
        _require(last_ts >= cursor, "Binance pagination failed to advance")
        next_cursor = last_ts + 1
        if next_cursor <= cursor or len(batch) < 1000:
            break
        cursor = next_cursor
        time.sleep(0.03)
    return records


def fetch_hyperliquid_funding(coin: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    _require(coin in HYPERLIQUID_COINS, "coin outside frozen scope")
    _require(end_ms < LOCKED_2026_START_MS, "locked 2026 access forbidden")
    records: list[dict[str, Any]] = []
    cursor = start_ms
    while cursor <= end_ms:
        payload = canonical_bytes({
            "type": "fundingHistory",
            "coin": coin,
            "startTime": cursor,
            "endTime": end_ms,
        })
        req = urllib.request.Request(
            HYPERLIQUID_INFO,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            method="POST",
        )
        batch = _request_json(req)
        _require(isinstance(batch, list), "unexpected Hyperliquid response shape")
        if not batch:
            break
        for row in batch:
            ts = int(row["time"])
            _require(ts < LOCKED_2026_START_MS, "Hyperliquid response leaked locked 2026")
            if start_ms <= ts <= end_ms:
                records.append(dict(row))
        last_ts = int(batch[-1]["time"])
        _require(last_ts >= cursor, "Hyperliquid pagination failed to advance")
        next_cursor = last_ts + 1
        if next_cursor <= cursor:
            raise ProvenanceFailure("Hyperliquid pagination stalled")
        cursor = next_cursor
        time.sleep(0.03)
    return records


def _month_bounds_ms(month: str) -> tuple[int, int]:
    year, mon = map(int, month.split("-"))
    start = datetime(year, mon, 1, tzinfo=timezone.utc)
    days = calendar.monthrange(year, mon)[1]
    end = datetime(year, mon, days, 23, 59, 59, 999000, tzinfo=timezone.utc)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def _month_key(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m")


def audit_series(spec: SeriesSpec, records: Iterable[dict[str, Any]], timestamp_field: str) -> dict[str, Any]:
    rows = [dict(row) for row in records]
    timestamps = [int(row[timestamp_field]) for row in rows]
    _require(all(AUDIT_START_MS <= ts <= AUDIT_END_MS for ts in timestamps), f"{spec.series_id}: timestamp outside audit boundary")
    ordered = sorted(zip(timestamps, rows), key=lambda pair: pair[0])
    ordered_ts = [pair[0] for pair in ordered]

    timestamp_counts = Counter(ordered_ts)
    duplicate_timestamps = {str(ts): count for ts, count in timestamp_counts.items() if count > 1}
    conflicting_duplicate_timestamps: list[int] = []
    if duplicate_timestamps:
        by_ts: dict[int, set[str]] = {}
        for ts, row in ordered:
            by_ts.setdefault(ts, set()).add(sha256_json(row))
        conflicting_duplicate_timestamps = sorted(ts for ts, hashes in by_ts.items() if len(hashes) > 1)

    unique_ts = sorted(set(ordered_ts))
    deltas = [b - a for a, b in zip(unique_ts, unique_ts[1:])]
    delta_hist = Counter(deltas)
    max_gap_ms = max(deltas) if deltas else None
    large_gaps = [
        {"from_ms": a, "to_ms": b, "gap_ms": b - a}
        for a, b in zip(unique_ts, unique_ts[1:])
        if b - a > spec.expected_max_gap_ms
    ]

    months_present: dict[str, list[int]] = {}
    for ts in unique_ts:
        months_present.setdefault(_month_key(ts), []).append(ts)

    full_months: list[str] = []
    month_diagnostics: dict[str, Any] = {}
    for month, ts_values in sorted(months_present.items()):
        month_start, month_end = _month_bounds_ms(month)
        first_ts, last_ts = ts_values[0], ts_values[-1]
        month_deltas = [b - a for a, b in zip(ts_values, ts_values[1:])]
        month_max_gap = max(month_deltas) if month_deltas else None
        starts_in_time = (first_ts - month_start) <= spec.expected_max_gap_ms
        ends_in_time = (month_end - last_ts) < spec.expected_max_gap_ms
        no_large_gap = month_max_gap is None or month_max_gap <= spec.expected_max_gap_ms
        eligible = starts_in_time and ends_in_time and no_large_gap
        if eligible:
            full_months.append(month)
        month_diagnostics[month] = {
            "record_count": len(ts_values),
            "first_timestamp_ms": first_ts,
            "last_timestamp_ms": last_ts,
            "max_gap_ms": month_max_gap,
            "full_month_coverage_by_timestamp_only": eligible,
        }

    canonical_records = [row for _, row in ordered]
    return {
        "series_id": spec.series_id,
        "venue": spec.venue,
        "instrument": spec.instrument,
        "record_count": len(rows),
        "unique_timestamp_count": len(unique_ts),
        "first_timestamp_ms": unique_ts[0] if unique_ts else None,
        "last_timestamp_ms": unique_ts[-1] if unique_ts else None,
        "duplicate_timestamp_count": sum(count - 1 for count in timestamp_counts.values() if count > 1),
        "conflicting_duplicate_timestamps": conflicting_duplicate_timestamps,
        "max_gap_ms": max_gap_ms,
        "large_gap_count": len(large_gaps),
        "large_gaps": large_gaps[:200],
        "interval_histogram_ms": {str(k): v for k, v in sorted(delta_hist.items())},
        "full_months_timestamp_eligible": full_months,
        "month_diagnostics": month_diagnostics,
        "canonical_raw_records_sha256": sha256_json(canonical_records),
        "economic_fields_summarized": False,
    }


def choose_common_replication_window(series_audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    expected_ids = {
        "BINANCE_BTCUSDT",
        "BINANCE_ETHUSDT",
        "HYPERLIQUID_BTC",
        "HYPERLIQUID_ETH",
    }
    _require(set(series_audits) == expected_ids, "unexpected series set")
    month_sets = [set(series_audits[sid]["full_months_timestamp_eligible"]) for sid in sorted(expected_ids)]
    common = sorted(set.intersection(*month_sets))
    _require(common, "no common full UTC month passes timestamp-only provenance coverage")
    # Window selection is availability-only: earliest common eligible month through the
    # latest common eligible month not later than 2025-12. No rate value is consulted.
    return {
        "first_common_full_month": common[0],
        "last_common_full_month": common[-1],
        "common_full_month_count": len(common),
        "common_full_months": common,
        "selection_rule": "EARLIEST_TO_LATEST_COMMON_TIMESTAMP_ELIGIBLE_FULL_UTC_MONTH_NO_OUTCOME_SELECTION",
    }


def run_audit() -> dict[str, Any]:
    _require(AUDIT_END_MS < LOCKED_2026_START_MS, "audit boundary reaches locked 2026")

    raw = {
        "BINANCE_BTCUSDT": fetch_binance_funding("BTCUSDT", AUDIT_START_MS, AUDIT_END_MS),
        "BINANCE_ETHUSDT": fetch_binance_funding("ETHUSDT", AUDIT_START_MS, AUDIT_END_MS),
        "HYPERLIQUID_BTC": fetch_hyperliquid_funding("BTC", AUDIT_START_MS, AUDIT_END_MS),
        "HYPERLIQUID_ETH": fetch_hyperliquid_funding("ETH", AUDIT_START_MS, AUDIT_END_MS),
    }
    specs = {
        "BINANCE_BTCUSDT": SeriesSpec("BINANCE_BTCUSDT", "BINANCE_USDM", "BTCUSDT", 8 * 60 * 60 * 1000),
        "BINANCE_ETHUSDT": SeriesSpec("BINANCE_ETHUSDT", "BINANCE_USDM", "ETHUSDT", 8 * 60 * 60 * 1000),
        "HYPERLIQUID_BTC": SeriesSpec("HYPERLIQUID_BTC", "HYPERLIQUID", "BTC", 60 * 60 * 1000),
        "HYPERLIQUID_ETH": SeriesSpec("HYPERLIQUID_ETH", "HYPERLIQUID", "ETH", 60 * 60 * 1000),
    }
    ts_fields = {
        "BINANCE_BTCUSDT": "fundingTime",
        "BINANCE_ETHUSDT": "fundingTime",
        "HYPERLIQUID_BTC": "time",
        "HYPERLIQUID_ETH": "time",
    }
    audits = {sid: audit_series(specs[sid], raw[sid], ts_fields[sid]) for sid in sorted(raw)}
    window = choose_common_replication_window(audits)

    conflicts = sum(len(a["conflicting_duplicate_timestamps"]) for a in audits.values())
    locked_leaks = any((a["last_timestamp_ms"] or 0) >= LOCKED_2026_START_MS for a in audits.values())
    status = "PASS" if conflicts == 0 and not locked_leaks else "FAIL"
    receipt = {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "audit_id": AUDIT_ID,
        "classification": "PROVENANCE_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": status,
        "audit_start_ms": AUDIT_START_MS,
        "audit_end_ms": AUDIT_END_MS,
        "locked_2026_start_ms": LOCKED_2026_START_MS,
        "locked_2026_accessed": locked_leaks,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "series": audits,
        "replication_window_provenance_only": window,
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    return receipt


def main() -> None:
    output = Path(os.environ.get("PREFREEZE_PROVENANCE_RECEIPT", "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_SHAKEDOWN_V01_RECEIPT.json"))
    receipt = run_audit()
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Do not print per-series records or rate values. The CI log receives only the gate summary.
    print(json.dumps({
        "lab_id": receipt["lab_id"],
        "audit_id": receipt["audit_id"],
        "status": receipt["status"],
        "locked_2026_accessed": receipt["locked_2026_accessed"],
        "carry_computed": receipt["carry_computed"],
        "pnl_computed": receipt["pnl_computed"],
        "first_common_full_month": receipt["replication_window_provenance_only"]["first_common_full_month"],
        "last_common_full_month": receipt["replication_window_provenance_only"]["last_common_full_month"],
        "receipt_sha256": receipt["receipt_sha256"],
    }, sort_keys=True))
    if receipt["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
