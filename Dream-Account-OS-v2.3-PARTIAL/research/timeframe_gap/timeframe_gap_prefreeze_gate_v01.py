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
VWAP_15M = HERE / "TFG_VWAP_15M_001_FREEZE.json"
VWAP_30M = HERE / "TFG_VWAP_30M_001_FREEZE.json"


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


def validate_manifest() -> None:
    d = _load(MANIFEST)
    _require(d.get("status") == "OUTCOME_BLIND_PREPARATION_ONLY", "manifest status changed")
    queue = d.get("queue", [])
    expected = [
        "TFG-PBR01-4H-001",
        "TFG-PBR01-1H-001",
        "TFG-VWAP-15M-001",
        "TFG-VWAP-30M-001",
    ]
    _require([x.get("experiment_id") for x in queue] == expected, "queue order changed")
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
    _require(tf.get("target_timeframe") == "1H", "PBR01 target timeframe changed")
    _require(tf.get("policy") == "BAR_COUNT_INVARIANT", "PBR01 transformation policy changed")
    _require(tf.get("parameter_rescaling_allowed") is False, "PBR01 rescaling must remain forbidden")
    p = d.get("parameters", {})
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
        _require(p.get(key) == value, f"PBR01 frozen parameter changed: {key}")
    stages = d.get("data_stages", {})
    _require(stages.get("validation_2025", {}).get("status") == "LOCKED_UNTIL_DISCOVERY_SURVIVES",
             "PBR01 2025 lock changed")
    _require(stages.get("holdout_2026", {}).get("status") == "LOCKED_REQUIRES_SEPARATE_EXPLICIT_AUTHORIZATION",
             "PBR01 2026 lock changed")


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
    stages = d.get("data_stages", {})
    _require(stages.get("internal_oos_2024", {}).get("status") == "LOCKED_UNTIL_DISCOVERY_SURVIVES",
             f"{experiment_id}: 2024 gate changed")
    _require(stages.get("protected_2025", {}).get("status") == "LOCKED", f"{experiment_id}: 2025 lock changed")
    _require(stages.get("locked_2026_onward", {}).get("status") == "LOCKED", f"{experiment_id}: 2026 lock changed")


def validate_all() -> None:
    validate_manifest()
    validate_pbr_1h()
    _validate_vwap(VWAP_15M, "TFG-VWAP-15M-001", "15m", 16)
    _validate_vwap(VWAP_30M, "TFG-VWAP-30M-001", "30m", 8)


if __name__ == "__main__":
    validate_all()
    print("TIMEFRAME_GAP_PREFREEZE_GATE: PASS")
