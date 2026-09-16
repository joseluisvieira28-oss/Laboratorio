from __future__ import annotations

import argparse
import json
import sys
import time

from .config import Settings
from .evidence import EvidenceStore
from .engine import RadarEngine
from .market import BinancePublicFeed, MarketDataError
from .strategy import StrategyRegistry


def build_engine() -> RadarEngine:
    settings = Settings.from_env()
    return RadarEngine(
        settings=settings,
        feed=BinancePublicFeed(timeout=settings.http_timeout),
        store=EvidenceStore(settings.db_path),
        registry=StrategyRegistry.empty(),
    )


def run_once(engine: RadarEngine) -> int:
    try:
        result = engine.run_cycle()
    except Exception as exc:
        # Fail closed: no signal output is emitted when market data or evaluation fails.
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CRYPTO EDGE RADAR V0.1 — shadow only")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("once", help="run one public-data observation cycle")
    loop = sub.add_parser("loop", help="poll public market data continuously")
    loop.add_argument("--interval", type=float, default=30.0)
    verify = sub.add_parser("verify-evidence", help="verify the local evidence hash chain")

    args = parser.parse_args(argv)
    engine = build_engine()

    if args.command == "once":
        return run_once(engine)
    if args.command == "verify-evidence":
        ok, detail = engine.store.verify_chain()
        print(json.dumps({"ok": ok, "detail": detail}, sort_keys=True))
        return 0 if ok else 3
    if args.command == "loop":
        if args.interval < 5:
            print(json.dumps({"status": "FAIL_CLOSED", "error": "interval must be >= 5 seconds"}))
            return 2
        while True:
            run_once(engine)
            time.sleep(args.interval)
    return 2


if __name__ == "__main__":
    sys.exit(main())
