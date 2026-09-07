from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Candle:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    closed: bool = True


@dataclass
class Book:
    bid: float
    ask: float
    bids: list[tuple[float, float]] = field(default_factory=list)
    asks: list[tuple[float, float]] = field(default_factory=list)

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def spread_pct(self) -> float:
        return ((self.ask - self.bid) / self.mid) * 100 if self.mid else 999.0


@dataclass
class Candidate:
    symbol: str
    market_type: str
    price: float
    volume_24h_usd: float
    spread_pct: float
    changes: dict[str, float]
    rvol_15m: float
    regime: str
    setup: str = "NONE"
    entry: float | None = None
    stop: float | None = None
    tp1: float | None = None
    tp2: float | None = None
    funding: float | None = None
    oi_change_1h: float | None = None
    pump_risk: float = 0.0
    subscores: dict[str, float] = field(default_factory=dict)
    score: float = 0.0
    tier: str = "REJECT"
    status: str = "NO_TRADE"
    rejection_reasons: list[str] = field(default_factory=list)
    observed_at: str = field(default_factory=utc_now)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

