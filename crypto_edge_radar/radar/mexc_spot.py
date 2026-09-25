from __future__ import annotations

import json
import re
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


MEXC_SPOT_BASE_URL = "https://api.mexc.com"
MEXC_SPOT_ALLOWED_EXACT = {"/api/v3/defaultSymbols", "/api/v3/exchangeInfo"}
MEXC_SPOT_ALLOWED_PREFIXES = (
    "/api/v3/ticker/bookTicker",
    "/api/v3/ticker/price",
    "/api/v3/depth",
)
SPOT_SYMBOL_RE = re.compile(r"^[A-Z0-9]+USDT$")


class MEXCSpotPublicError(RuntimeError):
    pass


class MEXCSpotPublicFeed:
    provider = "MEXC_SPOT_PUBLIC"
    base_url = MEXC_SPOT_BASE_URL

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    @staticmethod
    def _validate_symbol(symbol: str) -> str:
        value = symbol.upper()
        if not SPOT_SYMBOL_RE.fullmatch(value):
            raise MEXCSpotPublicError(f"invalid MEXC spot symbol: {symbol}")
        return value

    @staticmethod
    def _allowed(path: str) -> bool:
        parsed = urlparse(path)
        if parsed.path in MEXC_SPOT_ALLOWED_EXACT:
            return True
        return any(parsed.path == prefix for prefix in MEXC_SPOT_ALLOWED_PREFIXES)

    def _get_json(self, path: str):
        if not self._allowed(path):
            raise MEXCSpotPublicError(f"blocked non-allowlisted spot path: {path}")
        url = f"{self.base_url}{path}"
        parsed = urlparse(url)
        expected = urlparse(self.base_url)
        if parsed.scheme != "https" or parsed.netloc != expected.netloc:
            raise MEXCSpotPublicError("blocked spot host or scheme")
        request = Request(url, method="GET", headers={"User-Agent": "crypto-edge-radar-exec-v2/0.1 public-read-only"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise MEXCSpotPublicError(f"spot public feed HTTP {response.status}")
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            if isinstance(exc, MEXCSpotPublicError):
                raise
            raise MEXCSpotPublicError(f"spot public feed unavailable: {exc}") from exc

    def default_symbols(self) -> set[str]:
        payload = self._get_json("/api/v3/defaultSymbols")
        rows = payload
        if isinstance(payload, dict):
            rows = payload.get("data") or payload.get("symbols")
        if not isinstance(rows, list):
            raise MEXCSpotPublicError("defaultSymbols payload missing symbol list")
        out = {str(x).upper() for x in rows if isinstance(x, str)}
        if not out:
            raise MEXCSpotPublicError("defaultSymbols returned no symbols")
        return out

    def exchange_info(self, symbol: str) -> dict:
        symbol = self._validate_symbol(symbol)
        payload = self._get_json(f"/api/v3/exchangeInfo?{urlencode({'symbol': symbol})}")
        if not isinstance(payload, dict):
            raise MEXCSpotPublicError("exchangeInfo payload invalid")
        if isinstance(payload.get("symbols"), list):
            rows = [x for x in payload["symbols"] if isinstance(x, dict) and str(x.get("symbol", "")).upper() == symbol]
            if len(rows) != 1:
                raise MEXCSpotPublicError("exchangeInfo symbol row missing or ambiguous")
            return rows[0]
        if str(payload.get("symbol", "")).upper() == symbol:
            return payload
        raise MEXCSpotPublicError("exchangeInfo symbol row missing")

    def book_ticker(self, symbol: str) -> dict:
        symbol = self._validate_symbol(symbol)
        payload = self._get_json(f"/api/v3/ticker/bookTicker?{urlencode({'symbol': symbol})}")
        if not isinstance(payload, dict):
            raise MEXCSpotPublicError("bookTicker payload invalid")
        for field in ("bidPrice", "askPrice"):
            if field not in payload:
                raise MEXCSpotPublicError(f"bookTicker missing {field}")
        return payload

    def price(self, symbol: str) -> float:
        symbol = self._validate_symbol(symbol)
        payload = self._get_json(f"/api/v3/ticker/price?{urlencode({'symbol': symbol})}")
        if not isinstance(payload, dict) or "price" not in payload:
            raise MEXCSpotPublicError("ticker price payload invalid")
        value = float(payload["price"])
        if value <= 0:
            raise MEXCSpotPublicError("spot price non-positive")
        return value

    def depth(self, symbol: str, limit: int = 20) -> dict:
        symbol = self._validate_symbol(symbol)
        if limit not in {5, 10, 20, 50, 100, 500, 1000, 5000}:
            raise MEXCSpotPublicError("unsupported spot depth limit")
        payload = self._get_json(f"/api/v3/depth?{urlencode({'symbol': symbol, 'limit': limit})}")
        if not isinstance(payload, dict):
            raise MEXCSpotPublicError("spot depth payload invalid")
        bids, asks = payload.get("bids"), payload.get("asks")
        if not isinstance(bids, list) or not isinstance(asks, list) or not bids or not asks:
            raise MEXCSpotPublicError("spot depth has no usable book")
        return payload
