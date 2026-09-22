from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import sys

from .config import Settings
from .control_room import run_control_room
from .dashboard import serve_dashboard
from .deployment import RiskLimits, stop_based_position_size
from .evidence import build_evidence_store
from .engine import RadarEngine
from .forward_web import serve_forward_shadow
from .friction import mexc_friction_shadow_receipt
from .local_node import run_local_node
from .market import BinancePublicFeed, BinanceSpotPublicFeed, MEXCFuturesPublicFeed
from .risk import isolated_margin_validation_size
from .service import PublicShadowService, read_status
from .strategy import StrategyRegistry
from .strategies.etf_cme_adapter import ETFCMEInstFlowAdapter
from .strategies.etf_cme_source import current_signal_receipt


def build_feed(settings: Settings):
    if settings.provider == "binance_usdm":
        return BinancePublicFeed(timeout=settings.http_timeout)
    if settings.provider == "binance_spot_public":
        return BinanceSpotPublicFeed(timeout=settings.http_timeout)
    if settings.provider == "mexc_futures_public":
        return MEXCFuturesPublicFeed(timeout=settings.http_timeout)
    raise ValueError(f"unsupported provider: {settings.provider}")


def build_engine() -> tuple[RadarEngine, Settings]:
    settings = Settings.from_env()
    registry = StrategyRegistry((ETFCMEInstFlowAdapter(timeout=settings.http_timeout),))
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


def timing_status(engine: RadarEngine) -> dict:
    now = datetime.now(timezone.utc)
    plans = []
    for adapter in engine.registry.adapters:
        planner = getattr(adapter, "timing_plan", None)
        if planner is None:
            continue
        plans.append(planner(now))
    return {
        "checked_at_utc": now.isoformat().replace("+00:00", "Z"),
        "timed_strategy_count": len(plans),
        "plans": plans,
    }


def public_isolated_risk_receipt(equity: float) -> dict:
    feed = MEXCFuturesPublicFeed(timeout=10)
    snapshots = feed.all_market_snapshots()
    snap = snapshots.get("BTCUSDT")
    if snap is None:
        raise RuntimeError("MEXC BTCUSDT public snapshot unavailable")
    contract = feed.contract_row("BTC_USDT")
    if contract.get("apiAllowed") is False:
        raise RuntimeError("MEXC BTC_USDT is not API eligible")
    if contract.get("futureType") not in (None, 1) or contract.get("state") not in (None, 0):
        raise RuntimeError("MEXC BTC_USDT contract is not active perpetual")
    price = max(float(snap.bid_price), float(snap.ask_price), float(snap.last_price))
    result = isolated_margin_validation_size(
        account_equity=equity,
        price=price,
        contract_size=float(contract["contractSize"]),
        min_vol=int(contract["minVol"]),
        vol_unit=int(contract["volUnit"]),
        leverage=1.0,
        max_margin_fraction=0.001,
    )
    return {
        "receipt_type": "ETF_CME_MEXC_ISOLATED_RISK_ADVISORY_V1",
        "provider": feed.provider,
        "symbol": "BTC_USDT",
        "isolated_required": True,
        "auto_margin_add_required_off": True,
        "authenticated_state_verified": False,
        "capital_enabled": False,
        "orders_created": False,
        "sizing": result,
        "blockers": [
            "authenticated verification of isolated mode / 1x leverage / auto-margin-add OFF",
            "MEXC friction gate",
            "entry and exit order semantics",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="CRYPTO EDGE RADAR V0.9 — promoted-candidate shadow operations"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("once", help="run one public-data observation cycle")

    service = sub.add_parser("service", help="run heartbeat-enabled public shadow service")
    service.add_argument("--interval", type=float, default=30.0)
    service.add_argument("--max-cycles", type=int, default=None)

    sub.add_parser(
        "forward-once",
        help="run one replay-safe public forward-shadow cycle and exit",
    )

    web = sub.add_parser(
        "web-service",
        help="run Render-compatible TFG + BNB public forward shadow watchers",
    )
    web.add_argument("--interval", type=float, default=float(os.getenv("RADAR_SERVICE_INTERVAL", "120")))
    web.add_argument("--port", type=int, default=int(os.getenv("PORT", "10000")))

    dashboard = sub.add_parser("dashboard", help="serve the read-only multi-bot web control room")
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8787)
    dashboard.add_argument("--registry", default=None)

    control = sub.add_parser("control-room", help="run timing-aware public observation and web control room")
    control.add_argument("--host", default="127.0.0.1")
    control.add_argument("--port", type=int, default=8787)
    control.add_argument("--interval", type=float, default=30.0)
    control.add_argument("--registry", default=None)

    local = sub.add_parser("local-node", help="run the always-on local operator node on loopback only")
    local.add_argument("--port", type=int, default=8787)
    local.add_argument("--interval", type=float, default=30.0)
    local.add_argument("--registry", default=None)

    sub.add_parser("timing-status", help="show exact-timing plans for registered strategies")
    sub.add_parser("status", help="read latest persisted service health status")
    sub.add_parser("verify-evidence", help="verify the evidence hash chain")
    sub.add_parser("etf-cme-signal", help="fetch latest public CFTC rows and evaluate the scientific exact-time signal")
    sub.add_parser("mexc-friction-shadow", help="capture public-only BTC_USDT execution-friction observables; never creates orders")

    risk_budget = sub.add_parser("risk-budget", help="print default launch risk amounts for an account equity")
    risk_budget.add_argument("--equity", type=float, required=True)

    position_size = sub.add_parser("position-size", help="advisory stop-based size; valid only for a frozen bounded-loss model")
    position_size.add_argument("--equity", type=float, required=True)
    position_size.add_argument("--entry", type=float, required=True)
    position_size.add_argument("--stop", type=float, required=True)

    isolated = sub.add_parser(
        "isolated-risk-size",
        help="public MEXC isolated-margin sizing advisory for ETF-CME; never creates orders",
    )
    isolated.add_argument("--equity", type=float, required=True)

    args = parser.parse_args(argv)

    if args.command == "forward-once":
        try:
            settings = Settings.from_env()
            runtime = __import__(
                "radar.forward_web", fromlist=["ForwardShadowRuntime"]
            ).ForwardShadowRuntime(settings=settings)
            state = runtime.run_cycle()
            print(json.dumps(state, sort_keys=True))
            return 0 if state.get("health") == "OK" else 2
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    if args.command == "web-service":
        try:
            return serve_forward_shadow(port=args.port, interval=args.interval)
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    if args.command == "risk-budget":
        try:
            print(json.dumps(RiskLimits().money_budgets(args.equity), sort_keys=True))
            return 0
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    if args.command == "position-size":
        try:
            print(json.dumps(stop_based_position_size(args.equity, args.entry, args.stop), sort_keys=True))
            return 0
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    if args.command == "isolated-risk-size":
        try:
            print(json.dumps(public_isolated_risk_receipt(args.equity), sort_keys=True))
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

    if args.command == "mexc-friction-shadow":
        try:
            print(json.dumps(mexc_friction_shadow_receipt(), sort_keys=True))
            return 0
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    if args.command == "dashboard":
        try:
            settings = Settings.from_env()
            serve_dashboard(
                host=args.host,
                port=args.port,
                status_path=settings.status_path,
                notification_path=settings.notification_path,
                registry_path=args.registry,
            )
            return 0
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    try:
        engine, settings = build_engine()
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 2

    if args.command == "timing-status":
        try:
            print(json.dumps(timing_status(engine), sort_keys=True))
            return 0
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    if args.command == "control-room":
        try:
            run_control_room(
                engine=engine,
                status_path=settings.status_path,
                notification_path=settings.notification_path,
                host=args.host,
                port=args.port,
                interval=args.interval,
                registry_path=args.registry,
            )
            return 0
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
            return 2

    if args.command == "local-node":
        try:
            run_local_node(
                engine=engine,
                status_path=settings.status_path,
                notification_path=settings.notification_path,
                port=args.port,
                interval=args.interval,
                registry_path=args.registry,
            )
            return 0
        except KeyboardInterrupt:
            return 0
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
    return 2


if __name__ == "__main__":
    sys.exit(main())
