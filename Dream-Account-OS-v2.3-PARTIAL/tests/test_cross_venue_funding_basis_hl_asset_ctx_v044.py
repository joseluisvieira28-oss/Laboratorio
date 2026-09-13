from __future__ import annotations

import importlib.util
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "research" / "cross_venue_funding_basis_hl_asset_ctx_v044.py"
RUNNER_PATH = ROOT / "scripts" / "run_cross_venue_funding_basis_v044_windows.ps1"
INCIDENT_PATH = ROOT / "research" / "CROSS_VENUE_FUNDING_BASIS_V044_CONTROL_FLOW_INCIDENT_V01.json"
SPEC = importlib.util.spec_from_file_location("cvfb_v044", MOD_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def _blank_daily(day: date, full: bool = True):
    return {
        "schema_version": "0.1",
        "lab_id": mod.LAB_ID,
        "amendment_id": mod.AMENDMENT_ID,
        "date": day.isoformat(),
        "status": "DAY_PROVENANCE_INSPECTED",
        "schema_match": True,
        "target_assets": {
            "BTC": {"full_day": full},
            "ETH": {"full_day": full},
        },
        "semantic_counts": mod._blank_semantic(),
    }


def test_frozen_scope_excludes_2026_and_uses_btc_eth():
    assert mod.CANDIDATE_START == date(2023, 9, 1)
    assert mod.CANDIDATE_END == date(2025, 12, 31)
    assert mod.TARGET_ASSETS == ("BTC", "ETH")
    assert mod.SEMANTIC_PANEL == ("BTC", "ETH", "ARB", "AVAX", "SOL", "MATIC", "LINK", "ATOM")


def test_formula_candidates_preserved_from_v043a():
    assert mod.INTEREST_8H == Decimal("0.0001")
    assert mod.CANDIDATE_CLAMPS == (Decimal("0.0003"), Decimal("0.0005"))
    assert mod.CANDIDATE_DIVISORS == (1, 8)
    assert mod.TOL == Decimal("1e-12")
    p = Decimal("0.0010")
    assert mod._expected(p, Decimal("0.0003"), 8) == Decimal("0.0000875")
    assert mod._expected(p, Decimal("0.0005"), 8) == Decimal("0.0000625")


def test_prior_20240901_seed_is_fail_closed_without_economic_reinspection():
    r = mod.seed_prior_20240901()
    assert r["date"] == "2024-09-01"
    assert r["raw_sha256"] == "84be15acb2a7a02cb9a346c9c37c6f790153b517710ec4f010e9cb8e413ae948"
    assert r["target_assets"]["BTC"]["distinct_minute_buckets"] == 1018
    assert r["target_assets"]["ETH"]["distinct_minute_buckets"] == 1018
    assert r["target_assets"]["BTC"]["full_day"] is False
    assert r["target_assets"]["ETH"]["full_day"] is False
    assert r["economic_fields_reinspected"] is False
    assert r["economic_values_output"] is False


def test_coverage_requires_every_day_for_both_assets():
    receipts = []
    for day in range(1, 31):
        receipts.append(_blank_daily(date(2023, 9, day), full=True))
    result = mod.aggregate_coverage(receipts)
    assert result["months"]["2023-09"]["common_full_month"] is True
    assert "2023-09" in result["common_complete_months"]
    assert result["months"]["2023-10"]["common_full_month"] is False


def test_one_failed_day_fails_whole_month():
    receipts = []
    for day in range(1, 32):
        receipts.append(_blank_daily(date(2023, 10, day), full=(day != 17)))
    result = mod.aggregate_coverage(receipts)
    assert result["months"]["2023-10"]["common_full_month"] is False
    assert result["months"]["2023-10"]["failed_day_count"] == 1


def _semantic_day(day: date, scale_rows=0, early=None, late=None):
    r = _blank_daily(day, full=False)
    sem = r["semantic_counts"]
    for a in mod.SEMANTIC_PANEL:
        sem["panel_rows_by_asset"][a] = 1
    if scale_rows:
        for c in mod.CANDIDATE_CLAMPS:
            for div in mod.CANDIDATE_DIVISORS:
                k = mod._candidate_key(c, div)
                sem["scale_candidates"][k]["finite_rows"] = scale_rows
                sem["scale_candidates"][k]["matches"] = scale_rows if (c == Decimal("0.0003") and div == 8) else 0
    if early:
        sem["early"].update(early)
    if late:
        sem["late"].update(late)
    return r


def test_semantic_aggregate_passes_only_frozen_pattern_with_all_29_days():
    receipts = []
    for day in range(1, 8):
        receipts.append(_semantic_day(date(2023, 9, day), scale_rows=100))
    for day in range(1, 23):
        early = None
        late = None
        if day <= 11:
            early = {"discriminating_rows": 20, "old_clamp_matches": 20, "new_clamp_matches": 0, "neither_matches": 0}
        if day >= 12:
            late = {"discriminating_rows": 20, "old_clamp_matches": 0, "new_clamp_matches": 20, "neither_matches": 0}
        receipts.append(_semantic_day(date(2023, 12, day), early=early, late=late))
    result = mod.aggregate_semantics(receipts)
    assert result["source_days_seen"] == 29
    assert result["hourly_scale_pass"] is True
    assert result["clamp_transition_pass"] is True
    assert result["semantic_probe_pass"] is True
    assert result["discovery_authorized"] is False


def test_semantics_fail_when_neither_dominates_even_with_large_sample():
    receipts = []
    for day in range(1, 8):
        r = _semantic_day(date(2023, 9, day), scale_rows=100)
        for k in r["semantic_counts"]["scale_candidates"]:
            r["semantic_counts"]["scale_candidates"][k]["matches"] = 0
        receipts.append(r)
    for day in range(1, 23):
        b = {"discriminating_rows": 200, "old_clamp_matches": 10, "new_clamp_matches": 0, "neither_matches": 190}
        if day <= 11:
            receipts.append(_semantic_day(date(2023, 12, day), early=b))
        else:
            b2 = {"discriminating_rows": 200, "old_clamp_matches": 0, "new_clamp_matches": 10, "neither_matches": 190}
            receipts.append(_semantic_day(date(2023, 12, day), late=b2))
    result = mod.aggregate_semantics(receipts)
    assert result["semantic_probe_pass"] is False
    assert result["status"] == "FAIL_CLOSED"


def test_windows_runner_continuation_is_receipt_driven_after_incident():
    text = RUNNER_PATH.read_text(encoding="utf-8")
    assert "if (-not (Run-Semantics))" not in text
    assert "if (-not (Run-Coverage))" not in text
    assert "Assert-SemanticReceiptPass" in text
    assert "$S.semantic_probe_pass -ne $true" in text
    assert "HARD STOP: Stage B is forbidden because Stage A receipt is FAIL-CLOSED." in text
    assert "Assert-CoverageReceiptPass" in text
    assert INCIDENT_PATH.exists()


def test_all_economic_flags_stay_false():
    assert mod.carry_computed is False
    assert mod.basis_return_computed is False
    assert mod.pnl_computed is False
    assert mod.signals_computed is False
    assert mod.cross_venue_rate_comparison_computed is False
    assert mod.raw_economic_values_output is False
