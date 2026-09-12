"""Authorized Discovery Run 01: funding-rate carry screen for Cross-Venue Funding & Basis Lab.

Economic outcomes ARE authorized for the frozen 2024-09 through 2025-12 adversarial
replication window. This run is deliberately narrower than the full mechanism replication:
it measures realized funding-rate carry under a constant-notional normalization, frozen
round-trip taker fees, and DGS3MO opportunity cost. It does not compute historical basis
PnL, slippage, executable returns, liquidation exactness, APR/APY, Sharpe, or signals.

A positive Run 01 screen cannot confirm the mechanism or edge. Full replication remains
pending historical price/basis provenance.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any, Iterable, Mapping

import cross_venue_funding_basis_provenance_shakedown_v01 as v1

getcontext().prec = 40

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
RUN_ID = "CROSS_VENUE_FUNDING_BASIS_DISCOVERY_RUN01_RATE_SCREEN_V01"
START_MS = int(datetime(2024, 9, 1, tzinfo=timezone.utc).timestamp() * 1000)
END_MS = int(datetime(2025, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc).timestamp() * 1000)
START_DATE = date(2024, 9, 1)
END_DATE_EXCLUSIVE = date(2026, 1, 1)
EXPECTED_MONTHS = [
    f"{y:04d}-{m:02d}"
    for y, m in (
        [(2024, m) for m in range(9, 13)]
        + [(2025, m) for m in range(1, 13)]
    )
]
BINANCE_FEE = Decimal("0.00050")
HYPERLIQUID_FEE = Decimal("0.00045")
TOTAL_ROUND_TRIP_FEE = (BINANCE_FEE * 2) + (HYPERLIQUID_FEE * 2)
IMMOBILIZED_CAPITAL = Decimal("1.50")
FRED_SERIES = "DGS3MO"


class DiscoveryFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DiscoveryFailure(message)


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def validate_authorization(auth: Mapping[str, Any], contract: Mapping[str, Any], coverage: Mapping[str, Any]) -> None:
    require(auth.get("lab_id") == LAB_ID, "authorization wrong lab")
    require(auth.get("status") == "EXPLICIT_DISCOVERY_AUTHORIZED", "Discovery not explicitly authorized")
    scope = auth.get("authorized_scope", {})
    require(scope.get("replication_start_month") == "2024-09", "authorization start drift")
    require(scope.get("replication_end_month") == "2025-12", "authorization end drift")
    require(scope.get("assets") == ["BTC", "ETH"], "authorization asset drift")
    require(scope.get("primary_orientation") == "LONG_BINANCE_SHORT_HYPERLIQUID", "authorization orientation drift")
    require(scope.get("economic_outcomes_may_be_inspected") is True, "economic outcomes not authorized")

    require(contract.get("lab_id") == LAB_ID, "contract wrong lab")
    require(contract.get("status") == "FROZEN_BEFORE_DISCOVERY_OUTCOMES", "Discovery contract not frozen")
    require(contract.get("edge_status") == "UNPROVEN", "contract edge status drift")
    require(contract.get("primary_orientation") == "LONG_BINANCE_SHORT_HYPERLIQUID", "contract orientation drift")
    require(contract.get("window", {}).get("start_utc") == "2024-09-01T00:00:00.000Z", "contract start drift")
    require(contract.get("window", {}).get("end_utc") == "2025-12-31T23:59:59.999Z", "contract end drift")

    require(coverage.get("status") == "COVERAGE_PARTITION_MATERIALIZED", "coverage partition not materialized")
    require(coverage.get("primary_months") == EXPECTED_MONTHS, "coverage months do not match authorized Discovery window")
    require(coverage.get("imputation_used") is False, "coverage used imputation")
    require(coverage.get("economic_outcomes_used_for_selection") is False, "coverage used economic outcomes")


def specs() -> dict[str, v1.SeriesSpec]:
    return {
        "BINANCE_BTCUSDT": v1.SeriesSpec("BINANCE_BTCUSDT", "BINANCE_USDM", "BTCUSDT", 8 * 60 * 60 * 1000),
        "BINANCE_ETHUSDT": v1.SeriesSpec("BINANCE_ETHUSDT", "BINANCE_USDM", "ETHUSDT", 8 * 60 * 60 * 1000),
        "HYPERLIQUID_BTC": v1.SeriesSpec("HYPERLIQUID_BTC", "HYPERLIQUID", "BTC", 60 * 60 * 1000),
        "HYPERLIQUID_ETH": v1.SeriesSpec("HYPERLIQUID_ETH", "HYPERLIQUID", "ETH", 60 * 60 * 1000),
    }


def timestamp_fields() -> dict[str, str]:
    return {
        "BINANCE_BTCUSDT": "fundingTime",
        "BINANCE_ETHUSDT": "fundingTime",
        "HYPERLIQUID_BTC": "time",
        "HYPERLIQUID_ETH": "time",
    }


def fetch_all_frozen_raw() -> dict[str, list[dict[str, Any]]]:
    return {
        "BINANCE_BTCUSDT": v1.fetch_binance_funding("BTCUSDT", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
        "BINANCE_ETHUSDT": v1.fetch_binance_funding("ETHUSDT", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
        "HYPERLIQUID_BTC": v1.fetch_hyperliquid_funding("BTC", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
        "HYPERLIQUID_ETH": v1.fetch_hyperliquid_funding("ETH", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
    }


def verify_raw_against_prefreeze(raw: Mapping[str, list[dict[str, Any]]], prefreeze_v02: Mapping[str, Any]) -> dict[str, str]:
    require(prefreeze_v02.get("diagnostic_id") == "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_DIAGNOSTIC_V02", "wrong V0.2 provenance receipt")
    require(prefreeze_v02.get("status") == "DIAGNOSTIC_COMPLETE", "V0.2 provenance incomplete")
    require(prefreeze_v02.get("locked_2026_accessed") is False, "V0.2 touched 2026")
    out: dict[str, str] = {}
    sp = specs()
    tf = timestamp_fields()
    for sid in sorted(raw):
        audit = v1.audit_series(sp[sid], raw[sid], tf[sid])
        actual = str(audit["canonical_raw_records_sha256"])
        expected = str(prefreeze_v02["series"][sid]["canonical_raw_records_sha256"])
        require(actual == expected, f"raw historical data drift since Pre-Freeze: {sid}")
        require(len(audit["conflicting_duplicate_timestamps"]) == 0, f"conflicting duplicates: {sid}")
        out[sid] = actual
    return out


def filter_window(rows: Iterable[dict[str, Any]], timestamp_field: str) -> list[dict[str, Any]]:
    selected = [dict(r) for r in rows if START_MS <= int(r[timestamp_field]) <= END_MS]
    require(selected, "empty Discovery funding window")
    require(all(int(r[timestamp_field]) < v1.LOCKED_2026_START_MS for r in selected), "2026 funding record leaked")
    return selected


def sum_rates(rows: Iterable[dict[str, Any]]) -> Decimal:
    total = Decimal("0")
    for row in rows:
        total += Decimal(str(row["fundingRate"]))
    return total


def fred_url() -> str:
    params = urllib.parse.urlencode({"id": FRED_SERIES, "cosd": "2024-08-01", "coed": "2025-12-31"})
    return f"https://fred.stlouisfed.org/graph/fredgraph.csv?{params}"


def fetch_fred_dgs3mo() -> tuple[list[tuple[date, Decimal]], str]:
    req = urllib.request.Request(fred_url(), headers={"User-Agent": "DreamAccountOS-Research-Discovery/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    text = raw.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    require(header is not None and len(header) >= 2, "unexpected FRED CSV header")
    observations: list[tuple[date, Decimal]] = []
    normalized_rows: list[list[str]] = [list(header)]
    for row in reader:
        if len(row) < 2:
            continue
        normalized_rows.append([row[0], row[1]])
        value = row[1].strip()
        if not value or value == ".":
            continue
        observations.append((date.fromisoformat(row[0]), Decimal(value)))
    observations.sort(key=lambda x: x[0])
    require(observations, "no FRED DGS3MO observations")
    return observations, canonical_sha256(normalized_rows)


def opportunity_cost(observations: list[tuple[date, Decimal]], start: date = START_DATE, end_exclusive: date = END_DATE_EXCLUSIVE, capital: Decimal = IMMOBILIZED_CAPITAL) -> tuple[Decimal, int]:
    require(start < end_exclusive, "invalid opportunity-cost range")
    obs = sorted(observations, key=lambda x: x[0])
    total = Decimal("0")
    days = 0
    d = start
    while d < end_exclusive:
        prior = [rate for obs_date, rate in obs if obs_date < d]
        require(prior, f"no previously available DGS3MO observation before {d.isoformat()}")
        annual_percent = prior[-1]
        total += capital * (annual_percent / Decimal("100")) / Decimal("365")
        days += 1
        d += timedelta(days=1)
    return total, days


def compute_asset_screen(binance_rows: list[dict[str, Any]], hyperliquid_rows: list[dict[str, Any]], opp_cost: Decimal) -> dict[str, Any]:
    b_sum = sum_rates(binance_rows)
    h_sum = sum_rates(hyperliquid_rows)
    b_long = -b_sum
    h_short = h_sum
    gross = b_long + h_short
    net = gross - TOTAL_ROUND_TRIP_FEE - opp_cost
    capital_return = net / IMMOBILIZED_CAPITAL
    return {
        "binance_settlement_count": len(binance_rows),
        "hyperliquid_settlement_count": len(hyperliquid_rows),
        "binance_long_funding_component": str(b_long),
        "hyperliquid_short_funding_component": str(h_short),
        "gross_primary_funding_carry": str(gross),
        "frozen_round_trip_fee": str(TOTAL_ROUND_TRIP_FEE),
        "opportunity_cost": str(opp_cost),
        "net_normalized_rate_carry_screen": str(net),
        "net_screen_return_on_immobilized_capital": str(capital_return),
        "net_positive": net > 0,
    }


def build_run(root: Path) -> dict[str, Any]:
    project = root.parent
    auth = load_json(root / "CROSS_VENUE_FUNDING_BASIS_DISCOVERY_AUTHORIZATION_V01.json")
    contract = load_json(root / "CROSS_VENUE_FUNDING_BASIS_DISCOVERY_CONTRACT_V01.json")
    coverage = load_json(project / "CROSS_VENUE_FUNDING_BASIS_COVERAGE_V04_RECEIPT.json")
    prefreeze_v02 = load_json(project / "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_DIAGNOSTIC_V02_RECEIPT.json")
    validate_authorization(auth, contract, coverage)

    raw = fetch_all_frozen_raw()
    raw_hashes = verify_raw_against_prefreeze(raw, prefreeze_v02)
    fields = timestamp_fields()
    windowed = {sid: filter_window(raw[sid], fields[sid]) for sid in raw}

    fred_obs, fred_hash = fetch_fred_dgs3mo()
    opp_cost, accrual_days = opportunity_cost(fred_obs)

    btc = compute_asset_screen(windowed["BINANCE_BTCUSDT"], windowed["HYPERLIQUID_BTC"], opp_cost)
    eth = compute_asset_screen(windowed["BINANCE_ETHUSDT"], windowed["HYPERLIQUID_ETH"], opp_cost)
    combined_return = (Decimal(btc["net_screen_return_on_immobilized_capital"]) + Decimal(eth["net_screen_return_on_immobilized_capital"])) / Decimal("2")
    both_positive = bool(btc["net_positive"] and eth["net_positive"])
    screen_label = "RATE_CARRY_SCREEN_POSITIVE_BOTH_ASSETS" if both_positive else "RATE_CARRY_SCREEN_NOT_POSITIVE_BOTH_ASSETS"

    receipt = {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "run_id": RUN_ID,
        "phase": "DISCOVERY",
        "status": "RUN01_COMPLETE",
        "classification": "DIAGNOSTIC_RATE_CARRY_SCREEN_ONLY_NOT_FULL_MECHANISM_REPLICATION",
        "primary_orientation": "LONG_BINANCE_SHORT_HYPERLIQUID",
        "window": {"start_month": "2024-09", "end_month": "2025-12", "month_count": 16},
        "raw_prefreeze_hashes_reverified": True,
        "raw_series_sha256": raw_hashes,
        "fred_series": FRED_SERIES,
        "fred_csv_sha256": fred_hash,
        "opportunity_cost_accrual_days": accrual_days,
        "normalized_immobilized_capital_per_asset": str(IMMOBILIZED_CAPITAL),
        "assets": {"BTC": btc, "ETH": eth},
        "equal_deployed_capital_50_50_combined_net_screen_return": str(combined_return),
        "screen_label": screen_label,
        "screen_label_can_confirm_mechanism": False,
        "full_mechanism_replication_status": "PENDING_HISTORICAL_PRICE_BASIS_PROVENANCE",
        "historical_executable_return_claim_authorized": False,
        "apr_apy_computed": False,
        "sharpe_sortino_computed": False,
        "reverse_orientation_computed": False,
        "tuning_performed": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "exchange_mutation_used": False,
        "locked_2026_market_data_accessed": False,
        "mexc_2025_accessed": False,
        "edge_status": "UNPROVEN",
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    return receipt


def main() -> None:
    here = Path(__file__).resolve().parent
    output = Path(os.environ.get("DISCOVERY_RUN01_RECEIPT", str(here.parent / "CROSS_VENUE_FUNDING_BASIS_DISCOVERY_RUN01_RATE_SCREEN_V01_RECEIPT.json")))
    receipt = build_run(here)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "classification": receipt["classification"],
        "screen_label": receipt["screen_label"],
        "BTC": receipt["assets"]["BTC"],
        "ETH": receipt["assets"]["ETH"],
        "combined_net_screen_return": receipt["equal_deployed_capital_50_50_combined_net_screen_return"],
        "full_mechanism_replication_status": receipt["full_mechanism_replication_status"],
        "edge_status": receipt["edge_status"],
        "receipt_sha256": receipt["receipt_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
