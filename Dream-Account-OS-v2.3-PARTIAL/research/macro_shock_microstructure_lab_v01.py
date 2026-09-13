"""Macro Shock Microstructure Lab V0.1 — pre-holdout scientific core.

This module is intentionally OFFLINE and data-source agnostic. It implements only
mathematics and governance frozen in
MACRO_SHOCK_MICROSTRUCTURE_LAB_V01_PROSPECTIVE_RESEARCH_CONTRACT.json.

It MUST NOT fetch market data, access 2026 outcomes, mutate an exchange, or place
orders. Data acquisition and any future holdout execution require a separate,
explicit authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math
import random
from typing import Iterable, Sequence


ALLOWED_SYMBOLS = ("BTCUSDT", "ETHUSDT")
ALLOWED_EVENT_FAMILIES = ("US_CPI", "US_NFP", "US_FOMC")
CONTROL_LAGS_DAYS = (7, 14, 21, 28, 35, 42, 49, 56)
MIN_VALID_CONTROLS_PER_EVENT_SYMBOL = 4
MIN_RESOLVED_EVENT_SYMBOL_CASES = 30
MIN_DISTINCT_EVENT_DATES = 20
BOOTSTRAP_REPETITIONS = 5000


class ContractViolation(ValueError):
    """Raised when inputs violate the prospectively frozen contract."""


@dataclass(frozen=True)
class ClusterRecord:
    """One event-date cluster used by the frozen cluster bootstrap.

    event_successes contains resolved event-symbol binary outcomes for the date.
    control_successes contains matched non-event binary outcomes associated with
    those resolved event-symbol cases.
    """

    event_date: str
    event_successes: tuple[int, ...]
    control_successes: tuple[int, ...]


@dataclass(frozen=True)
class ClassificationResult:
    classification: str
    reason: str


def _binary(values: Iterable[int]) -> tuple[int, ...]:
    out = tuple(int(v) for v in values)
    if any(v not in (0, 1) for v in out):
        raise ContractViolation("continuation outcomes must be binary 0/1")
    return out


def sign(value: float) -> int:
    """Frozen sign rule: positive=>+1, negative=>-1, exact zero=>0."""
    if not math.isfinite(value):
        raise ContractViolation("non-finite value")
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def normalized_taker_flow(taker_buy_quote_notional: float, taker_sell_quote_notional: float) -> float:
    """Compute frozen normalized flow.

    normalized_flow = (buy_quote_notional - sell_quote_notional) /
                      (buy_quote_notional + sell_quote_notional)
    """
    buy = float(taker_buy_quote_notional)
    sell = float(taker_sell_quote_notional)
    if not math.isfinite(buy) or not math.isfinite(sell):
        raise ContractViolation("non-finite taker quote notional")
    if buy < 0 or sell < 0:
        raise ContractViolation("taker quote notionals cannot be negative")
    total = buy + sell
    if total == 0:
        return 0.0
    return (buy - sell) / total


def persistent_flow_sign(flow_window_1: float, flow_window_2: float) -> int:
    """Return +/-1 only when both pre-specified flow windows are nonzero and same-sign."""
    s1 = sign(flow_window_1)
    s2 = sign(flow_window_2)
    return s1 if s1 != 0 and s1 == s2 else 0


def outcome_return(close_at_15m: float, close_at_30m: float) -> float:
    """Frozen outcome: close_at_30m / close_at_15m - 1."""
    c15 = float(close_at_15m)
    c30 = float(close_at_30m)
    if not math.isfinite(c15) or not math.isfinite(c30) or c15 <= 0 or c30 <= 0:
        raise ContractViolation("outcome closes must be finite and positive")
    return c30 / c15 - 1.0


def continuation_success(close_at_15m: float, close_at_30m: float, persistent_sign: int) -> int:
    """Frozen binary continuation metric; zero return is failure."""
    if persistent_sign not in (-1, 1):
        raise ContractViolation("resolved case requires persistent flow sign +/-1")
    r = outcome_return(close_at_15m, close_at_30m)
    return int(r != 0.0 and sign(r) == persistent_sign)


def candidate_control_timestamps(event_timestamp_utc: datetime) -> tuple[datetime, ...]:
    """Frozen control candidates: same UTC clock time/weekday at 7..56 day lags."""
    if event_timestamp_utc.tzinfo is None or event_timestamp_utc.utcoffset() is None:
        raise ContractViolation("event timestamp must be timezone-aware UTC")
    if event_timestamp_utc.utcoffset().total_seconds() != 0:
        raise ContractViolation("event timestamp must be UTC")
    return tuple(event_timestamp_utc - timedelta(days=d) for d in CONTROL_LAGS_DAYS)


def filter_valid_controls(
    event_timestamp_utc: datetime,
    frozen_macro_event_timestamps_utc: Sequence[datetime],
) -> tuple[datetime, ...]:
    """Exclude candidate controls whose 0-30m window overlaps any frozen macro event 0-30m window."""
    candidates = candidate_control_timestamps(event_timestamp_utc)
    events = tuple(frozen_macro_event_timestamps_utc)
    for ts in events:
        if ts.tzinfo is None or ts.utcoffset() is None or ts.utcoffset().total_seconds() != 0:
            raise ContractViolation("all frozen event timestamps must be timezone-aware UTC")

    valid: list[datetime] = []
    thirty = timedelta(minutes=30)
    for candidate in candidates:
        c0, c1 = candidate, candidate + thirty
        overlaps = any(c0 < e + thirty and e < c1 for e in events)
        if not overlaps:
            valid.append(candidate)
    return tuple(valid)


def control_adequacy_pass(valid_control_count: int) -> bool:
    return int(valid_control_count) >= MIN_VALID_CONTROLS_PER_EVENT_SYMBOL


def continuation_rate_difference(event_successes: Iterable[int], control_successes: Iterable[int]) -> float:
    """Frozen primary statistic on resolved persistent-flow cases."""
    event = _binary(event_successes)
    control = _binary(control_successes)
    if not event or not control:
        raise ContractViolation("event and control samples must both be non-empty")
    return sum(event) / len(event) - sum(control) / len(control)


def cluster_bootstrap_difference(
    records: Sequence[ClusterRecord],
    repetitions: int = BOOTSTRAP_REPETITIONS,
    seed: int = 1729,
) -> tuple[float, float, float]:
    """Two-sided 95% event-date cluster bootstrap for the primary statistic.

    Clusters (event dates) are sampled with replacement. All event/control binary
    outcomes inside a sampled date are carried together. A deterministic seed is
    used only for reproducibility of the implementation test; it is not a tuning
    parameter.
    """
    if repetitions != BOOTSTRAP_REPETITIONS:
        raise ContractViolation("bootstrap repetitions are frozen at 5000")
    if not records:
        raise ContractViolation("at least one cluster is required")

    validated: list[ClusterRecord] = []
    all_event: list[int] = []
    all_control: list[int] = []
    for rec in records:
        ev = _binary(rec.event_successes)
        ct = _binary(rec.control_successes)
        if not ev or not ct:
            raise ContractViolation("each bootstrap cluster must contain event and control outcomes")
        validated.append(ClusterRecord(rec.event_date, ev, ct))
        all_event.extend(ev)
        all_control.extend(ct)

    point = continuation_rate_difference(all_event, all_control)
    rng = random.Random(seed)
    n = len(validated)
    draws: list[float] = []
    for _ in range(repetitions):
        e: list[int] = []
        c: list[int] = []
        for _j in range(n):
            rec = validated[rng.randrange(n)]
            e.extend(rec.event_successes)
            c.extend(rec.control_successes)
        draws.append(continuation_rate_difference(e, c))

    draws.sort()
    # Deterministic nearest-rank-style endpoints, adequate for the frozen 5000 draws.
    low = draws[int(0.025 * repetitions)]
    high = draws[int(0.975 * repetitions) - 1]
    return point, low, high


def classify(
    *,
    data_integrity_pass: bool,
    resolved_event_symbol_cases: int,
    distinct_macro_event_dates: int,
    point_estimate: float | None,
    ci_lower_bound: float | None,
) -> ClassificationResult:
    """Apply the frozen classification contract exactly."""
    if not data_integrity_pass:
        return ClassificationResult(
            "TECHNICAL_OR_DATA_FAILURE",
            "required data-integrity/governance gate failed",
        )

    if (
        int(resolved_event_symbol_cases) < MIN_RESOLVED_EVENT_SYMBOL_CASES
        or int(distinct_macro_event_dates) < MIN_DISTINCT_EVENT_DATES
    ):
        return ClassificationResult(
            "INSUFFICIENT_SAMPLE",
            "minimum sample contract not met",
        )

    if point_estimate is None or ci_lower_bound is None:
        return ClassificationResult(
            "TECHNICAL_OR_DATA_FAILURE",
            "primary statistic or confidence interval missing",
        )
    if not math.isfinite(point_estimate) or not math.isfinite(ci_lower_bound):
        return ClassificationResult(
            "TECHNICAL_OR_DATA_FAILURE",
            "primary statistic or confidence interval non-finite",
        )

    if point_estimate > 0.0 and ci_lower_bound > 0.0:
        return ClassificationResult(
            "SURVIVES",
            "minimum sample met and 95% cluster-bootstrap CI is entirely above zero",
        )

    return ClassificationResult(
        "NO_EDGE",
        "minimum sample met but frozen SURVIVES criteria not met",
    )


def preholdout_governance_receipt() -> dict[str, object]:
    """Static fail-closed receipt for this implementation stage."""
    return {
        "status": "PRE_HOLDOUT_IMPLEMENTATION_ONLY",
        "holdout_2026_accessed": False,
        "mexc_2025_09_through_2025_12_accessed": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "network_access_in_this_module": False,
        "stop_condition": "STOP_BEFORE_2026_OUTCOMES_UNTIL_SEPARATE_EXPLICIT_HOLDOUT_UNLOCK",
    }
