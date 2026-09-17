from __future__ import annotations

import json
from pathlib import Path
import threading
import time

from .engine import RadarEngine
from .friction import mexc_friction_shadow_receipt


class PublicFrictionMonitor:
    """Periodically capture public MEXC execution-friction diagnostics.

    This monitor has no authenticated API, no order path and no capital path.
    It writes the latest receipt atomically and appends it to the evidence
    chain. Failures are recorded fail-closed and retried on the next interval.
    """

    def __init__(
        self,
        *,
        engine: RadarEngine,
        latest_path: str,
        interval_seconds: float = 3600.0,
        sleeper=time.sleep,
    ) -> None:
        if interval_seconds < 60:
            raise ValueError("friction monitor interval must be >= 60 seconds")
        self.engine = engine
        self.latest_path = Path(latest_path)
        self.interval_seconds = float(interval_seconds)
        self.sleeper = sleeper

    def capture_once(self) -> dict:
        if getattr(self.engine.feed, "provider", None) != "MEXC_FUTURES_PUBLIC":
            raise RuntimeError("friction monitor requires MEXC_FUTURES_PUBLIC")
        receipt = mexc_friction_shadow_receipt(feed=self.engine.feed)
        if receipt.get("capital_enabled") is not False or receipt.get("orders_created") is not False:
            raise RuntimeError("friction receipt violated public-only safety contract")
        self.latest_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.latest_path.with_suffix(self.latest_path.suffix + ".tmp")
        tmp.write_text(json.dumps(receipt, sort_keys=True, indent=2), encoding="utf-8")
        tmp.replace(self.latest_path)
        self.engine.store.append("MEXC_FRICTION_SHADOW", receipt)
        return receipt

    def run(self, stop_event: threading.Event | None = None) -> None:
        stop_event = stop_event or threading.Event()
        while not stop_event.is_set():
            try:
                self.capture_once()
            except Exception as exc:
                self.engine.store.append(
                    "MEXC_FRICTION_SHADOW_FAIL_CLOSED",
                    {
                        "error": str(exc),
                        "capital_enabled": False,
                        "orders_created": False,
                    },
                )
            if stop_event.wait(self.interval_seconds):
                break
