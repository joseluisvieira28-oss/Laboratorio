from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

OFFICIAL_BINANCE_SPOT_BASE_URLS = (
    "https://data-api.binance.vision",
    "https://api.binance.com",
    "https://api-gcp.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
    "https://api4.binance.com",
)
KLINES_PATH = "/api/v3/klines"
RETRYABLE_HTTP_CODES = {418, 429, 500, 502, 503, 504}


class BinancePublicSourceUnavailable(RuntimeError):
    pass


class BinancePublicSourceDivergence(RuntimeError):
    pass


@dataclass(frozen=True)
class EndpointObservation:
    base_url: str
    status: str
    row_count: int | None = None
    canonical_sha256: str | None = None
    http_code: int | None = None
    error_class: str | None = None


def canonical_kline_rows(payload: Any) -> list[list[Any]]:
    if not isinstance(payload, list):
        raise BinancePublicSourceDivergence("kline payload is not a list")
    out: list[list[Any]] = []
    for row in payload:
        if not isinstance(row, list) or len(row) < 7:
            raise BinancePublicSourceDivergence("invalid kline row")
        # EMA6H science consumes only open time, OHLC, volume and close time.
        out.append(
            [
                int(row[0]),
                str(row[1]),
                str(row[2]),
                str(row[3]),
                str(row[4]),
                str(row[5]),
                int(row[6]),
            ]
        )
    return out


def canonical_kline_sha256(payload: Any) -> str:
    body = json.dumps(
        canonical_kline_rows(payload),
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


class BinanceOfficialKlineTransport:
    """Public-only resilient transport across Binance-documented Spot hosts.

    No API key, signature, account endpoint, order endpoint, or exchange
    mutation is supported by this class.
    """

    provider = "BINANCE_SPOT_PUBLIC_OFFICIAL_FAILOVER_V0.1"

    def __init__(
        self,
        *,
        timeout: int = 10,
        max_attempts_per_host: int = 1,
        retry_backoff_seconds: float = 0.25,
        base_urls: tuple[str, ...] = OFFICIAL_BINANCE_SPOT_BASE_URLS,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        if max_attempts_per_host < 1:
            raise ValueError("max_attempts_per_host must be >= 1")
        self.timeout = timeout
        self.max_attempts_per_host = max_attempts_per_host
        self.retry_backoff_seconds = retry_backoff_seconds
        self.base_urls = tuple(base_urls)
        self.opener = opener
        self.last_success_base_url: str | None = None
        self.last_observations: list[EndpointObservation] = []

    def _request(self, base_url: str, query: dict[str, Any]) -> Any:
        url = f"{base_url}{KLINES_PATH}?{urlencode(query)}"
        req = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/ema6h-source-resilience-v0.1"},
        )
        with self.opener(req, timeout=self.timeout) as response:
            if response.status != 200:
                raise BinancePublicSourceUnavailable(
                    f"Binance public HTTP {response.status}"
                )
            return json.loads(response.read().decode("utf-8"))

    def get_klines(self, query: dict[str, Any]) -> Any:
        observations: list[EndpointObservation] = []
        last_error: Exception | None = None

        for base_url in self.base_urls:
            for attempt in range(1, self.max_attempts_per_host + 1):
                try:
                    payload = self._request(base_url, query)
                    rows = canonical_kline_rows(payload)
                    observations.append(
                        EndpointObservation(
                            base_url=base_url,
                            status="PASS",
                            row_count=len(rows),
                            canonical_sha256=canonical_kline_sha256(payload),
                        )
                    )
                    self.last_success_base_url = base_url
                    self.last_observations = observations
                    return payload
                except HTTPError as exc:
                    last_error = exc
                    observations.append(
                        EndpointObservation(
                            base_url=base_url,
                            status=(
                                "RETRYABLE_HTTP"
                                if exc.code in RETRYABLE_HTTP_CODES
                                else "NON_RETRYABLE_HTTP"
                            ),
                            http_code=int(exc.code),
                            error_class=type(exc).__name__,
                        )
                    )
                    if exc.code not in RETRYABLE_HTTP_CODES:
                        self.last_observations = observations
                        raise BinancePublicSourceUnavailable(
                            f"non-retryable Binance public HTTP {exc.code}"
                        ) from exc
                except Exception as exc:
                    last_error = exc
                    observations.append(
                        EndpointObservation(
                            base_url=base_url,
                            status="TRANSPORT_ERROR",
                            error_class=type(exc).__name__,
                        )
                    )
                if (
                    attempt < self.max_attempts_per_host
                    and self.retry_backoff_seconds
                ):
                    time.sleep(self.retry_backoff_seconds * attempt)

        self.last_observations = observations
        raise BinancePublicSourceUnavailable(
            "all official Binance public kline hosts unavailable: "
            + (type(last_error).__name__ if last_error else "unknown")
        ) from last_error

    def equivalence_probe(
        self,
        query: dict[str, Any],
        *,
        minimum_matching_hosts: int = 2,
    ) -> dict[str, Any]:
        observations: list[EndpointObservation] = []
        successful: list[EndpointObservation] = []

        for base_url in self.base_urls:
            try:
                payload = self._request(base_url, query)
                obs = EndpointObservation(
                    base_url=base_url,
                    status="PASS",
                    row_count=len(canonical_kline_rows(payload)),
                    canonical_sha256=canonical_kline_sha256(payload),
                )
                successful.append(obs)
                observations.append(obs)
            except HTTPError as exc:
                observations.append(
                    EndpointObservation(
                        base_url=base_url,
                        status="HTTP_ERROR",
                        http_code=int(exc.code),
                        error_class=type(exc).__name__,
                    )
                )
            except Exception as exc:
                observations.append(
                    EndpointObservation(
                        base_url=base_url,
                        status="TRANSPORT_ERROR",
                        error_class=type(exc).__name__,
                    )
                )

        hashes = {x.canonical_sha256 for x in successful}
        passed = len(successful) >= minimum_matching_hosts and len(hashes) == 1
        classification = (
            "PASS_OFFICIAL_HOST_KLINE_EQUIVALENCE"
            if passed
            else (
                "FAIL_CLOSED_OFFICIAL_HOST_DIVERGENCE"
                if len(hashes) > 1
                else "INSUFFICIENT_RESPONDING_OFFICIAL_HOSTS"
            )
        )
        return {
            "schema_version": "EMA6H_BINANCE_SOURCE_RESILIENCE_V0.1",
            "classification": classification,
            "pass": passed,
            "minimum_matching_hosts": minimum_matching_hosts,
            "successful_hosts": len(successful),
            "matching_sha256": next(iter(hashes)) if len(hashes) == 1 else None,
            "observations": [x.__dict__ for x in observations],
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "science_changed": False,
        }
