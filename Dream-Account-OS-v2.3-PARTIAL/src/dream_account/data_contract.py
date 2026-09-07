from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class DataQuality(StrEnum):
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    INVALID = "INVALID"


@dataclass
class NormalizedSnapshot:
    timestamp_utc: str
    source: str
    symbol: str
    market_type: str
    price: float | None
    bid: float | None
    ask: float | None
    spread_pct: float | None
    volume_24h: float | None
    candles: dict[str, list[Any]] = field(default_factory=dict)
    depth: dict[str, list[tuple[float, float]]] | None = None
    funding: dict[str, Any] | None = None
    open_interest: float | None = None
    mark_price: float | None = None
    index_price: float | None = None
    data_age_seconds: float = 0.0
    data_quality: DataQuality = DataQuality.INVALID
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["data_quality"] = self.data_quality.value
        return value


@dataclass
class CollectionBatch:
    timestamp_utc: str
    expected_symbols: int
    snapshots: list[NormalizedSnapshot]
    failed_symbols: dict[str, str] = field(default_factory=dict)
    source_health: dict[str, Any] = field(default_factory=dict)

    @property
    def verified(self) -> list[NormalizedSnapshot]:
        return [x for x in self.snapshots if x.data_quality is DataQuality.VERIFIED]

    @property
    def stale_symbols(self) -> list[str]:
        return [x.symbol for x in self.snapshots if x.data_quality is DataQuality.STALE]

    @property
    def coverage_pct(self) -> float:
        return round(100 * len(self.verified) / self.expected_symbols, 2) if self.expected_symbols else 0.0

    @property
    def gate_passed(self) -> bool:
        return self.coverage_pct >= 95.0
