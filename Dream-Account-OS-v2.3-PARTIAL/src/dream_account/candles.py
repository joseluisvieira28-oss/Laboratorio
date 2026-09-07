from __future__ import annotations

from dataclasses import dataclass

from .models import Candle


INTERVAL_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "60m": 3_600_000}


@dataclass
class CandleIntegrity:
    valid: bool
    gaps: list[tuple[int, int]]
    open_candles: int
    reason: str


def validate_candles(candles: list[Candle], interval: str, server_time_ms: int) -> CandleIntegrity:
    width = INTERVAL_MS[interval]
    gaps = []
    open_count = 0
    if not candles:
        return CandleIntegrity(False, [], 0, "empty")
    previous = None
    for candle in candles:
        if candle.open_time % width != 0 or candle.close_time != candle.open_time + width - 1:
            return CandleIntegrity(False, gaps, open_count, "boundary_violation")
        candle.closed = candle.close_time < server_time_ms
        open_count += int(not candle.closed)
        if previous is not None and candle.open_time != previous + width:
            gaps.append((previous + width, candle.open_time))
        previous = candle.open_time
    return CandleIntegrity(not gaps and open_count <= 1, gaps, open_count, "ok" if not gaps else "gaps_detected")

