from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class TimingState(str, Enum):
    WAITING = "WAITING"
    ARMED = "ARMED"
    DUE = "DUE"
    MISSED = "MISSED"


@dataclass(frozen=True)
class ExactTimingPolicy:
    """Prospectively frozen operational timing layer.

    This is not a scientific signal rule and must not be used to rescue a late
    historical entry. It only defines when infrastructure may treat an exact
    frozen timestamp as technically executable.
    """

    arm_lead_seconds: float = 60.0
    max_late_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.arm_lead_seconds <= 0:
            raise ValueError("arm_lead_seconds must be > 0")
        if self.max_late_seconds < 0:
            raise ValueError("max_late_seconds must be >= 0")

    def classify(self, *, now: datetime, target: datetime) -> TimingState:
        now = _utc(now)
        target = _utc(target)
        arm_at = target - timedelta(seconds=self.arm_lead_seconds)
        expires_at = target + timedelta(seconds=self.max_late_seconds)

        if now < arm_at:
            return TimingState.WAITING
        if now < target:
            return TimingState.ARMED
        if now <= expires_at:
            return TimingState.DUE
        return TimingState.MISSED

    def receipt(self, *, now: datetime, target: datetime) -> dict:
        now = _utc(now)
        target = _utc(target)
        state = self.classify(now=now, target=target)
        return {
            "timing_state": state.value,
            "target_time_utc": _iso(target),
            "arm_at_utc": _iso(target - timedelta(seconds=self.arm_lead_seconds)),
            "expires_at_utc": _iso(target + timedelta(seconds=self.max_late_seconds)),
            "arm_lead_seconds": self.arm_lead_seconds,
            "max_late_seconds": self.max_late_seconds,
            "observed_at_utc": _iso(now),
            "entry_window_open": state is TimingState.DUE,
            "late_chase_allowed": False,
        }


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")
