"""Blind state-count gate for MRCR H02 outcome reveal.

This module deliberately contains no future-return field.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


ACCEPTANCE = "ACCEPTANCE"
REJECTION = "REJECTION"
ABSTAIN = "ABSTAIN"

EVENT_MINIMA = {
    "US_CPI": 10,
    "US_EMPLOYMENT_SITUATION": 10,
    "FOMC_STATEMENT": 6,
}
MIN_STATE_UNITS = 10
MIN_DISTINCT_CLASSIFIED_EVENTS = 20


@dataclass(frozen=True)
class DecisionStateLabel:
    event_id: str
    event_family: str
    asset: str
    state: str


@dataclass(frozen=True)
class RevealGateResult:
    action: str
    blockers: tuple[str, ...]
    acceptance_units: int
    rejection_units: int
    distinct_classified_events: int


def evaluate_reveal_gate(
    labels: Sequence[DecisionStateLabel],
    *,
    eligible_event_family_counts: Mapping[str, int],
    official_2027_calendar_exhausted: bool,
) -> RevealGateResult:
    blockers: list[str] = []
    for family, minimum in EVENT_MINIMA.items():
        if int(eligible_event_family_counts.get(family, 0)) < minimum:
            blockers.append(f"EVENT_FAMILY_MINIMUM_NOT_MET:{family}")

    acceptance = sum(row.state == ACCEPTANCE for row in labels)
    rejection = sum(row.state == REJECTION for row in labels)
    if acceptance < MIN_STATE_UNITS:
        blockers.append("ACCEPTANCE_STATE_MINIMUM_NOT_MET")
    if rejection < MIN_STATE_UNITS:
        blockers.append("REJECTION_STATE_MINIMUM_NOT_MET")

    event_ids = {
        row.event_id
        for row in labels
        if row.state in {ACCEPTANCE, REJECTION}
    }
    if len(event_ids) < MIN_DISTINCT_CLASSIFIED_EVENTS:
        blockers.append("DISTINCT_CLASSIFIED_EVENT_MINIMUM_NOT_MET")

    if not blockers:
        action = "READY_FOR_SINGLE_OUTCOME_REVEAL"
    elif official_2027_calendar_exhausted:
        action = "CLOSE_INSUFFICIENT_SAMPLE_WITHOUT_OUTCOME_REVEAL"
    else:
        action = "HOLD_OUTCOMES_LOCKED_CONTINUE_BLIND_COLLECTION"

    return RevealGateResult(
        action=action,
        blockers=tuple(sorted(blockers)),
        acceptance_units=acceptance,
        rejection_units=rejection,
        distinct_classified_events=len(event_ids),
    )
