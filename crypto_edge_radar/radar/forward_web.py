from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
from typing import Any

from .bnb_launchpool_watcher import (
    BNBLaunchpoolForwardShadowWatcher,
    BinanceOfficialLaunchpoolSource,
)
from .config import Settings
from .evidence import build_evidence_store
from .strategies.bnb_launchpool_demand import BinanceSpotBNBBTCKlineFeed
from .strategies.tfg_donchian_regime_forward import MEXCSpotKlineFeed
from .tfg_forward_watcher import (
    TFGForwardShadowWatcher,
    latest_certifiable_signal_close_ms,
)


class CachingBinanceOfficialLaunchpoolSource(BinanceOfficialLaunchpoolSource):
    """Caches immutable detail responses in-process; the catalog itself is always refreshed."""

    def __init__(self, timeout: int = 15) -> None:
        super().__init__(timeout=timeout)
        self._detail_cache: dict[str, tuple[Any, bytes]] = {}

    def detail(self, article_code: str) -> tuple[Any, bytes]:
        cached = self._detail_cache.get(article_code)
        if cached is not None:
            return cached
        result = super().detail(article_code)
        self._detail_cache[article_code] = result
        return result


def _atomic_json_write(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(target)


class ForwardShadowRuntime:
    """Runs TFG and BNB as independent public-data shadow watchers over one evidence store."""

    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self.store = build_evidence_store(settings.db_path, settings.database_url)
        self.tfg = TFGForwardShadowWatcher(
            store=self.store,
            feed=MEXCSpotKlineFeed(timeout=settings.http_timeout),
        )
        self.bnb = BNBLaunchpoolForwardShadowWatcher(
            store=self.store,
            source=CachingBinanceOfficialLaunchpoolSource(timeout=settings.http_timeout),
            market=BinanceSpotBNBBTCKlineFeed(timeout=settings.http_timeout),
        )
        self.status_path = os.getenv("RADAR_FORWARD_STATUS", settings.status_path)
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {
            "health": "STARTING",
            "mode": "PUBLIC_SHADOW_ONLY",
            "evidence_backend": self.store.backend,
            "orders_created": False,
        }
        self._last_tfg_due: int | None = None

    def state(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._state))

    def _set_state(self, value: dict[str, Any]) -> None:
        with self._lock:
            self._state = value
        _atomic_json_write(self.status_path, value)

    def run_cycle(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        checked = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        errors: dict[str, str] = {}

        try:
            bnb_state = self.bnb.run_once(now_ms=now_ms)
        except Exception as exc:
            bnb_state = {"status": "FAIL_CLOSED", "error": f"{type(exc).__name__}:{exc}"}
            errors["bnb_launchpool"] = bnb_state["error"]

        due = latest_certifiable_signal_close_ms(now_ms)
        if due is not None and due != self._last_tfg_due:
            try:
                tfg_state = self.tfg.run_once(now_ms=now_ms)
                self._last_tfg_due = due
            except Exception as exc:
                tfg_state = {"status": "FAIL_CLOSED", "error": f"{type(exc).__name__}:{exc}"}
                errors["tfg"] = tfg_state["error"]
        else:
            tfg_state = {
                "status": "IDLE_NO_NEW_CERTIFIABLE_12H_BOUNDARY",
                "latest_seen_boundary_ms": self._last_tfg_due,
            }

        chain_ok, chain_detail = self.store.verify_chain()
        if not chain_ok:
            errors["evidence_chain"] = chain_detail

        state = {
            "health": "OK" if not errors else "DEGRADED_FAIL_CLOSED",
            "mode": "PUBLIC_SHADOW_ONLY",
            "checked_at_utc": checked,
            "version": "0.9",
            "evidence_backend": self.store.backend,
            "evidence_chain_ok": chain_ok,
            "evidence_chain_detail": chain_detail,
            "tfg": tfg_state,
            "bnb_launchpool": bnb_state,
            "errors": errors,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        self._set_state(state)
        print(json.dumps(state, sort_keys=True), flush=True)
        return state

    def run_loop(self, *, interval_seconds: float) -> None:
        # The old V0.5 canary start command passes 30s. Do not hammer official CMS;
        # clamp the public-shadow poll interval to a conservative two minutes.
        interval_seconds = max(float(interval_seconds), 120.0)
        while True:
            started = time.monotonic()
            try:
                self.run_cycle()
            except Exception as exc:
                fatal = {
                    "health": "DEGRADED_FAIL_CLOSED",
                    "mode": "PUBLIC_SHADOW_ONLY",
                    "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "evidence_backend": self.store.backend,
                    "errors": {"runtime": f"{type(exc).__name__}:{exc}"},
                    "authenticated_exchange_api_used": False,
                    "orders_created": False,
                    "exchange_mutation_performed": False,
                    "live_capital_enabled": False,
                }
                self._set_state(fatal)
                print(json.dumps(fatal, sort_keys=True), flush=True)
            elapsed = time.monotonic() - started
            time.sleep(max(1.0, interval_seconds - elapsed))


class _Handler(BaseHTTPRequestHandler):
    runtime: ForwardShadowRuntime

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/health", "/api/state", "/"):
            state = self.runtime.state()
            status = 200 if state.get("health") in ("OK", "STARTING") else 503
            self._send_json(status, state)
            return
        self._send_json(404, {"error": "not_found"})

    def log_message(self, format: str, *args: Any) -> None:
        return


def serve_forward_shadow(*, port: int, interval: float) -> int:
    settings = Settings.from_env()
    runtime = ForwardShadowRuntime(settings=settings)
    runtime.run_cycle()
    worker = threading.Thread(
        target=runtime.run_loop,
        kwargs={"interval_seconds": interval},
        name="forward-shadow-watchers",
        daemon=True,
    )
    worker.start()

    handler = type("ForwardShadowHandler", (_Handler,), {"runtime": runtime})
    server = ThreadingHTTPServer(("0.0.0.0", int(port)), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0
