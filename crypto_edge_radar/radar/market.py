from __future__ import annotations

import json
from typing import Iterable
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from .models import MarketSnapshot, utc_now_iso

BASE_URL = "https://fapi.binance.com"
ALLOWED_PUBLIC_PATHS = {
    "/fapi/v1/ticker/24hr",
    "/fapi/v1/ticker/bookTicker",
    "/fapi/v1/exchangeInfo",
}


class MarketDataError(RuntimeError):
    pass


class BinancePublicFeed:
    """Tiny GET-only client for Binance USD-M public market data.

    There is intentionally no generic request method exposed to callers and no
    authenticated endpoint support. Anything outside the allowlist fails closed.
    """

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def _get_json(self, path: str):
        if path not in ALLOWED_PUBLIC_PATHS:
            raise MarketDataError(f"blocked non-allowlisted public path: {path}")
        url = f"{BASE_URL}{path}"
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "fapi.binance.com":
            raise MarketDataError("blocked host or scheme")
        request = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/0.1 shadow-only"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise MarketDataError(f"public feed HTTP {response.status}")
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # network/data errors must stop signal evaluation
            if isinstance(exc, MarketDataError):
                raise
            raise MarketDataError(f"public feed unavailable: {exc}") from exc

    def exchange_info(self) -> dict:
        payload = self._get_json("/fapi/v1/exchangeInfo")
        if not isinstance(payload, dict):
            raise MarketDataError("invalid exchangeInfo payload")
        return payload

    def all_market_snapshots(self) -> dict[str, MarketSnapshot]:
        tickers = self._get_json("/fapi/v1/ticker/24hr")
        books = self._get_json("/fapi/v1/ticker/bookTicker")
        if not isinstance(tickers, list) or not isinstance(books, list):
            raise MarketDataError("invalid ticker payload")

        book_by_symbol = {row.get("symbol"): row for row in books if row.get("symbol")}
        observed_at = utc_now_iso()
        out: dict[str, MarketSnapshot] = {}
        for row in tickers:
            symbol = row.get("symbol")
            book = book_by_symbol.get(symbol)
            if not symbol or not book:
                continue
            try:
                snapshot = MarketSnapshot(
                    symbol=symbol,
                    observed_at=observed_at,
                    last_price=float(row["lastPrice"]),
                    bid_price=float(book["bidPrice"]),
                    ask_price=float(book["askPrice"]),
                    quote_volume_24h=float(row["quoteVolume"]),
                )
            except (KeyError, TypeError, ValueError):
                continue
            if (
                snapshot.last_price <= 0
                or snapshot.bid_price <= 0
                or snapshot.ask_price <= 0
                or snapshot.ask_price < snapshot.bid_price
            ):
                continue
            out[symbol] = snapshot
        if not out:
            raise MarketDataError("no valid public market snapshots")
        return out

    def eligible_usdt_perpetual_symbols(self) -> set[str]:
        info = self.exchange_info()
        symbols = info.get("symbols")
        if not isinstance(symbols, list):
            raise MarketDataError("exchangeInfo missing symbols")
        return {
            row["symbol"]
            for row in symbols
            if row.get("contractType") == "PERPETUAL"
            and row.get("quoteAsset") == "USDT"
            and row.get("status") == "TRADING"
            and row.get("symbol")
        }

    @staticmethod
    def subset(
        snapshots: dict[str, MarketSnapshot], symbols: Iterable[str]
    ) -> dict[str, MarketSnapshot]:
        return {symbol: snapshots[symbol] for symbol in symbols if symbol in snapshots}
