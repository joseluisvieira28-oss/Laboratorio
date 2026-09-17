from __future__ import annotations

from .control_room import run_control_room
from .engine import RadarEngine


def run_local_node(
    *,
    engine: RadarEngine,
    status_path: str,
    notification_path: str,
    port: int = 8787,
    interval: float = 30.0,
    registry_path: str | None = None,
) -> None:
    """Run the always-on local operator node.

    The local node binds the dashboard to loopback only. It is designed to be
    the future home of local credentials/execution transport, but V0.7 remains
    read-only and has no authenticated exchange/order path.
    """
    run_control_room(
        engine=engine,
        status_path=status_path,
        notification_path=notification_path,
        host="127.0.0.1",
        port=port,
        interval=interval,
        registry_path=registry_path,
    )
