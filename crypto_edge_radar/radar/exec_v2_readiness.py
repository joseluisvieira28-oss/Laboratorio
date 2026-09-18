from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Any

from .timing import ExactTimingPolicy, TimingState

STRATEGY_ID = "ETF-CME-INSTFLOW-001"
MAX_ALLOCATION_FRACTION_OF_EQUITY = 0.001
STRESS_ROUND_TRIP_BPS = 20.0
ARM_LEAD_SECONDS = 60.0
MAX_LATE_SECONDS = 2.0


@dataclass(frozen=True)
class ExecV2Inputs:
    direction: str
    account_fee_verified_read_only: bool
    venue_min_notional_quote: float | None
    account_equity_quote: float | None
    public_market_binding_ok: bool
    observed_full_spread_bps: float | None
    simulated_market_impact_bps: float | None
    taker_fee_bps_per_side: float | None
    conservative_funding_burden_bps: float | None
    isolated_margin_confirmed: bool
    auto_margin_add_off_confirmed: bool
    leverage_1x_confirmed: bool
    conflicting_position_or_order: bool
    execution_authority_present: bool


def max_validation_allocation(account_equity_quote: float) -> float:
    if not isfinite(account_equity_quote) or account_equity_quote <= 0:
        raise ValueError("account equity must be finite and positive")
    return account_equity_quote * MAX_ALLOCATION_FRACTION_OF_EQUITY


def projected_round_trip_bps(
    *,
    direction: str,
    observed_full_spread_bps: float,
    simulated_market_impact_bps: float,
    taker_fee_bps_per_side: float,
    conservative_funding_burden_bps: float = 0.0,
) -> float:
    direction = direction.upper()
    if direction not in {"LONG", "SHORT"}:
        raise ValueError("direction must be LONG or SHORT")
    values = (
        observed_full_spread_bps,
        simulated_market_impact_bps,
        taker_fee_bps_per_side,
        conservative_funding_burden_bps,
    )
    if any((not isfinite(v) or v < 0) for v in values):
        raise ValueError("friction inputs must be finite and non-negative")
    funding = conservative_funding_burden_bps if direction == "SHORT" else 0.0
    return (
        2.0 * taker_fee_bps_per_side
        + 2.0 * observed_full_spread_bps
        + 2.0 * simulated_market_impact_bps
        + funding
    )


def evaluate_exec_v2_readiness(
    inputs: ExecV2Inputs,
    *,
    now: datetime,
    entry_target: datetime,
) -> dict[str, Any]:
    direction = inputs.direction.upper()
    if direction not in {"LONG", "SHORT"}:
        raise ValueError("direction must be LONG or SHORT")

    timing = ExactTimingPolicy(
        arm_lead_seconds=ARM_LEAD_SECONDS,
        max_late_seconds=MAX_LATE_SECONDS,
    ).receipt(now=now, target=entry_target)

    blockers: list[str] = []
    if not inputs.public_market_binding_ok:
        blockers.append("PUBLIC_MARKET_BINDING_FAIL")
    if not inputs.account_fee_verified_read_only:
        blockers.append("ACCOUNT_API_FEE_NOT_VERIFIED_READ_ONLY")
    if inputs.conflicting_position_or_order:
        blockers.append("CONFLICTING_POSITION_OR_ORDER")

    budget = None
    if inputs.account_equity_quote is None:
        blockers.append("ACCOUNT_EQUITY_UNKNOWN")
    else:
        budget = max_validation_allocation(float(inputs.account_equity_quote))

    if inputs.venue_min_notional_quote is None:
        blockers.append("VENUE_MIN_NOTIONAL_UNKNOWN")
    elif budget is not None and float(inputs.venue_min_notional_quote) > budget:
        blockers.append("VENUE_MIN_NOTIONAL_EXCEEDS_VALIDATION_BUDGET")

    if direction == "SHORT":
        if not inputs.isolated_margin_confirmed:
            blockers.append("SHORT_ISOLATED_MARGIN_NOT_CONFIRMED")
        if not inputs.auto_margin_add_off_confirmed:
            blockers.append("SHORT_AUTO_MARGIN_ADD_NOT_CONFIRMED_OFF")
        if not inputs.leverage_1x_confirmed:
            blockers.append("SHORT_LEVERAGE_NOT_CONFIRMED_1X")

    friction = None
    required = (
        inputs.observed_full_spread_bps,
        inputs.simulated_market_impact_bps,
        inputs.taker_fee_bps_per_side,
    )
    if any(v is None for v in required):
        blockers.append("ALL_IN_FRICTION_NOT_VERIFIED")
    elif direction == "SHORT" and inputs.conservative_funding_burden_bps is None:
        blockers.append("SHORT_FUNDING_BURDEN_NOT_VERIFIED")
    else:
        friction = projected_round_trip_bps(
            direction=direction,
            observed_full_spread_bps=float(inputs.observed_full_spread_bps),
            simulated_market_impact_bps=float(inputs.simulated_market_impact_bps),
            taker_fee_bps_per_side=float(inputs.taker_fee_bps_per_side),
            conservative_funding_burden_bps=float(inputs.conservative_funding_burden_bps or 0.0),
        )
        if friction > STRESS_ROUND_TRIP_BPS:
            blockers.append("PROJECTED_FRICTION_EXCEEDS_STRESS20")

    state = timing["timing_state"]
    if state == TimingState.MISSED.value:
        blockers.append("MISSED_ENTRY_NO_CHASE")
    elif state not in (TimingState.ARMED.value, TimingState.DUE.value):
        blockers.append("ENTRY_WINDOW_NOT_ARMED_OR_DUE")

    readiness_blockers = list(blockers)
    ready_for_execution_authority = len(readiness_blockers) == 0
    if not inputs.execution_authority_present:
        blockers.append("SEPARATE_EXECUTION_AUTHORITY_ABSENT")

    micro_live_allowed = len(blockers) == 0 and state == TimingState.DUE.value

    mapping = (
        {
            "market": "MEXC_SPOT",
            "symbol": "BTCUSDT",
            "entry_order": "MARKET BUY",
            "exit_order": "MARKET SELL",
            "leverage": 0,
            "loss_container": "UNLEVERED_SPOT_NOTIONAL_CAP",
        }
        if direction == "LONG"
        else {
            "market": "MEXC_USDT_PERPETUAL",
            "symbol": "BTC_USDT",
            "entry_order": "MARKET SELL/OPEN",
            "exit_order": "MARKET BUY/CLOSE REDUCE_ONLY",
            "leverage": 1,
            "margin_mode": "ISOLATED",
            "auto_margin_add": "OFF_REQUIRED",
            "loss_container": "INITIAL_ISOLATED_MARGIN_CAP",
        }
    )

    return {
        "strategy_id": STRATEGY_ID,
        "direction": direction,
        "classification": (
            "MICROLIVE_EXECUTION_WINDOW_OPEN"
            if micro_live_allowed
            else "EXEC_V2_READINESS_FAIL_CLOSED"
        ),
        "mapping": mapping,
        "entry_timing": timing,
        "hold_days": 7,
        "max_initial_allocation_fraction_of_equity": MAX_ALLOCATION_FRACTION_OF_EQUITY,
        "max_initial_allocation_quote": budget,
        "projected_round_trip_bps": friction,
        "stress_round_trip_budget_bps": STRESS_ROUND_TRIP_BPS,
        "ready_for_execution_authority": ready_for_execution_authority,
        "micro_live_allowed": micro_live_allowed,
        "late_chase_allowed": False,
        "maker_fallback_allowed": False,
        "partial_fill_rule": (
            "Do not chase remainder. Manage filled quantity to the frozen safety exit; "
            "mark execution deviation and exclude from valid micro-live evidence."
        ),
        "missed_exit_rule": (
            "Flatten at first safe opportunity; log EXECUTION_FAILURE; "
            "do not count as valid micro-live evidence."
        ),
        "blockers": blockers,
        "authenticated_exchange_api_used_by_this_evaluator": False,
        "order_created_by_this_evaluator": False,
        "exchange_mutation_performed_by_this_evaluator": False,
    }
