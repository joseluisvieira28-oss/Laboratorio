from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import math
from typing import Any


def _utc(value: Any) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def arbitrate_due_signals_multislot(
    signals: list[dict[str, Any]],
    *,
    now: datetime,
    active_reservations: list[dict[str, Any]],
    capacity: int = 3,
    lane_caps: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Select as many due signals as capacity permits without hindsight/chasing."""
    if capacity < 1:
        raise ValueError("capacity must be >=1")
    lane_caps = lane_caps or {}
    now = now.astimezone(timezone.utc)

    active_symbols = {
        str(row.get("symbol") or "").upper()
        for row in active_reservations
        if str(row.get("symbol") or "").strip()
    }
    active_lanes = Counter(
        str(row.get("candidate_id") or row.get("strategy_id") or "")
        for row in active_reservations
    )
    occupied = len(active_reservations)
    if occupied > capacity:
        return {
            "status": "FAIL_CLOSED_OVER_CAPACITY",
            "winners": [],
            "losers": [],
            "rejected": [],
            "capacity": capacity,
            "occupied": occupied,
        }

    due: list[tuple[datetime, str, str, dict[str, Any]]] = []
    rejected: list[dict[str, Any]] = []
    for signal in signals:
        candidate = str(signal.get("candidate_id") or signal.get("strategy_id") or "")
        key = str(signal.get("immutable_signal_key") or "")
        symbol = str(signal.get("symbol") or "").upper()
        if not candidate or not key or not symbol:
            rejected.append({"candidate_id": candidate, "signal_identity": key, "reason": "IDENTITY_OR_SYMBOL_MISSING"})
            continue
        try:
            target = _utc(signal["entry_target_utc"])
            max_late = float(signal.get("max_late_seconds", 2.0) or 2.0)
            if not math.isfinite(max_late) or max_late < 0:
                raise ValueError("invalid lateness")
        except Exception as exc:
            rejected.append({
                "candidate_id": candidate,
                "signal_identity": key,
                "reason": f"TIMING_INVALID:{type(exc).__name__}",
            })
            continue
        delta = (now - target).total_seconds()
        if delta < 0:
            rejected.append({"candidate_id": candidate, "signal_identity": key, "reason": "NOT_DUE_YET"})
            continue
        if delta > max_late:
            rejected.append({"candidate_id": candidate, "signal_identity": key, "reason": "MISSED_NO_CHASE"})
            continue
        due.append((target, candidate, key, signal))

    due.sort(key=lambda row: (row[0], row[1], row[2]))
    winners: list[dict[str, Any]] = []
    losers: list[dict[str, Any]] = []
    selected_symbols = set(active_symbols)
    selected_lanes = Counter(active_lanes)

    for _target, candidate, key, signal in due:
        symbol = str(signal["symbol"]).upper()
        if symbol in selected_symbols:
            losers.append({
                "candidate_id": candidate,
                "signal_identity": key,
                "reason": "MISSED_SYMBOL_CONFLICT_NO_CHASE",
            })
            continue
        cap = int(lane_caps.get(candidate, capacity))
        if selected_lanes[candidate] >= cap:
            losers.append({
                "candidate_id": candidate,
                "signal_identity": key,
                "reason": "MISSED_LANE_CAP_NO_CHASE",
            })
            continue
        if occupied + len(winners) >= capacity:
            losers.append({
                "candidate_id": candidate,
                "signal_identity": key,
                "reason": "MISSED_CAPACITY_NO_CHASE",
            })
            continue
        winners.append(signal)
        selected_symbols.add(symbol)
        selected_lanes[candidate] += 1

    status = "WINNERS_SELECTED" if winners else ("CAPACITY_OCCUPIED" if occupied >= capacity else "NO_DUE_ADMISSIBLE_SIGNAL")
    return {
        "status": status,
        "winners": winners,
        "winner_count": len(winners),
        "losers": losers,
        "rejected": rejected,
        "capacity": capacity,
        "occupied_before": occupied,
        "free_before": capacity - occupied,
        "tie_break_rule": "EARLIEST_ENTRY_TARGET_THEN_LEXICOGRAPHIC_CANDIDATE_ID_THEN_SIGNAL_KEY",
        "late_chase_allowed": False,
    }


__all__ = ["arbitrate_due_signals_multislot"]
