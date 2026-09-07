from __future__ import annotations

import json
import asyncio
import logging
import os
import socket
import ssl
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .collector import MEXCDataCollector
from .config import Settings
from .database import Journal
from .live_engine import DreamAccountEngine
from .mexc_client import MEXCClient


logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger("dream-account")
STATE = {"status": "BOOTING", "execution": "NONEXISTENT", "expectancy": "INSUFFICIENT SAMPLE", "scan_iteration": 0}


def log_event(event: str, **fields) -> None:
    LOGGER.info(json.dumps({"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, **fields}, sort_keys=True, default=str))


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
    def do_GET(self):
        if self.path not in {"/", "/health"}:
            self.send_response(404); self.end_headers(); return
        body = json.dumps(STATE, sort_keys=True, default=str).encode()
        self.send_response(200 if STATE.get("status") != "CRASHED" else 503)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, *_): pass


def collect_once(collector: MEXCDataCollector, engine: DreamAccountEngine, journal: Journal, client: MEXCClient) -> None:
    STATE["scan_iteration"] += 1
    iteration = STATE["scan_iteration"]
    log_event("collector_start", scan=iteration)
    batch = collector.collect_spot()
    for snapshot in batch.snapshots:
        journal.record_snapshot(snapshot)
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
    })
    event = "snapshot_completion" if batch.gate_passed else "fail_closed"
    health = batch.source_health.get("api.mexc.com", {})
    log_event(event, scan=iteration, mexc_rest="OK" if batch.gate_passed else "FAIL", verified=len(batch.verified), expected=batch.expected_symbols,
              coverage=batch.coverage_pct, latency_p95_ms=health.get("latency_p95_ms"), a_plus=sum(x.tier == "A+" for x in eligible),
              a=sum(x.tier == "A" for x in eligible), paper_open=STATE["paper_open"], result="NO TRADE" if not eligible else "WATCH")


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    interval = max(15, int(os.getenv("SCAN_INTERVAL_SECONDS", "60")))
    database_path = os.getenv("DREAM_DB_PATH", "/var/data/dream_account.sqlite3")
    log_event("startup", port=port, database_path=database_path, execution="NONEXISTENT")
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
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
            except Exception as exc:
                STATE.update({"status": "FAIL_CLOSED", "last_error": f"{type(exc).__name__}: {exc}", "top_3": []})
                log_event("fail_closed", error=f"{type(exc).__name__}: {exc}")
            time.sleep(interval)
    finally:
        journal.close(); server.shutdown()


if __name__ == "__main__":
    main()
