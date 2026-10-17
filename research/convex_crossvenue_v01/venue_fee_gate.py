"""Offline cost and evidence gate for the CONVEX cross-venue research programme.

Research only. No networking, exchange credentials, orders, capital or strategy mutations.
Fees are public reference scenarios, not account-specific rates or actual fills.
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

# Public base-tier references verified 2026-10-17, basis points PER FILL.
# DO NOT promote these to individual account fee receipts.
REFERENCE_FEES_BPS = {
    "MEXC_FUTURES_API": {"maker": "6", "taker": "8"},
    "KRAKEN_DERIVATIVES": {"maker": "2", "taker": "5"},
    "OKX_FUTURES": {"maker": "2", "taker": "5"},
    "BYBIT_FUTURES": {"maker": "2", "taker": "5.5"},
    "BITGET_FUTURES": {"maker": "2", "taker": "6"},
}

# Explicit true independent receipts required; absent/strings are a failure.
REQUIRED_LIVE_EVIDENCE = (
    "residency_derivatives_eligibility_confirmed",
    "account_specific_api_fee_verified",
    "symbol_contract_tick_min_notional_verified",
    "point_in_time_entry_exit_depth_and_quotes",
    "binance_signal_to_venue_price_parity_validated",
    "venue_specific_funding_costed",
    "immutable_forward_outcomes_sufficient",
    "original_trailing_risk_policy_resolved_prospectively",
    "broker_native_stop_ack_and_recovery_verified",
    "net_positive_independent_out_of_sample_gate",
)


def decimal_nonnegative(value: Any, name: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{name}: decimal value required")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{name}: invalid decimal") from exc
    if not d.is_finite() or d < 0:
        raise ValueError(f"{name}: must be finite and nonnegative")
    return d


def fee_bps(venue: str, liquidity: str) -> Decimal:
    if venue not in REFERENCE_FEES_BPS:
        raise ValueError("Unknown venue (never default a fee)")
    if liquidity not in ("maker", "taker"):
        raise ValueError("liquidity must be maker or taker")
    return Decimal(REFERENCE_FEES_BPS[venue][liquidity])


def scenario_cost_bps(
    venue: str, *, entry: str = "taker", exit: str = "taker",
    total_adverse_slippage_bps: str = "4", total_spread_impact_bps: str = "0",
    net_funding_cost_bps: str = "0", additional_cost_bps: str = "0",
) -> dict[str, str]:
    """Hypothetical all-in bps, with non-fee inputs TOTAL ROUND-TRIP.

    Funding permits a signed credit (negative cost). No venue quote is fetched.
    """
    fee = fee_bps(venue, entry) + fee_bps(venue, exit)
    slip = decimal_nonnegative(total_adverse_slippage_bps, "total_adverse_slippage_bps")
    spread = decimal_nonnegative(total_spread_impact_bps, "total_spread_impact_bps")
    extra = decimal_nonnegative(additional_cost_bps, "additional_cost_bps")
    try:
        funding = Decimal(str(net_funding_cost_bps))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("net_funding_cost_bps: invalid") from exc
    if not funding.is_finite():
        raise ValueError("net_funding_cost_bps: nonfinite")
    return {
        "fee_bps_roundtrip": str(fee),
        "total_cost_bps_roundtrip": str(fee + slip + spread + funding + extra),
        "not_account_verified": "true",
    }


def evidence_gate(receipts: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed: only explicit JSON true passes; even full receipts never permit orders."""
    if not isinstance(receipts, dict):
        raise ValueError("receipts must be an object")
    missing = [field for field in REQUIRED_LIVE_EVIDENCE if receipts.get(field) is not True]
    return {
        "state": "NO_LIVE_GO" if missing else "EVIDENCE_COMPLETE_REQUIRES_SEPARATE_HUMAN_AUTHORIZATION",
        "missing_evidence": missing,
        "does_not_authorize_trades": True,
    }


def report(slip: str, spread: str, funding: str, extra: str, receipts: dict[str, Any]) -> dict[str, Any]:
    return {
        "classification": "RESEARCH_ONLY_REFERENCE_COST_COMPARISON",
        "date_utc": "2026-10-17",
        "assumptions": {
            "total_adverse_slippage_bps": slip,
            "total_spread_impact_bps": spread,
            "net_funding_cost_bps": funding,
            "additional_cost_bps": extra,
        },
        "venues": {v: {
            "maker_taker_reference_bps": REFERENCE_FEES_BPS[v],
            "taker_taker": scenario_cost_bps(
                v, total_adverse_slippage_bps=slip, total_spread_impact_bps=spread,
                net_funding_cost_bps=funding, additional_cost_bps=extra,
            ),
            "maker_taker": scenario_cost_bps(
                v, entry="maker", exit="taker",
                total_adverse_slippage_bps=slip, total_spread_impact_bps=spread,
                net_funding_cost_bps=funding, additional_cost_bps=extra,
            ),
        } for v in REFERENCE_FEES_BPS},
        "evidence": evidence_gate(receipts),
        "warnings": [
            "Historical Binance V5 returns cannot be transferred to another venue by fee subtraction.",
            "Maker orders may fail to fill or change selection bias and adverse selection.",
            "Stops may gap; public order book does not prove fills or safety.",
            "No venue is selected for trading. No live authorization is granted.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slippage-bps", default="4", help="total round-trip adverse slippage assumption")
    parser.add_argument("--spread-bps", default="0", help="total round-trip spread/impact assumption")
    parser.add_argument("--funding-bps", default="0", help="signed net round-trip funding cost; negative credit")
    parser.add_argument("--other-bps", default="0", help="total other cost assumption")
    parser.add_argument("--receipts-json", type=Path, help="optional sanitized evidence JSON, no credentials")
    args = parser.parse_args()
    receipts = {}
    if args.receipts_json:
        receipts = json.loads(args.receipts_json.read_text(encoding="utf-8"))
    print(json.dumps(
        report(args.slippage_bps, args.spread_bps, args.funding_bps, args.other_bps, receipts),
        sort_keys=True, indent=2,
    ))


if __name__ == "__main__":
    main()
