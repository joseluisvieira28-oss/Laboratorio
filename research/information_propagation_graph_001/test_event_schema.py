from event_schema import clock_quality, normalize_binance, normalize_deribit


def test_binance_prefers_trade_time_and_preserves_publish_time():
    msg = {
        "stream": "btcusdt@aggTrade",
        "data": {
            "e": "aggTrade",
            "E": 1_700_000_000_120,
            "T": 1_700_000_000_100,
            "s": "BTCUSDT",
            "a": 42,
            "p": "65000.0",
            "q": "0.1",
        },
    }
    ev = normalize_binance(msg, recv_wall_ts_ms=1_700_000_000_140, recv_monotonic_ns=123)
    assert ev.source_event_ts_ms == 1_700_000_000_100
    assert ev.source_publish_ts_ms == 1_700_000_000_120
    assert ev.source_sequence == "a:42"
    assert ev.instrument == "BTCUSDT"
    assert clock_quality(ev)["usable_for_event_time"] is True


def test_deribit_keeps_book_sequence_evidence():
    msg = {
        "jsonrpc": "2.0",
        "method": "subscription",
        "params": {
            "channel": "book.BTC-PERPETUAL.100ms",
            "data": {
                "timestamp": 1_700_000_000_200,
                "instrument_name": "BTC-PERPETUAL",
                "change_id": 101,
                "prev_change_id": 100,
                "bids": [],
                "asks": [],
            },
        },
    }
    ev = normalize_deribit(msg, recv_wall_ts_ms=1_700_000_000_240, recv_monotonic_ns=456)
    assert ev.source_event_ts_ms == 1_700_000_000_200
    assert ev.source_sequence == "change_id:101;prev:100"
    assert ev.instrument == "BTC-PERPETUAL"


def test_missing_source_timestamp_fails_closed():
    msg = {"e": "bookTicker", "s": "BTCUSDT", "u": 7}
    ev = normalize_binance(msg, recv_wall_ts_ms=1_700_000_000_000, recv_monotonic_ns=999)
    quality = clock_quality(ev)
    assert quality["usable_for_event_time"] is False
    assert quality["reason"] == "MISSING_SOURCE_EVENT_TIMESTAMP"
