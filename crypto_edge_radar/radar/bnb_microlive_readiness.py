from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Any

from .timing import ExactTimingPolicy, TimingState

STRATEGY_ID = "BNB-LAUNCHPOOL-DEMAND-001"
MAX_NOTIONAL_CHF = 25.0
STRESS_ROUND_TRIP_BPS = 30.0
ENTRY_ORDER_TYPE = "MARKET"
EXIT_ORDER_TYPE = "MARKET"
ARM_LEAD_SECONDS = 60.0
MAX_LATE_SECONDS = 2.0


@dataclass(frozen=True)
class BNBMicroLiveInputs:
    signal_eligible: bool
    prospective_event: bool
    source_timestamp_unambiguous: bool
    bnbbtc_market_binding_ok: bool
    duplicate_or_cluster_violation: bool
    overlapping_active_trade: bool
    account_fee_verified_read_only: bool
    venue_min_notional_chf: float | None
    observed_full_spread_bps: float | None
    simulated_market_impact_bps: float | None
    taker_fee_bps_per_side: float | None
    execution_authority_present: bool


def projected_round_trip_bps(
    *,
    observed_full_spread_bps: float,
    simulated_market_impact_bps: float,
    taker_fee_bps_per_side: float,
) -> float:
    values = (
        observed_full_spread_bps,
        simulated_market_impact_bps,
        taker_fee_bps_per_side,
    )
    if any((not isfinite(v) or v < 0) for v in values):
        raise ValueError("friction inputs must be finite and non-negative")
    return (
        2.0 * taker_fee_bps_per_side
        + 2.0 * observed_full_spread_bps
        + 2.0 * simulated_market_impact_bps
    )


def evaluate_bnb_microlive_readiness(
    inputs: BNBMicroLiveInputs,
    *,
    now: datetime,
    entry_target: datetime,
) -> dict[str, Any]:
    policy = ExactTimingPolicy(
        arm_lead_seconds=ARM_LEAD_SECONDS,
        max_late_seconds=MAX_LATE_SECONDS,
    )
    timing = policy.receipt(now=now, target=entry_target)

    blockers: list[str] = []
    if not inputs.signal_eligible:
        blockers.append("SIGNAL_NOT_ELIGIBLE")
    if not inputs.prospective_event:
        blockers.append("EVENT_NOT_STRICTLY_PROSPECTIVE")
    if not inputs.source_timestamp_unambiguous:
        blockers.append("SOURCE_TIMESTAMP_AMBIGUOUS")
    if not inputs.bnbbtc_market_binding_ok:
        blockers.append("BNBBTC_MARKET_BINDING_FAIL")
    if inputs.duplicate_or_cluster_violation:
        blockers.append("DUPLICATE_OR_CLUSTER_VIOLATION")
    if inputs.overlapping_active_trade:
        blockers.append("ONE_ACTIVE_TRADE_VIOLATION")
    if not inputs.account_fee_verified_read_only:
        blockers.append("ACCOUNT_TAKER_FEE_NOT_VERIFIED_READ_ONLY")

    if inputs.venue_min_notional_chf is None:
        blockers.append("VENUE_MIN_NOTIONAL_UNKNOWN")
    elif inputs.venue_min_notional_chf > MAX_NOTIONAL_CHF:
        blockers.append("VENUE_MIN_NOTIONAL_EXCEEDS_CHF25_CAP")

    friction = None
    if (
        inputs.observed_full_spread_bps is None
        or inputs.simulated_market_impact_bps is None
        or inputs.taker_fee_bps_per_side is None
    ):
        blockers.append("ALL_IN_FRICTION_NOT_VERIFIED")
    else:
        friction = projected_round_trip_bps(
            observed_full_spread_bps=inputs.observed_full_spread_bps,
            simulated_market_impact_bps=inputs.simulated_market_impact_bps,
            taker_fee_bps_per_side=inputs.taker_fee_bps_per_side,
        )
        if friction > STRESS_ROUND_TRIP_BPS:
            blockers.append("PROJECTED_FRICTION_EXCEEDS_STRESS30")

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

    return {
        "strategy_id": STRATEGY_ID,
        "classification": (
            "MICROLIVE_EXECUTION_WINDOW_OPEN"
            if micro_live_allowed
            else "READINESS_FAIL_CLOSED"
        ),
        "ready_for_execution_authority": ready_for_execution_authority,
        "micro_live_allowed": micro_live_allowed,
        "max_real_money_notional_chf": MAX_NOTIONAL_CHF,
        "leverage_allowed": False,
        "max_simultaneous_positions": 1,
        "entry_order_type": ENTRY_ORDER_TYPE,
        "exit_order_type": EXIT_ORDER_TYPE,
        "entry_timing": timing,
        "hold_hours": 24,
        "late_chase_allowed": False,
        "maker_fallback_allowed": False,
        "averaging_down_allowed": False,
        "pyramiding_allowed": False,
        "projected_round_trip_bps": friction,
        "stress_round_trip_budget_bps": STRESS_ROUND_TRIP_BPS,
        "blockers": blockers,
        "safety_exit_rule": (
            "If exact 24h exit cannot execute because of venue/source outage, "
            "flatten the filled position at the first safe opportunity; log "
            "EXECUTION_FAILURE and do not count the event as valid micro-live evidence."
        ),
        "partial_entry_fill_rule": (
            "Do not chase remainder. Manage any filled quantity to safety exit; "
            "mark execution deviation and exclude from valid micro-live evidence."
        ),
        "authenticated_exchange_api_used_by_this_evaluator": False,
        "order_created_by_this_evaluator": False,
        "exchange_mutation_performed_by_this_evaluator": False,
    }
