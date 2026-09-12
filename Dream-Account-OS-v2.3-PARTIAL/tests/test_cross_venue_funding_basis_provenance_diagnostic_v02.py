from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))

MODULE_PATH = RESEARCH / "cross_venue_funding_basis_provenance_diagnostic_v02.py"
SPEC = importlib.util.spec_from_file_location("cvfb_diag_v02", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def ms(y, m, d, h=0):
    return int(datetime(y, m, d, h, tzinfo=timezone.utc).timestamp() * 1000)


def fake_rows(start, count, step, field):
    return [{field: start + i * step, "opaqueEconomicField": str(i)} for i in range(count)]


def test_month_keys_frozen_to_2023_2025():
    months = mod.month_keys()
    assert months[0] == "2023-01"
    assert months[-1] == "2025-12"
    assert len(months) == 36


def test_month_failure_reason_reports_gap_without_economic_values():
    spec = mod.v1.SeriesSpec("HYPERLIQUID_BTC", "HYPERLIQUID", "BTC", 3600000)
    rows = fake_rows(ms(2024, 1, 1), 24 * 31, 3600000, "time")
    del rows[100]
    audit = mod.v1.audit_series(spec, rows, "time")
    d = mod.month_failure_reason(audit, "2024-01", spec.expected_max_gap_ms)
    assert d["eligible"] is False
    assert "INTRA_MONTH_GAP_EXCEEDS_EXPECTED_MAX" in d["reason"]
    assert "fundingRate" not in d
    assert "average" not in d
    assert "pnl" not in d


def test_compact_series_is_outcome_blind():
    spec = mod.v1.SeriesSpec("BINANCE_BTCUSDT", "BINANCE_USDM", "BTCUSDT", 8 * 3600000)
    rows = fake_rows(ms(2024, 1, 1), 3 * 31, 8 * 3600000, "fundingTime")
    audit = mod.v1.audit_series(spec, rows, "fundingTime")
    c = mod.compact_series(audit)
    assert c["economic_fields_summarized"] is False
    forbidden = {"funding_rate_average", "carry", "apr", "apy", "pnl", "sharpe", "win_rate"}
    assert forbidden.isdisjoint(c)


def test_diagnostic_can_complete_with_zero_common_months(monkeypatch):
    def fake_binance(symbol, start_ms, end_ms):
        month = 1 if symbol == "BTCUSDT" else 2
        return fake_rows(ms(2024, month, 1), 3 * 28, 8 * 3600000, "fundingTime")

    def fake_hl(coin, start_ms, end_ms):
        month = 3 if coin == "BTC" else 4
        return fake_rows(ms(2024, month, 1), 24 * 28, 3600000, "time")

    monkeypatch.setattr(mod.v1, "fetch_binance_funding", fake_binance)
    monkeypatch.setattr(mod.v1, "fetch_hyperliquid_funding", fake_hl)
    d = mod.build_diagnostic()
    assert d["status"] == "DIAGNOSTIC_COMPLETE"
    assert d["common_eligible_full_month_count"] == 0
    assert d["decision"] == "V01_STILL_BLOCKED_NO_COMMON_FULL_MONTH"
    assert d["locked_2026_accessed"] is False
    assert d["carry_computed"] is False
    assert d["pnl_computed"] is False
    assert d["v01_coverage_rule_changed"] is False


def test_locked_boundary_inherited_from_v01():
    assert mod.v1.AUDIT_END_MS < mod.v1.LOCKED_2026_START_MS
