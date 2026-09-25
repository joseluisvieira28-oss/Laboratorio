"""Clock-integrity diagnostics for future MRCR prospective capture.

This module measures wall-clock versus monotonic-clock consistency without
selecting any scientific threshold. It is infrastructure provenance only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ClockSample:
    wall_ns: int
    monotonic_ns: int


@dataclass(frozen=True)
class ClockTransition:
    wall_delta_ns: int
    monotonic_delta_ns: int
    residual_ns: int
    wall_reversed: bool
    monotonic_reversed: bool


def transition(previous: ClockSample, current: ClockSample) -> ClockTransition:
    wall_delta = int(current.wall_ns) - int(previous.wall_ns)
    mono_delta = int(current.monotonic_ns) - int(previous.monotonic_ns)
    return ClockTransition(
        wall_delta_ns=wall_delta,
        monotonic_delta_ns=mono_delta,
        residual_ns=wall_delta - mono_delta,
        wall_reversed=wall_delta < 0,
        monotonic_reversed=mono_delta < 0,
    )


def analyze_clock_samples(samples: Iterable[ClockSample]) -> tuple[ClockTransition, ...]:
    rows = tuple(samples)
    if len(rows) < 2:
        return ()

    out: list[ClockTransition] = []
    previous = rows[0]
    for current in rows[1:]:
        item = transition(previous, current)
        if item.monotonic_reversed:
            raise ValueError("monotonic clock reversed")
        out.append(item)
        previous = current
    return tuple(out)


def summarize_clock_transitions(
    transitions: Iterable[ClockTransition],
) -> dict[str, int | bool | None]:
    rows = tuple(transitions)
    if not rows:
        return {
            "sample_transition_count": 0,
            "wall_reversal_seen": False,
            "monotonic_reversal_seen": False,
            "min_residual_ns": None,
            "max_residual_ns": None,
            "max_abs_residual_ns": None,
        }

    residuals = [row.residual_ns for row in rows]
    return {
        "sample_transition_count": len(rows),
        "wall_reversal_seen": any(row.wall_reversed for row in rows),
        "monotonic_reversal_seen": any(row.monotonic_reversed for row in rows),
        "min_residual_ns": min(residuals),
        "max_residual_ns": max(residuals),
        "max_abs_residual_ns": max(abs(value) for value in residuals),
    }
