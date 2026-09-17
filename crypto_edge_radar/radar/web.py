from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from typing import Any

from .engine import RadarEngine
from .service import PublicShadowService, read_status


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def assert_writable_storage(*paths: str | None) -> None:
    """Fail closed before runtime if configured local persistence paths are not writable."""
    usable = [path for path in paths if path]
    parents = {Path(path).expanduser().resolve().parent for path in usable}
    for parent in parents:
        parent.mkdir(parents=True, exist_ok=True)
        probe = parent / ".radar-write-probe"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            raise RuntimeError(f"radar storage is not writable: {parent}: {exc}") from exc


def build_handler(status_path: str):
    class RadarHandler(BaseHTTPRequestHandler):
        server_version = "CryptoEdgeRadar/0.5"

        def _send_json(self, code: int, payload: dict[str, Any]) -> None:
            body = _json_bytes(payload)
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - stdlib HTTP handler API
            path = self.path.split("?", 1)[0]
            if path not in {"/", "/health", "/status"}:
                self._send_json(404, {"error": "not_found"})
                return

            status = read_status(status_path)
            if path == "/health":
                health = status.get("health", "UNKNOWN")
                payload = {
                    "service": status.get("service", "CRYPTO_EDGE_RADAR"),
                    "version": status.get("version", "0.5"),
                    "mode": status.get("mode", "PUBLIC_SHADOW_ONLY"),
                    "health": health,
                    "cycle": status.get("cycle"),
                    "provider": status.get("provider"),
                    "evidence_backend": status.get("evidence_backend"),
                    "consecutive_failures": status.get("consecutive_failures"),
                }
                self._send_json(200 if health == "OK" else 503, payload)
                return

            self._send_json(200, status)

        def log_message(self, fmt: str, *args: Any) -> None:
            return

    return RadarHandler


def serve_render(
    *,
    engine: RadarEngine,
    status_path: str,
    notification_path: str,
    port: int,
    interval: float,
) -> int:
    if port <= 0 or port > 65535:
        raise ValueError("port must be between 1 and 65535")
    if interval < 5:
        raise ValueError("interval must be >= 5 seconds")

    # Postgres is validated by store construction. Only local files still need a
    # filesystem probe. SQLite adds its DB path to that probe automatically.
    assert_writable_storage(
        getattr(engine.store, "db_path", None), status_path, notification_path
    )
    runner = PublicShadowService(
        engine=engine,
        status_path=status_path,
        notification_path=notification_path,
    )

    # Produce a truthful initial status before the health endpoint starts serving.
    # A failed first cycle remains visible as HTTP 503 and the loop keeps retrying.
    runner.run_cycle()

    stop = threading.Event()

    def service_loop() -> None:
        while not stop.wait(interval):
            runner.run_cycle()

    worker = threading.Thread(target=service_loop, name="radar-service-loop", daemon=True)
    worker.start()

    server = ThreadingHTTPServer(("0.0.0.0", port), build_handler(status_path))
    server.daemon_threads = True
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        return 0
    finally:
        stop.set()
        # serve_forever runs in this thread, so calling shutdown() here would deadlock.
        server.server_close()
        worker.join(timeout=max(1.0, min(interval, 5.0)))
    return 0
