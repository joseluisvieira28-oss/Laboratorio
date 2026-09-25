from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from typing import Any, Callable
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .mexc_auth_readonly import MEXCCredentials

MEXC_SPOT_BASE_URL = "https://api.mexc.com"
CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,32}$")
_ALLOWED_SIGNED_GET = {"/api/v3/account", "/api/v3/order", "/api/v3/openOrders", "/api/v3/myTrades"}
_ALLOWED_SIGNED_POST = {"/api/v3/order"}


class MEXCSpotAuthError(RuntimeError):
    pass


def _sign(secret: str, total_params: str) -> str:
    return hmac.new(secret.encode("utf-8"), total_params.encode("utf-8"), hashlib.sha256).hexdigest()


class MEXCSpotAuthenticatedClient:
    def __init__(
        self,
        credentials: MEXCCredentials,
        *,
        timeout: int = 10,
        clock_ms: Callable[[], int] | None = None,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self._credentials = credentials
        self.timeout = timeout
        self._clock_ms = clock_ms or (lambda: int(time.time_ns() / 1_000_000))
        self._opener = opener

    def _signed(self, method: str, path: str, params: dict[str, Any]) -> Any:
        parsed = urlparse(path)
        if parsed.scheme or parsed.netloc:
            raise MEXCSpotAuthError("absolute URLs are forbidden")
        method = method.upper()
        if method == "GET" and parsed.path not in _ALLOWED_SIGNED_GET:
            raise MEXCSpotAuthError(f"blocked signed GET path: {parsed.path}")
        if method == "POST" and parsed.path not in _ALLOWED_SIGNED_POST:
            raise MEXCSpotAuthError(f"blocked signed POST path: {parsed.path}")
        if method not in {"GET", "POST"}:
            raise MEXCSpotAuthError("unsupported spot auth method")

        payload = dict(params)
        payload.setdefault("recvWindow", 5000)
        payload["timestamp"] = int(self._clock_ms())
        query = urlencode(payload)
        signature = _sign(self._credentials.api_secret, query)
        body = f"{query}&signature={signature}".encode("utf-8")

        if method == "GET":
            url = f"{MEXC_SPOT_BASE_URL}{parsed.path}?{body.decode('utf-8')}"
            request = Request(
                url,
                method="GET",
                headers={"X-MEXC-APIKEY": self._credentials.api_key, "User-Agent": "crypto-lab-options-autolive/0.1"},
            )
        else:
            url = f"{MEXC_SPOT_BASE_URL}{parsed.path}"
            request = Request(
                url,
                data=body,
                method="POST",
                headers={
                    "X-MEXC-APIKEY": self._credentials.api_key,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "crypto-lab-options-autolive/0.1",
                },
            )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                status = int(getattr(response, "status", 200))
                raw = response.read().decode("utf-8")
        except Exception as exc:
            raise MEXCSpotAuthError(f"MEXC spot auth transport failed: {type(exc).__name__}: {exc}") from exc
        if status != 200:
            raise MEXCSpotAuthError(f"MEXC spot auth HTTP {status}")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MEXCSpotAuthError("MEXC spot auth returned invalid JSON") from exc
        if isinstance(data, dict) and data.get("code") not in (None, 0, 200):
            raise MEXCSpotAuthError(f"MEXC spot API error code={data.get('code')}: {data.get('msg')}")
        return data

    def account(self) -> dict[str, Any]:
        out = self._signed("GET", "/api/v3/account", {})
        if not isinstance(out, dict):
            raise MEXCSpotAuthError("spot account response invalid")
        return out

    def order_by_client_id(self, *, symbol: str, client_order_id: str) -> dict[str, Any]:
        if symbol != "BTCUSDT":
            raise MEXCSpotAuthError("only BTCUSDT is allowlisted")
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        out = self._signed("GET", "/api/v3/order", {"symbol": symbol, "origClientOrderId": client_order_id})
        if not isinstance(out, dict):
            raise MEXCSpotAuthError("spot order lookup response invalid")
        return out

    def open_orders(self, *, symbol: str = "BTCUSDT") -> list[dict[str, Any]]:
        if symbol != "BTCUSDT":
            raise MEXCSpotAuthError("only BTCUSDT is allowlisted")
        out = self._signed("GET", "/api/v3/openOrders", {"symbol": symbol})
        if not isinstance(out, list):
            raise MEXCSpotAuthError("spot open orders response invalid")
        return out

    def my_trades(self, *, symbol: str = "BTCUSDT", order_id: str | None = None) -> list[dict[str, Any]]:
        if symbol != "BTCUSDT":
            raise MEXCSpotAuthError("only BTCUSDT is allowlisted")
        params: dict[str, Any] = {"symbol": symbol}
        if order_id:
            params["orderId"] = order_id
        out = self._signed("GET", "/api/v3/myTrades", params)
        if not isinstance(out, list):
            raise MEXCSpotAuthError("spot trades response invalid")
        return out

    def submit_market_buy_quote(self, *, quote_usdt: float, client_order_id: str) -> dict[str, Any]:
        if not 0 < quote_usdt <= 10.0:
            raise MEXCSpotAuthError("spot quote order must be >0 and <=10 USDT")
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        out = self._signed(
            "POST", "/api/v3/order",
            {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET",
             "quoteOrderQty": f"{quote_usdt:.8f}".rstrip("0").rstrip("."),
             "newClientOrderId": client_order_id},
        )
        if not isinstance(out, dict) or not out.get("orderId"):
            raise MEXCSpotAuthError("spot market buy response missing orderId")
        return out

    def submit_market_sell_quantity(self, *, quantity_btc: float, client_order_id: str) -> dict[str, Any]:
        if quantity_btc <= 0:
            raise MEXCSpotAuthError("spot sell quantity must be positive")
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        out = self._signed(
            "POST", "/api/v3/order",
            {"symbol": "BTCUSDT", "side": "SELL", "type": "MARKET",
             "quantity": f"{quantity_btc:.12f}".rstrip("0").rstrip("."),
             "newClientOrderId": client_order_id},
        )
        if not isinstance(out, dict) or not out.get("orderId"):
            raise MEXCSpotAuthError("spot market sell response missing orderId")
        return out


__all__ = ["MEXCSpotAuthenticatedClient", "MEXCSpotAuthError", "_sign"]
