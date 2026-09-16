from __future__ import annotations

import json
from typing import Iterable
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from .models import MarketSnapshot, utc_now_iso

USDM_BASE_URL = "https://fapi.binance.com"
USDM_ALLOWED_PUBLIC_PATHS = {
    "/fapi/v1/ticker/24hr",
    "/fapi/v1/ticker/bookTicker",
    "/fapi/v1/exchangeInfo",
}

SPOT_BASE_URL = "https://data-api.binance.vision"
SPOT_ALLOWED_PUBLIC_PATHS = {
    "/api/v3/ticker/24hr",
    "/api/v3/ticker/bookTicker",
    "/api/v3/exchangeInfo",
}


class MarketDataError(RuntimeError):
    pass


class _AllowlistedPublicFeed:
    provider = "unknown"
    base_url = ""
    allowed_paths: set[str] = set()

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def _get_json(self, path: str):
        if path not in self.allowed_paths:
            raise MarketDataError(f"blocked non-allowlisted public path: {path}")
        url = f"{self.base_url}{path}"
        parsed = urlparse(url)
        expected = urlparse(self.base_url)
        if parsed.scheme != "https" or parsed.netloc != expected.netloc:
            raise MarketDataError("blocked host or scheme")
        request = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/0.2 public-shadow-only"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise MarketDataError(f"public feed HTTP {response.status}")
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            if isinstance(exc, MarketDataError):
                raise
            raise MarketDataError(f"public feed unavailable: {exc}") from exc

    @staticmethod
    def subset(
        snapshots: dict[str, MarketSnapshot], symbols: Iterable[str]
    ) -> dict[str, MarketSnapshot]:
        return {symbol: snapshots[symbol] for symbol in symbols if symbol in snapshots}


class BinancePublicFeed(_AllowlistedPublicFeed):
    """GET-only Binance USD-M futures public market feed."""

    provider = "BINANCE_USDM_PUBLIC"
    base_url = USDM_BASE_URL
    allowed_paths = USDM_ALLOWED_PUBLIC_PATHS

    def exchange_info(self) -> dict:
        payload = self._get_json("/fapi/v1/exchangeInfo")
        if not isinstance(payload, dict):
            raise MarketDataError("invalid exchangeInfo payload")
        return payload

    def all_market_snapshots(self) -> dict[str, MarketSnapshot]:
        tickers = self._get_json("/fapi/v1/ticker/24hr")
        books = self._get_json("/fapi/v1/ticker/bookTicker")
        return _normalize_snapshots(tickers, books)

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


class BinanceSpotPublicFeed(_AllowlistedPublicFeed):
    """GET-only market-data-only Binance Spot feed.

    This provider exists for infrastructure validation where the USD-M host is
    geographically unavailable. It must never be treated as interchangeable
    with a futures provider by a strategy adapter.
    """

    provider = "BINANCE_SPOT_DATA_API_PUBLIC"
    base_url = SPOT_BASE_URL
    allowed_paths = SPOT_ALLOWED_PUBLIC_PATHS

    def exchange_info(self) -> dict:
        payload = self._get_json("/api/v3/exchangeInfo")
        if not isinstance(payload, dict):
            raise MarketDataError("invalid exchangeInfo payload")
        return payload

    def all_market_snapshots(self) -> dict[str, MarketSnapshot]:
        tickers = self._get_json("/api/v3/ticker/24hr")
        books = self._get_json("/api/v3/ticker/bookTicker")
        return _normalize_snapshots(tickers, books)

    def eligible_usdt_perpetual_symbols(self) -> set[str]:
        info = self.exchange_info()
        symbols = info.get("symbols")
        if not isinstance(symbols, list):
            raise MarketDataError("exchangeInfo missing symbols")
        return {
            row["symbol"]
            for row in symbols
            if row.get("quoteAsset") == "USDT"
            and row.get("status") == "TRADING"
            and row.get("symbol")
        }


def _normalize_snapshots(tickers, books) -> dict[str, MarketSnapshot]:
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
