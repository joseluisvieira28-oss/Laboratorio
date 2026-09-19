from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Callable
from urllib.request import Request, urlopen


DEFAULT_RENDER_BASE_URL = "https://crypto-edge-radar-v05-canary.onrender.com"
DEFAULT_INTERVAL_SECONDS = 300.0
DEFAULT_TIMEOUT_SECONDS = 45
DEFAULT_MAX_ATTEMPTS = 2


class RenderSentinelError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def evaluate_remote_state(payload: dict[str, Any], *, http_status: int = 200) -> dict[str, Any]:
    safety = {
        "authenticated_exchange_api_used": bool(payload.get("authenticated_exchange_api_used")),
        "orders_created": bool(payload.get("orders_created")),
        "exchange_mutation_performed": bool(payload.get("exchange_mutation_performed")),
        "live_capital_enabled": bool(payload.get("live_capital_enabled")),
    }
    remote_health = str(payload.get("health") or "MISSING")
    evidence_backend = str(payload.get("evidence_backend") or "MISSING")
    evidence_chain_ok = payload.get("evidence_chain_ok") is True
    errors = payload.get("errors") or {}
    liveness = str((payload.get("runtime_liveness") or {}).get("status") or "MISSING")

    hard_fail_reasons: list[str] = []
    if int(http_status) != 200:
        hard_fail_reasons.append(f"http_status={http_status}")
    if remote_health != "OK":
        hard_fail_reasons.append(f"remote_health={remote_health}")
    if evidence_backend != "postgres":
        hard_fail_reasons.append(f"evidence_backend={evidence_backend}")
    if not evidence_chain_ok:
        hard_fail_reasons.append("evidence_chain_not_ok")
    if any(safety.values()):
        hard_fail_reasons.append("safety_flag_true")
    if errors:
        hard_fail_reasons.append("remote_errors_present")

    if hard_fail_reasons:
        status = "REMOTE_FAIL_CLOSED"
    elif liveness == "RECOVERED_GAP_REVIEW_REQUIRED":
        status = "REMOTE_REVIEW_REQUIRED"
    else:
        status = "OK"

    return {
        "status": status,
        "remote_health": remote_health,
        "evidence_backend": evidence_backend,
        "evidence_chain_ok": evidence_chain_ok,
        "runtime_liveness": liveness,
        "hard_fail_reasons": hard_fail_reasons,
        "safety": safety,
        "remote_errors": errors,
    }


class RenderSentinel:
    """Read-only PC sentinel for the canonical Render/Postgres shadow runtime."""

    def __init__(
        self,
        *,
        root: str = "data",
        base_url: str = DEFAULT_RENDER_BASE_URL,
        interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        fetcher: Callable[[str, int], tuple[int, dict[str, Any]]] | None = None,
    ) -> None:
        if interval_seconds < 60:
            raise ValueError("sentinel interval must be >= 60 seconds")
        if timeout_seconds <= 0:
            raise ValueError("timeout must be positive")
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self.root = Path(root)
        self.base_url = base_url.rstrip("/")
        self.interval_seconds = float(interval_seconds)
        self.timeout_seconds = int(timeout_seconds)
        self.max_attempts = int(max_attempts)
        self.fetcher = fetcher or self._default_fetch
        self.status_path = self.root / "render_sentinel_status.json"
        self.receipts_path = self.root / "render_sentinel_receipts.jsonl"

    @staticmethod
    def _default_fetch(url: str, timeout: int) -> tuple[int, dict[str, Any]]:
        req = Request(url, method="GET", headers={"User-Agent": "crypto-edge-radar/windows-sentinel-v014"})
        with urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise RenderSentinelError("Render health payload is not an object")
            return int(response.status), payload

    def probe_once(self) -> dict[str, Any]:
        checked_at = _utc_now()
        started = time.monotonic()
        last_exc: Exception | None = None
        url = self.base_url + "/health"

        for attempt in range(1, self.max_attempts + 1):
            try:
                http_status, payload = self.fetcher(url, self.timeout_seconds)
                evaluated = evaluate_remote_state(payload, http_status=http_status)
                result = {
                    **evaluated,
                    "checked_at_utc": checked_at,
                    "url": url,
                    "http_status": int(http_status),
                    "attempt": attempt,
                    "latency_ms": round((time.monotonic() - started) * 1000.0, 3),
                    "mode": "READ_ONLY_KEEPALIVE_AND_RECONCILIATION",
                    "orders_created": False,
                    "exchange_mutation_performed": False,
                    "live_capital_enabled": False,
                }
                break
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_attempts:
                    time.sleep(5.0)
        else:
            result = {
                "status": "REMOTE_UNREACHABLE",
                "checked_at_utc": checked_at,
                "url": url,
                "http_status": None,
                "attempt": self.max_attempts,
                "latency_ms": round((time.monotonic() - started) * 1000.0, 3),
                "error": f"{type(last_exc).__name__}:{last_exc}",
                "mode": "READ_ONLY_KEEPALIVE_AND_RECONCILIATION",
                "orders_created": False,
                "exchange_mutation_performed": False,
                "live_capital_enabled": False,
            }

        canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
        result["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
        _atomic_json(self.status_path, result)
        _append_jsonl(self.receipts_path, result)
        return result

    def run_forever(self) -> None:
        while True:
            self.probe_once()
            time.sleep(self.interval_seconds)
