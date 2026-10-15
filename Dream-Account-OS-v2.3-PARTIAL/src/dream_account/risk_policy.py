from __future__ import annotations

from enum import Enum
from math import isfinite

from .config import Settings


class RiskState(str, Enum):
    NORMAL = "NORMAL"
    DEFENSIVE = "DEFENSIVE"
    HALT = "HALT"


def select_risk_state(drawdown_pct: float, consecutive_losses: int, settings: Settings) -> RiskState:
    if not isinstance(drawdown_pct, (int, float)) or not isfinite(drawdown_pct) or drawdown_pct < 0:
        raise ValueError("drawdown_pct must be a finite non-negative number")
    if not isinstance(consecutive_losses, int) or isinstance(consecutive_losses, bool) or consecutive_losses < 0:
        raise ValueError("consecutive_losses must be a non-negative integer")
    if drawdown_pct >= settings.drawdown_halt_pct:
        return RiskState.HALT
    if drawdown_pct >= settings.drawdown_defensive_pct or consecutive_losses >= settings.loss_streak_defensive:
        return RiskState.DEFENSIVE
    return RiskState.NORMAL


def active_risk_pct(state: RiskState, settings: Settings) -> float:
    if state is RiskState.NORMAL:
        return settings.normal_risk_pct
    if state is RiskState.DEFENSIVE:
        return settings.defensive_risk_pct
    if state is RiskState.HALT:
        return 0.0
    raise ValueError("unknown risk state")
