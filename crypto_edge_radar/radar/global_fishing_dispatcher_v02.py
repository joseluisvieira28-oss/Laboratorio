from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any


def _utc(value: Any) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def arbitrate_due_signals(
    signals: list[dict[str, Any]],
    *,
    now: datetime,
    global_slot_occupied: bool,
) -> dict[str, Any]:
    """Deterministic no-hindsight arbitration for the single global position slot.

    Existing position always owns the slot. Otherwise the earliest immutable
    entry target wins. Exact timestamp ties resolve lexicographically by
    candidate_id. Signals that lose a due conflict are not chased later.
    """
    now = now.astimezone(timezone.utc)
    due: list[tuple[datetime, str, str, dict[str, Any]]] = []
    rejected: list[dict[str, Any]] = []

    for signal in signals:
        candidate_id = str(signal.get("candidate_id") or signal.get("strategy_id") or "")
        signal_key = str(signal.get("immutable_signal_key") or "")
        if not candidate_id or not signal_key:
            rejected.append({
                "signal": signal,
                "reason": "IDENTITY_MISSING",
            })
            continue
        try:
            target = _utc(signal["entry_target_utc"])
            max_late = float(signal.get("max_late_seconds", 2.0) or 2.0)
            if not math.isfinite(max_late) or max_late < 0:
                raise ValueError("max_late_seconds must be finite and non-negative")
        except Exception as exc:
            rejected.append({
                "candidate_id": candidate_id,
                "signal_identity": signal_key,
                "reason": f"TIMING_INVALID:{type(exc).__name__}",
            })
            continue
        delta = (now - target).total_seconds()
        if delta < 0:
            rejected.append({
                "candidate_id": candidate_id,
                "signal_identity": signal_key,
                "reason": "NOT_DUE_YET",
            })
            continue
        if delta > max_late:
            rejected.append({
                "candidate_id": candidate_id,
                "signal_identity": signal_key,
                "reason": "MISSED_NO_CHASE",
            })
            continue
        due.append((target, candidate_id, signal_key, signal))

    due.sort(key=lambda row: (row[0], row[1], row[2]))

    if global_slot_occupied:
        return {
            "status": "GLOBAL_SLOT_OCCUPIED",
            "winner": None,
            "due_count": len(due),
            "losers": [
                {
                    "candidate_id": candidate_id,
                    "signal_identity": signal_key,
                    "reason": "MISSED_CONFLICT_NO_CHASE",
                }
                for _target, candidate_id, signal_key, _signal in due
            ],
            "rejected": rejected,
        }

    if not due:
        return {
            "status": "NO_DUE_SIGNAL",
            "winner": None,
            "due_count": 0,
            "losers": [],
            "rejected": rejected,
        }

    _target, candidate_id, signal_key, winner = due[0]
    losers = [
        {
            "candidate_id": c,
            "signal_identity": k,
            "reason": "MISSED_CONFLICT_NO_CHASE",
        }
        for _t, c, k, _s in due[1:]
    ]
    return {
        "status": "WINNER_SELECTED",
        "winner": winner,
        "winner_candidate_id": candidate_id,
        "winner_signal_identity": signal_key,
        "due_count": len(due),
        "losers": losers,
        "rejected": rejected,
        "tie_break_rule": "EARLIEST_ENTRY_TARGET_THEN_LEXICOGRAPHIC_CANDIDATE_ID_THEN_SIGNAL_KEY",
    }


__all__ = ["arbitrate_due_signals"]
