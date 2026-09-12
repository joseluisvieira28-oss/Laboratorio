from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
MODULE_PATH = RESEARCH / "cross_venue_funding_basis_coverage_materializer_v04.py"
SPEC = importlib.util.spec_from_file_location("coverage_v04", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def fake_v03(fail_months: set[str] | None = None):
    fail_months = fail_months or set()
    months = mod.month_keys()
    series = {}
    for sid in sorted(mod.EXPECTED_SERIES):
        series[sid] = {
            "months": {
                m: {"complete_by_unique_slot_occupancy": m not in fail_months}
                for m in months
            }
        }
    return {
        "lab_id": mod.LAB_ID,
        "diagnostic_id": "CROSS_VENUE_FUNDING_BASIS_SLOT_DIAGNOSTIC_V03",
        "classification": "SLOT_OCCUPANCY_PROVENANCE_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "DIAGNOSTIC_COMPLETE",
        "diagnostic_sha256": "abc123",
        "locked_2026_accessed": False,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "series": series,
    }


def test_august_2024_gap_materializes_september_2024_through_december_2025():
    r = mod.materialize(fake_v03({"2024-08"}))
    assert r["last_common_coverage_failure_month"] == "2024-08"
    assert r["primary_start_month"] == "2024-09"
    assert r["primary_end_month"] == "2025-12"
    assert r["primary_month_count"] == 16
    assert r["primary_months"][0] == "2024-09"
    assert r["primary_months"][-1] == "2025-12"


def test_latest_failure_deterministically_moves_start_after_failure():
    r = mod.materialize(fake_v03({"2023-06", "2024-08", "2025-02"}))
    assert r["last_common_coverage_failure_month"] == "2025-02"
    assert r["primary_start_month"] == "2025-03"
    assert r["primary_month_count"] == 10


def test_no_failures_uses_first_frozen_month():
    r = mod.materialize(fake_v03())
    assert r["last_common_coverage_failure_month"] is None
    assert r["primary_start_month"] == "2023-01"
    assert r["primary_end_month"] == "2025-12"
    assert r["primary_month_count"] == 36


def test_end_month_failure_fails_closed():
    try:
        mod.materialize(fake_v03({"2025-12"}))
    except mod.CoverageFailure:
        pass
    else:
        raise AssertionError("2025-12 failure must fail closed")


def test_boundary_markers_must_be_false():
    v03 = fake_v03({"2024-08"})
    v03["pnl_computed"] = True
    try:
        mod.materialize(v03)
    except mod.CoverageFailure:
        pass
    else:
        raise AssertionError("economic boundary violation must fail closed")


def test_output_remains_outcome_blind_and_does_not_authorize_discovery():
    r = mod.materialize(fake_v03({"2024-08"}))
    assert r["imputation_used"] is False
    assert r["economic_outcomes_used_for_selection"] is False
    assert r["funding_rate_values_summarized"] is False
    assert r["carry_computed"] is False
    assert r["apr_apy_computed"] is False
    assert r["pnl_computed"] is False
    assert r["signals_computed"] is False
    assert r["discovery_authorized"] is False
    assert r["edge_status"] == "UNPROVEN"
