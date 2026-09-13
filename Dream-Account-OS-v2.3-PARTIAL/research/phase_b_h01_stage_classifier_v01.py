from __future__ import annotations

"""Pure H01 stage classifier.

This module classifies already-produced H01 evidence only. It does not authorize or
open market data, does not contain a 2026 holdout path, and cannot authorize live or
exchange execution.
"""

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from math import isfinite

from research.phase_b_h01_research_evaluator_v01 import BASE_COHORT_SOURCE
from research.phase_b_research_evaluator_v01 import (
    BootstrapInterval,
    EvaluationMetrics,
    FixedCohortCostMetrics,
)


HYPOTHESIS_ID = "H01_PROTECT_AFTER_TP1_NEXT_BAR"
BASE_COST_SCENARIO = "BASE_SENSITIVITY"
STRESS_COST_SCENARIO = "STRESS"
DISCOVERY_MIN_RESOLVED_TRADES = 100
VALIDATION_MIN_RESOLVED_TRADES = 30
LIVE_AUTHORIZED = False
EXCHANGE_MUTATION_AUTHORIZED = False
HOLDOUT_2026_AUTHORIZED = False


class H01ResearchStage(str, Enum):
    DISCOVERY = "DISCOVERY"
    VALIDATION = "VALIDATION"


class H01StageClassification(str, Enum):
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    NO_EDGE = "NO_EDGE"
    SURVIVES = "SURVIVES"


@dataclass(frozen=True)
class H01StageDecision:
    stage: str
    hypothesis_id: str
    classification: str
    resolved_trade_count: int
    minimum_required_trades: int
    base_net_expectancy_r: float | None
    base_profit_factor_r: float | None
    base_bootstrap_lower_95: float | None
    fixed_cohort_stress_net_expectancy_r: float | None
    failed_conditions: tuple[str, ...]
    validation_unlock_eligible: bool
    holdout_2026_unlock_eligible: bool
    live_authorized: bool
    exchange_mutation_authorized: bool
    submitted_to_exchange: bool
    fingerprint: str


def _finite(value: float | None, name: str) -> float:
    if (
        value is None
        or not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not isfinite(value)
    ):
        raise ValueError(f"required evidence {name} must be finite and available")
    return float(value)


def _minimum(stage: H01ResearchStage) -> int:
    if stage is H01ResearchStage.DISCOVERY:
        return DISCOVERY_MIN_RESOLVED_TRADES
    if stage is H01ResearchStage.VALIDATION:
        return VALIDATION_MIN_RESOLVED_TRADES
    raise ValueError("unsupported H01 research stage")


def _fingerprint(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def assert_h01_classification_stage_access(
    stage: H01ResearchStage,
    *,
    discovery_classification: H01StageClassification | None = None,
) -> None:
    """Guard classification order only; this function never grants data access."""

    if stage is H01ResearchStage.DISCOVERY:
        return
    if stage is H01ResearchStage.VALIDATION:
        if discovery_classification is not H01StageClassification.SURVIVES:
            raise PermissionError(
                "H01 Validation classification is locked until unchanged H01 Discovery SURVIVES"
            )
        return
    raise ValueError("unsupported H01 research stage")


def classify_h01_stage(
    stage: H01ResearchStage,
    base_metrics: EvaluationMetrics,
    stress_fixed_cohort: FixedCohortCostMetrics,
    base_bootstrap: BootstrapInterval,
    *,
    hypothesis_id: str = HYPOTHESIS_ID,
    discovery_classification: H01StageClassification | None = None,
) -> H01StageDecision:
    """Apply the frozen H01 decision policy to already-produced offline evidence."""

    if hypothesis_id != HYPOTHESIS_ID:
        raise ValueError("only the frozen H01 hypothesis may receive this classification")
    assert_h01_classification_stage_access(
        stage,
        discovery_classification=discovery_classification,
    )
    if base_metrics.cost_scenario != BASE_COST_SCENARIO:
        raise ValueError("base metrics must use BASE_SENSITIVITY")
    if stress_fixed_cohort.cost_scenario != STRESS_COST_SCENARIO:
        raise ValueError("stress evidence must use STRESS")
    if stress_fixed_cohort.cohort_source != BASE_COHORT_SOURCE:
        raise ValueError("stress evidence must reprice the fixed BASE-selected H01 cohort")
    if stress_fixed_cohort.selected_trade_count != base_metrics.selected_trade_count:
        raise ValueError("stress evidence cohort size must match BASE-selected H01 cohort")
    if stress_fixed_cohort.resolved_trade_count != base_metrics.resolved_trade_count:
        raise ValueError("stress evidence resolved count must match BASE-resolved H01 cohort")
    if base_bootstrap.method != "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP":
        raise ValueError("bootstrap method mismatch")
    if base_bootstrap.confidence != 0.95:
        raise ValueError("bootstrap confidence must be 0.95")
    if base_bootstrap.repetitions != 5000:
        raise ValueError("bootstrap repetitions must equal frozen 5000")
    if base_bootstrap.seed != 230911:
        raise ValueError("bootstrap seed mismatch")

    minimum = _minimum(stage)
    resolved_count = base_metrics.resolved_trade_count
    if (
        not isinstance(resolved_count, int)
        or isinstance(resolved_count, bool)
        or resolved_count < 0
    ):
        raise ValueError("resolved_trade_count must be a non-negative integer")

    if resolved_count < minimum:
        classification = H01StageClassification.INSUFFICIENT_SAMPLE
        failed_conditions = (f"resolved_trade_count_below_{minimum}",)
        base_expectancy = base_metrics.net_expectancy_r
        base_pf = base_metrics.profit_factor_r
        bootstrap_lower = base_bootstrap.lower
        stress_expectancy = stress_fixed_cohort.net_expectancy_r
    else:
        base_expectancy = _finite(base_metrics.net_expectancy_r, "base_net_expectancy_r")
        base_pf = _finite(base_metrics.profit_factor_r, "base_profit_factor_r")
        bootstrap_lower = _finite(base_bootstrap.lower, "base_bootstrap_lower_95")
        stress_expectancy = _finite(
            stress_fixed_cohort.net_expectancy_r,
            "fixed_cohort_stress_net_expectancy_r",
        )
        failures: list[str] = []
        if base_expectancy <= 0:
            failures.append("base_net_expectancy_not_positive")
        if base_pf <= 1:
            failures.append("base_profit_factor_not_above_1")
        if bootstrap_lower <= 0:
            failures.append("base_bootstrap_lower_95_not_positive")
        if stress_expectancy <= 0:
            failures.append("fixed_cohort_stress_expectancy_not_positive")
        failed_conditions = tuple(failures)
        classification = (
            H01StageClassification.NO_EDGE
            if failures
            else H01StageClassification.SURVIVES
        )

    validation_unlock_eligible = (
        stage is H01ResearchStage.DISCOVERY
        and classification is H01StageClassification.SURVIVES
    )
    payload = {
        "stage": stage.value,
        "hypothesis_id": hypothesis_id,
        "classification": classification.value,
        "resolved_trade_count": resolved_count,
        "minimum_required_trades": minimum,
        "base_net_expectancy_r": base_expectancy,
        "base_profit_factor_r": base_pf,
        "base_bootstrap_lower_95": bootstrap_lower,
        "fixed_cohort_stress_net_expectancy_r": stress_expectancy,
        "failed_conditions": failed_conditions,
        "validation_unlock_eligible": validation_unlock_eligible,
        "holdout_2026_unlock_eligible": False,
        "live_authorized": LIVE_AUTHORIZED,
        "exchange_mutation_authorized": EXCHANGE_MUTATION_AUTHORIZED,
        "submitted_to_exchange": False,
    }
    return H01StageDecision(**payload, fingerprint=_fingerprint(payload))


def decision_as_dict(decision: H01StageDecision) -> dict:
    return asdict(decision)
