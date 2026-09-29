from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


class PromotionStatus(str, Enum):
    RESEARCH = "RESEARCH"
    CANDIDATE = "CANDIDATE"
    PROMOTED_SHADOW = "PROMOTED_SHADOW"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    observed_at: str
    last_price: float
    bid_price: float
    ask_price: float
    quote_volume_24h: float

    @property
    def spread_bps(self) -> float:
        mid = (self.bid_price + self.ask_price) / 2.0
        if mid <= 0:
            return float("inf")
        return (self.ask_price - self.bid_price) / mid * 10_000.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["spread_bps"] = self.spread_bps
        return data


@dataclass(frozen=True)
class StrategyDecision:
    strategy_id: str
    symbol: str
    evaluated_at: str
    direction: Direction
    reason: str
    promotion_status: PromotionStatus
    valid_signal: bool
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["direction"] = self.direction.value
        data["promotion_status"] = self.promotion_status.value
        return data


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
