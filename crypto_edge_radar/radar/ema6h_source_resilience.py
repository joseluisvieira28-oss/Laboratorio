from __future__ import annotations

from copy import deepcopy
import json
import time
from typing import Any, Callable, Iterable

from .strategies.ema6h_50x200_regime_forward import (
    BinanceSpotKlineFeed,
    Candle,
    EMA6HRegimeSourceError,
    _duration_ms,
    _parse_kline,
    _validate_symbol,
)

OFFICIAL_BINANCE_SPOT_TRANSPORTS: tuple[tuple[str, str, str], ...] = (
    ("MARKET_DATA_ONLY", "REST", "https://data-api.binance.vision"),
    ("WS_API", "WEBSOCKET_API", "wss://ws-api.binance.com:443/ws-api/v3"),
    ("PRIMARY", "REST", "https://api.binance.com"),
    ("GCP", "REST", "https://api-gcp.binance.com"),
    ("API1", "REST", "https://api1.binance.com"),
    ("API2", "REST", "https://api2.binance.com"),
    ("API3", "REST", "https://api3.binance.com"),
    ("API4", "REST", "https://api4.binance.com"),
)

_RETRYABLE_TRANSPORT_MARKERS = (
    "HTTP Error 418",
    "HTTP 418",
    "HTTP Error 429",
    "HTTP 429",
    "HTTP Error 451",
    "HTTP 451",
    "HTTP Error 500",
    "HTTP Error 502",
    "HTTP Error 503",
    "HTTP Error 504",
    "HTTP 500",
    "HTTP 502",
    "HTTP 503",
    "HTTP 504",
    "URLError",
    "TimeoutError",
    "timed out",
    "Temporary failure",
    "Connection reset",
    "Remote end closed",
    "Name or service not known",
    "InvalidStatus",
    "opening handshake failed",
    "ConnectionClosed",
)


def is_retryable_binance_transport_error(exc: BaseException | str) -> bool:
    text = f"{type(exc).__name__}:{exc}" if isinstance(exc, BaseException) else str(exc)
    return any(marker in text for marker in _RETRYABLE_TRANSPORT_MARKERS)


class BinanceSpotWebSocketKlineFeed:
    """Official public Binance WebSocket API kline transport.

    It returns the same frozen Candle type and applies the same parser,
    timestamp, OHLC and pagination checks as the REST feed.
    """

    provider = "BINANCE_SPOT_PUBLIC_WS_API"
    endpoint_url = "wss://ws-api.binance.com:443/ws-api/v3"

    def __init__(
        self,
        timeout: int = 10,
        *,
        connect_fn: Callable[..., Any] | None = None,
    ) -> None:
        self.timeout = int(timeout)
        self._connect_fn = connect_fn

    def _connect(self):
        if self._connect_fn is not None:
            return self._connect_fn(
                self.endpoint_url,
                open_timeout=self.timeout,
                close_timeout=self.timeout,
            )
        from websockets.sync.client import connect

        return connect(
            self.endpoint_url,
            open_timeout=self.timeout,
            close_timeout=self.timeout,
        )

    def klines(
        self,
        symbol: str,
        interval: str,
        *,
        start_ms: int,
        end_ms: int,
        now_ms: int,
    ) -> list[Candle]:
        symbol = _validate_symbol(symbol)
        step = _duration_ms(interval)
        if start_ms >= end_ms:
            raise EMA6HRegimeSourceError("invalid kline range")
        cursor = start_ms - (start_ms % step)
        end_exclusive = end_ms - (end_ms % step)
        if end_exclusive <= cursor:
            return []

        rows: dict[int, Candle] = {}
        request_id = 0

        try:
            with self._connect() as ws:
                while cursor < end_exclusive:
                    request_id += 1
                    request = {
                        "id": f"ema6h-{request_id}",
                        "method": "klines",
                        "params": {
                            "symbol": symbol,
                            "interval": interval,
                            "startTime": cursor,
                            "endTime": end_exclusive - 1,
                            "limit": 1000,
                        },
                    }
                    ws.send(json.dumps(request, separators=(",", ":")))
                    raw = ws.recv(timeout=self.timeout)
                    response = json.loads(raw)
                    if not isinstance(response, dict):
                        raise EMA6HRegimeSourceError(
                            "Binance WebSocket API response is not an object"
                        )
                    if response.get("status") != 200:
                        raise EMA6HRegimeSourceError(
                            "Binance WebSocket API request rejected: "
                            + json.dumps(
                                {
                                    "status": response.get("status"),
                                    "error": response.get("error"),
                                },
                                sort_keys=True,
                            )
                        )
                    payload = response.get("result")
                    if not isinstance(payload, list):
                        raise EMA6HRegimeSourceError(
                            "Binance WebSocket API kline result is not a list"
                        )
                    if not payload:
                        break
                    parsed = [_parse_kline(item, interval) for item in payload]
                    for candle in parsed:
                        if (
                            start_ms <= candle.open_time < end_exclusive
                            and candle.close_time < now_ms
                        ):
                            rows[candle.open_time] = candle
                    last_open = max(candle.open_time for candle in parsed)
                    next_cursor = last_open + step
                    if next_cursor <= cursor:
                        raise EMA6HRegimeSourceError(
                            "Binance WebSocket API pagination did not advance"
                        )
                    cursor = next_cursor
        except EMA6HRegimeSourceError:
            raise
        except Exception as exc:
            raise EMA6HRegimeSourceError(
                f"Binance WebSocket transport unavailable: {type(exc).__name__}: {exc}"
            ) from exc

        return [rows[t] for t in sorted(rows)]


class ResilientBinanceSpotKlineFeed:
    """Transport-only failover around the frozen EMA6H Binance source.

    Failover is allowed only after transport availability failures. Semantic,
    schema, timestamp, OHLC, pagination or scientific validation failures stay
    fail-closed and cannot be hidden by another endpoint.
    """

    provider = "BINANCE_SPOT_PUBLIC_RESILIENT"
    path = "/api/v3/klines"

    def __init__(
        self,
        timeout: int = 10,
        *,
        transports: Iterable[tuple[str, str, str]] = OFFICIAL_BINANCE_SPOT_TRANSPORTS,
        cooldown_seconds: int = 60 * 60,
        rest_feed_cls: Callable[..., Any] = BinanceSpotKlineFeed,
        ws_feed_cls: Callable[..., Any] = BinanceSpotWebSocketKlineFeed,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.timeout = int(timeout)
        self.transports = tuple(
            (str(label), str(kind), str(url).rstrip("/"))
            for label, kind, url in transports
        )
        if not self.transports:
            raise ValueError("at least one official Binance transport is required")
        if len({(kind, url) for _, kind, url in self.transports}) != len(self.transports):
            raise ValueError("duplicate Binance transport")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")
        self.cooldown_seconds = int(cooldown_seconds)
        self._rest_feed_cls = rest_feed_cls
        self._ws_feed_cls = ws_feed_cls
        self._monotonic = monotonic
        self._blocked_until: dict[tuple[str, str], float] = {}
        self._preferred: tuple[str, str] | None = None
        self._last_receipt: dict[str, Any] = {
            "schema_version": "EMA6H_BINANCE_SOURCE_RESILIENCE_V0.2",
            "classification": "NOT_YET_USED",
            "provider": self.provider,
            "official_transport_count": len(self.transports),
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
            "science_changed": False,
            "payloads_exposed": False,
        }

    def _ordered_transports(self, now: float) -> list[tuple[str, str, str]]:
        active = [
            item
            for item in self.transports
            if self._blocked_until.get((item[1], item[2]), 0.0) <= now
        ]
        cooled = [
            item
            for item in self.transports
            if self._blocked_until.get((item[1], item[2]), 0.0) > now
        ]
        if self._preferred is not None:
            active.sort(
                key=lambda item: 0
                if (item[1], item[2]) == self._preferred
                else 1
            )
        return active + cooled

    def _feed_for(self, kind: str, url: str) -> Any:
        if kind == "REST":
            feed = self._rest_feed_cls(
                timeout=self.timeout,
                max_attempts=1,
                retry_backoff_seconds=0,
            )
            feed.base_url = url
            return feed
        if kind == "WEBSOCKET_API":
            feed = self._ws_feed_cls(timeout=self.timeout)
            feed.endpoint_url = url
            return feed
        raise ValueError(f"unsupported Binance transport kind: {kind}")

    def transport_receipt(self) -> dict[str, Any]:
        return deepcopy(self._last_receipt)

    def klines(
        self,
        symbol: str,
        interval: str,
        *,
        start_ms: int,
        end_ms: int,
        now_ms: int,
    ) -> list[Candle]:
        now = self._monotonic()
        attempted: list[str] = []
        retryable_failures: list[dict[str, str]] = []

        for label, kind, url in self._ordered_transports(now):
            key = (kind, url)
            if self._blocked_until.get(key, 0.0) > now:
                continue
            attempted.append(label)
            feed = self._feed_for(kind, url)
            try:
                rows = feed.klines(
                    symbol,
                    interval,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    now_ms=now_ms,
                )
            except Exception as exc:
                if not is_retryable_binance_transport_error(exc):
                    self._last_receipt = {
                        "schema_version": "EMA6H_BINANCE_SOURCE_RESILIENCE_V0.2",
                        "classification": "FAIL_CLOSED_SEMANTIC_SOURCE_ERROR",
                        "provider": self.provider,
                        "selected_transport": None,
                        "attempted_transports": attempted,
                        "retryable_failures": retryable_failures,
                        "semantic_failure_transport": label,
                        "semantic_failure": f"{type(exc).__name__}:{exc}",
                        "authenticated_exchange_api_used": False,
                        "orders_created": False,
                        "exchange_mutation_performed": False,
                        "live_capital_enabled": False,
                        "science_changed": False,
                        "payloads_exposed": False,
                    }
                    raise
                self._blocked_until[key] = now + self.cooldown_seconds
                retryable_failures.append(
                    {
                        "transport": label,
                        "kind": kind,
                        "error_class": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                continue

            self._preferred = key
            primary_label = self.transports[0][0]
            self._last_receipt = {
                "schema_version": "EMA6H_BINANCE_SOURCE_RESILIENCE_V0.2",
                "classification": (
                    "PRIMARY_TRANSPORT_PASS"
                    if label == primary_label
                    else "OFFICIAL_FALLBACK_TRANSPORT_PASS"
                ),
                "provider": self.provider,
                "selected_transport": label,
                "selected_kind": kind,
                "selected_url": url,
                "fallback_used": label != primary_label,
                "attempted_transports": attempted,
                "retryable_failures": retryable_failures,
                "symbol": symbol,
                "interval": interval,
                "row_count": len(rows),
                "authenticated_exchange_api_used": False,
                "orders_created": False,
                "exchange_mutation_performed": False,
                "live_capital_enabled": False,
                "science_changed": False,
                "payloads_exposed": False,
            }
            return rows

        self._last_receipt = {
            "schema_version": "EMA6H_BINANCE_SOURCE_RESILIENCE_V0.2",
            "classification": "ALL_OFFICIAL_TRANSPORTS_UNAVAILABLE_FAIL_CLOSED",
            "provider": self.provider,
            "selected_transport": None,
            "attempted_transports": attempted,
            "retryable_failures": retryable_failures,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
            "science_changed": False,
            "payloads_exposed": False,
        }
        detail = "; ".join(
            f"{row['transport']}={row['error_class']}:{row['error']}"
            for row in retryable_failures
        )
        raise EMA6HRegimeSourceError(
            "all official Binance transports unavailable"
            + (f": {detail}" if detail else "")
        )
