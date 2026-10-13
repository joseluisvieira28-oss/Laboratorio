#!/usr/bin/env python3
"""Deterministic, offline OPTIONS V2.1 10x go/no-go auditor.

No credentials, web requests, account reads, or exchange mutation.
This computes an evidence-based readiness decision, NOT a forward P&L forecast.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path


def d(value: object) -> Decimal:
    return Decimal(str(value))


def economic_bridge(evidence: dict) -> dict:
    """Reproduce frozen sensitivity at the officially published API taker fee floor."""
    economics = evidence["economics"]
    base10 = d(economics["frozen_oos_net10_bps_per_opportunity"])
    stress20 = d(economics["frozen_oos_net20_bps_per_opportunity"])
    implied_weight = (base10 - stress20) / Decimal("10")
    implied_gross = base10 + Decimal("10") * implied_weight
    taker_per_fill = d(economics["mexc_api_market_taker_bps_per_fill"])
    fee_only_rt = taker_per_fill * Decimal("2")
    net_bridge = implied_gross - fee_only_rt * implied_weight
    break_even = implied_gross / implied_weight
    return {
        "net10_bps_per_opportunity": float(base10),
        "net20_bps_per_opportunity": float(stress20),
        "historical_average_executed_weight": float(implied_weight),
        "historical_implied_gross_bps_per_opportunity": float(implied_gross),
        "conservative_taker_bps_per_fill": float(taker_per_fill),
        "market_market_fee_only_bps_full_notional": float(fee_only_rt),
        "historical_implied_break_even_cost_bps": float(break_even),
        "historical_net_sensitivity_at_api_fee_floor_bps": float(net_bridge),
        "fee_floor_exceeds_historical_implied_break_even": fee_only_rt > break_even,
        "warning": "Historical spot-parent OOS sensitivity, not a proven Futures 10x forward result",
    }


def verdict(
    *,
    economic_evidence: dict,
    canonical_signal_source: str,
    execution_engine_source: str,
    transport_source: str,
    prospective_policy: str,
) -> dict:
    econ = economic_bridge(economic_evidence)
    blocks: list[str] = []
    checks = {
        "10x_signal_source": '"leverage": 10' in canonical_signal_source,
        "10x_engine_requires": 'int(signal.get("leverage") or 0) != 10' in execution_engine_source,
        "10x_transport_exact": '"leverage": 10' in transport_source,
        "isolated_future_only": '"margin_mode": "ISOLATED"' in canonical_signal_source
            and 'symbol != "BTC_USDT"' in transport_source,
        "stop_price_emitted_by_canonical_signal": '"protective_stop_loss_price":' in canonical_signal_source,
        "broker_stop_verification_code_present": "def _broker_stop_proven(" in execution_engine_source,
        "pre_outcome_10x_policy_exists": "PRE-OUTCOME ENGINEERING PROTOTYPE" in prospective_policy,
        "attributable_closed_10x_futures_sample_proven": False,
        "broker_real_stop_lifecycle_proven": False,
        "prospective_10x_stop_exit_net_edge_proven": False,
        "stop_recovery_and_exit_reconciled_on_exchange": False,
    }
    for key in ("10x_signal_source", "10x_engine_requires", "10x_transport_exact",
                "isolated_future_only", "broker_stop_verification_code_present",
                "pre_outcome_10x_policy_exists"):
        if not checks[key]:
            blocks.append("CODE_OR_FREEZE_MISMATCH:" + key)
    if not checks["stop_price_emitted_by_canonical_signal"]:
        blocks.append("NO_PRECOMMITTED_STOP_PRICE_FROM_CANONICAL_SIGNAL")
    if not checks["broker_real_stop_lifecycle_proven"]:
        blocks.append("NO_INDEPENDENT_MEXC_STOP_LIFECYCLE_PROOF")
    if not checks["stop_recovery_and_exit_reconciled_on_exchange"]:
        blocks.append("EXCHANGE_RESTART_TRIGGERED_STOP_RECONCILIATION_UNPROVEN")
    if not checks["prospective_10x_stop_exit_net_edge_proven"]:
        blocks.append("NO_PROSPECTIVE_NET_EDGE_FOR_10X_STOPPED_FORK")
    if not checks["attributable_closed_10x_futures_sample_proven"]:
        blocks.append("NO_ATTRIBUTABLE_10X_CLOSED_EXECUTION_RECEIPTS")
    if econ["fee_floor_exceeds_historical_implied_break_even"]:
        blocks.append("TAKER_TAKER_FEES_ALONE_EXCEED_FROZEN_HISTORICAL_BREAK_EVEN")
    if economic_evidence.get("status", "").find("WAITING_LOCAL_READ_ONLY_AUDIT") < 0:
        blocks.append("EXPECTED_FINAL_CANONICAL_ECONOMICS_RECEIPT_CHANGED")

    return {
        "strategy": "OPTIONS-SPOTPERP-001-V2.1",
        "fork": "OPTIONS-SPOTPERP-001-V2.1-FUTURES-10X-PROTECTED-PROSPECTIVE-V0.1",
        "scope": "BTC_USDT Futures LONG/SHORT 10x isolated, max 10 USDT NOTIONAL",
        "live_go": False,
        "decision": "NO_GO_LIVE_10X",
        "decision_scope": "this implementation and MEXC market/market route as audited",
        "code_checks": checks,
        "frozen_oos_cost_sensitivity": econ,
        "blockers": blocks,
        "not_concluded": "No proof every conceivable 10x strategy or cheaper execution venue is unprofitable",
        "action": "Keep Windows task disabled, ARMED absent; research-only, no order placement",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--require-go", action="store_true",
                   help="Return an error when full go authority is absent (it is absent here)")
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    repo = Path(__file__).resolve().parents[2]
    result = verdict(
        economic_evidence=json.loads((repo / "receipts/OPTIONS_SPOTPERP_001_V21_EXECUTION_ECONOMICS_FINAL_CANONICAL_2026-09-28.json").read_text(encoding="utf-8")),
        canonical_signal_source=(repo / "crypto_edge_radar/radar/options_v21_futures_execution_signal.py").read_text(encoding="utf-8"),
        execution_engine_source=(repo / "crypto_edge_radar/radar/options_v21_futures_autolive_engine.py").read_text(encoding="utf-8"),
        transport_source=(repo / "crypto_edge_radar/radar/mexc_auth_trade.py").read_text(encoding="utf-8"),
        prospective_policy=(repo / "governance/OPTIONS_V21_FUTURES_10X_PROTECTED_PROSPECTIVE_V01_2026-10-13.md").read_text(encoding="utf-8"),
    )
    payload = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    print(payload)
    if args.out is not None:
        args.out.write_text(payload, encoding="utf-8")
    if args.require_go and not result["live_go"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
