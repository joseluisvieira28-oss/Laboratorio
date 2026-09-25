from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import os
import time
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://api.mexc.com"
ALLOWED_SYMBOL = "BTCUSDT"


class MEXCSpotV3Error(RuntimeError):
    pass


@dataclass(frozen=True)
class MEXCSpotCredentials:
    api_key: str
    api_secret: str

    @classmethod
    def from_env(cls) -> "MEXCSpotCredentials":
        key = os.getenv("MEXC_API_KEY", "").strip()
        secret = os.getenv("MEXC_API_SECRET", "").strip()
        if not key or not secret:
            raise MEXCSpotV3Error("MEXC_API_KEY/MEXC_API_SECRET missing")
        return cls(key, secret)


class _BaseClient:
    def __init__(self, credentials: MEXCSpotCredentials, *, timeout: float = 10.0):
        self.credentials = credentials
        self.timeout = timeout

    def _signed(self, method: str, path: str, params: dict[str, Any] | None = None) -> Any:
        values = dict(params or {})
        values.setdefault("recvWindow", 5000)
        values.setdefault("timestamp", int(time.time() * 1000))
        payload = urlencode(values)
        signature = hmac.new(
            self.credentials.api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signed = payload + "&signature=" + signature
        headers = {
            "X-MEXC-APIKEY": self.credentials.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "crypto-edge-radar/mexc-spot-v03",
        }
        method = method.upper()
        url = BASE_URL + path
        body = None
        if method == "GET":
            url += "?" + signed
        elif method in {"POST", "DELETE"}:
            body = signed.encode("utf-8")
        else:
            raise MEXCSpotV3Error("unsupported signed method")
        request = Request(url, data=body, method=method, headers=headers)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                if response.status < 200 or response.status >= 300:
                    raise MEXCSpotV3Error(f"HTTP {response.status}: {raw[:500]}")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8")[:1000]
            except Exception:
                detail = ""
            raise MEXCSpotV3Error(f"HTTP {exc.code}: {detail}") from exc
        except MEXCSpotV3Error:
            raise
        except Exception as exc:
            raise MEXCSpotV3Error(f"{type(exc).__name__}: {exc}") from exc

    def _public(self, path: str) -> Any:
        request = Request(
            BASE_URL + path,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/mexc-spot-v03"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise MEXCSpotV3Error(f"public source unavailable: {type(exc).__name__}: {exc}") from exc


class MEXCSpotAuthenticatedReadOnlyClient(_BaseClient):
    def account(self) -> dict[str, Any]:
        row = self._signed("GET", "/api/v3/account")
        if not isinstance(row, dict):
            raise MEXCSpotV3Error("account response not object")
        return row

    def self_symbols(self) -> set[str]:
        row = self._signed("GET", "/api/v3/selfSymbols")
        values = row.get("data") if isinstance(row, dict) else None
        if not isinstance(values, list):
            raise MEXCSpotV3Error("selfSymbols response missing data")
        return {str(x).upper() for x in values}

    def open_orders(self, symbol: str = ALLOWED_SYMBOL) -> list[dict[str, Any]]:
        if symbol != ALLOWED_SYMBOL:
            raise MEXCSpotV3Error("symbol outside V0.3 allowlist")
        rows = self._signed("GET", "/api/v3/openOrders", {"symbol": symbol})
        if not isinstance(rows, list):
            raise MEXCSpotV3Error("openOrders response not list")
        return rows

    def order_by_client_id(self, *, client_order_id: str, symbol: str = ALLOWED_SYMBOL) -> dict[str, Any]:
        if symbol != ALLOWED_SYMBOL:
            raise MEXCSpotV3Error("symbol outside V0.3 allowlist")
        row = self._signed(
            "GET",
            "/api/v3/order",
            {"symbol": symbol, "origClientOrderId": client_order_id},
        )
        if not isinstance(row, dict):
            raise MEXCSpotV3Error("order response not object")
        return row

    def mx_deduct_enabled(self) -> bool:
        row = self._signed("GET", "/api/v3/mxDeduct/enable")
        try:
            return bool(row["data"]["mxDeductEnable"])
        except Exception as exc:
            raise MEXCSpotV3Error("invalid MX deduct status") from exc

    def trade_fee(self, symbol: str = ALLOWED_SYMBOL) -> dict[str, float]:
        if symbol != ALLOWED_SYMBOL:
            raise MEXCSpotV3Error("symbol outside V0.3 allowlist")
        row = self._signed("GET", "/api/v3/tradeFee", {"symbol": symbol})
        try:
            data = row["data"]
            return {
                "makerCommission": float(data["makerCommission"]),
                "takerCommission": float(data["takerCommission"]),
            }
        except Exception as exc:
            raise MEXCSpotV3Error("invalid tradeFee response") from exc

    def trades_for_order(self, *, order_id: str, symbol: str = ALLOWED_SYMBOL) -> list[dict[str, Any]]:
        if symbol != ALLOWED_SYMBOL:
            raise MEXCSpotV3Error("symbol outside V0.3 allowlist")
        rows = self._signed(
            "GET",
            "/api/v3/myTrades",
            {"symbol": symbol, "orderId": order_id, "limit": 100},
        )
        if not isinstance(rows, list):
            raise MEXCSpotV3Error("myTrades response not list")
        return rows

    def server_time_ms(self) -> int:
        row = self._public("/api/v3/time")
        try:
            return int(row["serverTime"])
        except Exception as exc:
            raise MEXCSpotV3Error("invalid server time") from exc

    def exchange_info(self, symbol: str = ALLOWED_SYMBOL) -> dict[str, Any]:
        if symbol != ALLOWED_SYMBOL:
            raise MEXCSpotV3Error("symbol outside V0.3 allowlist")
        row = self._public("/api/v3/exchangeInfo?" + urlencode({"symbol": symbol}))
        if not isinstance(row, dict):
            raise MEXCSpotV3Error("exchangeInfo response not object")
        symbols = row.get("symbols")
        if isinstance(symbols, list):
            match = next((x for x in symbols if isinstance(x, dict) and str(x.get("symbol","")).upper()==symbol), None)
            if match is None:
                raise MEXCSpotV3Error("exchangeInfo missing BTCUSDT")
            return match
        if str(row.get("symbol","")).upper() == symbol:
            return row
        raise MEXCSpotV3Error("exchangeInfo missing BTCUSDT")

    def default_symbols(self) -> set[str]:
        row = self._public("/api/v3/defaultSymbols")
        values = row
        if isinstance(row, dict):
            values = row.get("data") or row.get("symbols")
        if not isinstance(values, list):
            raise MEXCSpotV3Error("defaultSymbols response missing list")
        return {str(x).upper() for x in values}


class MEXCSpotMutationTransport(_BaseClient):
    def _check(self, symbol: str) -> None:
        if symbol != ALLOWED_SYMBOL:
            raise MEXCSpotV3Error("symbol outside V0.3 mutation allowlist")

    def test_market_buy(self, *, quote_order_qty: str, client_order_id: str, symbol: str = ALLOWED_SYMBOL) -> dict[str, Any]:
        self._check(symbol)
        row = self._signed(
            "POST",
            "/api/v3/order/test",
            {
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quoteOrderQty": quote_order_qty,
                "newClientOrderId": client_order_id,
            },
        )
        if not isinstance(row, dict):
            raise MEXCSpotV3Error("order/test response not object")
        return row

    def market_buy(self, *, quote_order_qty: str, client_order_id: str, symbol: str = ALLOWED_SYMBOL) -> dict[str, Any]:
        self._check(symbol)
        row = self._signed(
            "POST",
            "/api/v3/order",
            {
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quoteOrderQty": quote_order_qty,
                "newClientOrderId": client_order_id,
            },
        )
        if not isinstance(row, dict):
            raise MEXCSpotV3Error("order response not object")
        return row

    def test_market_sell(self, *, quantity: str, client_order_id: str, symbol: str = ALLOWED_SYMBOL) -> dict[str, Any]:
        self._check(symbol)
        row = self._signed(
            "POST",
            "/api/v3/order/test",
            {
                "symbol": symbol,
                "side": "SELL",
                "type": "MARKET",
                "quantity": quantity,
                "newClientOrderId": client_order_id,
            },
        )
        if not isinstance(row, dict):
            raise MEXCSpotV3Error("order/test response not object")
        return row

    def market_sell(self, *, quantity: str, client_order_id: str, symbol: str = ALLOWED_SYMBOL) -> dict[str, Any]:
        self._check(symbol)
        row = self._signed(
            "POST",
            "/api/v3/order",
            {
                "symbol": symbol,
                "side": "SELL",
                "type": "MARKET",
                "quantity": quantity,
                "newClientOrderId": client_order_id,
            },
        )
        if not isinstance(row, dict):
            raise MEXCSpotV3Error("order response not object")
        return row

    def cancel(self, *, client_order_id: str, symbol: str = ALLOWED_SYMBOL) -> dict[str, Any]:
        self._check(symbol)
        row = self._signed(
            "DELETE",
            "/api/v3/order",
            {"symbol": symbol, "origClientOrderId": client_order_id},
        )
        if not isinstance(row, dict):
            raise MEXCSpotV3Error("cancel response not object")
        return row


__all__ = [
    "ALLOWED_SYMBOL",
    "MEXCSpotCredentials",
    "MEXCSpotV3Error",
    "MEXCSpotAuthenticatedReadOnlyClient",
    "MEXCSpotMutationTransport",
]
