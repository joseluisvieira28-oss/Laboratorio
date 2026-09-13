from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
MODULE_PATH = RESEARCH / "cross_venue_funding_basis_semantic_identification_v043a.py"
SPEC = importlib.util.spec_from_file_location("cvfb_v043a", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def _row(p: str, f: str):
    return {"premium": p, "fundingRate": f}


def _expected_str(p: str, c: str, divisor: int) -> str:
    return str(mod._expected(Decimal(p), Decimal(c), divisor))


def test_parent_failure_is_preserved():
    assert mod.PARENT_FAILURE["status"] == "FAIL_CLOSED_SEMANTICS_UNRESOLVED"
    assert mod.PARENT_FAILURE["workflow_run_id"] == 34725362349
    assert mod.PARENT_FAILURE["workflow_job_id"] == 103638429814


def test_sampling_panel_and_candidates_are_frozen():
    assert mod.ASSETS == ("BTC", "ETH", "ARB", "AVAX", "SOL", "MATIC", "LINK", "ATOM")
    assert mod.CANDIDATE_CLAMPS == (Decimal("0.0003"), Decimal("0.0005"))
    assert mod.CANDIDATE_DIVISORS == (1, 8)
    assert mod.INTEREST_8H == Decimal("0.0001")
    assert mod.TOL == Decimal("1e-12")


def test_windows_are_identical_to_v043_and_exclude_2026():
    assert mod.WINDOWS["hourly_scale_check"] == ("2023-09-01T00:00:00Z", "2023-09-07T23:59:59Z")
    assert mod.WINDOWS["early_clamp_check"] == ("2023-12-01T00:00:00Z", "2023-12-11T22:59:59Z")
    assert mod.WINDOWS["late_clamp_check"] == ("2023-12-11T23:00:00Z", "2023-12-22T23:59:59Z")
    assert "2026" not in repr(mod.WINDOWS)


def test_scale_pass_uses_unchanged_formula_and_thresholds():
    rows = []
    for _ in range(100):
        p = "0.0010"
        rows.append(_row(p, _expected_str(p, "0.0003", 8)))
    fetched = {
        "hourly_scale_check": rows,
        "early_clamp_check": [_row("0.0010", _expected_str("0.0010", "0.0003", 8)) for _ in range(12)],
        "late_clamp_check": [_row("0.0010", _expected_str("0.0010", "0.0005", 8)) for _ in range(12)],
    }
    result = mod.classify_semantics(fetched)
    assert result["hourly_scale_pass"] is True
    assert result["clamp_transition_pass"] is True
    assert result["semantic_probe_pass"] is True


def test_insufficient_discriminating_rows_fail_closed():
    p = "0.0010"
    fetched = {
        "hourly_scale_check": [_row(p, _expected_str(p, "0.0003", 8)) for _ in range(100)],
        "early_clamp_check": [_row(p, _expected_str(p, "0.0003", 8)) for _ in range(9)],
        "late_clamp_check": [_row(p, _expected_str(p, "0.0005", 8)) for _ in range(9)],
    }
    result = mod.classify_semantics(fetched)
    assert result["clamp_transition_pass"] is False
    assert result["semantic_probe_pass"] is False


def test_wrong_era_minority_does_not_force_failure_when_frozen_majority_rule_passes():
    p = "0.0010"
    early = [_row(p, _expected_str(p, "0.0003", 8)) for _ in range(9)]
    early += [_row(p, _expected_str(p, "0.0005", 8)) for _ in range(3)]
    late = [_row(p, _expected_str(p, "0.0005", 8)) for _ in range(9)]
    late += [_row(p, _expected_str(p, "0.0003", 8)) for _ in range(3)]
    fetched = {
        "hourly_scale_check": [_row(p, _expected_str(p, "0.0003", 8)) for _ in range(100)],
        "early_clamp_check": early,
        "late_clamp_check": late,
    }
    result = mod.classify_semantics(fetched)
    assert result["early_clamp_match_ratio"] == 0.75
    assert result["late_clamp_match_ratio"] == 0.75
    assert result["clamp_transition_pass"] is True


def test_no_economic_flags_enabled():
    assert mod.carry_computed is False
    assert mod.apr_apy_computed is False
    assert mod.pnl_computed is False
    assert mod.signals_computed is False
    assert mod.cross_venue_rate_comparison_computed is False
    assert mod.price_values_output is False
