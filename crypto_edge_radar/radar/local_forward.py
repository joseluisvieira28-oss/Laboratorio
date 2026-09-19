from __future__ import annotations

from pathlib import Path
from typing import Callable

from .config import Settings
from .forward_web import ForwardShadowRuntime


LOCAL_FORWARD_INTERVAL_SECONDS = 30.0


def build_local_forward_settings(root: str = "data") -> Settings:
    base = Path(root)
    base.mkdir(parents=True, exist_ok=True)
    return Settings(
        db_path=str((base / "forward_local_evidence.sqlite3").resolve()),
        database_url=None,
        status_path=str((base / "forward_local_status.json").resolve()),
        notification_path=str((base / "forward_local_notifications.jsonl").resolve()),
        provider="mexc_futures_public",
        universe_mode="core5",
        max_symbols=50,
        min_quote_volume=50_000_000.0,
        http_timeout=15,
    )


class LocalForwardSupervisor:
    """Runs the five local non-DH03 public shadow engines on the Windows node. CED1D remains externally collected."""

    def __init__(
        self,
        *,
        root: str = "data",
        runtime_factory: Callable[..., ForwardShadowRuntime] = ForwardShadowRuntime,
    ) -> None:
        self.settings = build_local_forward_settings(root)
        self.runtime = runtime_factory(settings=self.settings)

    def run_forever(self) -> None:
        self.runtime.run_cycle()
        self.runtime.run_loop(interval_seconds=LOCAL_FORWARD_INTERVAL_SECONDS)
