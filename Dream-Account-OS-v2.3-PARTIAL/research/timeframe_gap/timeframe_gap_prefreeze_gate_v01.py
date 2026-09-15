#!/usr/bin/env python3
"""Fail-closed contract gate for the timeframe-gap campaign.

This module validates only prospective research contracts. It does not load
market data, compute signals, calculate returns/PnL, open protected phases, or
perform any exchange/network mutation.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

MANIFEST = HERE / "TIMEFRAME_GAP_CAMPAIGN_PREFREEZE_V0.1.json"
PBR_1H = HERE / "TFG_PBR01_1H_001_FREEZE.json"
PBR_1D = HERE / "TFG_PBR01_1D_001_FREEZE.json"
VWAP_15M = HERE / "TFG_VWAP_15M_001_FREEZE.json"
VWAP_30M = HERE / "TFG_VWAP_30M_001_FREEZE.json"
VWAP_PROVENANCE_AMENDMENT = HERE / "TFG_VWAP_PROVENANCE_AMENDMENT_01.json"
VWAP_PROVENANCE_PREFLIGHT = HERE / "tfg_vwap_provenance_preflight_v01.py"
VWAP_PROVENANCE_STATIC_GATE = HERE / "tfg_vwap_provenance_static_gate_v01.py"

HISTORICAL_H180_BUNDLE_FP = "51952d966395e34a0390e1da3063b999c4de68d00a3e0e965e27f6ee58ed01f3"
ACTIVE_H180_BUNDLE_FP_V2 = "ff8b787d3b27e8daf80574ee35251836c2893e1f7c8eb32b5b6531edabbb1b42"
H180_MONTHLY_RAW_FP = "e62523e28ab87da27e1aa0f992e94d1b4be461a00ef1d7a1ce807a3740348e8a"
H180_PROVENANCE_MANIFEST_SHA256 = "14ad215a99d367fdd7dd393cd533aa7c83d78b2dee036ee140dd9c7a1f49c8b3"
P00_REFERENCE_SOURCE_SHA256 = "31eff305411e5e5589e53b22e47554c9b50208d372322b19422270bfe5766e25"


class FreezeGateError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    if not path.exists():
        raise FreezeGateError(f"missing contract: {path.name}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeGateError(message)


def _validate_common(doc: dict, experiment_id: str) -> None:
    _require(doc.get("experiment_id") == experiment_id, f"{experiment_id}: ID mismatch")
    _require(doc.get("status") == "PREFROZEN_NOT_EXECUTED", f"{experiment_id}: must remain unexecuted")
    gov = doc.get("governance", {})
    for key in ("research_only", "fail_closed"):
        _require(gov.get(key) is True, f"{experiment_id}: {key} must be true")
    for key in (
        "live_trading",
        "exchange_mutation",
        "merge_to_main",
        "render_deploy",
        "2025_access",
        "2026_access",
        "workflow_trigger_authorized",
        "outcome_computation_authorized_by_this_file",
    ):
        _require(gov.get(key) is False, f"{experiment_id}: forbidden authority {key}")


def _validate_pbr_parameters(doc: dict, experiment_id: str) -> None:
    p = doc.get("parameters", {})
    frozen = {
        "lookback_bars": 96,
        "atr_length": 14,
        "zone_atr_fraction": 0.25,
        "retest_window_bars": 2,
        "stop_atr_fraction": 0.25,
        "tp1_r_multiple": 1.0,
        "tp2_r_multiple": 3.0,
        "min_net_rr": 2.0,
        "max_holding_bars": 96,
        "require_bullish_breakout_body": True,
    }
    for key, value in frozen.items():
        _require(p.get(key) == value, f"{experiment_id}: frozen parameter changed: {key}")


def validate_manifest() -> None:
    d = _load(MANIFEST)
    _require(d.get("status") == "OUTCOME_BLIND_PREPARATION_ONLY", "manifest status changed")
    queue = d.get("queue", [])
    expected = [
        "TFG-PBR01-4H-001",
        "TFG-PBR01-1H-001",
        "TFG-VWAP-15M-001",
        "TFG-VWAP-30M-001",
        "TFG-PBR01-1D-001",
    ]
    _require([x.get("experiment_id") for x in queue] == expected, "queue order changed")
    _require([x.get("priority") for x in queue] == [1, 2, 3, 4, 5], "queue priorities changed")
    policy = d.get("execution_policy", {})
    _require(policy.get("run_one_at_a_time") is True, "queue must run one at a time")
    _require(policy.get("next_experiment_may_not_be_changed_after_previous_result") is True,
             "sibling anti-selection rule missing")
    _require(policy.get("no_workflow_trigger_created_by_this_prefreeze") is True,
             "prefreeze may not authorize an execution workflow")


def validate_pbr_1h() -> None:
    d = _load(PBR_1H)
    _validate_common(d, "TFG-PBR01-1H-001")
    tf = d.get("timeframe_transformation", {})
    _require(tf.get("target_timeframe") == "1H", "PBR01 1H target timeframe changed")
    _require(tf.get("policy") == "BAR_COUNT_INVARIANT", "PBR01 1H transformation policy changed")
    _require(tf.get("parameter_rescaling_allowed") is False, "PBR01 1H rescaling must remain forbidden")
    _validate_pbr_parameters(d, "TFG-PBR01-1H-001")
    stages = d.get("data_stages", {})
    _require(stages.get("validation_2025", {}).get("status") == "LOCKED_UNTIL_DISCOVERY_SURVIVES",
             "PBR01 1H 2025 lock changed")
    _require(stages.get("holdout_2026", {}).get("status") == "LOCKED_REQUIRES_SEPARATE_EXPLICIT_AUTHORIZATION",
             "PBR01 1H 2026 lock changed")


def validate_pbr_1d() -> None:
    d = _load(PBR_1D)
    _validate_common(d, "TFG-PBR01-1D-001")
    _require(d.get("priority") == 5, "PBR01 1D priority changed")
    parent = d.get("parent_hypothesis", {})
    _require(parent.get("parent_verdict") == "CLOSED_NO_EDGE", "PBR01 1D parent verdict changed")
    _require(parent.get("parent_verdict_may_not_be_changed") is True, "PBR01 1D parent closure not preserved")
    tf = d.get("timeframe_transformation", {})
    _require(tf.get("target_timeframe") == "1D", "PBR01 1D target timeframe changed")
    _require(tf.get("policy") == "BAR_COUNT_INVARIANT", "PBR01 1D transformation policy changed")
    _require(tf.get("source_interval") == "15m", "PBR01 1D source interval changed")
    _require(tf.get("source_candles_per_target_bar") == 96, "PBR01 1D daily bucket size changed")
    _require(tf.get("complete_bucket_required") is True, "PBR01 1D complete bucket requirement changed")
    _require(tf.get("parameter_rescaling_allowed") is False, "PBR01 1D rescaling must remain forbidden")
    market = d.get("market", {})
    _require(market.get("provider") == "MEXC", "PBR01 1D provider changed")
    _require(market.get("market_type") == "SPOT", "PBR01 1D market type changed")
    _require(market.get("cross_exchange_backfill_allowed") is False, "PBR01 1D cross-exchange backfill enabled")
    _require(market.get("interpolation_allowed") is False, "PBR01 1D interpolation enabled")
    _require(market.get("reference_source_sha256") == P00_REFERENCE_SOURCE_SHA256,
             "PBR01 1D parent source reference changed")
    _require(market.get("known_parent_source_rows_per_symbol") == 67183,
             "PBR01 1D parent source row identity changed")
    _require(market.get("known_parent_effective_15m_candles_per_symbol") == 67151,
             "PBR01 1D parent effective candle identity changed")
    _require(market.get("known_parent_total_detected_gaps") == 36,
             "PBR01 1D parent gap identity changed")
    _require(market.get("known_parent_total_missing_15m_candles") == 102,
             "PBR01 1D parent missing-candle identity changed")
    _validate_pbr_parameters(d, "TFG-PBR01-1D-001")
    stages = d.get("data_stages", {})
    discovery = stages.get("discovery", {})
    _require(discovery.get("classification") == "EXPLORATORY_TIMEFRAME_EXTENSION_ON_PREVIOUSLY_OPEN_DATA",
             "PBR01 1D exploratory classification changed")
    _require(discovery.get("status") == "AUTHORIZED_ONLY_AFTER_EXACT_PARENT_CORPUS_PROVENANCE_GATE_AND_QUEUE_TURN",
             "PBR01 1D Discovery gate changed")
    _require(discovery.get("minimum_resolved_trades") == 100,
             "PBR01 1D minimum sample threshold changed")
    _require(stages.get("validation_2025", {}).get("status") ==
             "LOCKED_UNTIL_DISCOVERY_SURVIVES_AND_SEPARATE_EXPLICIT_AUTHORIZATION",
             "PBR01 1D 2025 lock changed")
    _require(stages.get("holdout_2026", {}).get("status") == "LOCKED_REQUIRES_SEPARATE_EXPLICIT_AUTHORIZATION",
             "PBR01 1D 2026 lock changed")
    dof = d.get("degrees_of_freedom_lock", {})
    _require(dof.get("sample_threshold_reduction_after_outcomes") is False,
             "PBR01 1D sample-threshold rescue enabled")
    _require(dof.get("clock_time_rescaling_after_outcomes") is False,
             "PBR01 1D clock-time rescue enabled")


def _validate_vwap(path: Path, experiment_id: str, target_tf: str, hold_bars: int) -> None:
    d = _load(path)
    _validate_common(d, experiment_id)
    tf = d.get("timeframe_transformation", {})
    _require(tf.get("target_signal_timeframe") == target_tf, f"{experiment_id}: signal TF changed")
    _require(tf.get("policy") == "SIGNAL_RESOLUTION_ONLY_WITH_ECONOMIC_HOLD_INVARIANT",
             f"{experiment_id}: transform policy changed")
    _require(tf.get("target_holding_bars") == hold_bars, f"{experiment_id}: hold bars changed")
    _require(tf.get("target_holding_horizon") == "4h", f"{experiment_id}: 4h horizon changed")
    ex = d.get("execution", {})
    _require(ex.get("holding_bars") == hold_bars, f"{experiment_id}: execution hold changed")
    _require(ex.get("holding_horizon") == "4h", f"{experiment_id}: execution horizon changed")
    _require(ex.get("base_roundtrip_cost_bps") == 10, f"{experiment_id}: base cost changed")
    _require(ex.get("stress_roundtrip_cost_bps") == 14, f"{experiment_id}: stress cost changed")
    market = d.get("market", {})
    _require(market.get("canonical_fingerprint") == HISTORICAL_H180_BUNDLE_FP,
             f"{experiment_id}: historical parent fingerprint changed or relabelled")
    _require(market.get("raw_monthly_fingerprint") == H180_MONTHLY_RAW_FP,
             f"{experiment_id}: raw source fingerprint changed")
    stages = d.get("data_stages", {})
    _require(stages.get("discovery", {}).get("status") == "AUTHORIZED_AFTER_PROVENANCE_PREFLIGHT_ONLY",
             f"{experiment_id}: Discovery provenance gate changed")
    _require(stages.get("internal_oos_2024", {}).get("status") == "LOCKED_UNTIL_DISCOVERY_SURVIVES",
             f"{experiment_id}: 2024 gate changed")
    _require(stages.get("protected_2025", {}).get("status") == "LOCKED", f"{experiment_id}: 2025 lock changed")
    _require(stages.get("locked_2026_onward", {}).get("status") == "LOCKED", f"{experiment_id}: 2026 lock changed")


def validate_vwap_provenance_amendment() -> None:
    d = _load(VWAP_PROVENANCE_AMENDMENT)
    _require(d.get("document_type") == "TIMEFRAME_GAP_VWAP_PROVENANCE_AMENDMENT",
             "VWAP provenance amendment type changed")
    _require(d.get("amendment_id") == "TFG-VWAP-PROVENANCE-AMEND-01",
             "VWAP provenance amendment ID changed")
    _require(d.get("status") == "FROZEN_BEFORE_ANY_TFG_VWAP_OUTCOME_EVALUATION",
             "VWAP provenance amendment must remain pre-outcome")
    _require(d.get("applies_to") == ["TFG-VWAP-15M-001", "TFG-VWAP-30M-001"],
             "VWAP provenance amendment scope changed")
    _require(d.get("historical_h180_bundle_fingerprint") == HISTORICAL_H180_BUNDLE_FP,
             "historical H180 bundle fingerprint changed")
    _require(d.get("active_h180_bundle_fingerprint_v2") == ACTIVE_H180_BUNDLE_FP_V2,
             "active H180 bundle fingerprint V2 changed")
    _require(d.get("monthly_raw_fingerprint") == H180_MONTHLY_RAW_FP,
             "H180 raw monthly fingerprint changed")
    _require(d.get("provenance_manifest_sha256") == H180_PROVENANCE_MANIFEST_SHA256,
             "H180 provenance-manifest hash changed")
    _require(d.get("normalized_candles_changed_by_h180_amendment") is False,
             "normalized-candle immutability claim changed")
    _require(d.get("event_mask_changed_by_h180_amendment") is True,
             "H180 event-mask amendment semantics changed")
    _require(d.get("outcome_computation_authorized") is False,
             "provenance amendment may not authorize outcomes")
    _require(d.get("workflow_trigger_authorized") is False,
             "provenance amendment may not authorize workflows")
    _require(VWAP_PROVENANCE_PREFLIGHT.exists(), "VWAP provenance preflight checker missing")
    _require(VWAP_PROVENANCE_STATIC_GATE.exists(), "VWAP provenance static gate missing")


def validate_all() -> None:
    validate_manifest()
    validate_pbr_1h()
    _validate_vwap(VWAP_15M, "TFG-VWAP-15M-001", "15m", 16)
    _validate_vwap(VWAP_30M, "TFG-VWAP-30M-001", "30m", 8)
    validate_pbr_1d()
    validate_vwap_provenance_amendment()


if __name__ == "__main__":
    validate_all()
    print("TIMEFRAME_GAP_PREFREEZE_GATE: PASS")
