from __future__ import annotations

import hashlib
import importlib.util
import io
import sys
import urllib.parse
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))

MODULE_PATH = RESEARCH / "cross_venue_funding_basis_provenance_archive_v03.py"
SPEC = importlib.util.spec_from_file_location("cvfb_prov_v03", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def make_zip(csv_text: str, name: str = "BTCUSDT-fundingRate-2024-01.csv") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(name, csv_text)
    return buf.getvalue()


def test_frozen_scope_ends_before_locked_2026():
    assert mod.AUDIT_END_MS < mod.LOCKED_2026_START_MS
    months = mod._month_iter()
    assert months[0] == "2023-01"
    assert months[-1] == "2025-12"
    assert len(months) == 36


def test_archive_url_is_exact_public_binance_vision_shape():
    url, checksum_url = mod.build_binance_archive_urls("BTCUSDT", "2024-01")
    parsed = urllib.parse.urlsplit(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "data.binance.vision"
    assert parsed.path == (
        "/data/futures/um/monthly/fundingRate/BTCUSDT/"
        "BTCUSDT-fundingRate-2024-01.zip"
    )
    assert parsed.query == ""
    assert checksum_url == url + ".CHECKSUM"


def test_unknown_symbol_and_locked_month_fail_before_network():
    with pytest.raises(mod.ArchiveProvenanceFailure):
        mod.build_binance_archive_urls("DOGEUSDT", "2024-01")
    with pytest.raises(mod.ArchiveProvenanceFailure):
        mod.build_binance_archive_urls("BTCUSDT", "2026-01")


def test_checksum_sidecar_parses_and_checks_filename():
    digest = "a" * 64
    raw = f"{digest}  BTCUSDT-fundingRate-2024-01.zip\n".encode()
    assert mod.parse_checksum_sidecar(raw, "BTCUSDT-fundingRate-2024-01.zip") == digest
    with pytest.raises(mod.ArchiveProvenanceFailure):
        mod.parse_checksum_sidecar(raw, "ETHUSDT-fundingRate-2024-01.zip")


def test_archive_parser_normalizes_timestamp_only_without_summarizing_rate():
    csv_text = (
        "calc_time,funding_interval_hours,last_funding_rate\n"
        "1704067200000,8,0.00010000\n"
        "1704096000000,8,-0.00005000\n"
    )
    rows = mod.parse_binance_funding_archive(
        make_zip(csv_text),
        symbol="BTCUSDT",
        month="2024-01",
    )
    assert [row["fundingTime"] for row in rows] == [1704067200000, 1704096000000]
    assert rows[0]["last_funding_rate"] == "0.00010000"
    assert not hasattr(mod, "funding_rate_average")
    assert mod.carry_computed is False
    assert mod.apr_apy_computed is False
    assert mod.pnl_computed is False
    assert mod.signals_computed is False


def test_archive_checksum_mismatch_fails_closed(monkeypatch):
    zip_bytes = make_zip(
        "calc_time,funding_interval_hours,last_funding_rate\n"
        "1704067200000,8,0.00010000\n"
    )
    url, checksum_url = mod.build_binance_archive_urls("BTCUSDT", "2024-01")

    def fake_request(candidate):
        if candidate == url:
            return zip_bytes
        if candidate == checksum_url:
            return (("0" * 64) + "  BTCUSDT-fundingRate-2024-01.zip\n").encode()
        raise AssertionError(candidate)

    monkeypatch.setattr(mod, "_request_bytes", fake_request)
    with pytest.raises(mod.ArchiveProvenanceFailure, match="checksum mismatch"):
        mod.fetch_binance_archive_month("BTCUSDT", "2024-01")


def test_archive_checksum_match_returns_rows_and_manifest(monkeypatch):
    zip_bytes = make_zip(
        "calc_time,funding_interval_hours,last_funding_rate\n"
        "1704067200000,8,0.00010000\n"
    )
    digest = hashlib.sha256(zip_bytes).hexdigest()
    url, checksum_url = mod.build_binance_archive_urls("BTCUSDT", "2024-01")

    def fake_request(candidate):
        if candidate == url:
            return zip_bytes
        if candidate == checksum_url:
            return f"{digest} *BTCUSDT-fundingRate-2024-01.zip\n".encode()
        raise AssertionError(candidate)

    monkeypatch.setattr(mod, "_request_bytes", fake_request)
    rows, manifest = mod.fetch_binance_archive_month("BTCUSDT", "2024-01")
    assert len(rows) == 1
    assert manifest["checksum_match"] is True
    assert manifest["checksum_expected_sha256"] == digest
    assert manifest["checksum_actual_sha256"] == digest


def test_common_month_diagnostic_preserves_v01_intersection_logic():
    audits = {
        "BINANCE_BTCUSDT": {"full_months_timestamp_eligible": ["2024-01", "2024-02"]},
        "BINANCE_ETHUSDT": {"full_months_timestamp_eligible": ["2024-01", "2024-02"]},
        "HYPERLIQUID_BTC": {"full_months_timestamp_eligible": ["2024-02"]},
        "HYPERLIQUID_ETH": {"full_months_timestamp_eligible": ["2024-02"]},
    }
    assert mod._common_months(audits) == ["2024-02"]


def test_no_common_month_is_diagnostic_not_silently_relaxed():
    audits = {
        "BINANCE_BTCUSDT": {"full_months_timestamp_eligible": ["2024-01"]},
        "BINANCE_ETHUSDT": {"full_months_timestamp_eligible": ["2024-01"]},
        "HYPERLIQUID_BTC": {"full_months_timestamp_eligible": ["2024-02"]},
        "HYPERLIQUID_ETH": {"full_months_timestamp_eligible": ["2024-02"]},
    }
    assert mod._common_months(audits) == []
