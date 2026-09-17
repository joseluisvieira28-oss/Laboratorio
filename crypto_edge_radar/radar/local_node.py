from __future__ import annotations

from .control_room import run_control_room
from .engine import RadarEngine
from .preflight import require_local_node_preflight


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

    The local node binds the dashboard to loopback only. Before arming the
    timing-aware control room it must pass a public/read-only preflight proving
    MEXC provider health, BTC_USDT execution eligibility, clock budget and
    durable evidence integrity. V0.7 still has no authenticated exchange/order
    transport.
    """
    require_local_node_preflight(feed=engine.feed, store=engine.store)
    run_control_room(
        engine=engine,
        status_path=status_path,
        notification_path=notification_path,
        host="127.0.0.1",
        port=port,
        interval=interval,
        registry_path=registry_path,
    )