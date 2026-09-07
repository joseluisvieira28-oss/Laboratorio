from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Book, Candle
from .reliability import ReliableDataError, ReliableHTTP


class DataUnavailable(RuntimeError):
    pass


@dataclass
class MEXCClient:
    timeout: float = 10.0
    spot_base: str = "https://api.mexc.com"
    futures_base: str = "https://contract.mexc.com"

    def __post_init__(self):
        self.transport = ReliableHTTP(connect_timeout=min(4, self.timeout), read_timeout=self.timeout, max_retries=2)

    def _get(self, base: str, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            ttl = 300 if path.endswith("exchangeInfo") or path.endswith("contract/detail") else 0
            return self.transport.get_json([base], path, params, cache_ttl=ttl)
        except ReliableDataError as exc:
            raise DataUnavailable(f"MEXC data unavailable: {exc}") from exc

    def health(self) -> dict[str, Any]:
        return self.transport.report()

    def server_time(self) -> int:
        data = self._get(self.spot_base, "/api/v3/time")
        try:
            return int(data["serverTime"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DataUnavailable("Malformed server time") from exc

    def exchange_info(self) -> dict[str, Any]:
        data = self._get(self.spot_base, "/api/v3/exchangeInfo")
        if not isinstance(data, dict) or not isinstance(data.get("symbols"), list):
            raise DataUnavailable("Malformed exchangeInfo")
        return data

    def tickers_24h(self) -> list[dict[str, Any]]:
        data = self._get(self.spot_base, "/api/v3/ticker/24hr")
        if not isinstance(data, list):
            raise DataUnavailable("Malformed 24h tickers")
        return data

    def book_ticker(self, symbol: str) -> Book:
        data = self._get(self.spot_base, "/api/v3/ticker/bookTicker", {"symbol": symbol})
        try:
            return Book(float(data["bidPrice"]), float(data["askPrice"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise DataUnavailable(f"Malformed book ticker for {symbol}") from exc

    def book_tickers(self) -> list[dict[str, Any]]:
        data = self._get(self.spot_base, "/api/v3/ticker/bookTicker")
        if not isinstance(data, list):
            raise DataUnavailable("Malformed all-symbol book tickers")
        return data

    def depth(self, symbol: str, limit: int = 100) -> Book:
        data = self._get(self.spot_base, "/api/v3/depth", {"symbol": symbol, "limit": limit})
        try:
            bids = [(float(p), float(q)) for p, q in data["bids"]]
            asks = [(float(p), float(q)) for p, q in data["asks"]]
            return Book(bids[0][0], asks[0][0], bids, asks)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise DataUnavailable(f"Malformed depth for {symbol}") from exc

    def klines(self, symbol: str, interval: str, limit: int = 120) -> list[Candle]:
        data = self._get(self.spot_base, "/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})
        try:
            candles = [Candle(int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5]), int(x[6])) for x in data]
        except (IndexError, TypeError, ValueError) as exc:
            raise DataUnavailable(f"Malformed klines for {symbol}/{interval}") from exc
        if len(candles) < 2:
            raise DataUnavailable(f"Insufficient klines for {symbol}/{interval}")
        return candles

    def futures_tickers(self) -> list[dict[str, Any]]:
        data = self._get(self.futures_base, "/api/v1/contract/ticker")
        if not isinstance(data, dict) or data.get("success") is not True or not isinstance(data.get("data"), list):
            raise DataUnavailable("Malformed futures tickers")
        return data["data"]

    def futures_detail(self) -> list[dict[str, Any]]:
        data = self._get(self.futures_base, "/api/v1/contract/detail")
        if not isinstance(data, dict) or data.get("success") is not True or not isinstance(data.get("data"), list):
            raise DataUnavailable("Malformed futures detail")
        return data["data"]

    def futures_funding(self, symbol: str) -> dict[str, Any]:
        data = self._get(self.futures_base, f"/api/v1/contract/funding_rate/{symbol}")
        if not isinstance(data, dict) or data.get("success") is not True or not isinstance(data.get("data"), dict):
            raise DataUnavailable(f"Malformed funding for {symbol}")
        required = {"fundingRate", "collectCycle", "nextSettleTime", "timestamp"}
        if not required.issubset(data["data"]):
            raise DataUnavailable(f"Incomplete funding for {symbol}")
        return data["data"]

    def futures_funding_history(self, symbol: str, limit: int = 20) -> list[dict[str, Any]]:
        data = self._get(self.futures_base, "/api/v1/contract/funding_rate/history", {"symbol": symbol, "page_num": 1, "page_size": limit})
        try:
            return data["data"]["resultList"] if data.get("success") is True else []
        except (KeyError, TypeError) as exc:
            raise DataUnavailable(f"Malformed funding history for {symbol}") from exc

    def futures_price_context(self, symbol: str) -> dict[str, Any]:
        index_data = self._get(self.futures_base, f"/api/v1/contract/index_price/{symbol}")
        fair_data = self._get(self.futures_base, f"/api/v1/contract/fair_price/{symbol}")
        if index_data.get("success") is not True or fair_data.get("success") is not True:
            raise DataUnavailable(f"Malformed price context for {symbol}")
        return {"index_price": float(index_data["data"]["indexPrice"]), "mark_price": float(fair_data["data"]["fairPrice"]), "timestamp": min(int(index_data["data"]["timestamp"]), int(fair_data["data"]["timestamp"]))}

    def futures_open_interest_snapshot(self) -> dict[str, dict[str, float]]:
        rows = self.futures_tickers()
        result = {}
        for row in rows:
            if "symbol" in row and "holdVol" in row:
                result[row["symbol"]] = {"open_interest": float(row["holdVol"]), "timestamp": float(row.get("timestamp", 0))}
        if not result:
            raise DataUnavailable("No verifiable holdVol/open-interest fields")
        return result
