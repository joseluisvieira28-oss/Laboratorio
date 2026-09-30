from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .evidence import EvidenceStore
from .options_v21_live import BinanceBTCUSDTDailyFeed, DeribitBTCOptionTradeFeed
from .options_v21_operator_signal_v03 import (
    build_operator_signal,
    latest_due_parent_entry,
)
from .options_v21_watcher import OptionsV21ForwardShadowWatcher


class OptionsV21OperatorSourceV03:
    """Public-source adapter only. It never contacts authenticated exchange APIs."""

    def __init__(
        self,
        *,
        db_path: str,
        state_path: str | None = None,
        source_timeout: int = 15,
    ) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.store = EvidenceStore(db_path)
        self.state_path = Path(state_path) if state_path else Path(db_path).with_suffix(".operator_state.json")
        if self.state_path.exists():
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeError("OPTIONS operator source state must be JSON object")
            self.state = payload
        else:
            self.state = {"signals": {}}
        self.state.setdefault("signals", {})
        self.watcher = OptionsV21ForwardShadowWatcher(
            store=self.store,
            options_feed=DeribitBTCOptionTradeFeed(timeout=source_timeout),
            btc_feed=BinanceBTCUSDTDailyFeed(timeout=source_timeout),
        )

    def poll(self, *, now_utc: datetime | None = None) -> dict[str, Any]:
        now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
        watcher = self.watcher.run_once(now_ms=int(now.timestamp() * 1000))
        status = str(watcher.get("status") or "")
        entry = latest_due_parent_entry(self.store, now_utc=now)
        if entry is None:
            return {
                "source_id": "OPTIONS_V21_OPERATOR_SOURCE_V0.3",
                "status": "WAITING_CANONICAL_PARENT_ENTRY",
                "watcher_status": status,
                "signal": None,
                "orders_created": False,
                "exchange_mutation_performed": False,
            }

        signal = build_operator_signal(
            entry,
            watcher_status=status,
            now_utc=now,
        )
        key = signal["immutable_signal_key"]
        row = self.state["signals"].setdefault(key, {"status": "OBSERVED"})
        if row.get("status") in {
            "CONSUMED_ACTIVE_REAL_MONEY",
            "MISSED_CONFLICT_NO_CHASE",
            "BLOCKED_AT_ENTRY_NO_CHASE",
            "ENTRY_RECONCILIATION_REQUIRED",
        }:
            return {
                "source_id": "OPTIONS_V21_OPERATOR_SOURCE_V0.3",
                "status": "SIGNAL_ALREADY_TERMINAL",
                "watcher_status": status,
                "signal": None,
                "signal_identity": key,
                "orders_created": False,
                "exchange_mutation_performed": False,
            }
        if not signal["source_healthy"]:
            source_status = "FAIL_CLOSED_SOURCE"
            signal_out = None
        elif not signal["entry_window_open"]:
            source_status = "MISSED_ENTRY_WINDOW_NO_CHASE"
            signal_out = None
        else:
            source_status = "SIGNAL_AVAILABLE"
            signal_out = signal

        return {
            "source_id": "OPTIONS_V21_OPERATOR_SOURCE_V0.3",
            "status": source_status,
            "watcher_status": status,
            "signal": signal_out,
            "signal_identity": signal["immutable_signal_key"],
            "entry_target_utc": signal["entry_target_utc"],
            "seconds_from_entry_target": signal["seconds_from_entry_target"],
            "orders_created": False,
            "exchange_mutation_performed": False,
        }


    def mark(self, signal_identity: str, status: str) -> None:
        row = self.state["signals"].setdefault(signal_identity, {})
        row["status"] = status
        row["updated_at_utc"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self.state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.state_path)


__all__ = ["OptionsV21OperatorSourceV03"]
