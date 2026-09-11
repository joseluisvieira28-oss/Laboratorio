from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class H04Decision:
    classification:str
    failed_conditions:tuple[str,...]
    holdout_2026_unlock_eligible:bool

def classify(metrics, stress, bootstrap, mechanism, mechanism_bootstrap, minimum=100):
    if metrics.resolved_trade_count < minimum:
        return H04Decision('INSUFFICIENT_SAMPLE',('minimum_resolved_h04_trade_count_not_met',),False)
    failed=[]
    if metrics.net_expectancy_r is None or metrics.net_expectancy_r<=0: failed.append('base_net_expectancy_not_positive')
    if metrics.profit_factor_r is None or metrics.profit_factor_r<=1: failed.append('base_profit_factor_not_above_1')
    if bootstrap.get('lower') is None or bootstrap['lower']<=0: failed.append('base_bootstrap_lower_95_not_positive')
    if stress.net_expectancy_r is None or stress.net_expectancy_r<=0: failed.append('fixed_cohort_stress_expectancy_not_positive')
    if mechanism.tp1_rate_difference is None or mechanism.tp1_rate_difference<=0: failed.append('mechanism_tp1_rate_difference_not_positive')
    if mechanism_bootstrap.get('lower') is None or mechanism_bootstrap['lower']<=0: failed.append('mechanism_bootstrap_lower_95_not_positive')
    return H04Decision('NO_EDGE' if failed else 'SURVIVES',tuple(failed),not failed)

def decision_as_dict(d): return asdict(d)
