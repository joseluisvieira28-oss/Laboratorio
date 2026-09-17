from __future__ import annotations

import json
import re
from typing import Iterable
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

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

MEXC_FUTURES_BASE_URL = "https://api.mexc.com"
MEXC_FUTURES_ALLOWED_PUBLIC_PATHS = {
    "/api/v1/contract/detail",
    "/api/v1/contract/ticker",
    "/api/v1/contract/ping",
}
MEXC_FUTURES_ALLOWED_PUBLIC_PREFIXES = (
    "/api/v1/contract/depth/",
    "/api/v1/contract/funding_rate/",
    "/api/v1/contract/deals/",
)
MEXC_CONTRACT_SYMBOL_RE = re.compile(r"^[A-Z0-9]+_USDT$")


class MarketDataError(RuntimeError):
    pass


class _AllowlistedPublicFeed:
    provider = "unknown"
    base_url = ""
    allowed_paths: set[str] = set()
    allowed_prefixes: tuple[str, ...] = ()

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def _path_allowed(self, parsed_path: str) -> bool:
        if parsed_path in self.allowed_paths:
            return True
        return any(parsed_path.startswith(prefix) for prefix in self.allowed_prefixes)

    def _get_json(self, path: str):
        parsed_relative = urlparse(path)
        if not self._path_allowed(parsed_relative.path):
            raise MarketDataError(f"blocked non-allowlisted public path: {parsed_relative.path}")
        url = f"{self.base_url}{path}"
        parsed = urlparse(url)
        expected = urlparse(self.base_url)
        if parsed.scheme != "https" or parsed.netloc != expected.netloc:
            raise MarketDataError("blocked host or scheme")
        request = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/0.7 public-read-only"},
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


class MEXCFuturesPublicFeed(_AllowlistedPublicFeed):
    """GET-only MEXC perpetual-futures market-data feed.

    Security boundary: this class has no API-key support, no signing logic and
    no POST/DELETE path. MEXC symbols such as BTC_USDT are normalized to the
    radar's canonical BTCUSDT form. It is a market-observation provider only.
    """

    provider = "MEXC_FUTURES_PUBLIC"
    base_url = MEXC_FUTURES_BASE_URL
    allowed_paths = MEXC_FUTURES_ALLOWED_PUBLIC_PATHS
    allowed_prefixes = MEXC_FUTURES_ALLOWED_PUBLIC_PREFIXES

    @staticmethod
    def _validate_contract_symbol(symbol: str) -> str:
        normalized = symbol.upper()
        if not MEXC_CONTRACT_SYMBOL_RE.fullmatch(normalized):
            raise MarketDataError(f"invalid MEXC contract symbol: {symbol}")
        return normalized

    def server_time_ms(self) -> int:
        payload = self._get_json("/api/v1/contract/ping")
        if not isinstance(payload, dict) or payload.get("success") is not True:
            raise MarketDataError("invalid MEXC server time payload")
        try:
            value = int(payload["data"])
        except (KeyError, TypeError, ValueError) as exc:
            raise MarketDataError("MEXC server time missing data") from exc
        if value <= 0:
            raise MarketDataError("MEXC server time is non-positive")
        return value

    def contract_detail(self) -> list[dict]:
        payload = self._get_json("/api/v1/contract/detail")
        if not isinstance(payload, dict) or payload.get("success") is not True:
            raise MarketDataError("invalid MEXC contract detail payload")
        rows = payload.get("data")
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list):
            raise MarketDataError("MEXC contract detail missing data")
        return rows

    def contract_row(self, symbol: str) -> dict:
        raw = self._validate_contract_symbol(symbol)
        for row in self.contract_detail():
            if str(row.get("symbol", "")).upper() == raw:
                return row
        raise MarketDataError(f"MEXC contract not found: {raw}")

    def order_book_depth(self, symbol: str, limit: int = 20) -> dict:
        raw = self._validate_contract_symbol(symbol)
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            raise MarketDataError("MEXC depth limit must be an integer from 1 to 100")
        query = urlencode({"limit": limit})
        payload = self._get_json(f"/api/v1/contract/depth/{raw}?{query}")
        if not isinstance(payload, dict) or payload.get("success") is not True:
            raise MarketDataError("invalid MEXC depth payload")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise MarketDataError("MEXC depth missing data")
        asks, bids = data.get("asks"), data.get("bids")
        if not isinstance(asks, list) or not isinstance(bids, list) or not asks or not bids:
            raise MarketDataError("MEXC depth has no usable book")
        return data

    def funding_rate(self, symbol: str) -> dict:
        raw = self._validate_contract_symbol(symbol)
        payload = self._get_json(f"/api/v1/contract/funding_rate/{raw}")
        if not isinstance(payload, dict) or payload.get("success") is not True:
            raise MarketDataError("invalid MEXC funding payload")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise MarketDataError("MEXC funding missing data")
        required = ("fundingRate", "collectCycle", "nextSettleTime", "idxPrice", "fairPrice")
        if any(key not in data for key in required):
            raise MarketDataError("MEXC funding payload missing required fields")
        return data

    def recent_trades(self, symbol: str, limit: int = 100) -> list[dict]:
        raw = self._validate_contract_symbol(symbol)
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            raise MarketDataError("MEXC trades limit must be an integer from 1 to 100")
        query = urlencode({"limit": limit})
        payload = self._get_json(f"/api/v1/contract/deals/{raw}?{query}")
        if not isinstance(payload, dict) or payload.get("success") is not True:
            raise MarketDataError("invalid MEXC recent trades payload")
        data = payload.get("data")
        if not isinstance(data, list):
            raise MarketDataError("MEXC recent trades missing data")
        return data

    def all_market_snapshots(self) -> dict[str, MarketSnapshot]:
        payload = self._get_json("/api/v1/contract/ticker")
        if not isinstance(payload, dict) or payload.get("success") is not True:
            raise MarketDataError("invalid MEXC ticker payload")
        rows = payload.get("data")
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list):
            raise MarketDataError("MEXC ticker missing data")

        observed_at = utc_now_iso()
        out: dict[str, MarketSnapshot] = {}
        for row in rows:
            raw_symbol = row.get("symbol")
            if not raw_symbol:
                continue
            symbol = _canonical_mexc_symbol(str(raw_symbol))
            try:
                snapshot = MarketSnapshot(
                    symbol=symbol,
                    observed_at=observed_at,
                    last_price=float(row["lastPrice"]),
                    bid_price=float(row["bid1"]),
                    ask_price=float(row["ask1"]),
                    quote_volume_24h=float(row["amount24"]),
                )
            except (KeyError, TypeError, ValueError):
                continue
            if (
                snapshot.last_price <= 0
                or snapshot.bid_price <= 0
                or snapshot.ask_price <= 0
                or snapshot.ask_price < snapshot.bid_price
                or snapshot.quote_volume_24h < 0
            ):
                continue
            out[symbol] = snapshot
        if not out:
            raise MarketDataError("no valid MEXC public market snapshots")
        return out

    def eligible_usdt_perpetual_symbols(self) -> set[str]:
        out: set[str] = set()
        for row in self.contract_detail():
            raw_symbol = row.get("symbol")
            if not raw_symbol or row.get("quoteCoin") != "USDT":
                continue
            if row.get("apiAllowed") is False:
                continue
            if row.get("futureType") not in (None, 1):
                continue
            if row.get("state") not in (None, 0):
                continue
            out.add(_canonical_mexc_symbol(str(raw_symbol)))
        return out


def _canonical_mexc_symbol(symbol: str) -> str:
    return symbol.replace("_", "").upper()


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