from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STRATEGY_ID = "BNB-LAUNCHPOOL-DEMAND-001"
FORWARD_BOUNDARY_UTC = "2026-09-16T20:51:23Z"
FORWARD_BOUNDARY_MS = 1_789_591_883_000
PAIR = "BNBBTC"
INTERVAL = "15m"
FIFTEEN_MIN_MS = 900_000
HOLD_MS = 24 * 60 * 60 * 1000
BASE_COST_BPS = 20.0
STRESS_COST_BPS = 30.0
BINANCE_SPOT_DATA_BASE_URL = "https://data-api.binance.vision"
KLINE_PATH = "/api/v3/klines"


class BNBLaunchpoolSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class SpotKline:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int


def _parse_binance_spot_kline(row: Any) -> SpotKline:
    if not isinstance(row, list) or len(row) < 7:
        raise BNBLaunchpoolSourceError("invalid Binance spot kline row")
    try:
        bar = SpotKline(
            open_time=int(row[0]),
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[5]),
            close_time=int(row[6]),
        )
    except (TypeError, ValueError) as exc:
        raise BNBLaunchpoolSourceError("invalid Binance spot kline values") from exc
    if bar.open_time % FIFTEEN_MIN_MS != 0:
        raise BNBLaunchpoolSourceError("BNBBTC 15m open timestamp not UTC-aligned")
    if bar.close_time != bar.open_time + FIFTEEN_MIN_MS - 1:
        raise BNBLaunchpoolSourceError("BNBBTC 15m close timestamp mismatch")
    values = (bar.open, bar.high, bar.low, bar.close, bar.volume)
    if any(not isfinite(v) for v in values):
        raise BNBLaunchpoolSourceError("non-finite BNBBTC kline value")
    if min(bar.open, bar.high, bar.low, bar.close) <= 0 or bar.volume < 0:
        raise BNBLaunchpoolSourceError("invalid BNBBTC OHLCV")
    if bar.high < max(bar.open, bar.close, bar.low) or bar.low > min(bar.open, bar.close, bar.high):
        raise BNBLaunchpoolSourceError("BNBBTC OHLC ordering violation")
    return bar


def first_eligible_entry_open_ms(signal_timestamp_ms: int) -> int:
    """First 15m bar open strictly greater than the canonical signal timestamp."""
    if signal_timestamp_ms <= 0:
        raise ValueError("signal timestamp must be positive")
    return (signal_timestamp_ms // FIFTEEN_MIN_MS + 1) * FIFTEEN_MIN_MS


def exact_exit_open_ms(entry_open_ms: int) -> int:
    if entry_open_ms % FIFTEEN_MIN_MS != 0:
        raise ValueError("entry must be aligned to a 15m open")
    return entry_open_ms + HOLD_MS


class BinanceSpotBNBBTCKlineFeed:
    """Read-only market-data route dedicated to the frozen BNBBTC execution rule."""

    provider = "BINANCE_SPOT_DATA_API_PUBLIC"
    base_url = BINANCE_SPOT_DATA_BASE_URL
    path = KLINE_PATH
    symbol = PAIR
    interval = INTERVAL

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def _get_json(self, query: dict[str, Any]) -> Any:
        url = f"{self.base_url}{self.path}?{urlencode(query)}"
        request = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/0.9 bnb-launchpool-read-only"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise BNBLaunchpoolSourceError(f"Binance spot HTTP {response.status}")
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            if isinstance(exc, BNBLaunchpoolSourceError):
                raise
            raise BNBLaunchpoolSourceError(
                f"Binance BNBBTC public source unavailable: {type(exc).__name__}: {exc}"
            ) from exc

    def klines(self, *, start_ms: int, end_ms: int, now_ms: int, limit: int = 1000) -> list[SpotKline]:
        if start_ms >= end_ms:
            raise BNBLaunchpoolSourceError("invalid BNBBTC time range")
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            raise BNBLaunchpoolSourceError("invalid Binance kline limit")
        start_aligned = start_ms - (start_ms % FIFTEEN_MIN_MS)
        payload = self._get_json(
            {
                "symbol": PAIR,
                "interval": INTERVAL,
                "startTime": start_aligned,
                "endTime": end_ms - 1,
                "limit": limit,
            }
        )
        if not isinstance(payload, list):
            raise BNBLaunchpoolSourceError("Binance BNBBTC payload is not a list")
        rows = [_parse_binance_spot_kline(row) for row in payload]
        complete = [
            bar
            for bar in rows
            if start_ms <= bar.open_time < end_ms and bar.close_time < now_ms
        ]
        complete.sort(key=lambda bar: bar.open_time)
        for i in range(1, len(complete)):
            if complete[i].open_time - complete[i - 1].open_time != FIFTEEN_MIN_MS:
                raise BNBLaunchpoolSourceError("BNBBTC 15m continuity gap")
        return complete

    def exact_bar(self, open_ms: int, *, now_ms: int) -> SpotKline | None:
        if open_ms % FIFTEEN_MIN_MS != 0:
            raise BNBLaunchpoolSourceError("requested BNBBTC open not 15m aligned")
        rows = self.klines(
            start_ms=open_ms,
            end_ms=open_ms + FIFTEEN_MIN_MS,
            now_ms=now_ms,
            limit=2,
        )
        return next((bar for bar in rows if bar.open_time == open_ms), None)


def bind_prospective_event(
    feed: BinanceSpotBNBBTCKlineFeed,
    *,
    signal_timestamp_ms: int,
    now_ms: int,
) -> dict[str, Any]:
    if signal_timestamp_ms <= FORWARD_BOUNDARY_MS:
        raise BNBLaunchpoolSourceError("event is not strictly post-forward-boundary")
    entry_open = first_eligible_entry_open_ms(signal_timestamp_ms)
    exit_open = exact_exit_open_ms(entry_open)
    entry_bar = feed.exact_bar(entry_open, now_ms=now_ms)
    if entry_bar is None:
        return {
            "status": "WAITING_ENTRY_BAR_FULLY_AVAILABLE",
            "strategy_id": STRATEGY_ID,
            "signal_timestamp_ms": signal_timestamp_ms,
            "entry_open_ms": entry_open,
            "exit_open_ms": exit_open,
        }
    exit_bar = feed.exact_bar(exit_open, now_ms=now_ms) if now_ms > exit_open + FIFTEEN_MIN_MS else None
    return {
        "status": "RESOLVED_MARKET_BINDING" if exit_bar is not None else "ENTRY_BOUND_EXIT_PENDING",
        "strategy_id": STRATEGY_ID,
        "pair": PAIR,
        "signal_timestamp_ms": signal_timestamp_ms,
        "entry_open_ms": entry_open,
        "entry_price": entry_bar.open,
        "exit_open_ms": exit_open,
        "exit_price": exit_bar.open if exit_bar else None,
        "base_cost_bps_round_trip": BASE_COST_BPS,
        "stress_cost_bps_round_trip": STRESS_COST_BPS,
        "authenticated_exchange_api_used": False,
        "order_created": False,
        "exchange_mutation_performed": False,
    }


def source_probe(feed: BinanceSpotBNBBTCKlineFeed, *, now_ms: int) -> dict[str, Any]:
    latest_closed_boundary = now_ms - (now_ms % FIFTEEN_MIN_MS)
    end_ms = latest_closed_boundary
    start_ms = end_ms - 48 * 60 * 60 * 1000
    rows = feed.klines(start_ms=start_ms, end_ms=end_ms, now_ms=now_ms, limit=300)
    if len(rows) < 190:
        raise BNBLaunchpoolSourceError(f"insufficient recent BNBBTC 15m coverage: {len(rows)}")
    return {
        "status": "PASS_SOURCE_ONLY",
        "strategy_id": STRATEGY_ID,
        "provider": feed.provider,
        "market": "SPOT",
        "symbol": PAIR,
        "interval": INTERVAL,
        "endpoint": feed.path,
        "complete_15m_rows": len(rows),
        "first_open_ms": rows[0].open_time,
        "last_open_ms": rows[-1].open_time,
        "strict_entry_rule_probe": {
            "signal_on_boundary": latest_closed_boundary - 10 * FIFTEEN_MIN_MS,
            "entry_after_boundary": first_eligible_entry_open_ms(latest_closed_boundary - 10 * FIFTEEN_MIN_MS),
            "signal_inside_bar": latest_closed_boundary - 10 * FIFTEEN_MIN_MS + 123_456,
            "entry_after_inside_bar": first_eligible_entry_open_ms(
                latest_closed_boundary - 10 * FIFTEEN_MIN_MS + 123_456
            ),
        },
        "authenticated_exchange_api_used": False,
        "order_created": False,
        "exchange_mutation_performed": False,
    }
