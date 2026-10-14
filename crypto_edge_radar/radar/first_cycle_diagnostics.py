"""Read-only, no-secret diagnostics for the first public-shadow collector cycle.

This module observes a potentially blocking run_cycle without cancelling it,
changing watchdog decisions, touching the evidence store, or making requests.
No stack locals, exception messages, URLs, environment values, or paths are logged.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import sys
import threading
import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")
_LOG_PREFIX = "RADAR_BOOTSTRAP_TRACE "


def _emit(kind: str, **details: Any) -> None:
    """Best-effort stderr logging must never change collector behavior."""
    receipt = {
        "kind": kind,
        "utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        **details,
    }
    try:
        print(
            _LOG_PREFIX + json.dumps(receipt, sort_keys=True, separators=(",", ":")),
            file=sys.stderr,
            flush=True,
        )
    except Exception:
        pass


def _radar_stack(thread_id: int) -> list[dict[str, Any]]:
    """Only code symbols and line numbers from the radar package; no frame locals."""
    try:
        frame = sys._current_frames().get(thread_id)
        result: list[dict[str, Any]] = []
        for _ in range(64):
            if frame is None:
                break
            path = frame.f_code.co_filename.replace("\\", "/")
            if "/radar/" in path and path.endswith(".py"):
                result.append({
                    "file": path.rsplit("/", 1)[-1],
                    "function": frame.f_code.co_name,
                    "line": int(frame.f_lineno),
                })
                if len(result) >= 8:
                    break
            frame = frame.f_back
        # No traceback snippets, locals, absolute paths, hostnames or URLs.
        return result or [{"file": "not_in_radar", "function": "unresolved", "line": 0}]
    except Exception:
        return [{"file": "unavailable", "function": "unresolved", "line": 0}]


def run_with_first_cycle_diagnostics(
    run_cycle: Callable[[], T], *, interval_seconds: float = 45.0
) -> T:
    """Run the original operation exactly once, instrumented but never retried.

    A daemon observer logs the active radar function/line after each interval.
    Its output does not affect the returned state or exception behavior.
    This is not a timeout enforcement mechanism and grants no trading authority.
    """
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")

    started = time.monotonic()
    target_thread_id = threading.get_ident()
    stop = threading.Event()
    _emit("FIRST_CYCLE_STARTED", mode="PUBLIC_SHADOW_ONLY")

    def observer() -> None:
        while not stop.wait(interval_seconds):
            _emit(
                "FIRST_CYCLE_STILL_RUNNING",
                elapsed_seconds=round(time.monotonic() - started, 1),
                radar_stack=_radar_stack(target_thread_id),
                action="DIAGNOSTIC_ONLY_NO_TIMEOUT_NO_RETRY",
            )

    watcher = threading.Thread(
        target=observer,
        name="radar-first-cycle-stall-observer",
        daemon=True,
    )
    observer_started = False
    try:
        watcher.start()
        observer_started = True
    except RuntimeError:
        _emit("OBSERVER_UNAVAILABLE")

    try:
        result = run_cycle()
    except BaseException as exc:
        _emit(
            "FIRST_CYCLE_FAILED",
            elapsed_seconds=round(time.monotonic() - started, 1),
            exception_type=type(exc).__name__,  # No exception message.
        )
        raise
    else:
        health = result.get("health") if isinstance(result, dict) else None
        _emit(
            "FIRST_CYCLE_FINISHED",
            elapsed_seconds=round(time.monotonic() - started, 1),
            health=health if health in {"OK", "STARTING", "DEGRADED_FAIL_CLOSED"} else "UNCLASSIFIED",
        )
        return result
    finally:
        stop.set()
        if observer_started:
            watcher.join(timeout=1.0)
