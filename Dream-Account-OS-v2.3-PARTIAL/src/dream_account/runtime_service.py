from __future__ import annotations

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .collector import MEXCDataCollector
from .config import Settings
from .database import Journal
from .live_engine import DreamAccountEngine
from .mexc_client import MEXCClient


STATE = {"status": "BOOTING", "execution": "NONEXISTENT", "expectancy": "INSUFFICIENT SAMPLE"}


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


def collect_once(collector: MEXCDataCollector, engine: DreamAccountEngine, journal: Journal) -> None:
    batch = collector.collect_spot()
    for snapshot in batch.snapshots:
        journal.record_snapshot(snapshot)
    candidates = engine.evaluate(batch, "UNVERIFIED") if batch.gate_passed else []
    STATE.update({
        "status": "DATA_PASS" if batch.gate_passed else "FAIL_CLOSED",
        "rest_health": batch.source_health,
        "ws_health": "STARTUP_RECONCILIATION_REQUIRED",
        "data_coverage": batch.coverage_pct,
        "last_verified_snapshot": batch.timestamp_utc if batch.gate_passed else None,
        "expected_symbols": batch.expected_symbols,
        "verified_symbols": len(batch.verified),
        "failed_symbols": len(batch.failed_symbols),
        "stale_symbols": len(batch.stale_symbols),
        "current_regime": "UNVERIFIED",
        "top_3": [x.as_dict() for x in candidates[:3]] if batch.gate_passed else [],
    })


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    interval = max(15, int(os.getenv("SCAN_INTERVAL_SECONDS", "60")))
    database_path = os.getenv("DREAM_DB_PATH", "/var/data/dream_account.sqlite3")
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    settings = Settings(database_path=database_path)
    journal = Journal(settings.database_path)
    collector = MEXCDataCollector(MEXCClient(settings.request_timeout_seconds))
    engine = DreamAccountEngine(settings)
    try:
        while True:
            try:
                collect_once(collector, engine, journal)
            except Exception as exc:
                STATE.update({"status": "FAIL_CLOSED", "last_error": f"{type(exc).__name__}: {exc}", "top_3": []})
            time.sleep(interval)
    finally:
        journal.close(); server.shutdown()


if __name__ == "__main__":
    main()
