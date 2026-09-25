from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .mexc_auth_readonly import MEXCCredentials
from .mexc_spot_auth import CLIENT_ID_RE, MEXCSpotAuthError, _signed_query


SPOT_SYMBOL_RE = re.compile(r"^[A-Z0-9]{5,24}$")
_ALLOWED = {
    ("GET", "/api/v3/account"),
    ("GET", "/api/v3/openOrders"),
    ("GET", "/api/v3/order"),
    ("GET", "/api/v3/myTrades"),
    ("POST", "/api/v3/order/test"),
    ("POST", "/api/v3/order"),
    ("DELETE", "/api/v3/order"),
}


@dataclass(frozen=True)
class SpotMutationPolicy:
    symbol: str
    max_quote_order_qty: float
    buy_allowed: bool = True
    sell_allowed: bool = True

    def normalized_symbol(self) -> str:
        value = self.symbol.upper()
        if not SPOT_SYMBOL_RE.fullmatch(value):
            raise MEXCSpotAuthError(f"invalid generic Spot symbol: {self.symbol}")
        if float(self.max_quote_order_qty) <= 0:
            raise MEXCSpotAuthError("max_quote_order_qty must be positive")
        return value


class MEXCSpotPolicyBoundClient:
    """Generic MEXC Spot mutation transport bound to explicit per-symbol policies.

    This is transport plumbing only. It does not confer candidate authority and
    does not convert scientific/risk caps between currencies. A candidate must
    supply an already-frozen quote-asset cap before this client can be wired to
    a live dispatcher.
    """

    base_url = "https://api.mexc.com"

    def __init__(
        self,
        credentials: MEXCCredentials,
        *,
        policies: list[SpotMutationPolicy],
        timeout: int = 10,
        clock_ms: Callable[[], int] | None = None,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self._credentials = credentials
        self.timeout = timeout
        self._clock_ms = clock_ms or (lambda: int(time.time_ns() / 1_000_000))
        self._opener = opener
        normalized: dict[str, SpotMutationPolicy] = {}
        for policy in policies:
            symbol = policy.normalized_symbol()
            if symbol in normalized:
                raise MEXCSpotAuthError(f"duplicate Spot policy: {symbol}")
            normalized[symbol] = policy
        if not normalized:
            raise MEXCSpotAuthError("at least one explicit Spot mutation policy is required")
        self._policies = normalized

    def _policy(self, symbol: str) -> SpotMutationPolicy:
        value = symbol.upper()
        if value not in self._policies:
            raise MEXCSpotAuthError(f"Spot symbol not policy-allowlisted: {value}")
        return self._policies[value]

    def _request(self, method: str, path: str, params: dict[str, Any] | None = None) -> Any:
        method = method.upper()
        parsed = urlparse(path)
        if parsed.scheme or parsed.netloc or (method, parsed.path) not in _ALLOWED:
            raise MEXCSpotAuthError(f"blocked generic Spot API route: {method} {path}")
        p = dict(params or {})
        p.setdefault("recvWindow", 5000)
        p["timestamp"] = int(self._clock_ms())
        query = _signed_query(self._credentials.api_secret, p)
        url = f"{self.base_url}{parsed.path}?{query}"
        final = urlparse(url)
        if final.scheme != "https" or final.netloc != urlparse(self.base_url).netloc:
            raise MEXCSpotAuthError("blocked generic Spot host or scheme")
        req = Request(
            url,
            method=method,
            headers={
                "X-MEXC-APIKEY": self._credentials.api_key,
                "Content-Type": "application/json",
                "User-Agent": "crypto-lab-policy-bound-spot/0.1",
            },
        )
        try:
            with self._opener(req, timeout=self.timeout) as response:
                status = int(getattr(response, "status", 200))
                body = response.read().decode("utf-8")
        except Exception as exc:
            raise MEXCSpotAuthError(
                f"generic Spot authenticated transport failed: {type(exc).__name__}: {exc}"
            ) from exc
        if status != 200:
            raise MEXCSpotAuthError(f"generic Spot authenticated HTTP {status}")
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError as exc:
            raise MEXCSpotAuthError("generic Spot authenticated response invalid JSON") from exc
        if isinstance(payload, dict) and payload.get("code") not in (None, 0, 200):
            raise MEXCSpotAuthError(
                f"MEXC Spot error code={payload.get('code')}: "
                f"{payload.get('msg') or payload.get('message')}"
            )
        return payload

    def account(self) -> dict[str, Any]:
        out = self._request("GET", "/api/v3/account")
        if not isinstance(out, dict):
            raise MEXCSpotAuthError("account payload invalid")
        return out

    def open_orders(self, symbol: str) -> list[dict[str, Any]]:
        policy = self._policy(symbol)
        out = self._request("GET", "/api/v3/openOrders", {"symbol": policy.normalized_symbol()})
        if not isinstance(out, list):
            raise MEXCSpotAuthError("openOrders payload invalid")
        return out

    def order(self, *, symbol: str, client_order_id: str) -> dict[str, Any]:
        policy = self._policy(symbol)
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        out = self._request(
            "GET",
            "/api/v3/order",
            {"symbol": policy.normalized_symbol(), "origClientOrderId": client_order_id},
        )
        if not isinstance(out, dict):
            raise MEXCSpotAuthError("order payload invalid")
        return out

    def my_trades(self, *, symbol: str, order_id: str | None = None) -> list[dict[str, Any]]:
        policy = self._policy(symbol)
        params: dict[str, Any] = {"symbol": policy.normalized_symbol()}
        if order_id is not None:
            params["orderId"] = order_id
        out = self._request("GET", "/api/v3/myTrades", params)
        if not isinstance(out, list):
            raise MEXCSpotAuthError("myTrades payload invalid")
        return out

    def test_market_buy(
        self,
        *,
        symbol: str,
        quote_order_qty: float,
        client_order_id: str,
    ) -> dict[str, Any]:
        return self._market_buy(
            path="/api/v3/order/test",
            symbol=symbol,
            quote_order_qty=quote_order_qty,
            client_order_id=client_order_id,
        )

    def submit_market_buy(
        self,
        *,
        symbol: str,
        quote_order_qty: float,
        client_order_id: str,
    ) -> dict[str, Any]:
        return self._market_buy(
            path="/api/v3/order",
            symbol=symbol,
            quote_order_qty=quote_order_qty,
            client_order_id=client_order_id,
        )

    def _market_buy(
        self,
        *,
        path: str,
        symbol: str,
        quote_order_qty: float,
        client_order_id: str,
    ) -> dict[str, Any]:
        policy = self._policy(symbol)
        if not policy.buy_allowed:
            raise MEXCSpotAuthError(f"Spot BUY forbidden by policy: {symbol}")
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        quantity = float(quote_order_qty)
        maximum = float(policy.max_quote_order_qty)
        if not (0 < quantity <= maximum):
            raise MEXCSpotAuthError(
                f"Spot BUY quoteOrderQty must be >0 and <= policy cap {maximum}"
            )
        out = self._request(
            "POST",
            path,
            {
                "symbol": policy.normalized_symbol(),
                "side": "BUY",
                "type": "MARKET",
                "quoteOrderQty": f"{quantity:.12f}".rstrip("0").rstrip("."),
                "newClientOrderId": client_order_id,
            },
        )
        if not isinstance(out, dict):
            raise MEXCSpotAuthError("Spot BUY response invalid")
        return out

    def submit_market_sell(
        self,
        *,
        symbol: str,
        quantity_base: float,
        client_order_id: str,
    ) -> dict[str, Any]:
        policy = self._policy(symbol)
        if not policy.sell_allowed:
            raise MEXCSpotAuthError(f"Spot SELL forbidden by policy: {symbol}")
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        quantity = float(quantity_base)
        if quantity <= 0:
            raise MEXCSpotAuthError("Spot SELL quantity must be positive")
        out = self._request(
            "POST",
            "/api/v3/order",
            {
                "symbol": policy.normalized_symbol(),
                "side": "SELL",
                "type": "MARKET",
                "quantity": format(quantity, ".16f").rstrip("0").rstrip("."),
                "newClientOrderId": client_order_id,
            },
        )
        if not isinstance(out, dict):
            raise MEXCSpotAuthError("Spot SELL response invalid")
        return out

    def cancel_order(self, *, symbol: str, client_order_id: str) -> dict[str, Any]:
        policy = self._policy(symbol)
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        out = self._request(
            "DELETE",
            "/api/v3/order",
            {"symbol": policy.normalized_symbol(), "origClientOrderId": client_order_id},
        )
        if not isinstance(out, dict):
            raise MEXCSpotAuthError("Spot cancel response invalid")
        return out


__all__ = ["SpotMutationPolicy", "MEXCSpotPolicyBoundClient"]
