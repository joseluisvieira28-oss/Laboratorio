from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from .data_contract import CollectionBatch, DataQuality, NormalizedSnapshot
from .mexc_client import DataUnavailable, MEXCClient
from .models import utc_now


class MEXCDataCollector:
    """Public-data adapter. It is the only layer allowed to parse raw MEXC payloads."""

    def __init__(self, client: MEXCClient, price_max_age_seconds: float = 10.0):
        self.client = client
        self.price_max_age_seconds = price_max_age_seconds

    def collect_spot(self) -> CollectionBatch:
        timestamp = utc_now()
        try:
            exchange = self.client.exchange_info()
            tickers = self.client.tickers_24h()
            books = self.client.book_tickers()
        except DataUnavailable as exc:
            return CollectionBatch(timestamp, 0, [], {"__SOURCE__": str(exc)}, self.client.health())
        expected = {
            row["symbol"] for row in exchange["symbols"]
            if row.get("quoteAsset") == "USDT" and row.get("status") in {"ENABLED", "TRADING", "1"}
        }
        ticker_map = {x.get("symbol"): x for x in tickers if x.get("symbol") in expected}
        book_map = {x.get("symbol"): x for x in books if x.get("symbol") in expected}
        snapshots, failed = [], {}
        for symbol in sorted(expected):
            ticker, book = ticker_map.get(symbol), book_map.get(symbol)
            try:
                if ticker is None or book is None:
                    raise ValueError("missing ticker or book")
                price = float(ticker["lastPrice"])
                bid, ask = float(book["bidPrice"]), float(book["askPrice"])
                volume = float(ticker["quoteVolume"])
                if min(price, bid, ask) <= 0 or ask < bid:
                    raise ValueError("invalid price/book")
                mid = (bid + ask) / 2
                snapshots.append(NormalizedSnapshot(timestamp, "MEXC", symbol, "SPOT", price, bid, ask,
                    (ask-bid)/mid*100, volume, data_quality=DataQuality.VERIFIED))
            except (KeyError, TypeError, ValueError) as exc:
                failed[symbol] = str(exc)
                snapshots.append(NormalizedSnapshot(timestamp, "MEXC", symbol, "SPOT", None, None, None,
                    None, None, data_quality=DataQuality.INVALID, errors=[str(exc)]))
        return CollectionBatch(timestamp, len(expected), snapshots, failed, self.client.health())

    def enrich(self, snapshot: NormalizedSnapshot) -> NormalizedSnapshot:
        """Deep data for fast-filter survivors. Any missing component fails closed."""
        try:
            book = self.client.depth(snapshot.symbol)
            candles = {tf: self.client.klines(snapshot.symbol, tf) for tf in ("1m", "5m", "15m")}
            snapshot.depth = {"bids": book.bids, "asks": book.asks}
            snapshot.candles = candles
            snapshot.data_quality = DataQuality.VERIFIED
        except DataUnavailable as exc:
            snapshot.data_quality = DataQuality.PARTIAL
            snapshot.errors.append(str(exc))
        return snapshot

    @staticmethod
    def mark_stale(snapshot: NormalizedSnapshot, age_seconds: float, max_age_seconds: float) -> None:
        snapshot.data_age_seconds = age_seconds
        if age_seconds > max_age_seconds:
            snapshot.data_quality = DataQuality.STALE


def cross_check_prices(mexc: dict[str, float], independent: dict[str, float], tolerance_pct: float = 1.0) -> dict[str, str]:
    """Corruption detector only. These values never feed setup or scoring logic."""
    flags = {}
    for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        if symbol not in mexc or symbol not in independent or independent[symbol] <= 0:
            flags[symbol] = "UNVERIFIED"
            continue
        divergence = abs(mexc[symbol] / independent[symbol] - 1) * 100
        flags[symbol] = "PASS" if divergence <= tolerance_pct else f"DATA_ANOMALY:{divergence:.3f}%"
    return flags
