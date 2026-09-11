from __future__ import annotations

"""Pure H03 Binance Discovery classifier.

Classifies already-produced offline H03 evidence only. It does not open market data,
authorize target-venue validation, access 2026, or expose live/exchange routes.
"""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite

from research.phase_b_h03_research_evaluator_v01 import BASE_COHORT_SOURCE, HYPOTHESIS_ID
from research.phase_b_research_evaluator_v01 import BootstrapInterval, EvaluationMetrics, FixedCohortCostMetrics


BASE_COST_SCENARIO = "BASE_SENSITIVITY"
STRESS_COST_SCENARIO = "STRESS"
DISCOVERY_MIN_RESOLVED_TRADES = 100
MEXC_VALIDATION_MIN_RESOLVED_TRADES = 30
LIVE_AUTHORIZED = False
EXCHANGE_MUTATION_AUTHORIZED = False
HOLDOUT_2026_AUTHORIZED = False
MEXC_VALIDATION_DATA_ACCESS_AUTHORIZED = False


@dataclass(frozen=True)
class H03DiscoveryDecision:
    hypothesis_id: str
    classification: str
    resolved_trade_count: int
    minimum_required_trades: int
    base_net_expectancy_r: float | None
    base_profit_factor_r: float | None
    base_bootstrap_lower_95: float | None
    fixed_cohort_stress_net_expectancy_r: float | None
    failed_conditions: tuple[str, ...]
    mexc_target_venue_validation_eligible: bool
    mexc_target_venue_validation_data_access_authorized: bool
    holdout_2026_unlock_eligible: bool
    live_authorized: bool
    exchange_mutation_authorized: bool
    submitted_to_exchange: bool
    fingerprint: str


def _finite(value: float | None, name: str) -> float:
    if value is None or not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
        raise ValueError(f"required evidence {name} must be finite and available")
    return float(value)


def _fingerprint(payload: dict) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def classify_h03_binance_discovery(
    base_metrics: EvaluationMetrics,
    stress_fixed_cohort: FixedCohortCostMetrics,
    base_bootstrap: BootstrapInterval,
    *,
    hypothesis_id: str = HYPOTHESIS_ID,
) -> H03DiscoveryDecision:
    if hypothesis_id != HYPOTHESIS_ID:
        raise ValueError("only frozen H03 may receive this classification")
    if base_metrics.cost_scenario != BASE_COST_SCENARIO:
        raise ValueError("base metrics must use BASE_SENSITIVITY")
    if stress_fixed_cohort.cost_scenario != STRESS_COST_SCENARIO:
        raise ValueError("stress evidence must use STRESS")
    if stress_fixed_cohort.cohort_source != BASE_COHORT_SOURCE:
        raise ValueError("stress evidence must reprice fixed H03 BASE cohort")
    if stress_fixed_cohort.selected_trade_count != base_metrics.selected_trade_count:
        raise ValueError("stress selected count must match H03 BASE cohort")
    if stress_fixed_cohort.resolved_trade_count != base_metrics.resolved_trade_count:
        raise ValueError("stress resolved count must match H03 BASE cohort")
    if (
        base_bootstrap.method != "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP"
        or base_bootstrap.confidence != 0.95
        or base_bootstrap.repetitions != 5000
        or base_bootstrap.seed != 230911
    ):
        raise ValueError("bootstrap protocol mismatch")

    resolved = base_metrics.resolved_trade_count
    if not isinstance(resolved, int) or isinstance(resolved, bool) or resolved < 0:
        raise ValueError("resolved_trade_count must be non-negative integer")

    if resolved < DISCOVERY_MIN_RESOLVED_TRADES:
        classification = "INSUFFICIENT_SAMPLE"
        failed = ("resolved_trade_count_below_100",)
        base_exp = base_metrics.net_expectancy_r
        base_pf = base_metrics.profit_factor_r
        boot_lower = base_bootstrap.lower
        stress_exp = stress_fixed_cohort.net_expectancy_r
    else:
        base_exp = _finite(base_metrics.net_expectancy_r, "base_net_expectancy_r")
        base_pf = _finite(base_metrics.profit_factor_r, "base_profit_factor_r")
        boot_lower = _finite(base_bootstrap.lower, "base_bootstrap_lower_95")
        stress_exp = _finite(stress_fixed_cohort.net_expectancy_r, "stress_net_expectancy_r")
        failures: list[str] = []
        if base_exp <= 0:
            failures.append("base_net_expectancy_not_positive")
        if base_pf <= 1:
            failures.append("base_profit_factor_not_above_1")
        if boot_lower <= 0:
            failures.append("base_bootstrap_lower_95_not_positive")
        if stress_exp <= 0:
            failures.append("fixed_cohort_stress_expectancy_not_positive")
        failed = tuple(failures)
        classification = "NO_EDGE" if failures else "SURVIVES"

    eligible = classification == "SURVIVES"
    payload = {
        "hypothesis_id": HYPOTHESIS_ID,
        "classification": classification,
        "resolved_trade_count": resolved,
        "minimum_required_trades": DISCOVERY_MIN_RESOLVED_TRADES,
        "base_net_expectancy_r": base_exp,
        "base_profit_factor_r": base_pf,
        "base_bootstrap_lower_95": boot_lower,
        "fixed_cohort_stress_net_expectancy_r": stress_exp,
        "failed_conditions": failed,
        "mexc_target_venue_validation_eligible": eligible,
        "mexc_target_venue_validation_data_access_authorized": False,
        "holdout_2026_unlock_eligible": False,
        "live_authorized": False,
        "exchange_mutation_authorized": False,
        "submitted_to_exchange": False,
    }
    return H03DiscoveryDecision(**payload, fingerprint=_fingerprint(payload))


def decision_as_dict(decision: H03DiscoveryDecision) -> dict:
    return asdict(decision)
