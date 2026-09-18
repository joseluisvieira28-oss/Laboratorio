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

BASE_URL = "https://fapi.binance.com"
MAX_TAKER_RATE = Decimal("0.0005")


class BinanceTradingError(RuntimeError):
    pass


class BinanceUSDMTradingClient:
    name = "BINANCE_USDM"

    def __init__(self, *, timeout: int = 10) -> None:
        self.api_key = os.getenv("BINANCE_API_KEY", "").strip()
        self.api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
        self.timeout = timeout
        if not self.api_key or not self.api_secret:
            raise BinanceTradingError("BINANCE_API_KEY / BINANCE_API_SECRET not configured")

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        signed: bool = False,
    ) -> Any:
        payload = dict(params or {})
        headers = {"User-Agent": "crypto-edge-radar-ced1d0031-microlive/0.2"}
        if signed:
            payload["timestamp"] = int(time.time() * 1000)
            payload.setdefault("recvWindow", 5000)
            query = urlencode(payload)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            query += "&signature=" + signature
            headers["X-MBX-APIKEY"] = self.api_key
        else:
            query = urlencode(payload)

        url = BASE_URL + path + (("?" + query) if query else "")
        request = Request(url, method=method, headers=headers)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            raise BinanceTradingError(f"Binance HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise BinanceTradingError(f"Binance network error: {exc}") from exc
        return json.loads(raw) if raw else {}

    def public_time(self) -> int:
        return int(self._request("GET", "/fapi/v1/time")["serverTime"])

    def book_ticker(self, symbol: str) -> dict[str, Decimal]:
        row = self._request("GET", "/fapi/v1/ticker/bookTicker", {"symbol": symbol})
        bid = Decimal(str(row["bidPrice"]))
        ask = Decimal(str(row["askPrice"]))
        if bid <= 0 or ask <= 0 or ask < bid:
            raise BinanceTradingError("invalid Binance book ticker")
        mid = (bid + ask) / Decimal("2")
        return {
            "bid": bid,
            "ask": ask,
            "mid": mid,
            "spread_bps": (ask - bid) / mid * Decimal("10000"),
        }

    def market_rules(self, symbol: str) -> dict[str, Decimal]:
        info = self._request("GET", "/fapi/v1/exchangeInfo")
        rows = [row for row in info.get("symbols", []) if row.get("symbol") == symbol]
        if len(rows) != 1:
            raise BinanceTradingError("symbol missing/ambiguous in exchangeInfo")
        filters = {row["filterType"]: row for row in rows[0].get("filters", [])}
        lot = filters.get("MARKET_LOT_SIZE") or filters.get("LOT_SIZE")
        if not lot:
            raise BinanceTradingError("market lot-size filter missing")
        min_notional = Decimal("0")
        nf = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL")
        if nf:
            min_notional = Decimal(str(nf.get("notional") or nf.get("minNotional") or "0"))
        return {
            "step_size": Decimal(str(lot["stepSize"])),
            "min_qty": Decimal(str(lot["minQty"])),
            "min_notional": min_notional,
        }

    def account_status(self) -> dict[str, Any]:
        row = self._request("GET", "/fapi/v2/account", signed=True)
        if row.get("canTrade") is not True:
            raise BinanceTradingError("account reports canTrade=false")
        return row

    def position_mode_is_hedged(self) -> bool:
        row = self._request("GET", "/fapi/v1/positionSide/dual", signed=True)
        return bool(row.get("dualSidePosition"))

    def position_risk(self, symbol: str) -> list[dict[str, Any]]:
        rows = self._request("GET", "/fapi/v3/positionRisk", {"symbol": symbol}, signed=True)
        return rows if isinstance(rows, list) else [rows]

    def open_orders(self, symbol: str) -> list[dict[str, Any]]:
        rows = self._request("GET", "/fapi/v1/openOrders", {"symbol": symbol}, signed=True)
        return rows if isinstance(rows, list) else []

    def taker_commission_rate(self, symbol: str) -> Decimal:
        row = self._request("GET", "/fapi/v1/commissionRate", {"symbol": symbol}, signed=True)
        return Decimal(str(row["takerCommissionRate"]))

    def query_order(self, symbol: str, client_order_id: str) -> dict[str, Any] | None:
        try:
            return self._request(
                "GET",
                "/fapi/v1/order",
                {"symbol": symbol, "origClientOrderId": client_order_id},
                signed=True,
            )
        except BinanceTradingError as exc:
            compact = str(exc).replace(" ", "")
            if '"code":-2013' in compact:
                return None
            raise

    def preflight(self, symbol: str) -> dict[str, Any]:
        self.account_status()

        server_ms = self.public_time()
        skew_ms = abs(server_ms - int(time.time() * 1000))
        if skew_ms > 1000:
            return {"ok": False, "reason": "CLOCK_SKEW", "skew_ms": skew_ms}

        if self.position_mode_is_hedged():
            return {"ok": False, "reason": "HEDGE_MODE_NOT_AUTHORIZED"}

        positions = self.position_risk(symbol)
        if len(positions) != 1:
            return {"ok": False, "reason": "POSITION_RISK_AMBIGUOUS", "rows": len(positions)}
        row = positions[0]

        leverage = int(row.get("leverage", -1))
        margin_type = str(row.get("marginType", "")).upper()
        if leverage != 1:
            return {"ok": False, "reason": "LEVERAGE_NOT_1X", "observed": leverage}
        if margin_type != "ISOLATED":
            return {"ok": False, "reason": "MARGIN_NOT_ISOLATED", "observed": margin_type}

        if Decimal(str(row.get("positionAmt", "0"))) != 0:
            return {"ok": False, "reason": "EXISTING_POSITION"}

        orders = self.open_orders(symbol)
        if orders:
            return {"ok": False, "reason": "EXISTING_OPEN_ORDERS", "count": len(orders)}

        taker = self.taker_commission_rate(symbol)
        if taker > MAX_TAKER_RATE:
            return {
                "ok": False,
                "reason": "TAKER_FEE_ABOVE_5_BPS",
                "observed": format(taker, "f"),
            }

        book = self.book_ticker(symbol)
        return {
            "ok": True,
            "clock_skew_ms": skew_ms,
            "leverage": leverage,
            "margin_type": margin_type,
            "hedge_mode": False,
            "taker_commission_rate": format(taker, "f"),
            "spread_bps": format(book["spread_bps"], "f"),
        }

    def test_market(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Decimal,
        reduce_only: bool,
        client_order_id: str,
    ) -> Any:
        return self._request(
            "POST",
            "/fapi/v1/order/test",
            {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": format(quantity, "f"),
                "reduceOnly": "true" if reduce_only else "false",
                "newClientOrderId": client_order_id,
            },
            signed=True,
        )

    def submit_market(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Decimal,
        reduce_only: bool,
        client_order_id: str,
    ) -> dict[str, Any]:
        existing = self.query_order(symbol, client_order_id)
        if existing is not None:
            out = dict(existing)
            out["_idempotent_recovery"] = True
            return out

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
        except BinanceTradingError as first_error:
            try:
                recovered = self.query_order(symbol, client_order_id)
            except BinanceTradingError:
                raise first_error
            if recovered is not None:
                out = dict(recovered)
                out["_idempotent_recovery_after_submit_error"] = True
                return out
            raise first_error

    def user_trades(self, symbol: str, *, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
        rows = self._request(
            "GET",
            "/fapi/v1/userTrades",
            {"symbol": symbol, "startTime": start_ms, "endTime": end_ms, "limit": 1000},
            signed=True,
        )
        return rows if isinstance(rows, list) else []

    def funding_income(self, symbol: str, *, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
        rows = self._request(
            "GET",
            "/fapi/v1/income",
            {
                "symbol": symbol,
                "incomeType": "FUNDING_FEE",
                "startTime": start_ms,
                "endTime": end_ms,
                "limit": 1000,
            },
            signed=True,
        )
        return rows if isinstance(rows, list) else []
