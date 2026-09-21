from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .mexc_auth_readonly import MEXCCredentials

MEXC_FUTURES_BASE_URL = "https://api.mexc.com"

_ALLOWED_POST_PATHS = {
    "/api/v1/private/position/change_leverage",
    "/api/v1/private/order/submit",
}


class MEXCTradeTransportError(RuntimeError):
    pass


def _canonical_post_body(payload: dict[str, Any]) -> str:
    # MEXC signs the exact JSON string for POST. Compact deterministic encoding
    # prevents accidental signature/body divergence.
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def _post_signature(
    *,
    api_key: str,
    api_secret: str,
    request_time_ms: int,
    body: str,
) -> str:
    target = f"{api_key}{request_time_ms}{body}"
    return hmac.new(
        api_secret.encode("utf-8"),
        target.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class MEXCFuturesMutationTransport:
    """Minimal MEXC Futures mutation transport.

    This class deliberately exposes only:
    - configure isolated leverage for a direction;
    - submit one contract order.

    It is never instantiated by Radar/shadow services. The local executor
    requires a separate active candidate-specific authority and explicit
    execution token before this transport can be reached.
    """

    base_url = MEXC_FUTURES_BASE_URL

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

    def _post_json(self, path: str, payload: dict[str, Any]) -> Any:
        parsed = urlparse(path)
        if parsed.scheme or parsed.netloc:
            raise MEXCTradeTransportError("absolute URLs are forbidden")
        if parsed.path not in _ALLOWED_POST_PATHS:
            raise MEXCTradeTransportError(f"blocked mutation path: {parsed.path}")

        body = _canonical_post_body(payload)
        request_time_ms = int(self._clock_ms())
        signature = _post_signature(
            api_key=self._credentials.api_key,
            api_secret=self._credentials.api_secret,
            request_time_ms=request_time_ms,
            body=body,
        )
        url = f"{self.base_url}{parsed.path}"
        final = urlparse(url)
        expected = urlparse(self.base_url)
        if final.scheme != "https" or final.netloc != expected.netloc:
            raise MEXCTradeTransportError("blocked MEXC host or scheme")

        request = Request(
            url,
            data=body.encode("utf-8"),
            method="POST",
            headers={
                "ApiKey": self._credentials.api_key,
                "Request-Time": str(request_time_ms),
                "Signature": signature,
                "Content-Type": "application/json",
                "User-Agent": "crypto-lab-mexc-live-executor/0.1",
            },
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                status = int(getattr(response, "status", 200))
                raw = response.read().decode("utf-8")
        except Exception as exc:
            raise MEXCTradeTransportError(
                f"MEXC mutation transport failed: {type(exc).__name__}: {exc}"
            ) from exc

        if status != 200:
            raise MEXCTradeTransportError(f"MEXC mutation HTTP {status}")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MEXCTradeTransportError("MEXC mutation returned invalid JSON") from exc
        if not isinstance(result, dict) or result.get("success") is not True:
            code = result.get("code") if isinstance(result, dict) else None
            message = (
                result.get("message") or result.get("msg")
                if isinstance(result, dict)
                else "invalid response"
            )
            raise MEXCTradeTransportError(f"MEXC mutation failed code={code}: {message}")
        return result.get("data")

    def configure_isolated_leverage(
        self,
        *,
        symbol: str,
        position_type: int,
        leverage: int = 1,
    ) -> Any:
        if symbol != "BTC_USDT":
            raise MEXCTradeTransportError("only BTC_USDT is allowlisted in V0.1")
        if position_type not in (1, 2):
            raise MEXCTradeTransportError("position_type must be 1 long or 2 short")
        if leverage != 1:
            raise MEXCTradeTransportError("V0.1 only permits exactly 1x leverage")
        return self._post_json(
            "/api/v1/private/position/change_leverage",
            {
                "openType": 1,
                "leverage": 1,
                "symbol": symbol,
                "positionType": position_type,
            },
        )

    def submit_market_order(
        self,
        *,
        symbol: str,
        volume_contracts: int,
        side: int,
        external_oid: str,
        position_mode: int = 1,
    ) -> Any:
        if symbol != "BTC_USDT":
            raise MEXCTradeTransportError("only BTC_USDT is allowlisted in V0.1")
        if not isinstance(volume_contracts, int) or volume_contracts < 1:
            raise MEXCTradeTransportError("volume_contracts must be integer >= 1")
        if side not in (1, 2, 3, 4):
            raise MEXCTradeTransportError("unsupported MEXC futures side")
        if position_mode not in (1, 2):
            raise MEXCTradeTransportError("position_mode must be hedge=1 or one-way=2")
        if not external_oid or len(external_oid) > 32:
            raise MEXCTradeTransportError("external_oid must be 1..32 chars")
        return self._post_json(
            "/api/v1/private/order/submit",
            {
                "symbol": symbol,
                "price": 0,
                "vol": volume_contracts,
                "leverage": 1,
                "side": side,
                "type": 5,
                "openType": 1,
                "externalOid": external_oid,
                "positionMode": position_mode,
            },
        )


__all__ = [
    "MEXCTradeTransportError",
    "MEXCFuturesMutationTransport",
    "_canonical_post_body",
    "_post_signature",
]
