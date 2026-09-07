from __future__ import annotations

import json
import random
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from statistics import median
from typing import Any


class ReliableDataError(RuntimeError):
    pass


@dataclass
class EndpointHealth:
    request_count: int = 0
    successes: int = 0
    http_4xx: int = 0
    http_5xx: int = 0
    timeouts: int = 0
    retries: int = 0
    consecutive_failures: int = 0
    circuit_open_until: float = 0.0
    last_successful_snapshot: str | None = None
    latencies_ms: list[float] = field(default_factory=list)

    def report(self) -> dict[str, Any]:
        ordered = sorted(self.latencies_ms)
        p95_index = max(0, int(len(ordered) * 0.95) - 1)
        return {
            "request_count": self.request_count,
            "success_rate": round(self.successes / self.request_count * 100, 2) if self.request_count else 0.0,
            "latency_p50_ms": round(median(ordered), 2) if ordered else None,
            "latency_p95_ms": round(ordered[p95_index], 2) if ordered else None,
            "HTTP_4xx": self.http_4xx,
            "HTTP_5xx": self.http_5xx,
            "timeouts": self.timeouts,
            "retries": self.retries,
            "last_successful_snapshot": self.last_successful_snapshot,
            "circuit_open": time.monotonic() < self.circuit_open_until,
        }


class ReliableHTTP:
    def __init__(self, connect_timeout: float = 4, read_timeout: float = 8, max_retries: int = 3, backoff_base: float = 0.25, circuit_threshold: int = 4, circuit_cooldown: float = 30):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.circuit_threshold = circuit_threshold
        self.circuit_cooldown = circuit_cooldown
        self.health: dict[str, EndpointHealth] = defaultdict(EndpointHealth)
        self.cache: dict[str, tuple[float, Any]] = {}

    def get_json(self, bases: list[str], path: str, params: dict[str, Any] | None = None, cache_ttl: float = 0) -> Any:
        query = urllib.parse.urlencode(params or {})
        cache_key = f"{path}?{query}"
        cached = self.cache.get(cache_key)
        if cached and time.monotonic() - cached[0] <= cache_ttl:
            return cached[1]
        errors = []
        for base in bases:
            endpoint = urllib.parse.urlparse(base).netloc
            state = self.health[endpoint]
            if time.monotonic() < state.circuit_open_until:
                errors.append(f"{endpoint}: circuit open")
                continue
            url = f"{base}{path}" + (f"?{query}" if query else "")
            for attempt in range(self.max_retries + 1):
                state.request_count += 1
                started = time.monotonic()
                request = urllib.request.Request(url, headers={"User-Agent": "DreamAccountOS/2.3", "Accept": "application/json"})
                try:
                    with urllib.request.urlopen(request, timeout=self.connect_timeout, context=ssl.create_default_context()) as response:
                        if getattr(response, "fp", None) and getattr(response.fp, "raw", None) and getattr(response.fp.raw, "_sock", None):
                            response.fp.raw._sock.settimeout(self.read_timeout)
                        payload = response.read()
                        status = response.status
                    if status >= 400:
                        raise urllib.error.HTTPError(url, status, "HTTP error", {}, None)
                    data = json.loads(payload.decode("utf-8"))
                    latency = (time.monotonic() - started) * 1000
                    state.latencies_ms.append(latency)
                    state.successes += 1
                    state.consecutive_failures = 0
                    state.last_successful_snapshot = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    if cache_ttl:
                        self.cache[cache_key] = (time.monotonic(), data)
                    return data
                except urllib.error.HTTPError as exc:
                    (setattr(state, "http_4xx", state.http_4xx + 1) if 400 <= exc.code < 500 else setattr(state, "http_5xx", state.http_5xx + 1))
                    retryable = exc.code == 429 or exc.code >= 500
                    errors.append(f"{endpoint}: HTTP {exc.code}")
                    if not retryable:
                        break
                except (TimeoutError, socket.timeout) as exc:
                    state.timeouts += 1
                    errors.append(f"{endpoint}: timeout {exc}")
                except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
                    errors.append(f"{endpoint}: {exc}")
                state.consecutive_failures += 1
                if attempt < self.max_retries:
                    state.retries += 1
                    time.sleep(self.backoff_base * (2**attempt) + random.uniform(0, self.backoff_base))
            if state.consecutive_failures >= self.circuit_threshold:
                state.circuit_open_until = time.monotonic() + self.circuit_cooldown
        raise ReliableDataError("; ".join(errors) or "no healthy endpoint")

    def report(self) -> dict[str, Any]:
        return {endpoint: state.report() for endpoint, state in self.health.items()}
