from datetime import datetime, timezone

import pytest

from radar.meta_layer import build_t0_snapshot, append_t0_snapshot


BASE_SIGNAL = {
    "candidate_id": "OPTIONS-SPOTPERP-001-V2.1",
    "immutable_signal_key": "opt-001",
    "symbol": "BTC_USDT",
    "direction": "SHORT",
    "entry_target_utc": "2026-10-01T12:00:00Z",
}

MARKET = {
    "symbol": "BTC_USDT",
    "observed_at": "2026-10-01T11:59:59Z",
    "last_price": 100000,
    "bid_price": 99999,
    "ask_price": 100001,
    "spread_bps": 0.2,
    "quote_volume_24h": 123456,
}


def test_snapshot_is_observational_and_deterministic():
    a = build_t0_snapshot(
        signal=BASE_SIGNAL,
        captured_at_utc="2026-10-01T12:00:00Z",
        market_snapshot=MARKET,
        public_context={"observed_at": "2026-10-01T11:59:58Z", "funding_rate": 0.0001},
    )
    b = build_t0_snapshot(
        signal=BASE_SIGNAL,
        captured_at_utc="2026-10-01T12:00:00Z",
        market_snapshot=MARKET,
        public_context={"observed_at": "2026-10-01T11:59:58Z", "funding_rate": 0.0001},
    )
    assert a == b
    assert a["safety"] == {
        "creates_signal": False,
        "changes_parent_signal": False,
        "changes_sizing": False,
        "changes_arbitration": False,
        "orders_allowed": False,
        "exchange_mutation_allowed": False,
    }


def test_future_market_snapshot_rejected():
    future = dict(MARKET, observed_at="2026-10-01T12:00:01Z")
    with pytest.raises(ValueError, match="future-dated"):
        build_t0_snapshot(
            signal=BASE_SIGNAL,
            captured_at_utc="2026-10-01T12:00:00Z",
            market_snapshot=future,
        )


def test_future_public_context_rejected():
    with pytest.raises(ValueError, match="future-dated"):
        build_t0_snapshot(
            signal=BASE_SIGNAL,
            captured_at_utc="2026-10-01T12:00:00Z",
            market_snapshot=MARKET,
            public_context={"observed_at": "2026-10-01T12:00:01Z", "funding_rate": 0.0001},
        )


def test_missing_features_are_not_backfilled():
    snap = build_t0_snapshot(
        signal=BASE_SIGNAL,
        captured_at_utc="2026-10-01T12:00:00Z",
        market_snapshot={},
    )
    assert snap["public_context"]["open_interest"] == "UNAVAILABLE_AT_T0"
    assert snap["market"]["last_price"] == "UNAVAILABLE_AT_T0"


def test_simultaneous_signal_order_does_not_change_snapshot():
    peers = [
        {"candidate_id": "Z", "immutable_signal_key": "2", "direction": "LONG"},
        {"candidate_id": "A", "immutable_signal_key": "1", "direction": "SHORT"},
    ]
    a = build_t0_snapshot(
        signal=BASE_SIGNAL,
        captured_at_utc="2026-10-01T12:00:00Z",
        market_snapshot=MARKET,
        simultaneous_signals=peers,
    )
    b = build_t0_snapshot(
        signal=BASE_SIGNAL,
        captured_at_utc="2026-10-01T12:00:00Z",
        market_snapshot=MARKET,
        simultaneous_signals=list(reversed(peers)),
    )
    assert a == b


class Store:
    def __init__(self):
        self.events = []
    def append(self, event_type, payload):
        self.events.append((event_type, payload))
        return {"id": len(self.events)}


def test_append_uses_existing_evidence_store_only():
    store = Store()
    snap = build_t0_snapshot(
        signal=BASE_SIGNAL,
        captured_at_utc="2026-10-01T12:00:00Z",
        market_snapshot=MARKET,
    )
    receipt = append_t0_snapshot(store, snap)
    assert receipt == {"id": 1}
    assert store.events[0][0] == "RADAR_META_T0_SNAPSHOT"
