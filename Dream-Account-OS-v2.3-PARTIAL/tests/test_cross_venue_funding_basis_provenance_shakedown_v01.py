from __future__ import annotations

import importlib.util
import json
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research" / "cross_venue_funding_basis_provenance_shakedown_v01.py"
SPEC = importlib.util.spec_from_file_location("cvfb_prov", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def ms(y, m, d, h=0):
    return int(datetime(y, m, d, h, tzinfo=timezone.utc).timestamp() * 1000)


def fake_rows(start, count, step, field):
    return [{field: start + i * step, "opaqueEconomicField": str(i)} for i in range(count)]


def test_hard_boundary_ends_before_locked_2026():
    assert mod.AUDIT_END_MS < mod.LOCKED_2026_START_MS
    assert datetime.fromtimestamp(mod.AUDIT_END_MS / 1000, tz=timezone.utc).year == 2025


def test_frozen_scope_is_btc_eth_only():
    assert mod.BINANCE_SYMBOLS == ("BTCUSDT", "ETHUSDT")
    assert mod.HYPERLIQUID_COINS == ("BTC", "ETH")


def test_binance_request_is_exact_public_read_only_funding_history_shape():
    req = mod.build_binance_funding_request("BTCUSDT", mod.AUDIT_START_MS, mod.AUDIT_END_MS)
    parsed = urllib.parse.urlsplit(req.full_url)
    query = urllib.parse.parse_qs(parsed.query)
    assert req.get_method() == "GET"
    assert req.data is None
    assert parsed.scheme == "https"
    assert parsed.netloc == "fapi.binance.com"
    assert parsed.path == "/fapi/v1/fundingRate"
    assert query == {
        "symbol": ["BTCUSDT"],
        "startTime": [str(mod.AUDIT_START_MS)],
        "endTime": [str(mod.AUDIT_END_MS)],
        "limit": ["1000"],
    }
    header_names = {k.lower() for k, _ in req.header_items()}
    assert "authorization" not in header_names
    assert "cookie" not in header_names
    assert "x-api-key" not in header_names


def test_hyperliquid_post_is_exact_public_info_query_not_exchange_mutation():
    req = mod.build_hyperliquid_funding_request("ETH", mod.AUDIT_START_MS, mod.AUDIT_END_MS)
    parsed = urllib.parse.urlsplit(req.full_url)
    payload = json.loads(req.data.decode("utf-8"))
    assert req.get_method() == "POST"
    assert parsed.scheme == "https"
    assert parsed.netloc == "api.hyperliquid.xyz"
    assert parsed.path == "/info"
    assert parsed.query == ""
    assert payload == {
        "type": "fundingHistory",
        "coin": "ETH",
        "startTime": mod.AUDIT_START_MS,
        "endTime": mod.AUDIT_END_MS,
    }
    assert set(payload) == {"type", "coin", "startTime", "endTime"}
    assert not ({"address", "user", "order", "orders", "action", "signature", "nonce", "vaultAddress"} & set(payload))
    header_names = {k.lower() for k, _ in req.header_items()}
    assert "authorization" not in header_names
    assert "cookie" not in header_names
    assert "x-api-key" not in header_names


def test_audit_does_not_summarize_economic_values():
    spec = mod.SeriesSpec("HYPERLIQUID_BTC", "HYPERLIQUID", "BTC", 3600000)
    rows = fake_rows(ms(2024, 1, 1), 24 * 31, 3600000, "time")
    audit = mod.audit_series(spec, rows, "time")
    assert audit["economic_fields_summarized"] is False
    assert "average" not in audit
    assert "funding_rate" not in audit
    assert "apr" not in audit
    assert "pnl" not in audit


def test_conflicting_duplicates_are_detected():
    spec = mod.SeriesSpec("BINANCE_BTCUSDT", "BINANCE_USDM", "BTCUSDT", 8 * 3600000)
    t = ms(2024, 1, 1)
    rows = [
        {"fundingTime": t, "fundingRate": "0.001"},
        {"fundingTime": t, "fundingRate": "0.002"},
    ]
    audit = mod.audit_series(spec, rows, "fundingTime")
    assert audit["conflicting_duplicate_timestamps"] == [t]


def test_large_gap_is_explicit_not_interpolated():
    spec = mod.SeriesSpec("HYPERLIQUID_ETH", "HYPERLIQUID", "ETH", 3600000)
    t = ms(2024, 1, 1)
    rows = [{"time": t}, {"time": t + 3600000}, {"time": t + 3 * 3600000}]
    audit = mod.audit_series(spec, rows, "time")
    assert audit["large_gap_count"] == 1
    assert audit["max_gap_ms"] == 2 * 3600000


def test_full_month_eligibility_is_timestamp_only():
    spec = mod.SeriesSpec("HYPERLIQUID_BTC", "HYPERLIQUID", "BTC", 3600000)
    rows = fake_rows(ms(2024, 1, 1), 24 * 31, 3600000, "time")
    audit = mod.audit_series(spec, rows, "time")
    assert "2024-01" in audit["full_months_timestamp_eligible"]


def test_missing_middle_timestamp_invalidates_month():
    spec = mod.SeriesSpec("HYPERLIQUID_BTC", "HYPERLIQUID", "BTC", 3600000)
    rows = fake_rows(ms(2024, 1, 1), 24 * 31, 3600000, "time")
    del rows[100]
    audit = mod.audit_series(spec, rows, "time")
    assert "2024-01" not in audit["full_months_timestamp_eligible"]


def test_common_window_uses_intersection_not_outcomes():
    audits = {
        "BINANCE_BTCUSDT": {"full_months_timestamp_eligible": ["2024-01", "2024-02", "2024-03"]},
        "BINANCE_ETHUSDT": {"full_months_timestamp_eligible": ["2024-01", "2024-02", "2024-03"]},
        "HYPERLIQUID_BTC": {"full_months_timestamp_eligible": ["2024-02", "2024-03"]},
        "HYPERLIQUID_ETH": {"full_months_timestamp_eligible": ["2024-02", "2024-03"]},
    }
    window = mod.choose_common_replication_window(audits)
    assert window["first_common_full_month"] == "2024-02"
    assert window["last_common_full_month"] == "2024-03"


def test_common_window_fails_closed_without_common_month():
    audits = {
        "BINANCE_BTCUSDT": {"full_months_timestamp_eligible": ["2024-01"]},
        "BINANCE_ETHUSDT": {"full_months_timestamp_eligible": ["2024-01"]},
        "HYPERLIQUID_BTC": {"full_months_timestamp_eligible": ["2024-02"]},
        "HYPERLIQUID_ETH": {"full_months_timestamp_eligible": ["2024-02"]},
    }
    with pytest.raises(mod.ProvenanceFailure):
        mod.choose_common_replication_window(audits)


def test_fetch_guards_reject_locked_2026_before_network(monkeypatch):
    called = False

    def fake_request(*args, **kwargs):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(mod, "_request_json", fake_request)
    with pytest.raises(mod.ProvenanceFailure):
        mod.fetch_binance_funding("BTCUSDT", mod.AUDIT_START_MS, mod.LOCKED_2026_START_MS)
    with pytest.raises(mod.ProvenanceFailure):
        mod.fetch_hyperliquid_funding("BTC", mod.AUDIT_START_MS, mod.LOCKED_2026_START_MS)
    assert called is False


def test_unknown_assets_fail_closed_before_network(monkeypatch):
    called = False

    def fake_request(*args, **kwargs):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(mod, "_request_json", fake_request)
    with pytest.raises(mod.ProvenanceFailure):
        mod.fetch_binance_funding("DOGEUSDT", mod.AUDIT_START_MS, mod.AUDIT_END_MS)
    with pytest.raises(mod.ProvenanceFailure):
        mod.fetch_hyperliquid_funding("SOL", mod.AUDIT_START_MS, mod.AUDIT_END_MS)
    assert called is False
