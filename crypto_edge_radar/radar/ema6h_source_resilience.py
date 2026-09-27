from __future__ import annotations

from copy import deepcopy
import time
from typing import Any, Callable, Iterable

from .strategies.ema6h_50x200_regime_forward import (
    BinanceSpotKlineFeed,
    Candle,
    EMA6HRegimeSourceError,
)

# Official Binance Spot REST endpoints documented in binance-spot-api-docs.
# Scientific rules, symbols, intervals, boundaries and candle parsing remain
# delegated to the frozen EMA6H strategy module.
OFFICIAL_BINANCE_SPOT_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("MARKET_DATA_ONLY", "https://data-api.binance.vision"),
    ("PRIMARY", "https://api.binance.com"),
    ("GCP", "https://api-gcp.binance.com"),
    ("API1", "https://api1.binance.com"),
    ("API2", "https://api2.binance.com"),
    ("API3", "https://api3.binance.com"),
    ("API4", "https://api4.binance.com"),
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
)


def is_retryable_binance_transport_error(exc: BaseException | str) -> bool:
    text = str(exc)
    return any(marker in text for marker in _RETRYABLE_TRANSPORT_MARKERS)


class ResilientBinanceSpotKlineFeed:
    """Transport-only failover around the frozen Binance EMA6H candle feed.

    Failover is permitted only for transport availability errors. Any semantic,
    schema, timestamp, OHLC, pagination or scientific validation error remains
    fail-closed and is never hidden by trying another endpoint.
    """

    provider = "BINANCE_SPOT_PUBLIC_RESILIENT"
    path = "/api/v3/klines"

    def __init__(
        self,
        timeout: int = 10,
        *,
        endpoints: Iterable[tuple[str, str]] = OFFICIAL_BINANCE_SPOT_ENDPOINTS,
        cooldown_seconds: int = 60 * 60,
        base_feed_cls: Callable[..., Any] = BinanceSpotKlineFeed,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.timeout = int(timeout)
        self.endpoints = tuple((str(label), str(url).rstrip("/")) for label, url in endpoints)
        if not self.endpoints:
            raise ValueError("at least one official Binance endpoint is required")
        if len({url for _, url in self.endpoints}) != len(self.endpoints):
            raise ValueError("duplicate Binance endpoint URL")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")
        self.cooldown_seconds = int(cooldown_seconds)
        self._base_feed_cls = base_feed_cls
        self._monotonic = monotonic
        self._blocked_until: dict[str, float] = {}
        self._preferred_url: str | None = None
        self._last_receipt: dict[str, Any] = {
            "schema_version": "EMA6H_BINANCE_SOURCE_RESILIENCE_V0.1",
            "classification": "NOT_YET_USED",
            "provider": self.provider,
            "official_endpoint_count": len(self.endpoints),
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
            "science_changed": False,
            "payloads_exposed": False,
        }

    def _ordered_endpoints(self, now: float) -> list[tuple[str, str]]:
        active = [
            (label, url)
            for label, url in self.endpoints
            if self._blocked_until.get(url, 0.0) <= now
        ]
        cooled = [
            (label, url)
            for label, url in self.endpoints
            if self._blocked_until.get(url, 0.0) > now
        ]
        if self._preferred_url:
            active.sort(key=lambda x: 0 if x[1] == self._preferred_url else 1)
        return active + cooled

    def _feed_for(self, url: str) -> Any:
        feed = self._base_feed_cls(
            timeout=self.timeout,
            max_attempts=1,
            retry_backoff_seconds=0,
        )
        feed.base_url = url
        return feed

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

        for label, url in self._ordered_endpoints(now):
            if self._blocked_until.get(url, 0.0) > now:
                continue
            attempted.append(label)
            feed = self._feed_for(url)
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
                        "schema_version": "EMA6H_BINANCE_SOURCE_RESILIENCE_V0.1",
                        "classification": "FAIL_CLOSED_SEMANTIC_SOURCE_ERROR",
                        "provider": self.provider,
                        "selected_endpoint": None,
                        "attempted_endpoints": attempted,
                        "retryable_failures": retryable_failures,
                        "semantic_failure_endpoint": label,
                        "semantic_failure": f"{type(exc).__name__}:{exc}",
                        "authenticated_exchange_api_used": False,
                        "orders_created": False,
                        "exchange_mutation_performed": False,
                        "live_capital_enabled": False,
                        "science_changed": False,
                        "payloads_exposed": False,
                    }
                    raise
                self._blocked_until[url] = now + self.cooldown_seconds
                retryable_failures.append(
                    {
                        "endpoint": label,
                        "error_class": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                continue

            self._preferred_url = url
            self._last_receipt = {
                "schema_version": "EMA6H_BINANCE_SOURCE_RESILIENCE_V0.1",
                "classification": (
                    "PRIMARY_TRANSPORT_PASS"
                    if label == self.endpoints[0][0]
                    else "OFFICIAL_FALLBACK_TRANSPORT_PASS"
                ),
                "provider": self.provider,
                "selected_endpoint": label,
                "selected_base_url": url,
                "fallback_used": label != self.endpoints[0][0],
                "attempted_endpoints": attempted,
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
            "schema_version": "EMA6H_BINANCE_SOURCE_RESILIENCE_V0.1",
            "classification": "ALL_OFFICIAL_ENDPOINTS_UNAVAILABLE_FAIL_CLOSED",
            "provider": self.provider,
            "selected_endpoint": None,
            "attempted_endpoints": attempted,
            "retryable_failures": retryable_failures,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
            "science_changed": False,
            "payloads_exposed": False,
        }
        detail = "; ".join(
            f"{row['endpoint']}={row['error_class']}:{row['error']}"
            for row in retryable_failures
        )
        raise EMA6HRegimeSourceError(
            "all official Binance Spot endpoints unavailable"
            + (f": {detail}" if detail else "")
        )
