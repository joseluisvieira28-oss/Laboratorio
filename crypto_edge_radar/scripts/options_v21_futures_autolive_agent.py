from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
import time
from datetime import datetime, timezone

from radar.mexc_auth_readonly import MEXCCredentials
from radar.options_v21_futures_autolive_engine import OptionsV21FuturesAutoLiveEngine

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


def _prevent_automatic_sleep() -> bool:
    if os.name != "nt":
        return False
    try:
        result = ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        )
        return bool(result)
    except Exception:
        return False


def _restore_sleep_policy() -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    except Exception:
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/options_v21_futures_autolive.sqlite3")
    ap.add_argument("--receipt-root", default="live_receipts/options_v21_futures")
    ap.add_argument("--armed", default="AUTO_MICROLIVE_FUTURES_ARMED.json")
    ap.add_argument("--kill-switch", default="KILL_SWITCH")
    ap.add_argument("--status", default="options_v21_futures_autolive_status.json")
    ap.add_argument("--interval", type=float, default=15.0)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    if args.interval < 5.0:
        raise SystemExit("interval must be >= 5 seconds")

    credentials = MEXCCredentials.from_env()
    engine = OptionsV21FuturesAutoLiveEngine(
        credentials=credentials,
        db_path=args.db,
        receipt_root=args.receipt_root,
        armed_path=args.armed,
        kill_switch_path=args.kill_switch,
        status_path=args.status,
    )

    keep_awake = _prevent_automatic_sleep()
    print(json.dumps({
        "status": "AGENT_START",
        "version": "OPTIONS_FUTURES_ONLY_AUTO_MICROLIVE_V0.2",
        "windows_automatic_sleep_prevented": keep_awake,
        "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }, sort_keys=True), flush=True)

    try:
        while True:
            try:
                result = engine.run_once()
                print(json.dumps(result, sort_keys=True, ensure_ascii=False), flush=True)
            except KeyboardInterrupt:
                return 0
            except Exception as exc:
                payload = {
                    "version": "OPTIONS_FUTURES_ONLY_AUTO_MICROLIVE_V0.2",
                    "status": "PROCESS_FAIL_CLOSED",
                    "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print(json.dumps(payload, sort_keys=True, ensure_ascii=False), flush=True)
            if args.once:
                return 0
            time.sleep(args.interval)
    finally:
        _restore_sleep_policy()


if __name__ == "__main__":
    raise SystemExit(main())
