from __future__ import annotations

import argparse
import json
import os
import sys

from .config import Settings
from .deployment import RiskLimits, stop_based_position_size
from .evidence import build_evidence_store
from .engine import RadarEngine
from .market import BinancePublicFeed, BinanceSpotPublicFeed
from .service import PublicShadowService, read_status
from .strategy import StrategyRegistry
from .strategies.etf_cme_adapter import ETFCMEInstFlowAdapter
from .strategies.etf_cme_source import current_signal_receipt
from .web import serve_render


def build_feed(settings: Settings):
    if settings.provider == "binance_usdm":
        return BinancePublicFeed(timeout=settings.http_timeout)
    if settings.provider == "binance_spot_public":
        return BinanceSpotPublicFeed(timeout=settings.http_timeout)
    raise ValueError(f"unsupported provider: {settings.provider}")


def build_engine() -> tuple[RadarEngine, Settings]:
    settings = Settings.from_env()
    registry = StrategyRegistry(
        (
            ETFCMEInstFlowAdapter(timeout=settings.http_timeout),
        )
    )
    engine = RadarEngine(
        settings=settings,
        feed=build_feed(settings),
        store=build_evidence_store(settings.db_path, settings.database_url),
        registry=registry,
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
        description="CRYPTO EDGE RADAR V0.6 — public shadow + promoted ETF-CME watcher + remote evidence persistence"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("once", help="run one public-data observation cycle")

    service = sub.add_parser("service", help="run heartbeat-enabled public shadow service")
    service.add_argument("--interval", type=float, default=30.0)
    service.add_argument("--max-cycles", type=int, default=None)

    web = sub.add_parser("web-service", help="run Render-compatible HTTP + public shadow service")
    web.add_argument("--interval", type=float, default=float(os.getenv("RADAR_SERVICE_INTERVAL", "30")))
    web.add_argument("--port", type=int, default=int(os.getenv("PORT", "10000")))

    sub.add_parser("status", help="read latest persisted service health status")
    sub.add_parser("verify-evidence", help="verify the configured evidence hash chain")
    sub.add_parser(
        "etf-cme-signal",
        help="fetch the latest public CFTC rows and evaluate the exact frozen ETF-CME signal",
    )

    risk_budget = sub.add_parser(
        "risk-budget", help="print default launch risk amounts for an account equity"
    )
    risk_budget.add_argument("--equity", type=float, required=True)

    position_size = sub.add_parser(
        "position-size",
        help="advisory stop-based size; valid only for a frozen bounded-loss model",
    )
    position_size.add_argument("--equity", type=float, required=True)
    position_size.add_argument("--entry", type=float, required=True)
    position_size.add_argument("--stop", type=float, required=True)

    args = parser.parse_args(argv)

    if args.command == "risk-budget":
        try:
            print(json.dumps(RiskLimits().money_budgets(args.equity), sort_keys=True))
            return 0
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    if args.command == "position-size":
        try:
            print(
                json.dumps(
                    stop_based_position_size(args.equity, args.entry, args.stop),
                    sort_keys=True,
                )
            )
            return 0
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    if args.command == "etf-cme-signal":
        try:
            print(json.dumps(current_signal_receipt(), sort_keys=True))
            return 0
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    try:
        engine, settings = build_engine()
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 2

    if args.command == "once":
        return run_once(engine)
    if args.command == "status":
        print(json.dumps(read_status(settings.status_path), sort_keys=True))
        return 0
    if args.command == "verify-evidence":
        ok, detail = engine.store.verify_chain()
        print(json.dumps({"ok": ok, "detail": detail, "backend": engine.store.backend}, sort_keys=True))
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
    if args.command == "web-service":
        try:
            return serve_render(
                engine=engine,
                status_path=settings.status_path,
                notification_path=settings.notification_path,
                port=args.port,
                interval=args.interval,
            )
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
