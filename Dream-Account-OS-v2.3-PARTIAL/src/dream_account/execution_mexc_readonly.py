from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import Request, urlopen


MEXC_SPOT_BASE = "https://api.mexc.com"
MAX_RECV_WINDOW_MS = 5_000
READ_ONLY_SIGNED_PATHS = frozenset(
    {
        "/api/v3/account",
        "/api/v3/openOrders",
        "/api/v3/order",
        "/api/v3/myTrades",
    }
)
PUBLIC_PATHS = frozenset({"/api/v3/time"})


class ReadOnlyMEXCError(RuntimeError):
    pass


class ReadOnlyPolicyViolation(ReadOnlyMEXCError):
    pass


class ReadOnlyTransport(Protocol):
    def get_json(self, url: str, headers: Mapping[str, str], timeout: float) -> Any:
        ...


class StdlibReadOnlyHTTP:
    """Minimal GET-only HTTP transport.

    There is intentionally no generic request(method=...) surface and no body.
    The execution layer cannot use this class to submit, amend, cancel, transfer,
    or withdraw anything.
    """

    def get_json(self, url: str, headers: Mapping[str, str], timeout: float) -> Any:
        request = Request(url=url, headers=dict(headers), method="GET")
        try:
            with urlopen(request, timeout=timeout) as response:  # nosec B310: HTTPS base is policy-pinned by client
                raw = response.read()
        except HTTPError as exc:
            raise ReadOnlyMEXCError(f"MEXC read-only HTTP error: {exc.code}") from exc
        except URLError as exc:
            raise ReadOnlyMEXCError("MEXC read-only transport unavailable") from exc
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReadOnlyMEXCError("MEXC read-only response was not valid JSON") from exc


@dataclass(frozen=True)
class SpotBalance:
    asset: str
    free: str
    locked: str


@dataclass(frozen=True)
class SpotAccount:
    account_type: str
    can_trade: bool
    can_withdraw: bool
    can_deposit: bool
    permissions: tuple[str, ...]
    balances: tuple[SpotBalance, ...]


@dataclass(frozen=True)
class SpotOrder:
    symbol: str
    order_id: str
    client_order_id: str
    status: str
    side: str
    order_type: str
    price: str
    original_quantity: str
    executed_quantity: str
    cumulative_quote_quantity: str
    created_time_ms: int | None
    updated_time_ms: int | None


@dataclass(frozen=True)
class SpotTrade:
    symbol: str
    trade_id: str
    order_id: str
    client_order_id: str | None
    price: str
    quantity: str
    quote_quantity: str
    commission: str
    commission_asset: str
    time_ms: int
    is_buyer: bool
    is_maker: bool


@dataclass(frozen=True)
class ReadOnlyReconciliationSnapshot:
    symbol: str
    observed_local_time_ms: int
    mexc_server_time_ms: int
    clock_skew_ms: int
    account: SpotAccount
    open_orders: tuple[SpotOrder, ...]
    queried_order: SpotOrder | None
    recent_trades: tuple[SpotTrade, ...]

    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class MEXCSpotReadOnlyClient:
    """Authenticated MEXC Spot reader with an immutable GET-only endpoint allow-list.

    Credentials are accepted in memory only; this class does not persist or log
    them. It is deliberately not wired into the production runtime in Gate K.
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        *,
        transport: ReadOnlyTransport | None = None,
        base_url: str = MEXC_SPOT_BASE,
        timeout: float = 10.0,
        recv_window_ms: int = MAX_RECV_WINDOW_MS,
        clock_ms: callable | None = None,
    ) -> None:
        if not access_key or not secret_key:
            raise ValueError("MEXC read-only credentials must be non-empty")
        if base_url.rstrip("/") != MEXC_SPOT_BASE:
            raise ReadOnlyPolicyViolation("Gate K pins authenticated MEXC reads to https://api.mexc.com")
        if recv_window_ms < 1 or recv_window_ms > MAX_RECV_WINDOW_MS:
            raise ValueError("recv_window_ms must be between 1 and 5000")
        if timeout <= 0 or timeout > 30:
            raise ValueError("timeout must be >0 and <=30 seconds")
        self._access_key = access_key
        self._secret_key = secret_key
        self._transport = transport or StdlibReadOnlyHTTP()
        self._base_url = MEXC_SPOT_BASE
        self._timeout = float(timeout)
        self._recv_window_ms = int(recv_window_ms)
        self._clock_ms = clock_ms or (lambda: int(time.time() * 1000))
        self._clock_offset_ms: int | None = None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(access_key=<redacted>, secret_key=<redacted>, "
            f"base_url={self._base_url!r}, recv_window_ms={self._recv_window_ms})"
        )

    @staticmethod
    def _validate_path(path: str, *, signed: bool) -> None:
        allowed = READ_ONLY_SIGNED_PATHS if signed else PUBLIC_PATHS
        if path not in allowed:
            raise ReadOnlyPolicyViolation(f"path is not in Gate K read-only allow-list: {path}")

    @staticmethod
    def _query(params: Mapping[str, Any]) -> str:
        pairs: list[tuple[str, str]] = []
        for key in sorted(params):
            value = params[key]
            if value is None:
                continue
            pairs.append((str(key), str(value)))
        return urlencode(pairs)

    def _signature(self, query: str) -> str:
        return hmac.new(
            self._secret_key.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _public_get(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        self._validate_path(path, signed=False)
        query = self._query(params or {})
        url = self._base_url + path + (f"?{query}" if query else "")
        return self._transport.get_json(
            url,
            {"Content-Type": "application/json"},
            self._timeout,
        )

    def _signed_get(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        self._validate_path(path, signed=True)
        if self._clock_offset_ms is None:
            self.sync_clock()
        signed_params = dict(params or {})
        signed_params["recvWindow"] = self._recv_window_ms
        signed_params["timestamp"] = self._clock_ms() + int(self._clock_offset_ms or 0)
        query = self._query(signed_params)
        signature = self._signature(query)
        url = f"{self._base_url}{path}?{query}&signature={signature}"
        return self._transport.get_json(
            url,
            {
                "X-MEXC-APIKEY": self._access_key,
                "Content-Type": "application/json",
            },
            self._timeout,
        )

    def sync_clock(self) -> int:
        before = self._clock_ms()
        payload = self._public_get("/api/v3/time")
        after = self._clock_ms()
        try:
            server = int(payload["serverTime"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ReadOnlyMEXCError("Malformed MEXC server-time response") from exc
        midpoint = before + ((after - before) // 2)
        self._clock_offset_ms = server - midpoint
        return self._clock_offset_ms

    @property
    def clock_offset_ms(self) -> int | None:
        return self._clock_offset_ms

    def account(self) -> SpotAccount:
        payload = self._signed_get("/api/v3/account")
        if not isinstance(payload, dict) or not isinstance(payload.get("balances"), list):
            raise ReadOnlyMEXCError("Malformed MEXC account response")
        balances: list[SpotBalance] = []
        try:
            for row in payload["balances"]:
                balances.append(
                    SpotBalance(
                        asset=str(row["asset"]),
                        free=str(row["free"]),
                        locked=str(row["locked"]),
                    )
                )
            permissions = tuple(str(value) for value in payload.get("permissions", []))
            return SpotAccount(
                account_type=str(payload.get("accountType", "")),
                can_trade=bool(payload.get("canTrade", False)),
                can_withdraw=bool(payload.get("canWithdraw", False)),
                can_deposit=bool(payload.get("canDeposit", False)),
                permissions=permissions,
                balances=tuple(balances),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ReadOnlyMEXCError("Malformed MEXC account fields") from exc

    @staticmethod
    def _parse_order(row: Mapping[str, Any]) -> SpotOrder:
        try:
            return SpotOrder(
                symbol=str(row["symbol"]),
                order_id=str(row["orderId"]),
                client_order_id=str(row.get("clientOrderId") or row.get("origClientOrderId") or ""),
                status=str(row["status"]),
                side=str(row["side"]),
                order_type=str(row["type"]),
                price=str(row.get("price", "0")),
                original_quantity=str(row.get("origQty", row.get("Qty", row.get("origOty", "0")))),
                executed_quantity=str(row.get("executedQty", "0")),
                cumulative_quote_quantity=str(row.get("cummulativeQuoteQty", "0")),
                created_time_ms=int(row["time"]) if row.get("time") is not None else None,
                updated_time_ms=int(row["updateTime"]) if row.get("updateTime") is not None else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ReadOnlyMEXCError("Malformed MEXC order response") from exc

    def open_orders(self, symbol: str) -> tuple[SpotOrder, ...]:
        if not symbol:
            raise ValueError("symbol is required for Gate K open-order reads")
        payload = self._signed_get("/api/v3/openOrders", {"symbol": symbol})
        if not isinstance(payload, list):
            raise ReadOnlyMEXCError("Malformed MEXC open-orders response")
        return tuple(self._parse_order(row) for row in payload)

    def query_order(
        self,
        symbol: str,
        *,
        order_id: str | None = None,
        client_order_id: str | None = None,
    ) -> SpotOrder:
        if not symbol:
            raise ValueError("symbol is required")
        if bool(order_id) == bool(client_order_id):
            raise ValueError("provide exactly one of order_id or client_order_id")
        params: dict[str, Any] = {"symbol": symbol}
        if order_id:
            params["orderId"] = order_id
        else:
            params["origClientOrderId"] = client_order_id
        payload = self._signed_get("/api/v3/order", params)
        if not isinstance(payload, dict):
            raise ReadOnlyMEXCError("Malformed MEXC order response")
        return self._parse_order(payload)

    def recent_trades(
        self,
        symbol: str,
        *,
        order_id: str | None = None,
        limit: int = 100,
    ) -> tuple[SpotTrade, ...]:
        if not symbol:
            raise ValueError("symbol is required")
        if limit < 1 or limit > 100:
            raise ValueError("MEXC myTrades limit must be between 1 and 100")
        params: dict[str, Any] = {"symbol": symbol, "limit": limit}
        if order_id:
            params["orderId"] = order_id
        payload = self._signed_get("/api/v3/myTrades", params)
        if not isinstance(payload, list):
            raise ReadOnlyMEXCError("Malformed MEXC trade-list response")
        rows: list[SpotTrade] = []
        try:
            for row in payload:
                rows.append(
                    SpotTrade(
                        symbol=str(row["symbol"]),
                        trade_id=str(row["id"]),
                        order_id=str(row["orderId"]),
                        client_order_id=(str(row["clientOrderId"]) if row.get("clientOrderId") is not None else None),
                        price=str(row["price"]),
                        quantity=str(row["qty"]),
                        quote_quantity=str(row["quoteQty"]),
                        commission=str(row.get("commission", "0")),
                        commission_asset=str(row.get("commissionAsset", "")),
                        time_ms=int(row["time"]),
                        is_buyer=bool(row.get("isBuyer", False)),
                        is_maker=bool(row.get("isMaker", row.get("isBuyerMaker", False))),
                    )
                )
        except (KeyError, TypeError, ValueError) as exc:
            raise ReadOnlyMEXCError("Malformed MEXC trade fields") from exc
        return tuple(rows)

    def reconciliation_snapshot(
        self,
        symbol: str,
        *,
        order_id: str | None = None,
        client_order_id: str | None = None,
        trade_limit: int = 100,
    ) -> ReadOnlyReconciliationSnapshot:
        offset = self.sync_clock()
        observed = self._clock_ms()
        account = self.account()
        open_orders = self.open_orders(symbol)
        queried_order: SpotOrder | None = None
        if order_id or client_order_id:
            queried_order = self.query_order(
                symbol,
                order_id=order_id,
                client_order_id=client_order_id,
            )
        trades = self.recent_trades(symbol, order_id=order_id, limit=trade_limit)
        return ReadOnlyReconciliationSnapshot(
            symbol=symbol,
            observed_local_time_ms=observed,
            mexc_server_time_ms=observed + offset,
            clock_skew_ms=offset,
            account=account,
            open_orders=open_orders,
            queried_order=queried_order,
            recent_trades=trades,
        )


def signed_query_components(url: str) -> tuple[str, dict[str, str]]:
    """Test/audit helper: returns path and query mapping without exposing secrets."""
    split = urlsplit(url)
    return split.path, dict(parse_qsl(split.query, keep_blank_values=True))
