from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import shutil
import socket
import sqlite3
import ssl
import stat
import threading
import time
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .collector import MEXCDataCollector
from .config import Settings
from .database import Journal
from .live_engine import DreamAccountEngine
from .mexc_client import MEXCClient


logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger("dream-account")
RESCUE_ROOT = Path("/var/data")
RESCUE_DB_NAME = "dream_account.sqlite3"
RESCUE_MIN_FREE_BYTES = 128 * 1024 * 1024
MAX_OPERATIONAL_SNAPSHOTS = 500_000
FORCE_MAINTENANCE_ENV = "DREAM_FORCE_MAINTENANCE"
RESCUE_TOKEN: str | None = None
STATE = {
    "status": "BOOTING",
    "rescue_mode": False,
    "collector_paused": False,
    "execution": "NONEXISTENT",
    "expectancy": "INSUFFICIENT SAMPLE",
    "scan_iteration": 0,
}


class RescueRequired(RuntimeError):
    pass


def log_event(event: str, **fields) -> None:
    LOGGER.info(json.dumps({"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, **fields}, sort_keys=True, default=str))


def _disk_usage(root: Path | None = None) -> dict[str, int]:
    target = root or RESCUE_ROOT
    usage = shutil.disk_usage(target)
    return {"total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free}


def _maintenance_forced() -> bool:
    return os.getenv(FORCE_MAINTENANCE_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _should_enter_rescue_mode(root: Path | None = None) -> bool:
    return _maintenance_forced() or _disk_usage(root)["free_bytes"] < RESCUE_MIN_FREE_BYTES


def _activate_rescue_mode(root: Path | None = None, reason: str | None = None) -> None:
    global RESCUE_TOKEN
    target = root or RESCUE_ROOT
    RESCUE_TOKEN = secrets.token_urlsafe(32)
    usage = _disk_usage(target)
    state_reason = reason or (
        f"Maintenance forced by {FORCE_MAINTENANCE_ENV}"
        if _maintenance_forced()
        else "Persistent disk free space below rescue threshold"
    )
    STATE.update({
        "status": "RESCUE_MODE",
        "rescue_mode": True,
        "collector_paused": True,
        "execution": "NONEXISTENT",
        "top_3": [],
        "data_coverage": None,
        "last_error": state_reason,
        "disk": usage,
    })
    # The token is intentionally emitted once to Render's private service log.
    log_event("rescue_mode_entered", rescue_token=RESCUE_TOKEN, root=str(target), reason=state_reason,
              threshold_bytes=RESCUE_MIN_FREE_BYTES, **usage)


def _require_storage_headroom(root: Path | None = None) -> None:
    if _maintenance_forced():
        raise RescueRequired(f"Maintenance forced by {FORCE_MAINTENANCE_ENV}")
    usage = _disk_usage(root)
    if usage["free_bytes"] < RESCUE_MIN_FREE_BYTES:
        raise RescueRequired("Persistent disk free space below rescue threshold")


def _is_authorized(token: str | None) -> bool:
    return bool(RESCUE_TOKEN and token and hmac.compare_digest(RESCUE_TOKEN, token))


def _safe_rescue_file(raw_path: str, root: Path | None = None) -> Path:
    target_root = (root or RESCUE_ROOT).resolve(strict=True)
    relative = Path(raw_path)
    if not raw_path or relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError("invalid path")
    candidate = target_root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("symlinks are not allowed")
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(target_root)
    except ValueError as exc:
        raise ValueError("path escapes rescue root") from exc
    metadata = resolved.stat(follow_symlinks=False)
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("path is not a regular file")
    return resolved


def _inventory(root: Path | None = None) -> dict:
    target_root = (root or RESCUE_ROOT).resolve(strict=True)
    files: list[dict] = []
    for directory, dirs, names in os.walk(target_root, followlinks=False):
        base = Path(directory)
        dirs[:] = sorted(name for name in dirs if not (base / name).is_symlink())
        for name in sorted(names):
            path = base / name
            if path.is_symlink():
                continue
            metadata = path.stat(follow_symlinks=False)
            if not stat.S_ISREG(metadata.st_mode):
                continue
            files.append({
                "path": path.relative_to(target_root).as_posix(),
                "size_bytes": metadata.st_size,
                "mtime_utc": datetime.fromtimestamp(metadata.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
            })
    return {"root": str(target_root), "disk": _disk_usage(target_root), "files": files}


def _sqlite_integrity(root: Path | None = None) -> dict:
    target_root = root or RESCUE_ROOT
    database = _safe_rescue_file(RESCUE_DB_NAME, target_root)
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        rows = [row[0] for row in connection.execute("PRAGMA integrity_check").fetchall()]
        return {
            "path": database.relative_to(target_root.resolve(strict=True)).as_posix(),
            "open_mode": "ro",
            "query_only": True,
            "journal_mode": journal_mode,
            "integrity_check": rows,
            "ok": rows == ["ok"],
        }
    finally:
        connection.close()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


async def _ws_handshake(name: str, uri: str) -> dict:
    import websockets
    started = time.perf_counter()
    try:
        async with websockets.connect(uri, open_timeout=8, close_timeout=2, ping_interval=None):
            result = {"status": "PASS", "latency_ms": round((time.perf_counter()-started)*1000, 2)}
            log_event("websocket_connect", stream=name, **result)
            return result
    except Exception as exc:
        result = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        log_event("websocket_disconnect", stream=name, **result)
        return result


def infrastructure_diagnostic(client: MEXCClient) -> dict:
    report = {"dns": {}, "tls": {}, "rest": {}, "websocket": {}}
    for host in ("api.mexc.com", "contract.mexc.com", "wbs-api.mexc.com"):
        try:
            report["dns"][host] = {"status": "PASS", "addresses": sorted({x[4][0] for x in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})[:4]}
        except Exception as exc:
            report["dns"][host] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    for host in ("api.mexc.com", "contract.mexc.com"):
        started = time.perf_counter()
        try:
            with socket.create_connection((host, 443), timeout=5) as raw:
                with ssl.create_default_context().wrap_socket(raw, server_hostname=host) as secured:
                    report["tls"][host] = {"status": "PASS", "version": secured.version(), "latency_ms": round((time.perf_counter()-started)*1000, 2)}
        except Exception as exc:
            report["tls"][host] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    try:
        started = time.perf_counter(); count = len(client.tickers_24h())
        report["rest"]["spot"] = {"status": "PASS", "rows": count, "latency_ms": round((time.perf_counter()-started)*1000, 2)}
    except Exception as exc:
        report["rest"]["spot"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    try:
        started = time.perf_counter(); count = len(client.futures_tickers())
        report["rest"]["futures"] = {"status": "PASS", "rows": count, "latency_ms": round((time.perf_counter()-started)*1000, 2)}
    except Exception as exc:
        report["rest"]["futures"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    async def both():
        return await asyncio.gather(_ws_handshake("spot", "wss://wbs-api.mexc.com/ws"), _ws_handshake("futures", "wss://contract.mexc.com/edge"))
    spot, futures = asyncio.run(both())
    report["websocket"] = {"spot": spot, "futures": futures}
    return report


class HealthHandler(BaseHTTPRequestHandler):
    def _json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, sort_keys=True, default=str).encode()
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _query_path(self) -> str:
        values = parse_qs(urlsplit(self.path).query, keep_blank_values=True).get("path", [])
        if len(values) != 1:
            raise ValueError("exactly one path parameter is required")
        return values[0]

    def do_GET(self):
        route = urlsplit(self.path).path
        if route in {"/", "/health"}:
            self._json(200 if STATE.get("status") != "CRASHED" else 503, STATE)
            return
        if not route.startswith("/rescue/"):
            self._json(404, {"error": "not found"})
            return
        if not STATE.get("rescue_mode"):
            self._json(409, {"error": "rescue mode is not active"})
            return
        if not _is_authorized(self.headers.get("X-Rescue-Token")):
            self._json(401, {"error": "unauthorized"})
            return
        try:
            if route == "/rescue/inventory":
                self._json(200, _inventory())
            elif route == "/rescue/sqlite-integrity":
                result = _sqlite_integrity()
                self._json(200 if result["ok"] else 503, result)
            elif route == "/rescue/sha256":
                path = _safe_rescue_file(self._query_path())
                self._json(200, {"path": path.relative_to(RESCUE_ROOT.resolve(strict=True)).as_posix(), "sha256": _sha256(path), "size_bytes": path.stat().st_size})
            elif route == "/rescue/download":
                path = _safe_rescue_file(self._query_path())
                file_descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
                try:
                    metadata = os.fstat(file_descriptor)
                    if not stat.S_ISREG(metadata.st_mode):
                        raise ValueError("path is not a regular file")
                    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in path.name)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
                    self.send_header("Content-Length", str(metadata.st_size))
                    self.end_headers()
                    with os.fdopen(file_descriptor, "rb") as source:
                        file_descriptor = -1
                        for chunk in iter(lambda: source.read(1024 * 1024), b""):
                            self.wfile.write(chunk)
                finally:
                    if file_descriptor >= 0:
                        os.close(file_descriptor)
            else:
                self._json(404, {"error": "not found"})
        except (FileNotFoundError, ValueError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            log_event("rescue_endpoint_error", route=route, error=f"{type(exc).__name__}: {exc}")
            self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, *_):
        pass


def collect_once(collector: MEXCDataCollector, engine: DreamAccountEngine, journal: Journal, client: MEXCClient) -> None:
    _require_storage_headroom()
    STATE["scan_iteration"] += 1
    iteration = STATE["scan_iteration"]
    log_event("collector_start", scan=iteration)
    batch = collector.collect_spot()
    _require_storage_headroom()
    persisted = journal.record_snapshots(batch.snapshots)
    storage = journal.prune_normalized_snapshots(MAX_OPERATIONAL_SNAPSHOTS)
    candidates = engine.evaluate(batch, "UNVERIFIED") if batch.gate_passed else []
    eligible = [x for x in candidates if x.tier in {"A", "A+"} and not x.rejection_reasons]
    diagnostic = infrastructure_diagnostic(client) if iteration == 1 or iteration % 10 == 0 else STATE.get("connectivity", {})
    counts = journal.counts()
    STATE.update({
        "status": "DATA_PASS" if batch.gate_passed else "FAIL_CLOSED",
        "rest_health": batch.source_health,
        "connectivity": diagnostic,
        "ws_health": diagnostic.get("websocket", {}),
        "data_coverage": batch.coverage_pct,
        "last_verified_snapshot": batch.timestamp_utc if batch.gate_passed else None,
        "expected_symbols": batch.expected_symbols,
        "verified_symbols": len(batch.verified),
        "failed_symbols": len(batch.failed_symbols),
        "stale_symbols": len(batch.stale_symbols),
        "current_regime": "UNVERIFIED",
        "last_error": next(iter(batch.failed_symbols.values()), None),
        "top_3": [x.as_dict() for x in eligible[:3]] if batch.gate_passed else [],
        "paper_signals": counts.get("signals", 0),
        "paper_open": journal.connection.execute("SELECT COUNT(*) FROM paper_trades WHERE closed_at IS NULL").fetchone()[0],
        "paper_closed": journal.connection.execute("SELECT COUNT(*) FROM paper_trades WHERE closed_at IS NOT NULL").fetchone()[0],
        "snapshot_storage": {**storage, "persisted_this_scan": persisted, "max_rows": MAX_OPERATIONAL_SNAPSHOTS},
        "disk": _disk_usage(),
    })
    event = "snapshot_completion" if batch.gate_passed else "fail_closed"
    health = batch.source_health.get("api.mexc.com", {})
    log_event(event, scan=iteration, mexc_rest="OK" if batch.gate_passed else "FAIL", verified=len(batch.verified), expected=batch.expected_symbols,
              coverage=batch.coverage_pct, latency_p95_ms=health.get("latency_p95_ms"), a_plus=sum(x.tier == "A+" for x in eligible),
              a=sum(x.tier == "A" for x in eligible), paper_open=STATE["paper_open"], snapshot_rows=storage["rows"],
              reusable_bytes=storage["reusable_bytes"], result="NO TRADE" if not eligible else "WATCH")


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    interval = max(15, int(os.getenv("SCAN_INTERVAL_SECONDS", "60")))
    database_path = os.getenv("DREAM_DB_PATH", "/var/data/dream_account.sqlite3")
    log_event("startup", port=port, database_path=database_path, execution="NONEXISTENT")
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    if _should_enter_rescue_mode():
        _activate_rescue_mode()
        try:
            while True:
                time.sleep(3600)
        finally:
            server.shutdown()
        return

    settings = Settings(database_path=database_path)
    journal = Journal(settings.database_path)
    log_event("sqlite_initialization", status="PASS", path=database_path)
    client = MEXCClient(settings.request_timeout_seconds)
    collector = MEXCDataCollector(client)
    engine = DreamAccountEngine(settings)
    try:
        while True:
            try:
                collect_once(collector, engine, journal, client)
            except RescueRequired as exc:
                _activate_rescue_mode(reason=str(exc))
                break
            except Exception as exc:
                STATE.update({"status": "FAIL_CLOSED", "last_error": f"{type(exc).__name__}: {exc}", "top_3": []})
                log_event("fail_closed", error=f"{type(exc).__name__}: {exc}")
            time.sleep(interval)
        while STATE.get("rescue_mode"):
            time.sleep(3600)
    finally:
        journal.close(); server.shutdown()


if __name__ == "__main__":
    main()
