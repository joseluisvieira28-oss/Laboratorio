from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))

MODULE_PATH = RESEARCH / "cross_venue_funding_basis_slot_diagnostic_v03.py"
SPEC = importlib.util.spec_from_file_location("cvfb_slot_v03", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def ms(y: int, m: int, d: int, h: int = 0, millis: int = 0) -> int:
    base = int(datetime(y, m, d, h, tzinfo=timezone.utc).timestamp() * 1000)
    return base + millis


def test_binance_millisecond_jitter_maps_to_expected_slot():
    cadence = 8 * 60 * 60 * 1000
    slot, offset, ambiguous = mod.nearest_slot(ms(2024, 1, 1, 8, 26), cadence)
    assert slot == ms(2024, 1, 1, 8)
    assert offset == 26
    assert ambiguous is False


def test_hyperliquid_small_jitter_maps_to_hourly_slot():
    cadence = 60 * 60 * 1000
    slot, offset, ambiguous = mod.nearest_slot(ms(2024, 1, 1, 1, 76), cadence)
    assert slot == ms(2024, 1, 1, 1)
    assert offset == 76
    assert ambiguous is False


def test_complete_hourly_month_survives_jitter():
    cadence = 60 * 60 * 1000
    start, end = mod.month_bounds("2024-01")
    timestamps = [slot + 100 for slot in range(start, end, cadence)]
    d = mod.diagnose_timestamps("HYPERLIQUID_BTC", timestamps)
    jan = d["months"]["2024-01"]
    assert jan["missing_slot_count"] == 0
    assert jan["collision_slot_count"] == 0
    assert jan["complete_by_unique_slot_occupancy"] is True
    assert "2024-01" in d["complete_full_months"]


def test_missing_hourly_slot_fails_month():
    cadence = 60 * 60 * 1000
    start, end = mod.month_bounds("2024-01")
    timestamps = [slot + 50 for slot in range(start, end, cadence)]
    del timestamps[100]
    d = mod.diagnose_timestamps("HYPERLIQUID_BTC", timestamps)
    jan = d["months"]["2024-01"]
    assert jan["missing_slot_count"] == 1
    assert jan["complete_by_unique_slot_occupancy"] is False


def test_collision_fails_month():
    cadence = 60 * 60 * 1000
    start, end = mod.month_bounds("2024-01")
    timestamps = [slot + 25 for slot in range(start, end, cadence)]
    timestamps.append(start + 100)
    d = mod.diagnose_timestamps("HYPERLIQUID_ETH", timestamps)
    jan = d["months"]["2024-01"]
    assert jan["collision_slot_count"] == 1
    assert jan["complete_by_unique_slot_occupancy"] is False


def test_exact_half_interval_is_ambiguous():
    cadence = 60 * 60 * 1000
    _, _, ambiguous = mod.nearest_slot(ms(2024, 1, 1, 0) + cadence // 2, cadence)
    assert ambiguous is True


def test_locked_2026_rejected():
    try:
        mod.diagnose_timestamps("HYPERLIQUID_BTC", [ms(2026, 1, 1)])
    except mod.v1.ProvenanceFailure:
        pass
    else:
        raise AssertionError("locked 2026 timestamp must fail closed")


def test_output_contract_is_outcome_blind(monkeypatch):
    def fake_binance(symbol, start_ms, end_ms):
        field = "fundingTime"
        start, end = mod.month_bounds("2024-01")
        return [{field: slot + 10, "fundingRate": "opaque"} for slot in range(start, end, 8 * 60 * 60 * 1000)]

    def fake_hl(coin, start_ms, end_ms):
        field = "time"
        start, end = mod.month_bounds("2024-01")
        return [{field: slot + 75, "fundingRate": "opaque"} for slot in range(start, end, 60 * 60 * 1000)]

    monkeypatch.setattr(mod.v1, "fetch_binance_funding", fake_binance)
    monkeypatch.setattr(mod.v1, "fetch_hyperliquid_funding", fake_hl)
    r = mod.build_diagnostic()
    assert r["funding_rate_values_summarized"] is False
    assert r["carry_computed"] is False
    assert r["apr_apy_computed"] is False
    assert r["pnl_computed"] is False
    assert r["signals_computed"] is False
    assert r["locked_2026_accessed"] is False
    assert r["common_complete_full_months"] == ["2024-01"]
