"""Availability-time guards for future prospective MRCR observations.

These helpers do not select a decision clock. They ensure that data was both
source-dated and actually available to the collector by a caller-supplied
decision boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class AvailabilityCheck:
    source_time_ns: int
    collector_arrival_ns: int
    effective_available_ns: int


def effective_available_ns(
    *,
    source_time_ns: int,
    collector_arrival_ns: int,
) -> int:
    source = int(source_time_ns)
    arrival = int(collector_arrival_ns)
    return max(source, arrival)


def assert_available_by_decision(
    rows: Iterable[T],
    *,
    source_time_ns: Callable[[T], int],
    collector_arrival_ns: Callable[[T], int | None],
    decision_ns: int,
    require_arrival_provenance: bool = True,
) -> tuple[AvailabilityCheck, ...]:
    checks: list[AvailabilityCheck] = []
    decision = int(decision_ns)

    for row in rows:
        source = int(source_time_ns(row))
        raw_arrival = collector_arrival_ns(row)

        if raw_arrival is None:
            if require_arrival_provenance:
                raise ValueError("collector arrival provenance is required")
            arrival = source
        else:
            arrival = int(raw_arrival)

        effective = effective_available_ns(
            source_time_ns=source,
            collector_arrival_ns=arrival,
        )

        if source > decision:
            raise ValueError(
                f"source timestamp exceeds decision boundary: source={source}, decision={decision}"
            )
        if arrival > decision:
            raise ValueError(
                "collector arrival exceeds decision boundary: "
                f"arrival={arrival}, decision={decision}"
            )
        if effective > decision:
            raise ValueError(
                "observation was not available by decision boundary: "
                f"effective={effective}, decision={decision}"
            )

        checks.append(
            AvailabilityCheck(
                source_time_ns=source,
                collector_arrival_ns=arrival,
                effective_available_ns=effective,
            )
        )

    return tuple(checks)
