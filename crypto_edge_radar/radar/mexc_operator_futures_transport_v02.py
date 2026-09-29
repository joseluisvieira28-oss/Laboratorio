from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .mexc_auth_readonly import MEXCCredentials

MEXC_FUTURES_BASE_URL = "https://api.mexc.com"
CONTRACT_RE = re.compile(r"^[A-Z0-9]+_USDT$")
EXTERNAL_OID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,32}$")

_ALLOWED_POST_PATHS = {
    "/api/v1/private/position/change_leverage",
    "/api/v1/private/position/change_auto_add_im",
    "/api/v1/private/order/create",
    "/api/v1/private/order/cancel_with_external",
}


class MEXCOperatorTransportError(RuntimeError):
    pass


@dataclass(frozen=True)
class OperatorFuturesPolicy:
    policy_id: str
    symbol: str
    allowed_directions: tuple[str, ...]
    required_leverage: int = 5

    def __post_init__(self) -> None:
        symbol = self.symbol.upper()
        if not CONTRACT_RE.fullmatch(symbol):
            raise ValueError(f"invalid futures symbol: {self.symbol}")
        dirs = tuple(d.upper() for d in self.allowed_directions)
        if not dirs or any(d not in {"LONG", "SHORT"} for d in dirs):
            raise ValueError("allowed_directions must contain LONG and/or SHORT")
        if self.required_leverage != 5:
            raise ValueError("operator V0.2 is frozen to exactly 5x")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "allowed_directions", dirs)


def _body(payload: Any) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def _signature(*, key: str, secret: str, ts: int, body: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        f"{key}{ts}{body}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def direction_meta(direction: str) -> dict[str, int]:
    direction = direction.upper()
    if direction == "LONG":
        return {"position_type": 1, "entry_side": 1, "exit_side": 4}
    if direction == "SHORT":
        return {"position_type": 2, "entry_side": 3, "exit_side": 2}
    raise MEXCOperatorTransportError(f"unsupported direction: {direction}")


class MEXCOperatorFuturesTransportV02:
    """Policy-bound mutation transport for the 5x operator lane.

    This transport cannot decide to trade. The caller must already prove:
    canonical signal, timing, fresh account/risk state, sizing, friction,
    duplicate identity and active execution authority.

    Hard boundaries:
    - one exact symbol per policy instance;
    - allowed direction(s) only;
    - isolated mode only;
    - exactly 5x leverage;
    - Hedge Mode only;
    - MARKET orders only;
    - Auto Margin Add can only be disabled;
    - no transfer, withdrawal, cross margin, leverage tuning or generic POST.
    """

    base_url = MEXC_FUTURES_BASE_URL

    def __init__(
        self,
        credentials: MEXCCredentials,
        policy: OperatorFuturesPolicy,
        *,
        timeout: int = 10,
        clock_ms: Callable[[], int] | None = None,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self._credentials = credentials
        self.policy = policy
        self.timeout = timeout
        self._clock_ms = clock_ms or (lambda: int(time.time_ns() / 1_000_000))
        self._opener = opener

    def _assert_symbol(self, symbol: str) -> str:
        symbol = symbol.upper()
        if symbol != self.policy.symbol:
            raise MEXCOperatorTransportError(
                f"symbol {symbol} not allowed by policy {self.policy.policy_id}"
            )
        return symbol

    def _assert_direction(self, direction: str) -> str:
        direction = direction.upper()
        if direction not in self.policy.allowed_directions:
            raise MEXCOperatorTransportError(
                f"direction {direction} not allowed by policy {self.policy.policy_id}"
            )
        return direction

    def _post_json(self, path: str, payload: Any) -> Any:
        parsed = urlparse(path)
        if parsed.scheme or parsed.netloc:
            raise MEXCOperatorTransportError("absolute URLs are forbidden")
        if parsed.path not in _ALLOWED_POST_PATHS:
            raise MEXCOperatorTransportError(f"blocked mutation path: {parsed.path}")

        body = _body(payload)
        ts = int(self._clock_ms())
        sig = _signature(
            key=self._credentials.api_key,
            secret=self._credentials.api_secret,
            ts=ts,
            body=body,
        )
        url = f"{self.base_url}{parsed.path}"
        final = urlparse(url)
        expected = urlparse(self.base_url)
        if final.scheme != "https" or final.netloc != expected.netloc:
            raise MEXCOperatorTransportError("blocked MEXC host or scheme")

        request = Request(
            url,
            data=body.encode("utf-8"),
            method="POST",
            headers={
                "ApiKey": self._credentials.api_key,
                "Request-Time": str(ts),
                "Signature": sig,
                "Content-Type": "application/json",
                "User-Agent": "crypto-lab-mexc-operator-v02",
            },
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                status = int(getattr(response, "status", 200))
                raw = response.read().decode("utf-8")
        except Exception as exc:
            raise MEXCOperatorTransportError(
                f"MEXC operator transport failed: {type(exc).__name__}: {exc}"
            ) from exc

        if status != 200:
            raise MEXCOperatorTransportError(f"MEXC mutation HTTP {status}")
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MEXCOperatorTransportError("MEXC mutation returned invalid JSON") from exc
        if not isinstance(result, dict) or result.get("success") is not True:
            code = result.get("code") if isinstance(result, dict) else None
            msg = (
                result.get("message") or result.get("msg") or "unknown MEXC error"
                if isinstance(result, dict)
                else "invalid response"
            )
            raise MEXCOperatorTransportError(f"MEXC mutation failed code={code}: {msg}")
        return result.get("data")

    def configure_isolated_leverage(self, *, symbol: str, direction: str) -> Any:
        symbol = self._assert_symbol(symbol)
        direction = self._assert_direction(direction)
        meta = direction_meta(direction)
        return self._post_json(
            "/api/v1/private/position/change_leverage",
            {
                "openType": 1,
                "leverage": self.policy.required_leverage,
                "symbol": symbol,
                "positionType": meta["position_type"],
            },
        )

    def set_auto_add_margin(self, *, position_id: int, enabled: bool) -> Any:
        if not isinstance(position_id, int) or position_id <= 0:
            raise MEXCOperatorTransportError("position_id must be positive integer")
        if enabled is not False:
            raise MEXCOperatorTransportError("Auto-Add Margin may only be disabled")
        return self._post_json(
            "/api/v1/private/position/change_auto_add_im",
            {"positionId": position_id, "isEnabled": False},
        )

    def cancel_by_external(self, *, symbol: str, external_oid: str) -> Any:
        symbol = self._assert_symbol(symbol)
        if not EXTERNAL_OID_RE.fullmatch(external_oid):
            raise MEXCOperatorTransportError("invalid external_oid")
        return self._post_json(
            "/api/v1/private/order/cancel_with_external",
            {"symbol": symbol, "externalOid": external_oid},
        )

    def submit_market_order(
        self,
        *,
        symbol: str,
        direction: str,
        phase: str,
        volume_contracts: int,
        external_oid: str,
        position_id: int | None = None,
    ) -> dict[str, Any]:
        symbol = self._assert_symbol(symbol)
        direction = self._assert_direction(direction)
        phase = phase.upper()
        if phase not in {"ENTRY", "EXIT"}:
            raise MEXCOperatorTransportError("phase must be ENTRY or EXIT")
        if not isinstance(volume_contracts, int) or volume_contracts < 1:
            raise MEXCOperatorTransportError("volume_contracts must be integer >= 1")
        if not EXTERNAL_OID_RE.fullmatch(external_oid):
            raise MEXCOperatorTransportError("invalid external_oid")

        meta = direction_meta(direction)
        side = meta["entry_side"] if phase == "ENTRY" else meta["exit_side"]
        if phase == "ENTRY" and position_id is not None:
            raise MEXCOperatorTransportError("ENTRY must not supply position_id")
        if phase == "EXIT" and (
            not isinstance(position_id, int) or position_id <= 0
        ):
            raise MEXCOperatorTransportError("EXIT requires positive position_id")

        payload: dict[str, Any] = {
            "symbol": symbol,
            "price": 0,
            "vol": volume_contracts,
            "leverage": self.policy.required_leverage,
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
            raise MEXCOperatorTransportError("order/create success missing orderId")
        return data


__all__ = [
    "OperatorFuturesPolicy",
    "MEXCOperatorFuturesTransportV02",
    "MEXCOperatorTransportError",
    "direction_meta",
]
