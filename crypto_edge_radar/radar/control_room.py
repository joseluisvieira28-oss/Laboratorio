from __future__ import annotations

import threading

from .dashboard import serve_dashboard
from .engine import RadarEngine
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
    wake the service at their frozen target. The web server is read-only and no
    authenticated exchange transport or order endpoint exists here.
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
    thread = threading.Thread(
        target=scheduler.run,
        kwargs={"max_cycles": None},
        name="radar-exact-timing-market-service",
        daemon=True,
    )
    thread.start()
    serve_dashboard(
        host=host,
        port=port,
        status_path=status_path,
        notification_path=notification_path,
        registry_path=registry_path,
    )
