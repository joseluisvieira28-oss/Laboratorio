from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))

MODULE_PATH = RESEARCH / "cross_venue_funding_basis_semantic_mark_provenance_v043.py"
SPEC = importlib.util.spec_from_file_location("cvfb_v043", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_hourly_semantic_formula_is_one_eighth_of_8h_formula():
    p = Decimal("0.0010")
    c = Decimal("0.0003")
    f8 = mod._expected(p, c, 1)
    fh = mod._expected(p, c, 8)
    assert fh * 8 == f8


def test_candidate_clamps_are_frozen():
    assert mod.CANDIDATE_CLAMPS == (Decimal("0.0003"), Decimal("0.0005"))
    assert mod.INTEREST_8H == Decimal("0.0001")


def test_month_keys_are_fixed_and_do_not_include_2026():
    months = mod._month_keys()
    assert months[0] == "2023-09"
    assert months[-1] == "2025-12"
    assert len(months) == 28
    assert all(not x.startswith("2026-") for x in months)


def test_no_economic_flags_enabled():
    assert mod.carry_computed is False
    assert mod.apr_apy_computed is False
    assert mod.pnl_computed is False
    assert mod.signals_computed is False
    assert mod.cross_venue_rate_comparison_computed is False
    assert mod.price_values_output is False
