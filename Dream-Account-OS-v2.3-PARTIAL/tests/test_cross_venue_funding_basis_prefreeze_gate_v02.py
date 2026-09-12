from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))
MODULE = RESEARCH / "cross_venue_funding_basis_prefreeze_gate_v02.py"
SPEC = importlib.util.spec_from_file_location("cvfb_gate_v02", MODULE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

SERIES = ["BINANCE_BTCUSDT", "BINANCE_ETHUSDT", "HYPERLIQUID_BTC", "HYPERLIQUID_ETH"]
MONTHS = [f"{y:04d}-{m:02d}" for y in range(2023, 2026) for m in range(1, 13)]


def raw_v02():
    series = {}
    for sid in SERIES:
        series[sid] = {
            "record_count": 100,
            "unique_timestamp_count": 100,
            "conflicting_duplicate_timestamp_count": 0,
            "canonical_raw_records_sha256": "a" * 64,
            "last_timestamp_utc": "2025-12-31T23:00:00Z",
        }
    return {
        "lab_id": mod.LAB_ID,
        "diagnostic_id": "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_DIAGNOSTIC_V02",
        "classification": "PROVENANCE_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "DIAGNOSTIC_COMPLETE",
        "locked_2026_accessed": False,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "v01_coverage_rule_changed": False,
        "diagnostic_sha256": "b" * 64,
        "series": series,
    }


def slot_v03(fail_months=None):
    fail_months = set(fail_months or {"2024-08"})
    series = {}
    for sid in SERIES:
        series[sid] = {
            "record_count": 100,
            "unique_timestamp_count": 100,
            "slot_collision_count_total": 0,
            "ambiguous_mapping_count_total": 0,
            "months": {
                m: {"complete_by_unique_slot_occupancy": m not in fail_months}
                for m in MONTHS
            },
        }
    return {
        "lab_id": mod.LAB_ID,
        "diagnostic_id": "CROSS_VENUE_FUNDING_BASIS_SLOT_DIAGNOSTIC_V03",
        "classification": "SLOT_OCCUPANCY_PROVENANCE_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "DIAGNOSTIC_COMPLETE",
        "locked_2026_accessed": False,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "diagnostic_sha256": "c" * 64,
        "series": series,
    }


def coverage_v04():
    months = [m for m in MONTHS if "2024-09" <= m <= "2025-12"]
    return {
        "lab_id": mod.LAB_ID,
        "materializer_id": "CROSS_VENUE_FUNDING_BASIS_COVERAGE_MATERIALIZER_V04",
        "classification": "CONTIGUOUS_COVERAGE_PARTITION_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "COVERAGE_PARTITION_MATERIALIZED",
        "source_v03_diagnostic_sha256": "c" * 64,
        "selection_rule": "EARLIEST_MONTH_AFTER_LAST_COMMON_COVERAGE_FAILURE_THROUGH_2025_12",
        "last_common_coverage_failure_month": "2024-08",
        "primary_start_month": "2024-09",
        "primary_end_month": "2025-12",
        "primary_month_count": 16,
        "primary_months": months,
        "imputation_used": False,
        "economic_outcomes_used_for_selection": False,
        "locked_2026_accessed": False,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "discovery_authorized": False,
        "edge_status": "UNPROVEN",
        "receipt_sha256": "d" * 64,
    }


def regime_v05():
    return json.loads((RESEARCH / "CROSS_VENUE_FUNDING_BASIS_REGIME_SEMANTICS_FREEZE_V05.json").read_text(encoding="utf-8"))


def write(tmp_path, name, value):
    p = tmp_path / name
    p.write_text(json.dumps(value), encoding="utf-8")
    return p


def evaluate(tmp_path, r2=None, r3=None, r4=None, r5=None):
    return mod.evaluate(
        RESEARCH,
        write(tmp_path, "v02.json", r2 or raw_v02()),
        write(tmp_path, "v03.json", r3 or slot_v03()),
        write(tmp_path, "v04.json", r4 or coverage_v04()),
        write(tmp_path, "v05.json", r5 or regime_v05()),
    )


def test_valid_evidence_only_makes_ready_to_request_not_authorized(tmp_path):
    out = evaluate(tmp_path)
    assert out["status"] == "READY_TO_REQUEST_SEPARATE_DISCOVERY_AUTHORIZATION"
    assert out["discovery_authorized"] is False
    assert out["edge_status"] == "UNPROVEN"
    assert out["replication_window_provenance_only"]["first_common_full_month"] == "2024-09"
    assert out["replication_window_provenance_only"]["last_common_full_month"] == "2025-12"
    assert out["replication_window_provenance_only"]["common_full_month_count"] == 16


def test_g03_g04_g10_are_evidence_linked(tmp_path):
    out = evaluate(tmp_path)
    assert out["gate_states"]["G03_FUNDING_REGIMES"].startswith("PASS_")
    assert out["gate_states"]["G04_RAW_PROVENANCE"].startswith("PASS_")
    assert out["gate_states"]["G10_REPLICATION_PARTITION"].startswith("PASS_")
    assert out["gate_states"]["G12_DISCOVERY_AUTHORIZATION"].startswith("BLOCKED_")


def test_raw_receipt_outcome_marker_fails_closed(tmp_path):
    r2 = raw_v02()
    r2["carry_computed"] = True
    with pytest.raises(mod.GateViolation):
        evaluate(tmp_path, r2=r2)


def test_slot_receipt_record_count_mismatch_fails_closed(tmp_path):
    r3 = slot_v03()
    r3["series"]["HYPERLIQUID_BTC"]["record_count"] = 99
    with pytest.raises(mod.GateViolation):
        evaluate(tmp_path, r3=r3)


def test_coverage_cannot_skip_internal_failure(tmp_path):
    r3 = slot_v03({"2024-08", "2025-03"})
    with pytest.raises(mod.GateViolation):
        evaluate(tmp_path, r3=r3)


def test_coverage_cannot_unlink_from_v03(tmp_path):
    r4 = coverage_v04()
    r4["source_v03_diagnostic_sha256"] = "f" * 64
    with pytest.raises(mod.GateViolation):
        evaluate(tmp_path, r4=r4)


def test_regime_date_drift_fails_closed(tmp_path):
    r5 = regime_v05()
    r5["binance_usdm"]["formula_change"]["effective_utc"] = "2025-09-19T08:01:00Z"
    with pytest.raises(mod.GateViolation):
        evaluate(tmp_path, r5=r5)


def test_no_trade_or_executable_return_claim_is_opened(tmp_path):
    out = evaluate(tmp_path)
    assert out["paper_trading_authorized"] is False
    assert out["live_trading_authorized"] is False
    assert out["historical_executable_return_claim_authorized"] is False
    assert out["economic_outcomes_inspected_by_gate_engine"] is False
