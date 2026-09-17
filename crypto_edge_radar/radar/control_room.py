from __future__ import annotations

from pathlib import Path
import threading

from .dashboard import serve_dashboard
from .engine import RadarEngine
from .friction_monitor import PublicFrictionMonitor
from .scheduler import ExactTimingScheduler
from .service import PublicShadowService


def run_control_room(
    *,
    engine: RadarEngine,
    status_path: str,
    notification_path: str,
    host: str,
    port: int,
    interval: float,
    registry_path: str | None = None,
) -> None:
    """Run timing-aware public observation and the read-only dashboard together.

    Normal heartbeat cadence remains `interval`, but exact-timing adapters can
    wake the service at their frozen target. On MEXC, a separate public-only
    friction monitor records hourly execution-cost diagnostics. The web server
    is read-only and no authenticated exchange transport or order endpoint
    exists here.
    """

    runner = PublicShadowService(
        engine=engine,
        status_path=status_path,
        notification_path=notification_path,
    )
    scheduler = ExactTimingScheduler(
        runner=runner,
        normal_interval=interval,
    )
    market_thread = threading.Thread(
        target=scheduler.run,
        kwargs={"max_cycles": None},
        name="radar-exact-timing-market-service",
        daemon=True,
    )
    market_thread.start()

    if getattr(engine.feed, "provider", None) == "MEXC_FUTURES_PUBLIC":
        friction_path = str(Path(status_path).with_name("mexc_friction_latest.json"))
        friction_monitor = PublicFrictionMonitor(
            engine=engine,
            latest_path=friction_path,
            interval_seconds=3600.0,
        )
        friction_thread = threading.Thread(
            target=friction_monitor.run,
            name="radar-public-friction-monitor",
            daemon=True,
        )
        friction_thread.start()

    serve_dashboard(
        host=host,
        port=port,
        status_path=status_path,
        notification_path=notification_path,
        registry_path=registry_path,
    )
