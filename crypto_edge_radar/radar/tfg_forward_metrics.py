from __future__ import annotations

from math import isfinite
from typing import Any

MIN_RESOLVED_FORWARD_TRADES = 10


def _profit_factor(values: list[float]) -> tuple[float | None, bool]:
    positive = sum(x for x in values if x > 0)
    negative = -sum(x for x in values if x < 0)
    if negative == 0:
        return (None, positive > 0)
    return positive / negative, False


def _max_additive_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    worst = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        worst = min(worst, equity - peak)
    return worst


def _event_key(payload: dict[str, Any]) -> str:
    key = payload.get("event_key")
    if not isinstance(key, str) or not key:
        raise ValueError("forward evidence payload missing event_key")
    return key


def evaluate_tfg_forward_evidence(store) -> dict[str, Any]:
    signals = store.read_payloads("TFG_FORWARD_SIGNAL")
    resolutions = store.read_payloads("TFG_FORWARD_RESOLUTION")
    deviations = store.read_payloads("TFG_FORWARD_RULE_DEVIATION")
    missed = store.read_payloads("TFG_FORWARD_MISSED_ELIGIBLE_SIGNAL")

    signal_keys = [_event_key(x) for x in signals]
    resolution_keys = [_event_key(x) for x in resolutions]
    unique_signal_keys = set(signal_keys)
    unique_resolution_keys = set(resolution_keys)

    duplicate_signals = len(signal_keys) - len(unique_signal_keys)
    duplicate_resolutions = len(resolution_keys) - len(unique_resolution_keys)
    unresolved_keys = sorted(unique_signal_keys - unique_resolution_keys)

    base_values: list[float] = []
    stress_values: list[float] = []
    for payload in resolutions:
        outcome = payload.get("outcome") or {}
        base = outcome.get("base_net_r")
        stress = outcome.get("stress_net_r")
        if not isinstance(base, (int, float)) or not isinstance(stress, (int, float)):
            raise ValueError("TFG resolution missing base/stress net R")
        base = float(base)
        stress = float(stress)
        if not isfinite(base) or not isfinite(stress):
            raise ValueError("TFG resolution contains non-finite net R")
        base_values.append(base)
        stress_values.append(stress)

    n = len(base_values)
    base_expectancy = sum(base_values) / n if n else None
    stress_expectancy = sum(stress_values) / n if n else None
    base_pf, base_pf_inf = _profit_factor(base_values)
    stress_pf, stress_pf_inf = _profit_factor(stress_values)

    enough = n >= MIN_RESOLVED_FORWARD_TRADES
    base_expectancy_pass = base_expectancy is not None and base_expectancy > 0
    stress_expectancy_pass = stress_expectancy is not None and stress_expectancy > 0
    base_pf_pass = base_pf_inf or (base_pf is not None and base_pf > 1)
    stress_pf_pass = stress_pf_inf or (stress_pf is not None and stress_pf > 1)
    integrity_pass = (
        len(unresolved_keys) == 0
        and len(deviations) == 0
        and len(missed) == 0
        and duplicate_signals == 0
        and duplicate_resolutions == 0
    )

    gate_pass = (
        enough
        and base_expectancy_pass
        and stress_expectancy_pass
        and base_pf_pass
        and stress_pf_pass
        and integrity_pass
    )

    if gate_pass:
        classification = "MICRO_LIVE_RISK_REVIEW_ELIGIBLE"
    elif enough:
        classification = "FORWARD_READINESS_GATE_FAIL"
    else:
        classification = "FORWARD_EVIDENCE_ACCUMULATING"

    return {
        "strategy_id": "TFG-DONCHIAN-REGIME-ADAPTATION-V1",
        "classification": classification,
        "resolved_forward_trades": n,
        "minimum_resolved_forward_trades": MIN_RESOLVED_FORWARD_TRADES,
        "progress": f"{n}/{MIN_RESOLVED_FORWARD_TRADES}",
        "base_expectancy_r": base_expectancy,
        "base_profit_factor": base_pf,
        "base_profit_factor_infinite": base_pf_inf,
        "base_total_r": sum(base_values),
        "base_max_additive_drawdown_r": _max_additive_drawdown(base_values),
        "stress_expectancy_r": stress_expectancy,
        "stress_profit_factor": stress_pf,
        "stress_profit_factor_infinite": stress_pf_inf,
        "stress_total_r": sum(stress_values),
        "stress_max_additive_drawdown_r": _max_additive_drawdown(stress_values),
        "unresolved_execution_paths": len(unresolved_keys),
        "unresolved_event_keys": unresolved_keys,
        "rule_deviations": len(deviations),
        "missed_eligible_signals": len(missed),
        "duplicate_signals": duplicate_signals,
        "duplicate_resolutions": duplicate_resolutions,
        "gate_checks": {
            "minimum_resolved_filtered_forward_trades_gte_10": enough,
            "base_expectancy_r_gt_0": base_expectancy_pass,
            "base_profit_factor_gt_1": base_pf_pass,
            "stress_expectancy_r_gt_0": stress_expectancy_pass,
            "stress_profit_factor_gt_1": stress_pf_pass,
            "unresolved_execution_paths_eq_0": len(unresolved_keys) == 0,
            "rule_deviations_eq_0": len(deviations) == 0,
            "missed_eligible_signals_eq_0": len(missed) == 0,
            "duplicate_signals_eq_0": duplicate_signals == 0,
        },
        "readiness_gate_pass": gate_pass,
        "live_trading_automatically_authorized": False,
        "next_state_if_pass": "MICRO_LIVE_RISK_REVIEW_ELIGIBLE",
    }
