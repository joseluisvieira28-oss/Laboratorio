from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any

from .engine import RadarEngine


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    os.replace(tmp, path)


@dataclass
class JsonlNotifier:
    path: Path

    def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {"ts_utc": _utc_now(), "event_type": event_type, "payload": payload}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


class PublicShadowService:
    def __init__(
        self,
        engine: RadarEngine,
        status_path: str,
        notification_path: str,
    ) -> None:
        self.engine = engine
        self.status_path = Path(status_path)
        self.notifier = JsonlNotifier(Path(notification_path))
        self.cycle_no = 0
        self.consecutive_failures = 0

    def _publish_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        _atomic_json_write(self.status_path, payload)
        return payload

    def run_cycle(self) -> tuple[int, dict[str, Any]]:
        self.cycle_no += 1
        started = _utc_now()
        configured_provider = getattr(self.engine.feed, "provider", "UNKNOWN_PUBLIC_PROVIDER")
        try:
            result = self.engine.run_cycle()
            self.consecutive_failures = 0
            status = {
                "service": "CRYPTO_EDGE_RADAR",
                "version": "0.3",
                "mode": "PUBLIC_SHADOW_ONLY",
                "provider": result["provider"],
                "health": "OK",
                "cycle": self.cycle_no,
                "started_at_utc": started,
                "completed_at_utc": _utc_now(),
                "universe": result["universe"],
                "registered_strategies": result["registered_strategies"],
                "valid_signal_count": len(result["valid_signals"]),
                "duplicate_signal_count": result.get("duplicate_signal_count", 0),
                "consecutive_failures": 0,
            }
            heartbeat = self.engine.store.append("SERVICE_HEARTBEAT", status)
            status["heartbeat_receipt"] = heartbeat
            self._publish_status(status)
            if result["valid_signals"]:
                self.notifier.emit(
                    "VALID_SHADOW_SIGNAL",
                    {"provider": result["provider"], "signals": result["valid_signals"]},
                )
            return 0, status
        except Exception as exc:
            self.consecutive_failures += 1
            status = {
                "service": "CRYPTO_EDGE_RADAR",
                "version": "0.2",
                "mode": "PUBLIC_SHADOW_ONLY",
                "provider": configured_provider,
                "health": "FAIL_CLOSED",
                "cycle": self.cycle_no,
                "started_at_utc": started,
                "completed_at_utc": _utc_now(),
                "error": str(exc),
                "consecutive_failures": self.consecutive_failures,
                "valid_signal_count": 0,
            }
            try:
                self.engine.store.append("SERVICE_FAILURE", status)
            finally:
                self._publish_status(status)
                self.notifier.emit("SERVICE_FAIL_CLOSED", status)
            return 2, status

    def run(self, interval: float, max_cycles: int | None = None) -> int:
        if interval < 5:
            raise ValueError("interval must be >= 5 seconds")
        if max_cycles is not None and max_cycles <= 0:
            raise ValueError("max_cycles must be > 0")

        overall = 0
        while max_cycles is None or self.cycle_no < max_cycles:
            code, _ = self.run_cycle()
            overall = max(overall, code)
            if max_cycles is not None and self.cycle_no >= max_cycles:
                break
            time.sleep(interval)
        return overall


def read_status(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"health": "UNKNOWN", "reason": "status file does not exist"}
    return json.loads(p.read_text(encoding="utf-8"))
