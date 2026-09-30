from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import math
from typing import Any

CANDIDATE_ID = "OPTIONS-SPOTPERP-001-V2.1"
PARENT_ENTRY_EVENT = "OPTIONS_V21_FORWARD_ENTRY"
FIRST_OPERATOR_ENTRY_DAY = date(2026, 9, 26)
ENTRY_TTL_SECONDS = 300.0
MAX_MARGIN_USDT = 10.0
MAX_NOTIONAL_USDT = 50.0
FRICTION_CEILING_BPS = 20.0
EXECUTION_FORK_ID = "OPTIONS-SPOTPERP-001-V2.1-OPERATOR-FUTURES-V0.3"


class OptionsV21OperatorSignalError(RuntimeError):
    pass


def latest_due_parent_entry(
    store: Any,
    *,
    now_utc: datetime | None = None,
) -> dict[str, Any] | None:
    now_utc = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    rows = store.read_payloads(PARENT_ENTRY_EVENT)
    due: list[dict[str, Any]] = []
    for row in rows:
        raw = row.get("entry_date")
        if not isinstance(raw, str):
            continue
        try:
            entry_day = date.fromisoformat(raw)
        except ValueError:
            continue
        if entry_day < FIRST_OPERATOR_ENTRY_DAY or entry_day != now_utc.date():
            continue
        if int(row.get("position") or 0) not in (-1, 1):
            continue
        due.append(row)
    if len(due) > 1:
        raise OptionsV21OperatorSignalError(
            "multiple due OPTIONS parent entries for one UTC day"
        )
    return due[0] if due else None


def build_operator_signal(
    entry: dict[str, Any],
    *,
    watcher_status: str,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now_utc = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    event_key = str(entry.get("event_key") or "")
    if not event_key.startswith("OPTIONS-SPOTPERP-001:V2.1:"):
        raise OptionsV21OperatorSignalError("parent event identity mismatch")

    entry_day = date.fromisoformat(str(entry.get("entry_date")))
    signal_day = date.fromisoformat(str(entry.get("signal_date")))
    if entry_day != signal_day + timedelta(days=1):
        raise OptionsV21OperatorSignalError("parent t+1 entry identity mismatch")
    if entry_day < FIRST_OPERATOR_ENTRY_DAY:
        raise OptionsV21OperatorSignalError("entry predates prospective operator boundary")

    position = int(entry.get("position") or 0)
    if position not in (-1, 1):
        raise OptionsV21OperatorSignalError("parent position must be +1 or -1")
    weight = float(entry.get("weight") or 0.0)
    if not math.isfinite(weight) or not 0.0 < weight <= 1.0:
        raise OptionsV21OperatorSignalError("parent risk weight outside (0,1]")

    target = datetime(entry_day.year, entry_day.month, entry_day.day, tzinfo=timezone.utc)
    exit_target = target + timedelta(days=1)
    seconds_from_target = (now_utc - target).total_seconds()
    within_ttl = 0.0 <= seconds_from_target <= ENTRY_TTL_SECONDS
    direction = "LONG" if position > 0 else "SHORT"

    # Preserve the parent's frozen risk weight while mapping the operator fork
    # to the V0.2/V0.3 account envelope. This fork receives no scientific credit.
    margin = MAX_MARGIN_USDT * weight
    notional = MAX_NOTIONAL_USDT * weight

    return {
        "candidate_id": CANDIDATE_ID,
        "strategy_id": CANDIDATE_ID,
        "execution_fork_id": EXECUTION_FORK_ID,
        "immutable_signal_key": event_key,
        "canonical_parent_event_type": PARENT_ENTRY_EVENT,
        "canonical": True,
        "source_healthy": watcher_status == "OK",
        "watcher_status": watcher_status,
        "signal_date": signal_day.isoformat(),
        "entry_date": entry_day.isoformat(),
        "symbol": "BTC_USDT",
        "direction": direction,
        "entry_target_utc": target.isoformat().replace("+00:00", "Z"),
        "exit_target_utc": exit_target.isoformat().replace("+00:00", "Z"),
        "max_late_seconds": ENTRY_TTL_SECONDS,
        "entry_window_open": within_ttl,
        "seconds_from_entry_target": seconds_from_target,
        "max_initial_margin_usdt": margin,
        "max_notional_usdt": notional,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "max_projected_roundtrip_friction_bps": FRICTION_CEILING_BPS,
        "parent_weight": weight,
        "parent_entry_price_reference": entry.get("entry_price"),
        "late_chase_allowed": False,
        "scientific_credit": False,
        "promotion_credit_to_spot_parent": False,
        "operator_proxy": True,
        "generated_at_utc": now_utc.isoformat().replace("+00:00", "Z"),
    }


__all__ = [
    "CANDIDATE_ID",
    "PARENT_ENTRY_EVENT",
    "FIRST_OPERATOR_ENTRY_DAY",
    "ENTRY_TTL_SECONDS",
    "MAX_MARGIN_USDT",
    "MAX_NOTIONAL_USDT",
    "FRICTION_CEILING_BPS",
    "EXECUTION_FORK_ID",
    "OptionsV21OperatorSignalError",
    "latest_due_parent_entry",
    "build_operator_signal",
]
