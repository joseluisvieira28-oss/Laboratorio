from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

from .binance_trading import BinanceUSDMTradingClient
from .execution import ExecutionBlocked, MicroLiveCoordinator, MicroLiveSettings

UTC = timezone.utc


def _offset_path() -> Path:
    return Path(os.getenv("MICROLIVE_CURSOR", "microlive_notification_cursor.json"))


def _load_offset(source: Path) -> int:
    cursor = _offset_path()
    if cursor.exists():
        try:
            data = json.loads(cursor.read_text(encoding="utf-8"))
            if data.get("source") == str(source):
                return int(data.get("offset", 0))
        except Exception:
            pass
    # First boot is intentionally non-replaying: start at EOF.
    return source.stat().st_size if source.exists() else 0


def _save_offset(source: Path, offset: int) -> None:
    cursor = _offset_path()
    cursor.parent.mkdir(parents=True, exist_ok=True)
    tmp = cursor.with_suffix(cursor.suffix + ".tmp")
    tmp.write_text(
        json.dumps({"source": str(source), "offset": offset}, sort_keys=True),
        encoding="utf-8",
    )
    os.replace(tmp, cursor)


def _handle_record(coordinator: MicroLiveCoordinator, record: dict) -> None:
    if record.get("event_type") != "VALID_SHADOW_SIGNAL":
        return
    payload = record.get("payload") or {}
    signals = payload.get("signals") or []
    for signal in signals:
        try:
            receipt = coordinator.process_signal(signal, now=datetime.now(UTC))
            print(json.dumps(receipt, sort_keys=True), flush=True)
        except ExecutionBlocked as exc:
            print(
                json.dumps(
                    {
                        "event": "MICROLIVE_SIGNAL_NOT_EXECUTED",
                        "reason": str(exc),
                        "strategy_id": signal.get("strategy_id"),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )


def run_forever() -> int:
    settings = MicroLiveSettings.from_env()
    # Instantiation itself is fail-closed: no secrets => no execution daemon.
    venue = BinanceUSDMTradingClient(
        timeout=int(os.getenv("MICROLIVE_HTTP_TIMEOUT", "10"))
    )
    coordinator = MicroLiveCoordinator(settings, venue)
    source = Path(os.getenv("RADAR_NOTIFICATIONS", "radar_notifications.jsonl"))
    poll = max(float(os.getenv("MICROLIVE_POLL_SECONDS", "1.0")), 0.5)

    offset = _load_offset(source)
    print(
        json.dumps(
            {
                "service": "CED1D0031_MICROLIVE_DAEMON",
                "status": "STARTED_FAIL_CLOSED",
                "execution_enabled": settings.enabled,
                "source": str(source),
                "cursor": offset,
            },
            sort_keys=True,
        ),
        flush=True,
    )

    while True:
        try:
            exit_receipt = coordinator.maybe_exit_due(now=datetime.now(UTC))
            if exit_receipt:
                print(json.dumps(exit_receipt, sort_keys=True), flush=True)

            if source.exists():
                with source.open("r", encoding="utf-8") as handle:
                    handle.seek(offset)
                    while True:
                        line = handle.readline()
                        if not line:
                            break
                        offset = handle.tell()
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        _handle_record(coordinator, record)
                    _save_offset(source, offset)
        except ExecutionBlocked as exc:
            print(
                json.dumps(
                    {"event": "MICROLIVE_FAIL_CLOSED", "reason": str(exc)},
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception as exc:
            print(
                json.dumps(
                    {"event": "MICROLIVE_UNEXPECTED_FAIL_CLOSED", "reason": str(exc)},
                    sort_keys=True,
                ),
                flush=True,
            )
        time.sleep(poll)


if __name__ == "__main__":
    raise SystemExit(run_forever())
