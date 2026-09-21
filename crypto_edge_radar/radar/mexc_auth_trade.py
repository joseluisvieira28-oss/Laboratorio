from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .mexc_auth_readonly import MEXCCredentials

MEXC_FUTURES_BASE_URL = "https://api.mexc.com"
EXTERNAL_OID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,32}$")

_ALLOWED_POST_PATHS = {
    "/api/v1/private/position/change_leverage",
    "/api/v1/private/position/change_auto_add_im",
    "/api/v1/private/order/create",
    "/api/v1/private/order/cancel_with_external",
}


class MEXCTradeTransportError(RuntimeError):
    pass


def _canonical_post_body(payload: Any) -> str:
    # MEXC signs the exact JSON string used as the POST body.
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
    """Tiny mutation surface for candidate-authorized BTC_USDT micro-live.

    Deliberately allowlisted to:
    - set a direction to isolated 1x before entry;
    - create a BTC_USDT market order;
    - disable Auto-Add Margin on an existing isolated position.

    It has no transfer, withdrawal, generic account mutation, batch order,
    cancel-all, leverage >1x or cross-margin method.
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

    def _post_json(self, path: str, payload: Any) -> Any:
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
                "User-Agent": "crypto-lab-mexc-live-executor/0.2",
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
                (result.get("message") or result.get("msg") or "unknown MEXC error")
                if isinstance(result, dict)
                else "invalid response"
            )
            raise MEXCTradeTransportError(
                f"MEXC mutation failed code={code}: {message}"
            )
        return result.get("data")

    def configure_isolated_leverage(
        self,
        *,
        symbol: str,
        position_type: int,
        leverage: int = 1,
    ) -> Any:
        if symbol != "BTC_USDT":
            raise MEXCTradeTransportError("only BTC_USDT is allowlisted in V0.2")
        if position_type not in (1, 2):
            raise MEXCTradeTransportError("position_type must be 1 long or 2 short")
        if leverage != 1:
            raise MEXCTradeTransportError("V0.2 only permits exactly 1x leverage")
        return self._post_json(
            "/api/v1/private/position/change_leverage",
            {
                "openType": 1,
                "leverage": 1,
                "symbol": symbol,
                "positionType": position_type,
            },
        )

    def set_auto_add_margin(
        self,
        *,
        position_id: int,
        enabled: bool,
    ) -> Any:
        if not isinstance(position_id, int) or position_id <= 0:
            raise MEXCTradeTransportError("position_id must be positive integer")
        if enabled is not False:
            raise MEXCTradeTransportError(
                "V0.2 can only DISABLE Auto-Add Margin; enabling is forbidden"
            )
        return self._post_json(
            "/api/v1/private/position/change_auto_add_im",
            {
                "positionId": position_id,
                "isEnabled": False,
            },
        )

    def cancel_by_external(
        self,
        *,
        symbol: str,
        external_oid: str,
    ) -> Any:
        if symbol != "BTC_USDT":
            raise MEXCTradeTransportError("only BTC_USDT is allowlisted in V0.2")
        if not EXTERNAL_OID_RE.fullmatch(external_oid):
            raise MEXCTradeTransportError("invalid external_oid")
        # Current/legacy MEXC contract documentation agrees this endpoint
        # accepts one object, unlike the batch cancel endpoint.
        return self._post_json(
            "/api/v1/private/order/cancel_with_external",
            {"symbol": symbol, "externalOid": external_oid},
        )

    def submit_market_order(
        self,
        *,
        symbol: str,
        volume_contracts: int,
        side: int,
        external_oid: str,
        position_mode: int = 1,
        position_id: int | None = None,
    ) -> dict[str, Any]:
        if symbol != "BTC_USDT":
            raise MEXCTradeTransportError("only BTC_USDT is allowlisted in V0.2")
        if not isinstance(volume_contracts, int) or volume_contracts < 1:
            raise MEXCTradeTransportError("volume_contracts must be integer >= 1")
        if side not in (2, 3):
            raise MEXCTradeTransportError(
                "V0.2 ETF-CME Futures path permits only open-short(3) or close-short(2)"
            )
        if position_mode != 1:
            raise MEXCTradeTransportError("V0.2 requires Hedge Mode (positionMode=1)")
        if not EXTERNAL_OID_RE.fullmatch(external_oid):
            raise MEXCTradeTransportError("external_oid must be safe 1..32 chars")
        if side == 2 and (not isinstance(position_id, int) or position_id <= 0):
            raise MEXCTradeTransportError("close-short requires a positive position_id")
        if side == 3 and position_id is not None:
            raise MEXCTradeTransportError("open-short must not supply position_id")

        payload: dict[str, Any] = {
            "symbol": symbol,
            "price": 0,
            "vol": volume_contracts,
            "leverage": 1,
            "side": side,
            "type": 5,
            "openType": 1,
            "externalOid": external_oid,
            "positionMode": 1,
        }
        if position_id is not None:
            payload["positionId"] = position_id

        data = self._post_json("/api/v1/private/order/create", payload)
        if not isinstance(data, dict) or not data.get("orderId"):
            raise MEXCTradeTransportError("order/create success response missing orderId")
        return data


__all__ = [
    "MEXCTradeTransportError",
    "MEXCFuturesMutationTransport",
    "_canonical_post_body",
    "_post_signature",
]
