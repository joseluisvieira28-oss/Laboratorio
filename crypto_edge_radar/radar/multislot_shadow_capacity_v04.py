from __future__ import annotations

from collections import Counter
import math
from typing import Any


def _finite(value: Any, name: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise ValueError(f"{name} must be finite")
    return x


def evaluate_shadow_capacity(
    *,
    candidate: dict[str, Any],
    existing: list[dict[str, Any]],
    policy: dict[str, Any],
    daily_realized_loss_usdt: float = 0.0,
    rolling_7d_realized_loss_usdt: float = 0.0,
) -> dict[str, Any]:
    """Read-only/synthetic V0.4 portfolio capacity model.

    This function never contacts an exchange and never authorizes an order.
    It only evaluates whether a hypothetical additional lane would remain
    inside the frozen three-slot small-exposure envelope.
    """
    blockers: list[str] = []
    lane_id = str(candidate.get("candidate_id") or "")
    symbol = str(candidate.get("symbol") or "").upper()
    lanes = policy.get("lanes") or {}
    lane = lanes.get(lane_id)
    if not isinstance(lane, dict):
        return {"pass": False, "blockers": ["LANE_NOT_IN_FROZEN_POLICY"]}

    max_positions = int((policy.get("capacity") or {}).get("max_simultaneous_positions", 0))
    global_cfg = policy.get("global_risk") or {}

    try:
        requested_notional = _finite(candidate.get("max_notional_usdt"), "candidate.max_notional_usdt")
        requested_margin = _finite(candidate.get("max_initial_margin_usdt"), "candidate.max_initial_margin_usdt")
        leverage = int(candidate.get("leverage"))
        daily = _finite(daily_realized_loss_usdt, "daily_realized_loss_usdt")
        rolling = _finite(rolling_7d_realized_loss_usdt, "rolling_7d_realized_loss_usdt")
    except Exception as exc:
        return {"pass": False, "blockers": [f"INPUT_INVALID:{type(exc).__name__}"]}

    if leverage != int(lane.get("leverage", -1)):
        blockers.append("LANE_LEVERAGE_MISMATCH")
    if requested_notional <= 0 or requested_notional > float(lane.get("max_notional_usdt", 0)) + 1e-12:
        blockers.append("LANE_NOTIONAL_CAP_EXCEEDED")
    if requested_margin <= 0 or requested_margin > float(lane.get("max_initial_margin_usdt", 0)) + 1e-12:
        blockers.append("LANE_MARGIN_CAP_EXCEEDED")
    allowed_symbols = {str(x).upper() for x in lane.get("symbol_policy", [])}
    if symbol not in allowed_symbols:
        blockers.append("SYMBOL_NOT_ALLOWED")

    daily_kill = float(global_cfg.get("daily_realized_loss_kill_usdt", 0))
    rolling_kill = float(global_cfg.get("rolling_7d_realized_loss_kill_usdt", 0))
    if daily >= daily_kill:
        blockers.append("DAILY_KILL_ACTIVE")
    if rolling >= rolling_kill:
        blockers.append("ROLLING_7D_KILL_ACTIVE")

    lane_counts = Counter()
    symbols = set()
    used_notional = 0.0
    used_margin = 0.0
    identities = set()
    for row in existing:
        if not isinstance(row, dict):
            blockers.append("EXISTING_ROW_INVALID")
            continue
        ident = str(row.get("signal_identity") or row.get("immutable_signal_key") or "")
        if ident and ident in identities:
            continue
        if ident:
            identities.add(ident)
        rid = str(row.get("candidate_id") or "")
        rsymbol = str(row.get("symbol") or "").upper()
        try:
            rn = _finite(row.get("estimated_notional_usdt", row.get("max_notional_usdt")), "existing.notional")
            rm = _finite(row.get("estimated_initial_margin_usdt", row.get("max_initial_margin_usdt")), "existing.margin")
        except Exception:
            blockers.append("EXISTING_RISK_UNKNOWN")
            continue
        lane_counts[rid] += 1
        symbols.add(rsymbol)
        used_notional += rn
        used_margin += rm

    if len(existing) >= max_positions:
        blockers.append("THREE_SLOT_CAPACITY_FULL")
    if symbol in symbols:
        blockers.append("SYMBOL_ALREADY_OCCUPIED")
    if lane_counts[lane_id] >= int(lane.get("max_positions", 1)):
        blockers.append("LANE_CAPACITY_FULL")

    projected_notional = used_notional + requested_notional
    projected_margin = used_margin + requested_margin
    if projected_notional > float(global_cfg.get("max_total_notional_usdt", 0)) + 1e-12:
        blockers.append("GLOBAL_NOTIONAL_CAP_EXCEEDED")
    if projected_margin > float(global_cfg.get("max_total_initial_margin_usdt", 0)) + 1e-12:
        blockers.append("GLOBAL_MARGIN_CAP_EXCEEDED")

    blockers = list(dict.fromkeys(blockers))
    return {
        "pass": not blockers,
        "status": "SHADOW_CAPACITY_PASS" if not blockers else "SHADOW_CAPACITY_BLOCKED",
        "blockers": blockers,
        "existing_positions": len(existing),
        "projected_positions": len(existing) + 1,
        "projected_notional_usdt": projected_notional,
        "projected_initial_margin_usdt": projected_margin,
        "live_authority": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
    }


__all__ = ["evaluate_shadow_capacity"]
