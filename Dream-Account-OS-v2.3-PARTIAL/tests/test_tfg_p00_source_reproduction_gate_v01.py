from types import SimpleNamespace

from research.timeframe_gap import tfg_p00_source_reproduction_gate_v01 as gate


def _fake_manifest(symbol: str, *, fingerprint: str | None = None, status: str = "PASS_CORPUS_AUDIT_ONLY_WITH_GAPS"):
    return SimpleNamespace(
        status=status,
        fingerprint=fingerprint or gate.EXPECTED_CORPUS_FINGERPRINTS[symbol],
        passed_month_count=23,
        expected_month_count=23,
        total_row_count=67183,
        months_with_gaps_count=2,
        total_detected_gap_count=6,
        total_missing_candle_count=17,
    )


def _patch_builder(monkeypatch, *, mismatched_symbol: str | None = None, blocked_symbol: str | None = None):
    def fake_build(raw_dir, output_dir, *, symbol, start_month, end_month):
        assert start_month == "2023-02"
        assert end_month == "2024-12"
        if symbol == blocked_symbol:
            return _fake_manifest(symbol, status="BLOCKED_CORPUS")
        if symbol == mismatched_symbol:
            return _fake_manifest(symbol, fingerprint="0" * 64)
        return _fake_manifest(symbol)

    monkeypatch.setattr(gate, "build_discovery_corpus", fake_build)
    monkeypatch.setattr(gate, "write_manifest", lambda path, manifest: None)


def test_frozen_scope_and_hard_safety_flags():
    assert gate.START_MONTH == "2023-02"
    assert gate.END_MONTH == "2024-12"
    assert gate.SYMBOLS == (
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "XRPUSDT",
        "DOGEUSDT",
    )
    assert len(gate.EXPECTED_CORPUS_FINGERPRINTS) == 6
    assert gate.P00_EVALUATION_PERFORMED is False
    assert gate.MARKET_OUTCOME_EVALUATION_PERFORMED is False
    assert gate.NETWORK_ACCESS_PERFORMED is False
    assert gate.EXCHANGE_MUTATION_PERFORMED is False
    assert gate.ACCESS_2025_PERFORMED is False
    assert gate.ACCESS_2026_PERFORMED is False


def test_exact_six_of_six_reproduction_passes(monkeypatch, tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    _patch_builder(monkeypatch)

    result = gate.reproduce_exact_p00_corpus(raw_dir, tmp_path / "work")

    assert result.status == gate.PASS_STATUS
    assert result.matched_symbol_count == 6
    assert len(result.symbols) == 6
    assert all(item.fingerprint_match for item in result.symbols)
    assert result.reasons == ()
    assert result.p00_evaluation_performed is False
    assert result.market_outcome_evaluation_performed is False
    assert result.network_access_performed is False
    assert result.exchange_mutation_performed is False
    assert result.access_2025_performed is False
    assert result.access_2026_performed is False


def test_one_fingerprint_mismatch_blocks_everything(monkeypatch, tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    _patch_builder(monkeypatch, mismatched_symbol="SOLUSDT")

    result = gate.reproduce_exact_p00_corpus(raw_dir, tmp_path / "work")

    assert result.status == gate.BLOCK_STATUS
    assert result.matched_symbol_count == 5
    assert any(reason == "SOLUSDT:HISTORICAL_CORPUS_FINGERPRINT_MISMATCH" for reason in result.reasons)
    sol = next(item for item in result.symbols if item.symbol == "SOLUSDT")
    assert sol.fingerprint_match is False


def test_one_structural_corpus_failure_blocks_everything(monkeypatch, tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    _patch_builder(monkeypatch, blocked_symbol="XRPUSDT")

    result = gate.reproduce_exact_p00_corpus(raw_dir, tmp_path / "work")

    assert result.status == gate.BLOCK_STATUS
    assert result.matched_symbol_count == 5
    assert any(reason.startswith("XRPUSDT:CORPUS_AUDIT_NOT_PASS:") for reason in result.reasons)


def test_missing_raw_directory_fails_closed(tmp_path):
    result = gate.reproduce_exact_p00_corpus(tmp_path / "does-not-exist", tmp_path / "work")

    assert result.status == gate.BLOCK_STATUS
    assert result.matched_symbol_count == 0
    assert result.reasons == ("RAW_DIRECTORY_NOT_FOUND",)
