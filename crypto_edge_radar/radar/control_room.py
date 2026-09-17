from __future__ import annotations

import threading

from .dashboard import serve_dashboard
from .engine import RadarEngine
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
    """Run public market observation and the read-only dashboard together.

    The background service remains fail-closed. The web server is read-only and
    has no authenticated exchange transport or order endpoint.
    """

    runner = PublicShadowService(
        engine=engine,
        status_path=status_path,
        notification_path=notification_path,
    )
    thread = threading.Thread(
        target=runner.run,
        kwargs={"interval": interval, "max_cycles": None},
        name="radar-public-market-service",
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
