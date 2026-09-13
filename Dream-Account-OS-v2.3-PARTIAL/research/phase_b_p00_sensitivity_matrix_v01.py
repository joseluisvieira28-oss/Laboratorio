from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from dream_account.models import Candle
from research.phase_b_p00_discovery_runner_v01 import (
    END_MONTH,
    FROZEN_UNIVERSE,
    ROOT,
    START_MONTH,
    _cost_from_freeze,
    _freeze_bindings,
    _load_canonical_window,
    _month_sequence,
    _parameters_from_freeze,
    _prefix,
    run_p00_discovery,
)
from research.phase_b_research_evaluator_v01 import day_block_bootstrap_expectancy, evaluate_universe
from research.phase_b_signal_formation_v01 import ResearchParameters, validate_candles


CLOSEOUT_PATH = ROOT / "research" / "PHASE_B_P00_DISCOVERY_CLOSEOUT_V0.1.json"
VERSION = "0.1"
EXPECTED_PROFILE_IDS = (
    "P01_LOOKBACK_48",
    "P02_LOOKBACK_192",
    "P03_ZONE_010_ATR",
    "P04_ZONE_040_ATR",
    "P05_RETEST_1",
    "P06_RETEST_4",
    "P07_STOP_010_ATR",
    "P08_STOP_050_ATR",
    "P09_TP2_25R",
    "P10_TP2_35R",
    "P11_HOLD_48",
    "P12_HOLD_192",
)


@dataclass(frozen=True)
class SensitivityProfileDiagnostic:
    profile_id: str
    change_only: dict[str, Any]
    parameters: dict[str, Any]
    metrics: dict[str, Any]
    bootstrap: dict[str, Any]
    delta_vs_closed_p00: dict[str, Any]
    classification: None
    promotion_eligible: bool
    may_rescue_p00: bool


@dataclass(frozen=True)
class SensitivityMatrixReceipt:
    document_type: str
    version: str
    status: str
    stage: str
    setup_id: str
    closed_profile_id: str
    closed_classification: str
    reproduction_run_fingerprint: str
    reproduction_decision_fingerprint: str
    effective_start_utc_inclusive: str
    effective_end_utc_exclusive: str
    base_cost_scenario: str
    profile_order: tuple[str, ...]
    profiles: tuple[SensitivityProfileDiagnostic, ...]
    governance: dict[str, Any]
    validation_2025_access_performed: bool
    holdout_2026_access_performed: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    submitted_to_exchange: bool
    fingerprint: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _with_fingerprint(receipt: SensitivityMatrixReceipt) -> SensitivityMatrixReceipt:
    payload = asdict(receipt)
    payload.pop("fingerprint", None)
    return replace(receipt, fingerprint=_canonical_hash(payload))


def _validate_sensitivity_freeze(freeze: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    policy = freeze.get("sensitivity_policy", {})
    if policy.get("method") != "ONE_FACTOR_AT_A_TIME":
        raise RuntimeError("sensitivity method is not frozen ONE_FACTOR_AT_A_TIME")
    if policy.get("may_replace_primary_after_results") is not False:
        raise RuntimeError("sensitivity rescue unexpectedly enabled")
    if policy.get("may_be_selected_as_winner") is not False:
        raise RuntimeError("sensitivity winner selection unexpectedly enabled")
    if policy.get("parameter_tuning_after_outcome_inspection") is not False:
        raise RuntimeError("post-outcome parameter tuning unexpectedly enabled")

    profiles = tuple(freeze.get("sensitivity_profiles", ()))
    ids = tuple(item.get("profile_id") for item in profiles)
    if ids != EXPECTED_PROFILE_IDS:
        raise RuntimeError("pre-registered sensitivity profile set or order changed")
    for item in profiles:
        change = item.get("change_only")
        if not isinstance(change, dict) or len(change) != 1:
            raise RuntimeError(f"{item.get('profile_id')} is not a one-factor change")
    return profiles


def _parameters_for_profile(base: ResearchParameters, profile: dict[str, Any]) -> ResearchParameters:
    change = dict(profile["change_only"])
    allowed = {
        "lookback_bars",
        "zone_atr_fraction",
        "retest_window_bars",
        "stop_atr_fraction",
        "tp2_r_multiple",
        "max_holding_bars",
    }
    key = next(iter(change))
    if key not in allowed:
        raise RuntimeError(f"unexpected sensitivity field: {key}")
    parameters = replace(base, **change)
    parameters.validate()
    return parameters


def _load_effective_candles(output_root: Path, start_ms: int, end_ms: int) -> dict[str, list[Candle]]:
    months = _month_sequence(START_MONTH, END_MONTH)
    candles_by_symbol: dict[str, list[Candle]] = {}
    for symbol in FROZEN_UNIVERSE:
        series: list[Candle] = []
        prefix = _prefix(symbol)
        for month in months:
            canonical = output_root / "canonical" / f"{prefix}-Min15-{month}-01.canonical.csv"
            if not canonical.is_file():
                raise RuntimeError(f"canonical file missing after P00 reproduction: {canonical.name}")
            series.extend(_load_canonical_window(canonical, start_ms=start_ms, end_ms=end_ms))
        series = validate_candles(series, require_regular_spacing=False)
        if not series:
            raise RuntimeError(f"empty effective series: {symbol}")
        if series[0].open_time != start_ms:
            raise RuntimeError(f"effective start mismatch: {symbol}")
        if series[-1].open_time >= end_ms:
            raise RuntimeError(f"effective end violation: {symbol}")
        candles_by_symbol[symbol] = series
    return candles_by_symbol


def run_sensitivity_matrix(raw_dir: str | Path, output_dir: str | Path) -> SensitivityMatrixReceipt:
    raw_root = Path(raw_dir)
    output_root = Path(output_dir)
    closeout = _load_json(CLOSEOUT_PATH)
    if closeout.get("status") != "CLOSED_NO_EDGE" or closeout.get("classification") != "NO_EDGE":
        raise RuntimeError("P00 must remain frozen CLOSED_NO_EDGE")

    reproduction = run_p00_discovery(raw_root, output_root)
    decision = reproduction.decision or {}
    if reproduction.status != "P00_DISCOVERY_COMPLETE":
        raise RuntimeError(f"P00 reproduction failed: {reproduction.status}")
    if reproduction.fingerprint != closeout.get("run_fingerprint"):
        raise RuntimeError("closed P00 run fingerprint did not reproduce")
    if decision.get("fingerprint") != closeout.get("decision_fingerprint"):
        raise RuntimeError("closed P00 decision fingerprint did not reproduce")
    if decision.get("classification") != "NO_EDGE" or decision.get("next_stage_unlocked") is not False:
        raise RuntimeError("closed P00 decision changed")
    if reproduction.validation_2025_access_performed or reproduction.holdout_2026_access_performed:
        raise RuntimeError("future-stage access detected during reproduction")
    if reproduction.network_access_performed or reproduction.exchange_mutation_performed or reproduction.submitted_to_exchange:
        raise RuntimeError("forbidden network/exchange activity detected during reproduction")

    freeze, amendment, start_ms, end_ms = _freeze_bindings()
    frozen_profiles = _validate_sensitivity_freeze(freeze)
    base_parameters = _parameters_from_freeze(freeze)
    base_costs = _cost_from_freeze(freeze, "BASE_SENSITIVITY")
    candles_by_symbol = _load_effective_candles(output_root, start_ms, end_ms)

    baseline = reproduction.base_metrics or {}
    baseline_expectancy = baseline.get("net_expectancy_r")
    baseline_selected = baseline.get("selected_trade_count")
    baseline_rejected = baseline.get("net_rr_rejected_count")

    diagnostics: list[SensitivityProfileDiagnostic] = []
    for profile in frozen_profiles:
        parameters = _parameters_for_profile(base_parameters, profile)
        records, metrics = evaluate_universe(candles_by_symbol, parameters, base_costs)
        bootstrap = day_block_bootstrap_expectancy(records, repetitions=5000, seed=230911, confidence=0.95)
        expectancy = metrics.net_expectancy_r
        diagnostics.append(
            SensitivityProfileDiagnostic(
                profile_id=profile["profile_id"],
                change_only=dict(profile["change_only"]),
                parameters=asdict(parameters),
                metrics=asdict(metrics),
                bootstrap=asdict(bootstrap),
                delta_vs_closed_p00={
                    "net_expectancy_r": (expectancy - baseline_expectancy)
                    if expectancy is not None and baseline_expectancy is not None
                    else None,
                    "selected_trade_count": metrics.selected_trade_count - baseline_selected
                    if isinstance(baseline_selected, int)
                    else None,
                    "net_rr_rejected_count": metrics.net_rr_rejected_count - baseline_rejected
                    if isinstance(baseline_rejected, int)
                    else None,
                },
                classification=None,
                promotion_eligible=False,
                may_rescue_p00=False,
            )
        )

    receipt = SensitivityMatrixReceipt(
        document_type="PHASE_B_P00_PRE_REGISTERED_SENSITIVITY_MATRIX",
        version=VERSION,
        status="DIAGNOSTIC_SENSITIVITY_MATRIX_COMPLETE",
        stage="DISCOVERY_OPEN_DATA_DIAGNOSTIC_ONLY",
        setup_id="PBR01_BREAKOUT_RETEST_LONG",
        closed_profile_id="P00_PRIMARY",
        closed_classification="NO_EDGE",
        reproduction_run_fingerprint=reproduction.fingerprint,
        reproduction_decision_fingerprint=decision["fingerprint"],
        effective_start_utc_inclusive=amendment["effective_discovery_window"]["start_utc_inclusive"],
        effective_end_utc_exclusive=amendment["effective_discovery_window"]["end_utc_exclusive"],
        base_cost_scenario=base_costs.name,
        profile_order=EXPECTED_PROFILE_IDS,
        profiles=tuple(diagnostics),
        governance={
            "diagnostic_only": True,
            "profiles_were_pre_registered_before_p00_outcome_inspection": True,
            "one_factor_at_a_time": True,
            "winner_selection_forbidden": True,
            "ranking_for_promotion_forbidden": True,
            "may_rescue_p00": False,
            "may_retune_p00": False,
            "may_define_posthoc_p00_filter": False,
            "may_unlock_2025": False,
            "may_open_2026": False,
            "new_hypothesis_required_for_future_tradable_candidate": True,
            "note": "Sensitivity results explain local fragility/robustness only. They are not candidate selection evidence and cannot promote any P01-P12 profile.",
        },
        validation_2025_access_performed=False,
        holdout_2026_access_performed=False,
        network_access_performed=False,
        exchange_mutation_performed=False,
        submitted_to_exchange=False,
        fingerprint="",
    )
    return _with_fingerprint(receipt)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pre-registered P01-P12 diagnostic sensitivity matrix on already-open P00 Discovery data.")
    parser.add_argument("raw_dir")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()

    receipt = run_sensitivity_matrix(args.raw_dir, args.output_dir)
    path = Path(args.receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(receipt)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
