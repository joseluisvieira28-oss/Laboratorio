from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


STATES = {"DISCOVERED", "WATCHING", "ARMED", "ACTIVATED", "PAPER_OPEN", "TP1_HIT", "TP2_HIT", "STOPPED", "INVALIDATED", "EXPIRED", "CANCELLED"}
TERMINAL = {"TP2_HIT", "STOPPED", "INVALIDATED", "EXPIRED", "CANCELLED"}
ALLOWED = {
    "DISCOVERED": {"WATCHING", "CANCELLED"},
    "WATCHING": {"ARMED", "EXPIRED", "INVALIDATED", "CANCELLED"},
    "ARMED": {"ACTIVATED", "EXPIRED", "INVALIDATED", "CANCELLED"},
    "ACTIVATED": {"PAPER_OPEN", "INVALIDATED", "EXPIRED", "CANCELLED"},
    "PAPER_OPEN": {"TP1_HIT", "TP2_HIT", "STOPPED", "INVALIDATED"},
    "TP1_HIT": {"TP2_HIT", "STOPPED", "INVALIDATED"},
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SignalStateMachine:
    signal_id: str
    state: str = "DISCOVERED"
    history: list[dict] = field(default_factory=list)

    def transition(self, target: str, reason: str, timestamp: str | None = None) -> None:
        if target not in STATES:
            raise ValueError(f"unknown state {target}")
        if target not in ALLOWED.get(self.state, set()):
            raise ValueError(f"invalid transition {self.state}->{target}")
        at = timestamp or now_utc()
        self.history.append({"from": self.state, "to": target, "reason": reason, "timestamp": at})
        self.state = target


@dataclass
class PaperTrade:
    signal_id: str
    entry_timestamp: str
    entry_price: float
    stop: float
    tp1: float
    tp2: float
    size: float
    risk_chf: float
    estimated_costs: float
    score: float
    tier: str
    regime: str
    fees_estimate: float = 0.0
    slippage_estimate: float = 0.0
    mfe: float = 0.0
    mae: float = 0.0
    exit_timestamp: str | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    realized_r: float | None = None

    def update(self, high: float, low: float, close: float, timestamp: str, early_invalidation: bool = False) -> str:
        self.mfe = max(self.mfe, (high - self.entry_price) / (self.entry_price - self.stop))
        self.mae = min(self.mae, (low - self.entry_price) / (self.entry_price - self.stop))
        if low <= self.stop:
            return self._close(self.stop, timestamp, "STOPPED")
        if high >= self.tp2:
            return self._close(self.tp2, timestamp, "TP2_HIT")
        if early_invalidation:
            return self._close(close, timestamp, "INVALIDATED")
        if high >= self.tp1:
            return "TP1_HIT"
        return "PAPER_OPEN"

    def _close(self, price: float, timestamp: str, reason: str) -> str:
        self.exit_timestamp, self.exit_price, self.exit_reason = timestamp, price, reason
        risk_per_unit = self.entry_price - self.stop
        self.realized_r = (price - self.entry_price) / risk_per_unit - (self.estimated_costs / self.risk_chf if self.risk_chf else 0)
        return reason

