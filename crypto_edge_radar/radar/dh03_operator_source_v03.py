from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import threading
from typing import Any

from .dh03_12h_core import MAX_HOLD_MS
from .dh03_12h_local import DH03LocalCollector, OPERATOR_MAX_RECEIPT_LATENCY_MS

CANDIDATE_ID = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
FRICTION_CEILING_BPS = 30.0

_SYMBOL_MAP = {
    "BTCUSDT": "BTC_USDT",
    "ETHUSDT": "ETH_USDT",
    "SOLUSDT": "SOL_USDT",
    "BNBUSDT": "BNB_USDT",
    "XRPUSDT": "XRP_USDT",
    "DOGEUSDT": "DOGE_USDT",
}


def _iso_ms(ms: int) -> str:
    return (
        datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


class DH03OperatorSourceV03:
    """Prospective DH03 websocket source.

    Scientific shadow evidence remains unchanged. Operator eligibility is a
    separate no-credit fork requiring the local receipt and Binance event time
    to both land inside the frozen two-second translation window.
    """

    def __init__(
        self,
        *,
        data_db: str,
        evidence_db: str,
        state_path: str,
    ) -> None:
        self.collector = DH03LocalCollector(
            data_db=data_db,
            evidence_db=evidence_db,
        )
        self.state_path = Path(state_path)
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._runtime_status = "NOT_STARTED"
        self._runtime_error: str | None = None
        self._bootstrap: dict[str, Any] | None = None
        if self.state_path.exists():
            try:
                payload = json.loads(self.state_path.read_text(encoding="utf-8"))
                self.state = payload if isinstance(payload, dict) else {}
            except Exception:
                self.state = {}
        else:
            self.state = {}
        self.state.setdefault("signals", {})

    def _save(self) -> None:
        self.state["version"] = "DH03_OPERATOR_SOURCE_V0.3"
        self.state["candidate_id"] = CANDIDATE_ID
        self.state["runtime_status"] = self._runtime_status
        self.state["runtime_error"] = self._runtime_error
        self.state["checked_at_utc"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        _atomic_write(self.state_path, self.state)

    def _run(self) -> None:
        try:
            with self._lock:
                self._runtime_status = "BOOTSTRAPPING"
                self._save()
            bootstrap = self.collector.bootstrap()
            with self._lock:
                self._bootstrap = bootstrap
                self._runtime_status = "COLLECTING"
                self._save()
            self.collector.run_forever()
        except Exception as exc:
            with self._lock:
                self._runtime_status = "FAIL_CLOSED"
                self._runtime_error = f"{type(exc).__name__}:{exc}"
                self._save()

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._thread = threading.Thread(
                target=self._run,
                name="DH03OperatorSourceV03",
                daemon=True,
            )
            self._thread.start()

    def _signal_from_entry(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        op = payload.get("operator_candidate")
        signal = payload.get("signal")
        if not isinstance(op, dict) or not isinstance(signal, dict):
            return None
        if op.get("eligible") is not True:
            return None
        symbol = str(payload.get("symbol") or "").upper()
        mexc_symbol = _SYMBOL_MAP.get(symbol)
        if not mexc_symbol:
            return None
        try:
            entry_ms = int(signal["entry_open_time"])
            entry = float(signal["entry"])
            stop = float(signal["stop"])
            target = float(signal["target"])
            risk = float(signal["initial_risk_fraction"])
            received_ms = int(op["received_at_ms"])
            source_event_ms = int(op["source_event_time_ms"])
            if any(not math.isfinite(x) for x in (entry, stop, target, risk)):
                return None
            if not (0 < stop < entry < target and 0 < risk < 1):
                return None
            stop_distance = (entry - stop) / entry
            target_distance = (target - entry) / entry
            if abs(stop_distance - risk) > 1e-9:
                return None
            if target_distance <= 0:
                return None
        except Exception:
            return None

        return {
            "candidate_id": CANDIDATE_ID,
            "strategy_id": CANDIDATE_ID,
            "immutable_signal_key": str(payload["event_key"]),
            "symbol": mexc_symbol,
            "source_symbol": symbol,
            "direction": "LONG",
            "entry_target_utc": _iso_ms(entry_ms),
            "exit_target_utc": _iso_ms(entry_ms + MAX_HOLD_MS),
            "max_late_seconds": OPERATOR_MAX_RECEIPT_LATENCY_MS / 1000.0,
            "max_initial_margin_usdt": 10.0,
            "max_notional_usdt": 50.0,
            "leverage": 5,
            "margin_mode": "ISOLATED",
            "max_projected_roundtrip_friction_bps": FRICTION_CEILING_BPS,
            "transaction_cost_ceiling_excludes_funding": True,
            "protective_exit": {
                "required": True,
                "stop_distance_fraction": stop_distance,
                "take_profit_distance_fraction": target_distance,
                "trigger_basis": "LATEST_PRICE",
                "source_geometry": "BINANCE_DH03_RELATIVE_DISTANCE_MAPPED_TO_MEXC_FILL",
            },
            "source_reference": {
                "binance_entry": entry,
                "binance_stop": stop,
                "binance_target": target,
                "initial_risk_fraction": risk,
                "signal_fingerprint": signal.get("fingerprint"),
                "received_at_ms": received_ms,
                "source_event_time_ms": source_event_ms,
                "receipt_latency_ms": op.get("receipt_latency_ms"),
                "source_event_latency_ms": op.get("source_event_latency_ms"),
            },
            "late_chase_allowed": False,
            "scientific_credit": False,
            "operator_proxy": True,
        }

    def poll(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        self.start()
        entries = self.collector.evidence.read_payloads("DH03_LOCAL_ENTRY")
        signals: list[dict[str, Any]] = []
        for payload in entries:
            signal = self._signal_from_entry(payload)
            if signal is None:
                continue
            key = signal["immutable_signal_key"]
            row = self.state["signals"].setdefault(key, {"status": "OBSERVED"})
            if row.get("status") in {"CONSUMED", "MISSED_CONFLICT_NO_CHASE", "MISSED_LATE_NO_CHASE"}:
                continue
            target_ms = int(
                datetime.fromisoformat(
                    signal["entry_target_utc"].replace("Z", "+00:00")
                ).timestamp() * 1000
            )
            max_late_ms = int(float(signal["max_late_seconds"]) * 1000)
            if now_ms > target_ms + max_late_ms:
                row["status"] = "MISSED_LATE_NO_CHASE"
                row["observed_at_utc"] = _iso_ms(now_ms)
                continue
            signals.append(signal)

        with self._lock:
            self._save()
            status = self._runtime_status
            error = self._runtime_error
        return {
            "source_id": "DH03_OPERATOR_SOURCE_V0.3",
            "status": status,
            "error": error,
            "signals": sorted(
                signals,
                key=lambda s: (s["entry_target_utc"], s["immutable_signal_key"]),
            ),
            "orders_created": False,
            "exchange_mutation_performed": False,
            "science_credit": False,
        }

    def mark(self, signal_identity: str, status: str) -> None:
        row = self.state["signals"].setdefault(signal_identity, {})
        row["status"] = status
        row["updated_at_utc"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        with self._lock:
            self._save()


__all__ = ["DH03OperatorSourceV03", "CANDIDATE_ID", "FRICTION_CEILING_BPS"]
