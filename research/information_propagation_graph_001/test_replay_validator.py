from replay_validator import canonical_hash, validate_rows


def _row(**overrides):
    payload = {"x": 1}
    row = {
        "source_event_ts_ms": 1000,
        "recv_monotonic_ns": 10,
        "venue": "BINANCE",
        "instrument": "BTCUSDT",
        "source_sequence": None,
        "raw_payload": payload,
        "raw_sha256": canonical_hash(payload),
    }
    row.update(overrides)
    return row


def test_valid_capture_is_valid():
    rows = [_row(recv_monotonic_ns=10), _row(recv_monotonic_ns=11)]
    out = validate_rows(rows)
    assert out.valid is True
    assert out.rows == 2


def test_raw_hash_mismatch_fails():
    row = _row(raw_sha256="0" * 64)
    out = validate_rows([row])
    assert out.valid is False
    assert out.hash_mismatch == 1


def test_monotonic_receive_clock_regression_fails():
    rows = [_row(recv_monotonic_ns=12), _row(recv_monotonic_ns=11)]
    out = validate_rows(rows)
    assert out.valid is False
    assert out.monotonic_regressions == 1


def test_deribit_change_id_gap_fails():
    rows = [
        _row(
            venue="DERIBIT",
            instrument="BTC-PERPETUAL",
            recv_monotonic_ns=10,
            source_sequence="change_id:101;prev:100",
        ),
        _row(
            venue="DERIBIT",
            instrument="BTC-PERPETUAL",
            recv_monotonic_ns=11,
            source_sequence="change_id:103;prev:999",
        ),
    ]
    out = validate_rows(rows)
    assert out.valid is False
    assert out.deribit_sequence_gaps == 1


def test_missing_source_timestamp_counted_but_not_silently_imputed():
    out = validate_rows([_row(source_event_ts_ms=None)])
    assert out.source_timestamp_missing == 1
