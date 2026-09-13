from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "research" / "derivatives_positioning_phase0e_schema_inventory_v01.py"
spec = importlib.util.spec_from_file_location("dp0e", MODULE_PATH)
dp0e = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(dp0e)


def _write_daily(root: Path, asset: str, day: str, header: str = "create_time,open_interest,funding_rate\n") -> None:
    d = root / asset
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{asset}_{day}.csv").write_text(header + "1700000000,123,0.0001\n", encoding="utf-8")


def test_pass_reads_headers_only_and_skips_2025(tmp_path: Path) -> None:
    for asset in dp0e.ASSETS:
        _write_daily(tmp_path, asset, "2024-12-31")
    # Must never be opened because it is outside the allowed window.
    p2025 = tmp_path / "BTCUSDT" / "BTCUSDT_2025-01-01.csv"
    p2025.write_bytes(b"\xff\xfe\x00\x00not-valid-utf8")

    result = dp0e.inventory(tmp_path)
    assert result["status"] == "DP_PHASE0E_PASS_SCHEMA_INVENTORIED"
    assert result["data_rows_read"] == 0
    assert result["files_opened_header_only"] == 6
    assert result["forbidden_year_files_seen_but_not_opened"]["2025"] == 1
    assert result["forbidden_year_files_opened"]["2025"] == 0
    assert all(result["per_asset"][a]["in_window_header_files"] == 1 for a in dp0e.ASSETS)
    assert result["schema_variant_count"] == 1
    only_schema = next(iter(result["schema_variants"].values()))
    assert "create_time" in only_schema["timestamp_fields_present"]


def test_unknown_date_supported_file_fails_closed_without_opening_it(tmp_path: Path) -> None:
    for asset in dp0e.ASSETS:
        _write_daily(tmp_path, asset, "2024-12-31")
    unknown = tmp_path / "BTCUSDT" / "mystery.csv"
    unknown.write_bytes(b"\xff\xfe\x00bad")

    result = dp0e.inventory(tmp_path)
    assert result["status"] == "DP_PHASE0E_FAIL_CLOSED"
    assert "BTCUSDT/mystery.csv" in result["unknown_date_supported_files"]
    assert result["files_opened_header_only"] == 6


def test_unknown_asset_in_window_fails_closed(tmp_path: Path) -> None:
    for asset in dp0e.ASSETS:
        _write_daily(tmp_path, asset, "2024-12-31")
    (tmp_path / "OTHER_2024-12-31.csv").write_text("create_time,x\n1,2\n", encoding="utf-8")

    result = dp0e.inventory(tmp_path)
    assert result["status"] == "DP_PHASE0E_FAIL_CLOSED"
    assert result["unknown_asset_in_window_files"] == ["OTHER_2024-12-31.csv"]


def test_audit_directory_is_excluded(tmp_path: Path) -> None:
    for asset in dp0e.ASSETS:
        _write_daily(tmp_path, asset, "2024-12-31")
    audit = tmp_path / "AUDIT"
    audit.mkdir()
    (audit / "undated.csv").write_text("anything\n", encoding="utf-8")

    result = dp0e.inventory(tmp_path)
    assert result["status"] == "DP_PHASE0E_PASS_SCHEMA_INVENTORIED"
    assert not result["unknown_date_supported_files"]


def test_date_and_asset_inference() -> None:
    assert dp0e.infer_date("BTCUSDT_2024-01-31.csv").isoformat() == "2024-01-31"
    assert dp0e.infer_date("BTCUSDT_20240131.csv").isoformat() == "2024-01-31"
    assert dp0e.infer_asset("foo/SOLUSDT/20240131.csv") == "SOLUSDT"
