from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .execution import ExecutionBlocked

BASE_URL = "https://api.mexc.com"


class MEXCFuturesTradingClient:
    """Prepared connector shell.

    MEXC announced Futures API trading in March 2026 and moved the Futures API
    domain to api.mexc.com. The accessible legacy contract reference still marks
    its old private order endpoint as under maintenance, so this branch deliberately
    refuses private order placement until the current authenticated order schema is
    re-verified during credential setup.

    This class may be used for auth/signature smoke tests once the exact current
    private endpoint is pinned. It is never a fallback venue for CED1D-0031,
    whose scientific identity is Binance USD-M.
    """

    name = "MEXC_FUTURES_BLOCKED_PENDING_SCHEMA_PIN"

    def __init__(self, *, timeout: int = 10) -> None:
        self.api_key = os.getenv("MEXC_API_KEY", "").strip()
        self.api_secret = os.getenv("MEXC_API_SECRET", "").strip()
        self.timeout = timeout
        if not self.api_key or not self.api_secret:
            raise ExecutionBlocked("MEXC_API_KEY / MEXC_API_SECRET not configured")

    def sign_private(self, params: dict[str, Any] | None = None) -> dict[str, str]:
        # Legacy contract signature form retained only for later compatibility
        # verification; it does not authorize or submit an order here.
        ts = str(int(time.time() * 1000))
        body = json.dumps(params or {}, separators=(",", ":"), sort_keys=False)
        target = self.api_key + ts + body
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            target.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "ApiKey": self.api_key,
            "Request-Time": ts,
            "Signature": signature,
            "Content-Type": "application/json",
        }

    def preflight(self, symbol: str) -> dict[str, Any]:
        return {
            "ok": False,
            "reason": "MEXC_PRIVATE_FUTURES_ORDER_SCHEMA_NOT_PINNED",
            "symbol": symbol,
            "venue_substitution_for_CED1D_0031_forbidden": True,
        }

    def market_rules(self, symbol: str):
        raise ExecutionBlocked("MEXC execution disabled pending current schema pin")

    def mark_or_last_price(self, symbol: str):
        raise ExecutionBlocked("MEXC execution disabled pending current schema pin")

    def submit_market(self, **kwargs):
        raise ExecutionBlocked("MEXC execution disabled pending current schema pin")
