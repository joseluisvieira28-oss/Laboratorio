"""Frozen MRCR H02 primary outcome and inference helpers.

This module contains no data acquisition and cannot open target outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable, Mapping, Sequence


H02_ACCEPTANCE = "ACCEPTANCE"
H02_REJECTION = "REJECTION"

PRIMARY_DECISION_CLOCK_SECONDS = 180
PRIMARY_FORWARD_HORIZON_SECONDS = 900
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 1729
MIN_STATE_UNITS = 10
MIN_DISTINCT_CLASSIFIED_EVENTS = 20
FIRST_LOOK_EVENT_MINIMA = {
    "US_CPI": 10,
    "US_EMPLOYMENT_SITUATION": 10,
    "FOMC_STATEMENT": 6,
}


@dataclass(frozen=True)
class OutcomeRow:
    event_id: str
    asset: str
    state: str
    signed_forward_return_bps: float


@dataclass(frozen=True)
class SampleGate:
    ready: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class PrimaryResult:
    acceptance_mean_bps: float
    rejection_mean_bps: float
    contrast_bps: float
    ci_lower_bps: float
    ci_upper_bps: float
    classification: str


def signed_forward_return_bps(
    *,
    decision_mid: float,
    outcome_mid: float,
    direction: int,
) -> float:
    if decision_mid <= 0 or outcome_mid <= 0:
        raise ValueError("mid prices must be > 0")
    if direction not in {-1, 1}:
        raise ValueError("direction must be -1 or 1")
    return direction * math.log(outcome_mid / decision_mid) * 10_000.0


def sample_gate(
    rows: Sequence[OutcomeRow],
    *,
    eligible_event_family_counts: Mapping[str, int],
) -> SampleGate:
    blockers: list[str] = []

    for family, minimum in FIRST_LOOK_EVENT_MINIMA.items():
        if int(eligible_event_family_counts.get(family, 0)) < minimum:
            blockers.append(f"EVENT_FAMILY_MINIMUM_NOT_MET:{family}")

    acceptance = sum(row.state == H02_ACCEPTANCE for row in rows)
    rejection = sum(row.state == H02_REJECTION for row in rows)
    if acceptance < MIN_STATE_UNITS:
        blockers.append("ACCEPTANCE_STATE_MINIMUM_NOT_MET")
    if rejection < MIN_STATE_UNITS:
        blockers.append("REJECTION_STATE_MINIMUM_NOT_MET")

    classified_events = {
        row.event_id
        for row in rows
        if row.state in {H02_ACCEPTANCE, H02_REJECTION}
    }
    if len(classified_events) < MIN_DISTINCT_CLASSIFIED_EVENTS:
        blockers.append("DISTINCT_CLASSIFIED_EVENT_MINIMUM_NOT_MET")

    return SampleGate(
        ready=not blockers,
        blockers=tuple(sorted(blockers)),
    )


def _mean(values: Iterable[float]) -> float:
    rows = list(values)
    if not rows:
        raise ValueError("mean requires at least one observation")
    return sum(rows) / len(rows)


def primary_contrast(rows: Sequence[OutcomeRow]) -> float:
    acceptance = [
        row.signed_forward_return_bps
        for row in rows
        if row.state == H02_ACCEPTANCE
    ]
    rejection = [
        row.signed_forward_return_bps
        for row in rows
        if row.state == H02_REJECTION
    ]
    return _mean(acceptance) - _mean(rejection)


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("quantile requires values")
    if q < 0 or q > 1:
        raise ValueError("q must be in [0,1]")
    pos = (len(sorted_values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_values[lo])
    weight = pos - lo
    return (
        float(sorted_values[lo]) * (1.0 - weight)
        + float(sorted_values[hi]) * weight
    )


def cluster_bootstrap_ci(
    rows: Sequence[OutcomeRow],
    *,
    reps: int = BOOTSTRAP_REPS,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    if reps <= 0:
        raise ValueError("reps must be > 0")

    clusters: dict[str, list[OutcomeRow]] = {}
    for row in rows:
        if row.state in {H02_ACCEPTANCE, H02_REJECTION}:
            clusters.setdefault(row.event_id, []).append(row)
    event_ids = sorted(clusters)
    if len(event_ids) < 2:
        raise ValueError("at least two event clusters are required")

    rng = random.Random(seed)
    diffs: list[float] = []
    attempts = 0
    max_attempts = reps * 50

    while len(diffs) < reps and attempts < max_attempts:
        attempts += 1
        sampled: list[OutcomeRow] = []
        for _ in event_ids:
            event_id = event_ids[rng.randrange(len(event_ids))]
            sampled.extend(clusters[event_id])
        states = {row.state for row in sampled}
        if not {H02_ACCEPTANCE, H02_REJECTION}.issubset(states):
            continue
        diffs.append(primary_contrast(sampled))

    if len(diffs) != reps:
        raise RuntimeError("unable to obtain requested valid bootstrap replicates")

    diffs.sort()
    return _quantile(diffs, 0.025), _quantile(diffs, 0.975)


def evaluate_primary(
    rows: Sequence[OutcomeRow],
    *,
    eligible_event_family_counts: Mapping[str, int],
    reps: int = BOOTSTRAP_REPS,
    seed: int = BOOTSTRAP_SEED,
) -> PrimaryResult:
    gate = sample_gate(
        rows,
        eligible_event_family_counts=eligible_event_family_counts,
    )
    if not gate.ready:
        raise ValueError("INSUFFICIENT_SAMPLE:" + ",".join(gate.blockers))

    acceptance_mean = _mean(
        row.signed_forward_return_bps
        for row in rows
        if row.state == H02_ACCEPTANCE
    )
    rejection_mean = _mean(
        row.signed_forward_return_bps
        for row in rows
        if row.state == H02_REJECTION
    )
    contrast = acceptance_mean - rejection_mean
    lower, upper = cluster_bootstrap_ci(rows, reps=reps, seed=seed)

    if lower > 0:
        classification = "H02_SUPPORTED"
    elif upper < 0:
        classification = "H02_WRONG_SIGN"
    else:
        classification = "H02_NO_EDGE"

    return PrimaryResult(
        acceptance_mean_bps=acceptance_mean,
        rejection_mean_bps=rejection_mean,
        contrast_bps=contrast,
        ci_lower_bps=lower,
        ci_upper_bps=upper,
        classification=classification,
    )
