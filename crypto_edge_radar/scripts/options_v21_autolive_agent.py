from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

from radar.mexc_auth_readonly import MEXCCredentials
from radar.options_v21_autolive_engine import OptionsV21AutoLiveEngine


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/options_v21_autolive.sqlite3")
    ap.add_argument("--receipt-root", default="live_receipts/options_v21")
    ap.add_argument("--armed", default="AUTO_MICROLIVE_ARMED.json")
    ap.add_argument("--kill-switch", default="KILL_SWITCH")
    ap.add_argument("--status", default="options_v21_autolive_status.json")
    ap.add_argument("--interval", type=float, default=15.0)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    if args.interval < 5.0:
        raise SystemExit("interval must be >= 5 seconds")

    credentials = MEXCCredentials.from_env()
    engine = OptionsV21AutoLiveEngine(
        credentials=credentials,
        db_path=args.db,
        receipt_root=args.receipt_root,
        armed_path=args.armed,
        kill_switch_path=args.kill_switch,
        status_path=args.status,
    )

    while True:
        try:
            result = engine.run_once()
            print(json.dumps(result, sort_keys=True, ensure_ascii=False), flush=True)
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            payload = {
                "version": "OPTIONS_AUTO_MICROLIVE_V0.1",
                "status": "PROCESS_FAIL_CLOSED",
                "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "error": f"{type(exc).__name__}: {exc}",
            }
            print(json.dumps(payload, sort_keys=True, ensure_ascii=False), flush=True)
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
