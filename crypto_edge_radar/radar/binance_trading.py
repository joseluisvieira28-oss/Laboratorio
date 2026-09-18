from __future__ import annotations

from decimal import Decimal
import hashlib
import hmac
import json
import os
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .execution import ExecutionBlocked

BASE_URL = "https://fapi.binance.com"
MAX_TAKER_RATE = Decimal("0.0005")  # 5 bps/fill, frozen STRESS fee floor


class BinanceUSDMTradingClient:
    name = "BINANCE_USDM"

    def __init__(self, *, timeout: int = 10) -> None:
        self.api_key = os.getenv("BINANCE_API_KEY", "").strip()
        self.api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
        self.timeout = timeout
        if not self.api_key or not self.api_secret:
            raise ExecutionBlocked("BINANCE_API_KEY / BINANCE_API_SECRET not configured")

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        signed: bool = False,
    ) -> Any:
        payload = dict(params or {})
        headers = {"User-Agent": "crypto-edge-radar-microlive/0.1"}
        if signed:
            payload["timestamp"] = int(time.time() * 1000)
            payload.setdefault("recvWindow", 5000)
            query = urlencode(payload)
            sig = hmac.new(
                self.api_secret.encode("utf-8"),
                query.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            query = query + "&signature=" + sig
            headers["X-MBX-APIKEY"] = self.api_key
        else:
            query = urlencode(payload)

        url = BASE_URL + path + (("?" + query) if query else "")
        req = Request(url, method=method, headers=headers)
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            raise ExecutionBlocked(f"Binance HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise ExecutionBlocked(f"Binance network error: {exc}") from exc
        return json.loads(raw) if raw else {}

    def public_time(self) -> int:
        return int(self._request("GET", "/fapi/v1/time")["serverTime"])

    def book_ticker(self, symbol: str) -> dict[str, Decimal]:
        row = self._request("GET", "/fapi/v1/ticker/bookTicker", {"symbol": symbol})
        bid = Decimal(str(row["bidPrice"]))
        ask = Decimal(str(row["askPrice"]))
        if bid <= 0 or ask <= 0 or ask < bid:
            raise ExecutionBlocked("invalid Binance book ticker")
        mid = (bid + ask) / Decimal("2")
        spread_bps = (ask - bid) / mid * Decimal("10000")
        return {"bid": bid, "ask": ask, "mid": mid, "spread_bps": spread_bps}

    def mark_or_last_price(self, symbol: str) -> Decimal:
        return self.book_ticker(symbol)["mid"]

    def market_rules(self, symbol: str) -> dict[str, Decimal]:
        info = self._request("GET", "/fapi/v1/exchangeInfo")
        rows = [x for x in info.get("symbols", []) if x.get("symbol") == symbol]
        if len(rows) != 1:
            raise ExecutionBlocked("symbol not uniquely present in exchangeInfo")
        filters = {x["filterType"]: x for x in rows[0].get("filters", [])}
        lot = filters.get("MARKET_LOT_SIZE") or filters.get("LOT_SIZE")
        if not lot:
            raise ExecutionBlocked("market lot-size filter missing")
        min_notional = Decimal("0")
        notional_filter = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL")
        if notional_filter:
            min_notional = Decimal(
                str(
                    notional_filter.get("notional")
                    or notional_filter.get("minNotional")
                    or "0"
                )
            )
        return {
            "step_size": Decimal(str(lot["stepSize"])),
            "min_qty": Decimal(str(lot["minQty"])),
            "min_notional": min_notional,
        }

    def _symbol_config(self, symbol: str) -> dict[str, Any]:
        rows = self._request(
            "GET", "/fapi/v1/symbolConfig", {"symbol": symbol}, signed=True
        )
        if isinstance(rows, dict):
            rows = [rows]
        matches = [x for x in rows if x.get("symbol") == symbol]
        if len(matches) != 1:
            raise ExecutionBlocked("Binance symbolConfig unavailable or ambiguous")
        return matches[0]

    def _position_risk(self, symbol: str) -> list[dict[str, Any]]:
        rows = self._request(
            "GET", "/fapi/v3/positionRisk", {"symbol": symbol}, signed=True
        )
        return rows if isinstance(rows, list) else [rows]

    def _open_orders(self, symbol: str) -> list[dict[str, Any]]:
        rows = self._request(
            "GET", "/fapi/v1/openOrders", {"symbol": symbol}, signed=True
        )
        return rows if isinstance(rows, list) else []

    def _position_mode(self) -> bool:
        row = self._request("GET", "/fapi/v1/positionSide/dual", signed=True)
        return bool(row.get("dualSidePosition"))

    def _commission_rate(self, symbol: str) -> Decimal:
        row = self._request(
            "GET", "/fapi/v1/commissionRate", {"symbol": symbol}, signed=True
        )
        return Decimal(str(row["takerCommissionRate"]))

    def query_order_if_exists(self, symbol: str, client_order_id: str) -> dict[str, Any] | None:
        try:
            return self._request(
                "GET",
                "/fapi/v1/order",
                {"symbol": symbol, "origClientOrderId": client_order_id},
                signed=True,
            )
        except ExecutionBlocked as exc:
            msg = str(exc)
            if '"code":-2013' in msg.replace(" ", ""):
                return None
            raise

    def preflight(self, symbol: str) -> dict[str, Any]:
        server_ms = self.public_time()
        local_ms = int(time.time() * 1000)
        skew_ms = abs(server_ms - local_ms)
        if skew_ms > 1000:
            return {"ok": False, "reason": "CLOCK_SKEW", "skew_ms": skew_ms}

        if self._position_mode():
            return {"ok": False, "reason": "HEDGE_MODE_NOT_AUTHORIZED"}

        cfg = self._symbol_config(symbol)
        leverage = int(cfg.get("leverage", -1))
        margin_type = str(cfg.get("marginType", "")).upper()
        if leverage != 1:
            return {"ok": False, "reason": "LEVERAGE_NOT_1X", "observed": leverage}
        if margin_type != "ISOLATED":
            return {
                "ok": False,
                "reason": "MARGIN_NOT_ISOLATED",
                "observed": margin_type,
            }

        taker_rate = self._commission_rate(symbol)
        if taker_rate > MAX_TAKER_RATE:
            return {
                "ok": False,
                "reason": "TAKER_FEE_ABOVE_FROZEN_STRESS_FLOOR",
                "observed": format(taker_rate, "f"),
                "max": format(MAX_TAKER_RATE, "f"),
            }

        open_orders = self._open_orders(symbol)
        if open_orders:
            return {"ok": False, "reason": "EXISTING_OPEN_ORDERS", "count": len(open_orders)}

        positions = self._position_risk(symbol)
        nonzero = []
        for row in positions:
            try:
                if Decimal(str(row.get("positionAmt", "0"))) != 0:
                    nonzero.append(row)
            except Exception:
                return {"ok": False, "reason": "POSITION_PARSE_FAILED"}
        if nonzero:
            return {"ok": False, "reason": "EXISTING_POSITION", "count": len(nonzero)}

        book = self.book_ticker(symbol)
        return {
            "ok": True,
            "clock_skew_ms": skew_ms,
            "leverage": leverage,
            "margin_type": margin_type,
            "hedge_mode": False,
            "taker_commission_rate": format(taker_rate, "f"),
            "spread_bps": format(book["spread_bps"], "f"),
            "open_orders": 0,
            "nonzero_positions": 0,
        }

    def test_market(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Decimal,
        reduce_only: bool,
        client_order_id: str,
    ) -> dict[str, Any]:
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": format(quantity, "f"),
            "reduceOnly": "true" if reduce_only else "false",
            "newClientOrderId": client_order_id,
        }
        return self._request("POST", "/fapi/v1/order/test", params, signed=True)

    def submit_market(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Decimal,
        reduce_only: bool,
        client_order_id: str,
    ) -> dict[str, Any]:
        existing = self.query_order_if_exists(symbol, client_order_id)
        if existing is not None:
            existing = dict(existing)
            existing["_idempotent_recovery"] = True
            return existing

        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": format(quantity, "f"),
            "reduceOnly": "true" if reduce_only else "false",
            "newClientOrderId": client_order_id,
            "newOrderRespType": "RESULT",
        }
        try:
            return self._request("POST", "/fapi/v1/order", params, signed=True)
        except ExecutionBlocked as first_error:
            try:
                recovered = self.query_order_if_exists(symbol, client_order_id)
            except ExecutionBlocked:
                raise first_error
            if recovered is not None:
                recovered = dict(recovered)
                recovered["_idempotent_recovery_after_submit_error"] = True
                return recovered
            raise first_error
