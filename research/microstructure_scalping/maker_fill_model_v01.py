"""Conservative passive fill model for aggregated historical L2 + public trades.

This model intentionally under-credits fills.
It never treats a quote touch, book deletion, or future price crossing as a fill.
"""
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class Trade:
    timestamp_ms: int
    side: str       # taker side: Buy or Sell
    price: float
    size: float


@dataclass(frozen=True)
class FillResult:
    filled: bool
    fill_time_ms: Optional[int]
    executed_at_price: float
    required_volume: float
    matched_volume: float


def full_passive_fill(
    *,
    order_side: str,          # Buy = passive bid; Sell = passive ask
    price: float,
    order_size: float,
    displayed_queue_ahead: float,
    effective_placement_ms: int,
    deadline_ms: int,
    trades: Iterable[Trade],
    queue_multiplier: float = 1.0,
) -> FillResult:
    if order_side not in {"Buy","Sell"}:
        raise ValueError("invalid_order_side")
    if order_size <= 0 or displayed_queue_ahead < 0 or queue_multiplier < 1:
        raise ValueError("invalid_size_or_queue")
    if deadline_ms < effective_placement_ms:
        raise ValueError("deadline_before_placement")

    # Full fill requires all assumed queue ahead plus our full order size.
    required = displayed_queue_ahead * queue_multiplier + order_size
    matched = 0.0
    needed_taker_side = "Sell" if order_side=="Buy" else "Buy"

    prev=None
    for t in trades:
        if prev is not None and t.timestamp_ms < prev:
            raise ValueError("nonmonotonic_trade_time")
        prev=t.timestamp_ms
        if t.timestamp_ms <= effective_placement_ms:
            continue
        if t.timestamp_ms > deadline_ms:
            break
        if t.side != needed_taker_side:
            continue
        # Exact-price only. Trades through the level are intentionally not
        # credited because historical sequencing is not exact enough.
        if abs(t.price-price) > 1e-12:
            continue
        matched += t.size
        if matched >= required:
            return FillResult(True,t.timestamp_ms,price,required,matched)

    return FillResult(False,None,price,required,matched)
