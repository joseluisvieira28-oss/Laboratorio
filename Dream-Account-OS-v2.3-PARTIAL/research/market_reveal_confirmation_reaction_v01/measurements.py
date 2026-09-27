"""Decision-time-only continuous measurements for MRCR V0.1.

No target outcome, classifier or action logic is implemented here.
"""

from __future__ import annotations

import math
from typing import Optional, Dict


def _positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and > 0")


def signed_flow_imbalance(buy_notional: float, sell_notional: float) -> Optional[float]:
    if buy_notional < 0 or sell_notional < 0:
        raise ValueError("notional values must be >= 0")
    total = buy_notional + sell_notional
    if total == 0:
        return None
    return (buy_notional - sell_notional) / total


def log_return_bps(pre_mid: float, decision_mid: float) -> float:
    _positive("pre_mid", pre_mid)
    _positive("decision_mid", decision_mid)
    return math.log(decision_mid / pre_mid) * 10_000.0


def price_response_per_unit_flow(
    decision_return_bps: float, flow_imbalance: Optional[float]
) -> Optional[float]:
    if flow_imbalance is None or flow_imbalance == 0:
        return None
    return decision_return_bps / flow_imbalance


def alignment_sign(
    decision_return_bps: float, flow_imbalance: Optional[float]
) -> int:
    if flow_imbalance is None or flow_imbalance == 0 or decision_return_bps == 0:
        return 0
    return 1 if (decision_return_bps > 0) == (flow_imbalance > 0) else -1


def retracement_fraction(
    pre_mid: float, extreme_mid_to_decision: float, decision_mid: float
) -> Optional[float]:
    _positive("pre_mid", pre_mid)
    _positive("extreme_mid_to_decision", extreme_mid_to_decision)
    _positive("decision_mid", decision_mid)

    if extreme_mid_to_decision > pre_mid:
        return (extreme_mid_to_decision - decision_mid) / (
            extreme_mid_to_decision - pre_mid
        )
    if extreme_mid_to_decision < pre_mid:
        return (decision_mid - extreme_mid_to_decision) / (
            pre_mid - extreme_mid_to_decision
        )
    return None


def ratio(current: float, baseline: float) -> float:
    if not math.isfinite(current) or current < 0:
        raise ValueError("current must be finite and >= 0")
    _positive("baseline", baseline)
    return current / baseline


def effort_per_result(
    aggressive_notional: float, decision_return_bps: float
) -> Optional[float]:
    if aggressive_notional < 0 or not math.isfinite(aggressive_notional):
        raise ValueError("aggressive_notional must be finite and >= 0")
    if decision_return_bps == 0:
        return None
    return aggressive_notional / abs(decision_return_bps)


def state_vector(
    *,
    pre_mid: float,
    decision_mid: float,
    extreme_mid_to_decision: float,
    buy_notional: float,
    sell_notional: float,
    spread_pre: float,
    spread_now: float,
    max_spread_to_decision: float,
    depth_pre: float,
    depth_now: float,
) -> Dict[str, Optional[float]]:
    flow = signed_flow_imbalance(buy_notional, sell_notional)
    ret = log_return_bps(pre_mid, decision_mid)
    return {
        "flow_imbalance": flow,
        "decision_return_bps": ret,
        "price_response_per_unit_flow": price_response_per_unit_flow(ret, flow),
        "alignment_sign": float(alignment_sign(ret, flow)),
        "retracement_fraction": retracement_fraction(
            pre_mid, extreme_mid_to_decision, decision_mid
        ),
        "spread_vs_pre": ratio(spread_now, spread_pre),
        "spread_vs_max_to_decision": ratio(spread_now, max_spread_to_decision),
        "depth_vs_pre": ratio(depth_now, depth_pre),
        "effort_per_result": effort_per_result(
            buy_notional + sell_notional, ret
        ),
    }
