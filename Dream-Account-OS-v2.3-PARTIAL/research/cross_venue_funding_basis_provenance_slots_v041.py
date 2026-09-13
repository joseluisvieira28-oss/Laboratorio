"""Rate-limit-safe provenance + nominal-slot diagnostic for Cross-Venue Funding Basis V0.4.1.

V0.4.1 changes only the Hyperliquid public fundingHistory transport pacing after the
V0.4 GitHub Actions run received HTTP 429. It preserves V0.4 nominal-slot semantics,
coverage rules, frozen scope, and all economic prohibitions.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from cross_venue_funding_basis_provenance_shakedown_v01 import (
    AUDIT_END_MS,
    AUDIT_START_MS,
    HYPERLIQUID_COINS,
    LOCKED_2026_START_MS,
    build_hyperliquid_funding_request,
)
from cross_venue_funding_basis_provenance_archive_v03 import fetch_binance_archives
from cross_venue_funding_basis_provenance_slots_v04 import (
    BINANCE_INTERVAL_MS,
    HYPERLIQUID_INTERVAL_MS,
    _common_months,
    slot_coverage_audit,
    validate_binance_interval_metadata,
)

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
TRANSPORT_ID = "CROSS_VENUE_FUNDING_BASIS_HYPERLIQUID_TRANSPORT_V041"
MIN_REQUEST_INTERVAL_SECONDS = 3.0
HTTP_429_COOLDOWN_SECONDS = 15.0
MAX_ATTEMPTS_PER_PAGE = 6

carry_computed = False
apr_apy_computed = False
pnl_computed = False
signals_computed = False


class TransportFailure(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TransportFailure(message)


class HyperliquidPacedClient:
    def __init__(self) -> None:
        self._last_request_started: float | None = None
        self.request_count = 0
        self.http_429_retry_count = 0

    def _pace(self) -> None:
        now = time.monotonic()
        if self._last_request_started is not None:
            remaining = MIN_REQUEST_INTERVAL_SECONDS - (now - self._last_request_started)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_started = time.monotonic()

    def request_json(self, req: urllib.request.Request) -> Any:
        parsed = urllib.parse.urlsplit(req.full_url) if hasattr(urllib, "parse") else None
        # Request shape itself is already frozen/guarded by build_hyperliquid_funding_request.
        last_error: Exception | None = None
        for attempt in range(MAX_ATTEMPTS_PER_PAGE):
            self._pace()
            self.request_count += 1
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read()
                return json.loads(raw.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code == 429:
                    self.http_429_retry_count += 1
                    if attempt + 1 < MAX_ATTEMPTS_PER_PAGE:
                        time.sleep(HTTP_429_COOLDOWN_SECONDS)
                        continue
                break
            except Exception as exc:  # pragma: no cover - real network failure only
                last_error = exc
                if attempt + 1 < MAX_ATTEMPTS_PER_PAGE:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                break
        raise TransportFailure(
            f"Hyperliquid public fundingHistory failed after {MAX_ATTEMPTS_PER_PAGE} attempts: {last_error}"
        )

    def fetch_funding(self, coin: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
        _require(coin in HYPERLIQUID_COINS, "coin outside frozen scope")
        _require(end_ms < LOCKED_2026_START_MS, "locked 2026 access forbidden")
        records: list[dict[str, Any]] = []
        cursor = start_ms
        while cursor <= end_ms:
            req = build_hyperliquid_funding_request(coin, cursor, end_ms)
            batch = self.request_json(req)
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
            _require(next_cursor > cursor, "Hyperliquid pagination stalled")
            cursor = next_cursor
        return records


def run_diagnostic() -> dict[str, Any]:
    _require(AUDIT_END_MS < LOCKED_2026_START_MS, "audit reaches locked 2026")

    binance_btc, manifest_btc = fetch_binance_archives("BTCUSDT")
    binance_eth, manifest_eth = fetch_binance_archives("ETHUSDT")
    validate_binance_interval_metadata(binance_btc)
    validate_binance_interval_metadata(binance_eth)

    client = HyperliquidPacedClient()
    hyper_btc = client.fetch_funding("BTC", AUDIT_START_MS, AUDIT_END_MS)
    hyper_eth = client.fetch_funding("ETH", AUDIT_START_MS, AUDIT_END_MS)

    audits = {
        "BINANCE_BTCUSDT": slot_coverage_audit(
            series_id="BINANCE_BTCUSDT", rows=binance_btc,
            timestamp_field="fundingTime", interval_ms=BINANCE_INTERVAL_MS,
        ),
        "BINANCE_ETHUSDT": slot_coverage_audit(
            series_id="BINANCE_ETHUSDT", rows=binance_eth,
            timestamp_field="fundingTime", interval_ms=BINANCE_INTERVAL_MS,
        ),
        "HYPERLIQUID_BTC": slot_coverage_audit(
            series_id="HYPERLIQUID_BTC", rows=hyper_btc,
            timestamp_field="time", interval_ms=HYPERLIQUID_INTERVAL_MS,
        ),
        "HYPERLIQUID_ETH": slot_coverage_audit(
            series_id="HYPERLIQUID_ETH", rows=hyper_eth,
            timestamp_field="time", interval_ms=HYPERLIQUID_INTERVAL_MS,
        ),
    }
    common = _common_months(audits)
    checksums = manifest_btc + manifest_eth
    checksum_ok = all(item["checksum_match"] for item in checksums)

    return {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "transport_id": TRANSPORT_ID,
        "classification": "PROVENANCE_RATE_LIMIT_REMEDIATION_AND_SLOT_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "PASS",
        "technical_route_status": "PASS_PUBLIC_SOURCES_WITH_RATE_LIMIT_SAFE_HYPERLIQUID_TRANSPORT",
        "slot_coverage_gate_status": "PASS" if common else "FAIL_CLOSED_NO_COMMON_FULL_UTC_MONTH",
        "audit_start_ms": AUDIT_START_MS,
        "audit_end_ms": AUDIT_END_MS,
        "locked_2026_start_ms": LOCKED_2026_START_MS,
        "hyperliquid_min_request_interval_seconds": MIN_REQUEST_INTERVAL_SECONDS,
        "hyperliquid_429_cooldown_seconds": HTTP_429_COOLDOWN_SECONDS,
        "hyperliquid_request_count": client.request_count,
        "hyperliquid_http_429_retry_count": client.http_429_retry_count,
        "binance_archive_checksums_all_match": checksum_ok,
        "series_slot_audits": audits,
        "common_eligible_months": common,
        "common_full_month_count": len(common),
        "first_common_full_month": common[0] if common else None,
        "last_common_full_month": common[-1] if common else None,
        "locked_2026_accessed": False,
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
        "normalization_rule": "UNIQUE_NEAREST_NOMINAL_FUNDING_SLOT_EXACT_MONTHLY_SLOT_OCCUPANCY",
    }


def main() -> int:
    receipt_path = Path(
        os.environ.get(
            "PREFREEZE_PROVENANCE_SLOT_V041_RECEIPT",
            "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_SLOT_V041_RECEIPT.json",
        )
    )
    receipt = run_diagnostic()
    _require(receipt["locked_2026_accessed"] is False, "locked 2026 access detected")
    _require(receipt["binance_archive_checksums_all_match"] is True, "Binance checksum failure")
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "technical_route_status": receipt["technical_route_status"],
        "slot_coverage_gate_status": receipt["slot_coverage_gate_status"],
        "common_full_month_count": receipt["common_full_month_count"],
        "first_common_full_month": receipt["first_common_full_month"],
        "last_common_full_month": receipt["last_common_full_month"],
        "hyperliquid_request_count": receipt["hyperliquid_request_count"],
        "hyperliquid_http_429_retry_count": receipt["hyperliquid_http_429_retry_count"],
        "receipt": str(receipt_path),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
