from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from .models import Direction, MarketSnapshot, PromotionStatus, StrategyDecision, utc_now_iso


@dataclass(frozen=True)
class RawSignal:
    direction: Direction
    reason: str
    metadata: dict


class StrategyAdapter(ABC):
    strategy_id: str
    promotion_status: PromotionStatus

    @abstractmethod
    def evaluate(self, snapshot: MarketSnapshot) -> RawSignal:
        raise NotImplementedError


def enforce_promotion_gate(
    adapter: StrategyAdapter, snapshot: MarketSnapshot
) -> StrategyDecision:
    raw = adapter.evaluate(snapshot)
    promoted = adapter.promotion_status is PromotionStatus.PROMOTED_SHADOW
    directional = raw.direction in {Direction.LONG, Direction.SHORT}
    valid_signal = promoted and directional

    if not promoted and directional:
        reason = f"BLOCKED_NOT_PROMOTED: {raw.reason}"
    else:
        reason = raw.reason

    return StrategyDecision(
        strategy_id=adapter.strategy_id,
        symbol=snapshot.symbol,
        evaluated_at=utc_now_iso(),
        direction=raw.direction,
        reason=reason,
        promotion_status=adapter.promotion_status,
        valid_signal=valid_signal,
        metadata=raw.metadata,
    )


class StrategyRegistry:
    def __init__(self, adapters: Iterable[StrategyAdapter] = ()) -> None:
        self._adapters = tuple(adapters)
        ids = [a.strategy_id for a in self._adapters]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate strategy_id in registry")

    @property
    def adapters(self) -> tuple[StrategyAdapter, ...]:
        return self._adapters

    @classmethod
    def empty(cls) -> "StrategyRegistry":
        return cls(())
