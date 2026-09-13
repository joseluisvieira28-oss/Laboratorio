from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from math import isfinite

from research.phase_b_research_evaluator_v01 import (
    BootstrapInterval,
    EvaluationMetrics,
    FixedCohortCostMetrics,
)


PRIMARY_PROFILE_ID = "P00_PRIMARY"
BASE_COST_SCENARIO = "BASE_SENSITIVITY"
STRESS_COST_SCENARIO = "STRESS"
DISCOVERY_MIN_RESOLVED_TRADES = 100
VALIDATION_MIN_RESOLVED_TRADES = 30
LIVE_AUTHORIZED = False


class ResearchStage(str, Enum):
    DISCOVERY = "DISCOVERY"
    VALIDATION = "VALIDATION"


class StageClassification(str, Enum):
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    NO_EDGE = "NO_EDGE"
    SURVIVES = "SURVIVES"


@dataclass(frozen=True)
class StageDecision:
    stage: str
    profile_id: str
    classification: str
    resolved_trade_count: int
    minimum_required_trades: int
    base_net_expectancy_r: float | None
    base_profit_factor_r: float | None
    base_bootstrap_lower_95: float | None
    fixed_cohort_stress_net_expectancy_r: float | None
    failed_conditions: tuple[str, ...]
    next_stage_unlocked: bool
    live_authorized: bool
    submitted_to_exchange: bool
    fingerprint: str


def _finite(value: float | None, name: str) -> float:
    if value is None or not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
        raise ValueError(f"required evidence {name} must be finite and available")
    return float(value)


def _minimum(stage: ResearchStage) -> int:
    if stage is ResearchStage.DISCOVERY:
        return DISCOVERY_MIN_RESOLVED_TRADES
    if stage is ResearchStage.VALIDATION:
        return VALIDATION_MIN_RESOLVED_TRADES
    raise ValueError("unsupported research stage")


def _fingerprint(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def assert_stage_access(
    stage: ResearchStage,
    *,
    discovery_classification: StageClassification | None = None,
) -> None:
    """Fail closed before any stage-specific data is read.

    Discovery is the only initially accessible historical stage. Validation may be
    read only after unchanged P00 discovery is machine-classified SURVIVES.
    2026 holdout access is intentionally not represented here and therefore cannot
    be unlocked by this module.
    """

    if stage is ResearchStage.DISCOVERY:
        return
    if stage is ResearchStage.VALIDATION:
        if discovery_classification is not StageClassification.SURVIVES:
            raise PermissionError("2025 validation is locked until P00 discovery SURVIVES")
        return
    raise ValueError("unsupported research stage")


def classify_stage(
    stage: ResearchStage,
    base_metrics: EvaluationMetrics,
    stress_fixed_cohort: FixedCohortCostMetrics,
    base_bootstrap: BootstrapInterval,
    *,
    profile_id: str = PRIMARY_PROFILE_ID,
) -> StageDecision:
    if profile_id != PRIMARY_PROFILE_ID:
        raise ValueError("only P00_PRIMARY may receive a stage classification")
    if base_metrics.cost_scenario != BASE_COST_SCENARIO:
        raise ValueError("base metrics must use BASE_SENSITIVITY")
    if stress_fixed_cohort.cost_scenario != STRESS_COST_SCENARIO:
        raise ValueError("stress evidence must use STRESS")
    if stress_fixed_cohort.cohort_source != "BASE_SENSITIVITY_SELECTED_P00_TRADES":
        raise ValueError("stress evidence must reprice the fixed BASE-selected P00 cohort")
    if stress_fixed_cohort.selected_trade_count != base_metrics.selected_trade_count:
        raise ValueError("stress evidence cohort size must match BASE-selected cohort")
    if stress_fixed_cohort.resolved_trade_count != base_metrics.resolved_trade_count:
        raise ValueError("stress evidence resolved count must match BASE-resolved cohort")
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
    if not isinstance(resolved_count, int) or isinstance(resolved_count, bool) or resolved_count < 0:
        raise ValueError("resolved_trade_count must be a non-negative integer")

    if resolved_count < minimum:
        classification = StageClassification.INSUFFICIENT_SAMPLE
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
        classification = StageClassification.NO_EDGE if failures else StageClassification.SURVIVES

    next_stage_unlocked = stage is ResearchStage.DISCOVERY and classification is StageClassification.SURVIVES
    payload = {
        "stage": stage.value,
        "profile_id": profile_id,
        "classification": classification.value,
        "resolved_trade_count": resolved_count,
        "minimum_required_trades": minimum,
        "base_net_expectancy_r": base_expectancy,
        "base_profit_factor_r": base_pf,
        "base_bootstrap_lower_95": bootstrap_lower,
        "fixed_cohort_stress_net_expectancy_r": stress_expectancy,
        "failed_conditions": failed_conditions,
        "next_stage_unlocked": next_stage_unlocked,
        "live_authorized": LIVE_AUTHORIZED,
        "submitted_to_exchange": False,
    }
    return StageDecision(**payload, fingerprint=_fingerprint(payload))


def decision_as_dict(decision: StageDecision) -> dict:
    return asdict(decision)
