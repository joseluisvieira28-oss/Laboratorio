from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from .options_v21_execution_signal import (
    FIRST_AUTO_MICROLIVE_ENTRY_DAY,
    MAX_NOTIONAL_USDT,
    PARENT_ENTRY_EVENT,
    STRATEGY_ID,
    latest_due_parent_entry,
)

ENTRY_TTL_SECONDS = 300.0
EXECUTION_FORK_ID = "OPTIONS-SPOTPERP-001-V2.1-FUTURES-EXECUTION-FORK-V0.2"


class OptionsV21FuturesExecutionSignalError(RuntimeError):
    pass


def build_futures_execution_signal(
    entry: dict[str, Any],
    *,
    watcher_status: str,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now_utc = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    event_key = str(entry.get("event_key") or "")
    if not event_key.startswith("OPTIONS-SPOTPERP-001:V2.1:"):
        raise OptionsV21FuturesExecutionSignalError("parent event identity mismatch")

    entry_day = date.fromisoformat(str(entry.get("entry_date")))
    signal_day = date.fromisoformat(str(entry.get("signal_date")))
    if entry_day != signal_day + timedelta(days=1):
        raise OptionsV21FuturesExecutionSignalError("parent t+1 entry identity mismatch")
    if entry_day < FIRST_AUTO_MICROLIVE_ENTRY_DAY:
        raise OptionsV21FuturesExecutionSignalError("entry predates prospective auto-microlive boundary")

    position = int(entry.get("position") or 0)
    if position not in (-1, 1):
        raise OptionsV21FuturesExecutionSignalError("parent position must be +1 or -1")
    weight = float(entry.get("weight") or 0.0)
    if not 0.0 < weight <= 1.0:
        raise OptionsV21FuturesExecutionSignalError("parent risk weight outside (0,1]")

    target = datetime(entry_day.year, entry_day.month, entry_day.day, tzinfo=timezone.utc)
    exit_target = target + timedelta(days=1)
    seconds_from_target = (now_utc - target).total_seconds()
    within_ttl = 0.0 <= seconds_from_target <= ENTRY_TTL_SECONDS
    direction = "LONG" if position > 0 else "SHORT"

    return {
        "strategy_id": STRATEGY_ID,
        "execution_fork_id": EXECUTION_FORK_ID,
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
        "route": "MEXC_USDT_PERP_BTC_USDT",
        "symbol": "BTC_USDT",
        "instrument_type": "USDT_PERPETUAL",
        "leverage": 1,
        "margin_mode": "ISOLATED",
        "position_mode": "HEDGE",
        "maximum_program_notional_usdt": MAX_NOTIONAL_USDT,
        "planned_notional_usdt": MAX_NOTIONAL_USDT * weight,
        "entry_ttl_seconds": ENTRY_TTL_SECONDS,
        "seconds_from_entry_target": seconds_from_target,
        "entry_window_open": within_ttl,
        "late_chase_allowed": False,
        "scientific_parent_instrument": "BTCUSDT_SPOT",
        "scientific_parent_horizon_hours": 24,
        "execution_fork_instrument": "BTC_USDT_PERPETUAL",
        "execution_fork_horizon_hours": 24,
        "promotion_credit_to_spot_parent": False,
        "parent_entry_price_reference": entry.get("entry_price"),
        "generated_at_utc": now_utc.isoformat().replace("+00:00", "Z"),
    }


__all__ = [
    "ENTRY_TTL_SECONDS",
    "EXECUTION_FORK_ID",
    "OptionsV21FuturesExecutionSignalError",
    "latest_due_parent_entry",
    "build_futures_execution_signal",
]
