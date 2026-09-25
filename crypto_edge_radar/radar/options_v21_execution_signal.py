from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

STRATEGY_ID = "OPTIONS-SPOTPERP-001-V2.1"
PARENT_ENTRY_EVENT = "OPTIONS_V21_FORWARD_ENTRY"
FIRST_AUTO_MICROLIVE_ENTRY_DAY = date(2026, 9, 26)
ENTRY_TTL_SECONDS = 300.0
MAX_NOTIONAL_USDT = 10.0


class OptionsV21ExecutionSignalError(RuntimeError):
    pass


def _utc_midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)


def latest_due_parent_entry(store: Any, *, now_utc: datetime | None = None) -> dict[str, Any] | None:
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
        if entry_day < FIRST_AUTO_MICROLIVE_ENTRY_DAY or entry_day != now_utc.date():
            continue
        if int(row.get("position") or 0) not in (-1, 1):
            continue
        due.append(row)
    if len(due) > 1:
        raise OptionsV21ExecutionSignalError("multiple due OPTIONS parent entries for one UTC day")
    return due[0] if due else None


def build_execution_signal(
    entry: dict[str, Any],
    *,
    watcher_status: str,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now_utc = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    event_key = str(entry.get("event_key") or "")
    if not event_key.startswith("OPTIONS-SPOTPERP-001:V2.1:"):
        raise OptionsV21ExecutionSignalError("parent event identity mismatch")

    entry_day = date.fromisoformat(str(entry.get("entry_date")))
    signal_day = date.fromisoformat(str(entry.get("signal_date")))
    if entry_day != signal_day + timedelta(days=1):
        raise OptionsV21ExecutionSignalError("parent t+1 entry identity mismatch")
    if entry_day < FIRST_AUTO_MICROLIVE_ENTRY_DAY:
        raise OptionsV21ExecutionSignalError("entry predates auto-microlive prospective boundary")

    position = int(entry.get("position") or 0)
    if position not in (-1, 1):
        raise OptionsV21ExecutionSignalError("parent position must be +1 or -1")
    weight = float(entry.get("weight") or 0.0)
    if not 0.0 < weight <= 1.0:
        raise OptionsV21ExecutionSignalError("parent risk weight outside (0,1]")

    target = _utc_midnight(entry_day)
    exit_target = target + timedelta(days=1)
    seconds_from_target = (now_utc - target).total_seconds()
    within_ttl = 0.0 <= seconds_from_target <= ENTRY_TTL_SECONDS
    direction = "LONG" if position > 0 else "SHORT"
    route = "MEXC_SPOT_BTCUSDT" if position > 0 else "MEXC_USDT_PERP_BTC_USDT"
    planned_notional = MAX_NOTIONAL_USDT * weight

    return {
        "strategy_id": STRATEGY_ID,
        "immutable_signal_key": event_key,
        "canonical_parent_event_type": PARENT_ENTRY_EVENT,
        "canonical": True,
        "watcher_status": watcher_status,
        "source_healthy": watcher_status == "OK",
        "signal_date": signal_day.isoformat(),
        "entry_date": entry_day.isoformat(),
        "entry_target_utc": target.isoformat().replace("+00:00", "Z"),
        "exit_target_utc": exit_target.isoformat().replace("+00:00", "Z"),
        "signal_direction": direction,
        "position": position,
        "weight": weight,
        "route": route,
        "maximum_program_notional_usdt": MAX_NOTIONAL_USDT,
        "planned_notional_usdt": planned_notional,
        "entry_ttl_seconds": ENTRY_TTL_SECONDS,
        "seconds_from_entry_target": seconds_from_target,
        "entry_window_open": within_ttl,
        "late_chase_allowed": False,
        "parent_entry_price_reference": entry.get("entry_price"),
        "generated_at_utc": now_utc.isoformat().replace("+00:00", "Z"),
    }


__all__ = [
    "STRATEGY_ID",
    "PARENT_ENTRY_EVENT",
    "FIRST_AUTO_MICROLIVE_ENTRY_DAY",
    "ENTRY_TTL_SECONDS",
    "MAX_NOTIONAL_USDT",
    "OptionsV21ExecutionSignalError",
    "latest_due_parent_entry",
    "build_execution_signal",
]
