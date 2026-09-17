from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Callable

from .service import PublicShadowService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("scheduler timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class SchedulerDecision:
    sleep_seconds: float
    reason: str
    target_time_utc: str | None = None
    strategy_id: str | None = None


class ExactTimingScheduler:
    """Adaptive scheduler for adapters exposing timing_plan(now).

    Normal observation cadence remains intact. When an adapter is ARMED, this
    scheduler wakes the service at the frozen target instead of waiting for the
    next coarse polling interval. It does not submit orders and it never wakes
    *after* a missed window to chase an entry.
    """

    def __init__(
        self,
        *,
        runner: PublicShadowService,
        normal_interval: float = 30.0,
        clock: Callable[[], datetime] = _utc_now,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if normal_interval < 5:
            raise ValueError("normal_interval must be >= 5 seconds")
        self.runner = runner
        self.normal_interval = normal_interval
        self.clock = clock
        self.sleeper = sleeper

    def _plans(self, now: datetime) -> list[dict]:
        plans: list[dict] = []
        for adapter in self.runner.engine.registry.adapters:
            planner = getattr(adapter, "timing_plan", None)
            if planner is None:
                continue
            plan = planner(now)
            if not isinstance(plan, dict):
                raise RuntimeError("timing_plan must return a dict")
            plans.append(plan)
        return plans

    def next_decision(self, now: datetime | None = None) -> SchedulerDecision:
        now = (now or self.clock()).astimezone(timezone.utc)
        best = SchedulerDecision(self.normal_interval, "NORMAL_HEARTBEAT")

        for plan in self._plans(now):
            timing = plan.get("operational_timing") or {}
            state = timing.get("timing_state")
            strategy_id = plan.get("strategy_id")

            if state == "DUE":
                return SchedulerDecision(
                    0.0,
                    "EXACT_ENTRY_DUE_NOW",
                    timing.get("target_time_utc"),
                    strategy_id,
                )

            if state == "ARMED":
                target_raw = timing.get("target_time_utc")
                if not target_raw:
                    raise RuntimeError("armed timing plan missing target_time_utc")
                target = _parse_utc(target_raw)
                delay = max(0.0, (target - now).total_seconds())
                if delay < best.sleep_seconds:
                    best = SchedulerDecision(
                        delay,
                        "WAKE_AT_EXACT_ENTRY",
                        target_raw,
                        strategy_id,
                    )
                continue

            if state == "WAITING":
                arm_raw = timing.get("arm_at_utc")
                if not arm_raw:
                    continue
                arm_at = _parse_utc(arm_raw)
                delay = max(0.0, (arm_at - now).total_seconds())
                if 0.0 < delay < best.sleep_seconds:
                    best = SchedulerDecision(
                        delay,
                        "WAKE_AT_ARM_WINDOW",
                        timing.get("target_time_utc"),
                        strategy_id,
                    )
                continue

            # MISSED is intentionally ignored: normal cadence may refresh the
            # upstream source later, but this scheduler never chases the event.

        return best

    def run(self, max_cycles: int | None = None) -> int:
        if max_cycles is not None and max_cycles <= 0:
            raise ValueError("max_cycles must be > 0")

        overall = 0
        while max_cycles is None or self.runner.cycle_no < max_cycles:
            code, _ = self.runner.run_cycle()
            overall = max(overall, code)
            if max_cycles is not None and self.runner.cycle_no >= max_cycles:
                break

            decision = self.next_decision()
            # A zero-delay DUE state can occur immediately after a pre-target
            # cycle. Yield minimally so the dedicated due cycle gets a fresh
            # market timestamp without spinning the CPU.
            self.sleeper(max(0.001, decision.sleep_seconds))

        return overall
