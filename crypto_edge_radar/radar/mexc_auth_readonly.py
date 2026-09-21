from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

MEXC_FUTURES_BASE_URL = "https://api.mexc.com"
DEFAULT_TIMEOUT_SECONDS = 10
CONTRACT_RE = re.compile(r"^[A-Z0-9]+_USDT$")
EXTERNAL_OID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,32}$")

_PRIVATE_EXACT_PATHS = {
    "/api/v1/private/account/assets",
    "/api/v1/private/position/open_positions",
    "/api/v1/private/position/position_mode",
    "/api/v1/private/position/leverage",
    "/api/v1/private/account/risk_limit",
    "/api/v1/private/account/tiered_fee_rate/v2",
    "/api/v1/private/order/list/open_orders",
}
_PRIVATE_PREFIX_PATHS = (
    "/api/v1/private/order/external/",
)


class MEXCAuthenticatedReadError(RuntimeError):
    pass


@dataclass(frozen=True)
class MEXCCredentials:
    api_key: str
    api_secret: str

    @classmethod
    def from_env(cls) -> "MEXCCredentials":
        key = os.getenv("MEXC_API_KEY", "").strip()
        secret = os.getenv("MEXC_API_SECRET", "").strip()
        if not key or not secret:
            raise MEXCAuthenticatedReadError(
                "MEXC_API_KEY and MEXC_API_SECRET must exist only in the local process environment"
            )
        return cls(api_key=key, api_secret=secret)


def _encoded_query(params: dict[str, Any] | None) -> str:
    if not params:
        return ""
    clean = {k: v for k, v in params.items() if v is not None}
    ordered = sorted((str(k), str(v)) for k, v in clean.items())
    return urlencode(ordered, doseq=False, quote_via=quote, safe="")


def _signature(*, api_key: str, api_secret: str, request_time_ms: int, query: str) -> str:
    target = f"{api_key}{request_time_ms}{query}"
    return hmac.new(
        api_secret.encode("utf-8"),
        target.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _contract(symbol: str) -> str:
    value = symbol.upper()
    if not CONTRACT_RE.fullmatch(value):
        raise MEXCAuthenticatedReadError(f"invalid MEXC futures contract: {symbol}")
    return value


class MEXCFuturesAuthenticatedReadOnlyClient:
    """Authenticated MEXC Futures GET-only client bound to current documented endpoints.

    Security boundary:
    - only explicitly allowlisted private GET endpoints are reachable;
    - no POST/DELETE method exists here;
    - credentials remain caller-memory/environment only;
    - credentials are never returned or persisted.
    """

    provider = "MEXC_FUTURES_AUTHENTICATED_READ_ONLY"
    base_url = MEXC_FUTURES_BASE_URL

    def __init__(
        self,
        credentials: MEXCCredentials,
        *,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        clock_ms: Callable[[], int] | None = None,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self._credentials = credentials
        self.timeout = timeout
        self._clock_ms = clock_ms or (lambda: int(time.time_ns() / 1_000_000))
        self._opener = opener

    @staticmethod
    def _allowed(path: str) -> bool:
        parsed = urlparse(path)
        if parsed.path in _PRIVATE_EXACT_PATHS:
            return True
        return any(parsed.path.startswith(prefix) for prefix in _PRIVATE_PREFIX_PATHS)

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        parsed = urlparse(path)
        if parsed.scheme or parsed.netloc:
            raise MEXCAuthenticatedReadError("absolute URLs are forbidden")
        if not self._allowed(path):
            raise MEXCAuthenticatedReadError(
                f"blocked non-allowlisted private GET path: {parsed.path}"
            )

        query = _encoded_query(params)
        request_time_ms = int(self._clock_ms())
        signature = _signature(
            api_key=self._credentials.api_key,
            api_secret=self._credentials.api_secret,
            request_time_ms=request_time_ms,
            query=query,
        )

        url = f"{self.base_url}{parsed.path}"
        if query:
            url += f"?{query}"
        expected = urlparse(self.base_url)
        final = urlparse(url)
        if final.scheme != "https" or final.netloc != expected.netloc:
            raise MEXCAuthenticatedReadError("blocked MEXC host or scheme")

        request = Request(
            url,
            method="GET",
            headers={
                "ApiKey": self._credentials.api_key,
                "Request-Time": str(request_time_ms),
                "Signature": signature,
                "Content-Type": "application/json",
                "User-Agent": "crypto-lab-mexc-auth/0.2 GET-only",
            },
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                status = int(getattr(response, "status", 200))
                body = response.read().decode("utf-8")
        except Exception as exc:
            raise MEXCAuthenticatedReadError(
                f"authenticated GET transport failed: {type(exc).__name__}: {exc}"
            ) from exc

        if status != 200:
            raise MEXCAuthenticatedReadError(f"authenticated GET HTTP {status}")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise MEXCAuthenticatedReadError("authenticated GET returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise MEXCAuthenticatedReadError("authenticated GET payload is not an object")
        if payload.get("success") is not True:
            code = payload.get("code")
            message = payload.get("message") or payload.get("msg") or "unknown MEXC error"
            raise MEXCAuthenticatedReadError(
                f"MEXC private read failed code={code}: {message}"
            )
        return payload.get("data")

    def assets(self) -> list[dict[str, Any]]:
        data = self._get_json("/api/v1/private/account/assets")
        if not isinstance(data, list):
            raise MEXCAuthenticatedReadError("account assets payload missing list")
        return data

    def open_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        params = {"symbol": _contract(symbol)} if symbol else None
        data = self._get_json("/api/v1/private/position/open_positions", params)
        if data is None:
            return []
        if not isinstance(data, list):
            raise MEXCAuthenticatedReadError("open positions payload missing list")
        return data

    def open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        data = self._get_json(
            "/api/v1/private/order/list/open_orders",
            {"page_num": 1, "page_size": 100},
        )
        if data is None:
            rows: list[dict[str, Any]] = []
        elif isinstance(data, dict) and isinstance(data.get("resultList"), list):
            rows = data["resultList"]
        elif isinstance(data, list):
            rows = data
        else:
            raise MEXCAuthenticatedReadError("open orders payload has unsupported shape")
        if symbol:
            wanted = _contract(symbol)
            return [row for row in rows if str(row.get("symbol", "")).upper() == wanted]
        return rows

    def fee_details(self, symbol: str = "BTC_USDT") -> dict[str, Any]:
        data = self._get_json(
            "/api/v1/private/account/tiered_fee_rate/v2",
            {"symbol": _contract(symbol)},
        )
        if not isinstance(data, dict):
            raise MEXCAuthenticatedReadError("fee details payload missing object")
        return data

    # Compatibility name for callers from V0.1.
    def tiered_fee_rate(self, symbol: str = "BTC_USDT") -> dict[str, Any]:
        return self.fee_details(symbol)

    def leverage(self, symbol: str = "BTC_USDT") -> list[dict[str, Any]]:
        data = self._get_json(
            "/api/v1/private/position/leverage",
            {"symbol": _contract(symbol)},
        )
        if isinstance(data, dict):
            return [data]
        if not isinstance(data, list):
            raise MEXCAuthenticatedReadError("leverage payload has unsupported shape")
        return data

    def position_mode(self) -> int:
        data = self._get_json("/api/v1/private/position/position_mode")
        try:
            value = int(data)
        except (TypeError, ValueError) as exc:
            raise MEXCAuthenticatedReadError("position mode payload invalid") from exc
        if value not in (1, 2):
            raise MEXCAuthenticatedReadError(f"unsupported position mode: {value}")
        return value

    def risk_limit(self, symbol: str = "BTC_USDT") -> Any:
        return self._get_json(
            "/api/v1/private/account/risk_limit",
            {"symbol": _contract(symbol)},
        )

    def order_by_external(self, *, symbol: str, external_oid: str) -> dict[str, Any]:
        symbol = _contract(symbol)
        if not EXTERNAL_OID_RE.fullmatch(external_oid):
            raise MEXCAuthenticatedReadError("invalid external_oid")
        data = self._get_json(
            f"/api/v1/private/order/external/{symbol}/{external_oid}"
        )
        if not isinstance(data, dict):
            raise MEXCAuthenticatedReadError("external order lookup missing object")
        return data


__all__ = [
    "MEXCAuthenticatedReadError",
    "MEXCCredentials",
    "MEXCFuturesAuthenticatedReadOnlyClient",
    "_encoded_query",
    "_signature",
]
