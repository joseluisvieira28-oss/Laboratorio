"""Outcome-blind provenance remediation for Cross-Venue Funding & Basis Lab V0.3.

Purpose
-------
The frozen V0.1 Binance REST provenance route can return HTTP 451 in GitHub Actions.
This diagnostic-only remediation substitutes Binance's public historical archive at
data.binance.vision, verifies every monthly ZIP against its SHA-256 CHECKSUM sidecar,
normalizes only the archive timestamp field, and re-runs the unchanged V0.1
timestamp-coverage audit.

It MUST NOT compute or summarize funding rates, carry, PnL, APR/APY, expectancy,
win rate, profit factor, Sharpe, rankings, thresholds, or trading signals.
It does not authorize Discovery, trading, 2026 access, MEXC access, authenticated
account data, or exchange mutation.

A V0.3 PASS means the provenance remediation executed successfully. The frozen
V0.1 coverage gate is reported separately as v01_gate_status and is not relaxed.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from cross_venue_funding_basis_provenance_shakedown_v01 import (
    AUDIT_END_MS,
    AUDIT_START_MS,
    BINANCE_SYMBOLS,
    HYPERLIQUID_COINS,
    LOCKED_2026_START_MS,
    SeriesSpec,
    audit_series,
    fetch_hyperliquid_funding,
)

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
REMEDIATION_ID = "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_ARCHIVE_REMEDIATION_V03"
BINANCE_ARCHIVE_BASE = "https://data.binance.vision"
USER_AGENT = "DreamAccountOS-Research-Provenance-Archive/0.3"

# Explicit governance markers consumed by static guards.
carry_computed = False
apr_apy_computed = False
pnl_computed = False
signals_computed = False

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class ArchiveProvenanceFailure(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ArchiveProvenanceFailure(message)


def _month_iter() -> list[str]:
    """Return the frozen complete UTC months 2023-01 through 2025-12."""
    months: list[str] = []
    year, month = 2023, 1
    while (year, month) <= (2025, 12):
        months.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    _require(months[0] == "2023-01" and months[-1] == "2025-12", "unexpected frozen month range")
    return months


def build_binance_archive_urls(symbol: str, month: str) -> tuple[str, str]:
    _require(symbol in BINANCE_SYMBOLS, "symbol outside frozen scope")
    _require(month in _month_iter(), "month outside frozen pre-2026 scope")
    filename = f"{symbol}-fundingRate-{month}.zip"
    path = f"/data/futures/um/monthly/fundingRate/{symbol}/{filename}"
    url = f"{BINANCE_ARCHIVE_BASE}{path}"
    checksum_url = f"{url}.CHECKSUM"

    for candidate in (url, checksum_url):
        parsed = urllib.parse.urlsplit(candidate)
        _require(parsed.scheme == "https", "Binance archive scheme must be https")
        _require(parsed.netloc == "data.binance.vision", "unexpected Binance archive host")
        _require(parsed.query == "" and parsed.fragment == "", "Binance archive URL must not contain query/fragment")
        _require(parsed.path.startswith("/data/futures/um/monthly/fundingRate/"), "unexpected Binance archive path")
    return url, checksum_url


def _request_bytes(url: str) -> bytes:
    parsed = urllib.parse.urlsplit(url)
    _require(parsed.scheme == "https" and parsed.netloc == "data.binance.vision", "network request outside frozen Binance archive host")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    header_names = {k.lower() for k, _ in req.header_items()}
    _require(req.data is None, "archive GET must not carry request body")
    _require(
        "authorization" not in header_names and "cookie" not in header_names and "x-api-key" not in header_names,
        "authenticated Binance archive header forbidden",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.read()
    except Exception as exc:  # pragma: no cover - network only
        raise ArchiveProvenanceFailure(f"Binance public archive request failed: {url}: {exc}") from exc


def parse_checksum_sidecar(raw: bytes, expected_filename: str) -> str:
    try:
        text = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise ArchiveProvenanceFailure("checksum sidecar is not UTF-8") from exc
    _require(bool(text), "empty checksum sidecar")
    first_line = text.splitlines()[0].strip()
    parts = first_line.split()
    _require(len(parts) >= 1 and bool(_SHA256_RE.fullmatch(parts[0])), "invalid SHA-256 checksum sidecar")
    if len(parts) >= 2:
        sidecar_name = parts[-1].lstrip("*")
        _require(Path(sidecar_name).name == expected_filename, "checksum sidecar filename mismatch")
    return parts[0].lower()


def parse_binance_funding_archive(zip_bytes: bytes, *, symbol: str, month: str) -> list[dict[str, Any]]:
    """Normalize the archive timestamp while keeping economic fields opaque."""
    _require(symbol in BINANCE_SYMBOLS, "symbol outside frozen scope")
    _require(month in _month_iter(), "month outside frozen scope")
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            members = [name for name in zf.namelist() if not name.endswith("/")]
            _require(len(members) == 1, f"expected exactly one archive member, got {len(members)}")
            member = members[0]
            _require(Path(member).name == member and member.endswith(".csv"), "unsafe or unexpected archive member")
            raw_csv = zf.read(member)
    except zipfile.BadZipFile as exc:
        raise ArchiveProvenanceFailure("invalid Binance funding archive ZIP") from exc

    try:
        text = raw_csv.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ArchiveProvenanceFailure("funding archive CSV is not UTF-8") from exc

    reader = csv.DictReader(io.StringIO(text))
    _require(reader.fieldnames is not None, "funding archive missing header")
    headers = [header.strip() for header in reader.fieldnames]
    _require("calc_time" in headers, f"funding archive schema missing calc_time: {headers}")

    out: list[dict[str, Any]] = []
    for source_row in reader:
        row = {(key or "").strip(): value for key, value in source_row.items()}
        raw_ts = row.get("calc_time")
        _require(raw_ts is not None and raw_ts != "", "funding archive row missing calc_time")
        try:
            ts = int(str(raw_ts))
        except ValueError as exc:
            raise ArchiveProvenanceFailure(f"non-integer calc_time: {raw_ts!r}") from exc
        _require(AUDIT_START_MS <= ts <= AUDIT_END_MS, "archive timestamp outside frozen audit window")
        _require(ts < LOCKED_2026_START_MS, "archive leaked locked 2026")
        row["fundingTime"] = ts
        out.append(row)
    _require(bool(out), f"empty Binance funding archive for {symbol} {month}")
    return out


def fetch_binance_archive_month(symbol: str, month: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    url, checksum_url = build_binance_archive_urls(symbol, month)
    zip_bytes = _request_bytes(url)
    checksum_bytes = _request_bytes(checksum_url)
    filename = Path(urllib.parse.urlsplit(url).path).name
    expected_sha = parse_checksum_sidecar(checksum_bytes, filename)
    actual_sha = hashlib.sha256(zip_bytes).hexdigest()
    _require(actual_sha == expected_sha, f"checksum mismatch for {filename}")
    rows = parse_binance_funding_archive(zip_bytes, symbol=symbol, month=month)
    return rows, {
        "symbol": symbol,
        "month": month,
        "archive_url": url,
        "checksum_url": checksum_url,
        "checksum_expected_sha256": expected_sha,
        "checksum_actual_sha256": actual_sha,
        "checksum_match": True,
        "record_count": len(rows),
    }


def fetch_binance_archives(symbol: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _require(symbol in BINANCE_SYMBOLS, "symbol outside frozen scope")
    all_rows: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    for month in _month_iter():
        rows, manifest = fetch_binance_archive_month(symbol, month)
        all_rows.extend(rows)
        manifests.append(manifest)
    return all_rows, manifests


def _common_months(audits: dict[str, dict[str, Any]]) -> list[str]:
    expected_ids = {
        "BINANCE_BTCUSDT",
        "BINANCE_ETHUSDT",
        "HYPERLIQUID_BTC",
        "HYPERLIQUID_ETH",
    }
    _require(set(audits) == expected_ids, "unexpected series set")
    month_sets = [set(audits[series_id]["full_months_timestamp_eligible"]) for series_id in sorted(expected_ids)]
    return sorted(set.intersection(*month_sets))


def run_diagnostic() -> dict[str, Any]:
    _require(AUDIT_END_MS < LOCKED_2026_START_MS, "audit boundary reaches locked 2026")

    binance_btc, manifest_btc = fetch_binance_archives("BTCUSDT")
    binance_eth, manifest_eth = fetch_binance_archives("ETHUSDT")
    raw = {
        "BINANCE_BTCUSDT": binance_btc,
        "BINANCE_ETHUSDT": binance_eth,
        "HYPERLIQUID_BTC": fetch_hyperliquid_funding("BTC", AUDIT_START_MS, AUDIT_END_MS),
        "HYPERLIQUID_ETH": fetch_hyperliquid_funding("ETH", AUDIT_START_MS, AUDIT_END_MS),
    }
    specs = {
        "BINANCE_BTCUSDT": SeriesSpec("BINANCE_BTCUSDT", "BINANCE_USDM_ARCHIVE", "BTCUSDT", 8 * 60 * 60 * 1000),
        "BINANCE_ETHUSDT": SeriesSpec("BINANCE_ETHUSDT", "BINANCE_USDM_ARCHIVE", "ETHUSDT", 8 * 60 * 60 * 1000),
        "HYPERLIQUID_BTC": SeriesSpec("HYPERLIQUID_BTC", "HYPERLIQUID", "BTC", 60 * 60 * 1000),
        "HYPERLIQUID_ETH": SeriesSpec("HYPERLIQUID_ETH", "HYPERLIQUID", "ETH", 60 * 60 * 1000),
    }
    timestamp_fields = {
        "BINANCE_BTCUSDT": "fundingTime",
        "BINANCE_ETHUSDT": "fundingTime",
        "HYPERLIQUID_BTC": "time",
        "HYPERLIQUID_ETH": "time",
    }
    audits = {
        series_id: audit_series(specs[series_id], raw[series_id], timestamp_fields[series_id])
        for series_id in sorted(raw)
    }
    common = _common_months(audits)

    conflicts = sum(len(audit["conflicting_duplicate_timestamps"]) for audit in audits.values())
    locked_leaks = any((audit["last_timestamp_ms"] or 0) >= LOCKED_2026_START_MS for audit in audits.values())
    all_checksums = manifest_btc + manifest_eth
    checksum_ok = all(manifest["checksum_match"] for manifest in all_checksums)

    return {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "remediation_id": REMEDIATION_ID,
        "classification": "PROVENANCE_REMEDIATION_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "PASS",
        "technical_route_status": "PASS_BINANCE_ARCHIVE_CHECKSUM_VERIFIED",
        "v01_gate_status": "PASS" if common else "FAIL_CLOSED_NO_COMMON_FULL_UTC_MONTH",
        "audit_start_ms": AUDIT_START_MS,
        "audit_end_ms": AUDIT_END_MS,
        "locked_2026_start_ms": LOCKED_2026_START_MS,
        "binance_source": "https://data.binance.vision/data/futures/um/monthly/fundingRate",
        "binance_rest_fallback_used": False,
        "binance_archive_month_count": len(all_checksums),
        "binance_archive_checksums_all_match": checksum_ok,
        "binance_archive_manifests": all_checksums,
        "series_audits": audits,
        "common_eligible_months": common,
        "first_common_full_month": common[0] if common else None,
        "last_common_full_month": common[-1] if common else None,
        "common_full_month_count": len(common),
        "conflicting_duplicate_timestamp_count": conflicts,
        "locked_2026_accessed": locked_leaks,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "economic_fields_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "discovery_authorized": False,
        "trading_authorized": False,
        "decision_rule": "Diagnostic transport/provenance PASS does not relax the frozen V0.1 common-month gate and does not authorize economic Discovery."
    }


def main() -> int:
    receipt_path = Path(
        os.environ.get(
            "PREFREEZE_PROVENANCE_ARCHIVE_V03_RECEIPT",
            "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_ARCHIVE_V03_RECEIPT.json",
        )
    )
    receipt = run_diagnostic()
    _require(receipt["locked_2026_accessed"] is False, "locked 2026 access detected")
    _require(receipt["binance_archive_checksums_all_match"] is True, "archive checksum verification failed")
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "technical_route_status": receipt["technical_route_status"],
                "v01_gate_status": receipt["v01_gate_status"],
                "common_full_month_count": receipt["common_full_month_count"],
                "receipt": str(receipt_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
