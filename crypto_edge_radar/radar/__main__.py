from __future__ import annotations

import argparse
import json
import sys

from .config import Settings
from .evidence import EvidenceStore
from .engine import RadarEngine
from .market import BinancePublicFeed, BinanceSpotPublicFeed
from .promoted import build_promoted_registry
from .service import PublicShadowService, read_status


def build_feed(settings: Settings):
    if settings.provider == "binance_usdm":
        return BinancePublicFeed(timeout=settings.http_timeout)
    if settings.provider == "binance_spot_public":
        return BinanceSpotPublicFeed(timeout=settings.http_timeout)
    raise ValueError(f"unsupported provider: {settings.provider}")


def build_engine() -> tuple[RadarEngine, Settings]:
    settings = Settings.from_env()
    feed = build_feed(settings)
    engine = RadarEngine(
        settings=settings,
        feed=feed,
        store=EvidenceStore(settings.db_path),
        registry=build_promoted_registry(feed),
    )
    return engine, settings


def run_once(engine: RadarEngine) -> int:
    try:
        result = engine.run_cycle()
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="CRYPTO EDGE RADAR V0.3 — promoted shadow motors + isolated micro-live layer"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("once", help="run one public-data observation cycle")

    service = sub.add_parser("service", help="run heartbeat-enabled public shadow service")
    service.add_argument("--interval", type=float, default=30.0)
    service.add_argument("--max-cycles", type=int, default=None)

    sub.add_parser("status", help="read latest persisted service health status")
    sub.add_parser("verify-evidence", help="verify the local evidence hash chain")
    sub.add_parser(
        "microlive",
        help="run isolated CED1D-0031 micro-live daemon; requires explicit runtime arming and secrets",
    )

    args = parser.parse_args(argv)

    if args.command == "microlive":
        try:
            from .microlive_service import run_forever

            return run_forever()
        except Exception as exc:
            print(
                json.dumps(
                    {"status": "MICROLIVE_FAIL_CLOSED", "error": str(exc)},
                    sort_keys=True,
                )
            )
            return 2

    engine, settings = build_engine()

    if args.command == "once":
        return run_once(engine)
    if args.command == "status":
        print(json.dumps(read_status(settings.status_path), sort_keys=True))
        return 0
    if args.command == "verify-evidence":
        ok, detail = engine.store.verify_chain()
        print(json.dumps({"ok": ok, "detail": detail}, sort_keys=True))
        return 0 if ok else 3
    if args.command == "service":
        try:
            runner = PublicShadowService(
                engine=engine,
                status_path=settings.status_path,
                notification_path=settings.notification_path,
            )
            code = runner.run(interval=args.interval, max_cycles=args.max_cycles)
            print(json.dumps(read_status(settings.status_path), sort_keys=True))
            return code
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
