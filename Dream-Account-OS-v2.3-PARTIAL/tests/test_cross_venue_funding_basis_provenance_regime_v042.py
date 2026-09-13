from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))

MODULE_PATH = RESEARCH / "cross_venue_funding_basis_provenance_regime_v042.py"
SPEC = importlib.util.spec_from_file_location("cvfb_regime_v042", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_contiguous_blocks_do_not_choose_a_favorable_block():
    months = ["2023-09", "2023-10", "2023-11", "2024-01", "2024-02"]
    assert mod._contiguous_blocks(months) == [
        ["2023-09", "2023-10", "2023-11"],
        ["2024-01", "2024-02"],
    ]


def test_binance_interval_metadata_requires_exactly_8h_for_every_month():
    rows = [
        {"fundingTime": 1672531200000, "funding_interval_hours": "8"},
        {"fundingTime": 1675209600000, "funding_interval_hours": "8"},
    ]
    result = mod._binance_interval_metadata(rows)
    assert result["observed_values_hours"] == [8]
    assert result["all_rows_exactly_8h"] is False


def test_slot_details_reports_exact_missing_nominal_slot_without_interpolation(monkeypatch):
    monkeypatch.setattr(mod, "_months_in_scope", lambda: ["2023-01"])
    start, end = mod._month_bounds_ms("2023-01")
    interval = 8 * 60 * 60 * 1000
    rows = []
    expected = list(range(start, end, interval))
    missing = expected[1]
    for ts in expected:
        if ts != missing:
            rows.append({"fundingTime": ts})
    result = mod._slot_details(
        series_id="SYNTH",
        rows=rows,
        timestamp_field="fundingTime",
        interval_ms=interval,
    )
    diag = result["month_details"]["2023-01"]
    assert diag["missing_slot_count"] == 1
    assert diag["missing_nominal_slot_ms"] == [missing]
    assert diag["full_month_coverage_by_nominal_slot"] is False


def test_no_economic_markers_enabled():
    assert mod.carry_computed is False
    assert mod.apr_apy_computed is False
    assert mod.pnl_computed is False
    assert mod.signals_computed is False
