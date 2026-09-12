"""Fail-closed pre-freeze invariants for Cross-Venue Funding & Basis Lab V0.1.

This module is deliberately outcome-blind and network-free.  It exists only to make
scientific-governance, accounting-sign and partition rules machine-checkable before
any economic result from this lab is evaluated.

A PASS from this module is NOT evidence of edge, profitability, execution quality or
trading readiness.  Discovery, paper trading, live trading and exchange mutation remain
blocked by the authority/contract files.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping


LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
PHASE = "PRE_FREEZE"
PASS_LABEL = "PREFREEZE_INVARIANTS_PASS_DISCOVERY_BLOCKED"
FAIL_LABEL = "PREFREEZE_INVARIANTS_FAIL"
AUTHORITY_PRIMARY_ORIENTATION = "LONG_BINANCE_PERP_SHORT_HYPERLIQUID_PERP"
PRIMARY_ORIENTATION = "LONG_BINANCE_SHORT_HYPERLIQUID"
FROZEN_ASSETS = ("BTC", "ETH")
LOCKED_CALENDAR_YEAR = 2026
LATEST_REPLICATION_END_YEAR = 2025


class PreFreezeViolation(RuntimeError):
    """Raised whenever a frozen scientific boundary is violated."""


@dataclass(frozen=True)
class SettlementCashflow:
    venue: str
    side: str
    funding_rate: Decimal
    funding_notional: Decimal
    cashflow: Decimal


@dataclass(frozen=True)
class PricePnL:
    venue: str
    side: str
    base_quantity: Decimal
    entry_price: Decimal
    exit_price: Decimal
    pnl: Decimal


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def load_json(path: Path) -> Mapping[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PreFreezeViolation(f"expected JSON object: {path}")
    return data


def funding_cashflow(*, venue: str, side: str, funding_rate: Decimal, funding_notional: Decimal) -> SettlementCashflow:
    """Return the settlement cashflow sign without annualizing anything.

    Positive funding means longs pay shorts on both frozen venues.  Therefore a
    positive rate produces a negative cashflow for LONG and positive for SHORT.
    """
    normalized_side = side.upper()
    if normalized_side not in {"LONG", "SHORT"}:
        raise PreFreezeViolation("side must be LONG or SHORT")
    if funding_notional < 0:
        raise PreFreezeViolation("funding_notional must be non-negative")
    multiplier = Decimal("-1") if normalized_side == "LONG" else Decimal("1")
    cashflow = funding_notional * funding_rate * multiplier
    return SettlementCashflow(venue, normalized_side, funding_rate, funding_notional, cashflow)


def linear_price_pnl(*, venue: str, side: str, base_quantity: Decimal, entry_price: Decimal, exit_price: Decimal) -> PricePnL:
    normalized_side = side.upper()
    if normalized_side not in {"LONG", "SHORT"}:
        raise PreFreezeViolation("side must be LONG or SHORT")
    if base_quantity < 0:
        raise PreFreezeViolation("base_quantity must be non-negative")
    signed = Decimal("1") if normalized_side == "LONG" else Decimal("-1")
    pnl = signed * base_quantity * (exit_price - entry_price)
    return PricePnL(venue, normalized_side, base_quantity, entry_price, exit_price, pnl)


def consolidated_basis_pnl(
    *,
    base_quantity: Decimal,
    binance_entry: Decimal,
    binance_exit: Decimal,
    hyperliquid_entry: Decimal,
    hyperliquid_exit: Decimal,
) -> Decimal:
    """Price PnL of equal-base-quantity long Binance / short Hyperliquid legs."""
    long_leg = linear_price_pnl(
        venue="BINANCE_USDM",
        side="LONG",
        base_quantity=base_quantity,
        entry_price=binance_entry,
        exit_price=binance_exit,
    )
    short_leg = linear_price_pnl(
        venue="HYPERLIQUID",
        side="SHORT",
        base_quantity=base_quantity,
        entry_price=hyperliquid_entry,
        exit_price=hyperliquid_exit,
    )
    return long_leg.pnl + short_leg.pnl


def deterministic_common_window_start(candidate_full_utc_months: Mapping[str, Iterable[str]]) -> str:
    """Choose earliest common full month by availability only, never by outcomes."""
    required = {
        "BINANCE_BTCUSDT",
        "BINANCE_ETHUSDT",
        "HYPERLIQUID_BTC",
        "HYPERLIQUID_ETH",
    }
    if set(candidate_full_utc_months) != required:
        raise PreFreezeViolation("coverage keys do not match frozen two-venue/two-asset scope")
    sets = [set(candidate_full_utc_months[key]) for key in sorted(required)]
    common = set.intersection(*sets)
    eligible = sorted(month for month in common if int(month[:4]) <= LATEST_REPLICATION_END_YEAR)
    if not eligible:
        raise PreFreezeViolation("no common provenance-eligible full UTC month")
    return eligible[0]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreFreezeViolation(message)


def validate_authority(authority: Mapping[str, Any]) -> None:
    _require(authority.get("lab_id") == LAB_ID, "wrong lab id")
    _require(authority.get("phase") == PHASE, "wrong phase")
    _require(authority.get("status") == "AUTHORIZED_PRE_FREEZE_ONLY", "authority is not pre-freeze-only")
    _require(authority.get("edge_status") == "UNPROVEN", "edge must remain unproven")
    for field in (
        "discovery_backtest_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
        "exchange_mutation_authorized",
        "authenticated_account_data_authorized",
        "merge_to_main_authorized",
        "render_deploy_authorized",
    ):
        _require(authority.get(field) is False, f"{field} must remain false")
    _require(tuple(authority.get("asset_scope_frozen", ())) == FROZEN_ASSETS, "asset scope drift")
    _require(authority.get("primary_candidate_orientation_frozen") == AUTHORITY_PRIMARY_ORIENTATION, "orientation drift")
    governance = authority.get("data_governance", {})
    _require(governance.get("locked_2026_market_outcomes_must_not_be_used_for_hypothesis_generation_or_parameter_selection") is True, "2026 lock missing")
    _require(governance.get("MEXC_2025_locked_data_must_not_be_accessed") is True, "MEXC lock missing")


def validate_contract(contract: Mapping[str, Any]) -> None:
    _require(contract.get("lab_id") == LAB_ID, "wrong contract lab id")
    _require(contract.get("phase") == PHASE, "wrong contract phase")
    _require(contract.get("status") == "PRE_FREEZE_CONTRACT_ACTIVE_DISCOVERY_BLOCKED", "Discovery must be blocked")
    _require(contract.get("edge_status") == "UNPROVEN", "contract cannot establish edge")
    _require(contract.get("primary_orientation") == PRIMARY_ORIENTATION, "primary orientation drift")
    assets = tuple(item.get("base") for item in contract.get("assets", []))
    _require(assets == FROZEN_ASSETS, "contract assets must remain BTC then ETH")
    _require(contract.get("dynamic_threshold_entry_exit") == "FORBIDDEN_UNTIL_PRIMARY_BASELINE_CLOSEOUT", "dynamic thresholding opened early")
    _require(contract.get("machine_learning") == "FORBIDDEN_UNTIL_PRIMARY_BASELINE_CLOSEOUT", "ML opened early")
    partition = contract.get("data_partition_policy", {})
    _require(partition.get("locked_2026_market_data") == "DO_NOT_ACCESS_FOR_THIS_LAB", "2026 access opened")
    _require(partition.get("MEXC_2025") == "OUT_OF_SCOPE_AND_LOCKED", "MEXC access opened")
    _require(partition.get("earliest_independent_calendar_year_under_current_governance") >= 2027, "independent validation leaks into locked year")
    execution = contract.get("execution_cost_policy", {})
    _require(execution.get("maker_fill_guarantee") is False, "maker fills cannot be guaranteed")
    _require(execution.get("vip_discount") is False, "VIP discount cannot enter baseline")
    _require(execution.get("referral_discount") is False, "referral discount cannot enter baseline")
    ledger = contract.get("ledger_model", {})
    _require(ledger.get("venue_level_equity_independent") is True, "venue equity must be independent")
    _require(ledger.get("cross_venue_profit_netting_for_liquidation") is False, "cross-venue liquidation netting forbidden")
    _require(ledger.get("instantaneous_collateral_transfer") is False, "instant collateral transfer forbidden")
    gates = {item["gate"]: item["status"] for item in contract.get("pre_freeze_gates", [])}
    _require(gates.get("G12_DISCOVERY_AUTHORIZATION") == "BLOCKED", "Discovery gate opened")


def validate_source_matrix(matrix: Mapping[str, Any]) -> None:
    _require(matrix.get("lab_id") == LAB_ID, "wrong source matrix lab id")
    _require(matrix.get("economic_outcomes_inspected") is False, "source inventory inspected outcomes")
    gates = matrix.get("provenance_gates", {})
    _require(all(value in {"PENDING", "PASS", "UNOBSERVABLE"} for value in gates.values()), "invalid provenance gate state")
    source_ids = {item.get("source_id") for item in matrix.get("sources", [])}
    required = {
        "BINANCE_USDM_FUNDING_RATE_HISTORY",
        "BINANCE_USDM_FUNDING_INFO",
        "HYPERLIQUID_FUNDING_HISTORY",
        "HYPERLIQUID_FUNDING_MECHANISM",
    }
    _require(required.issubset(source_ids), "missing primary funding provenance sources")


def validate_prefreeze_files(root: Path) -> Mapping[str, Any]:
    authority_path = root / "CROSS_VENUE_FUNDING_BASIS_LAB_PREFREEZE_AUTHORITY_V01.json"
    matrix_path = root / "CROSS_VENUE_FUNDING_BASIS_LAB_SOURCE_PROVENANCE_MATRIX_V01.json"
    contract_path = root / "CROSS_VENUE_FUNDING_BASIS_LAB_PREFREEZE_CONTRACT_V01.json"
    authority = load_json(authority_path)
    matrix = load_json(matrix_path)
    contract = load_json(contract_path)
    validate_authority(authority)
    validate_source_matrix(matrix)
    validate_contract(contract)
    return {
        "lab_id": LAB_ID,
        "phase": PHASE,
        "status": PASS_LABEL,
        "discovery": "BLOCKED",
        "edge": "UNPROVEN",
        "authority_fingerprint": canonical_fingerprint(authority),
        "source_matrix_fingerprint": canonical_fingerprint(matrix),
        "contract_fingerprint": canonical_fingerprint(contract),
        "frozen_assets": list(FROZEN_ASSETS),
        "primary_orientation": PRIMARY_ORIENTATION,
        "locked_2026": True,
        "mexc_locked": True,
        "network_access": "NONE",
        "market_outcomes_evaluated": False,
    }


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    print(json.dumps(validate_prefreeze_files(here), sort_keys=True))
