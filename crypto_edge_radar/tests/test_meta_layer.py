import pytest

from radar.evidence import EvidenceStore
from radar.global_fishing_dispatcher_v02 import arbitrate_due_signals
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


def _snap(captured="2026-10-01T12:00:00Z"):
    return build_t0_snapshot(
        signal=BASE_SIGNAL, captured_at_utc=captured, market_snapshot=MARKET,
        public_context={"observed_at": "2026-10-01T11:59:58Z", "funding_rate": 0.0001},
    )


def test_snapshot_is_observational_and_deterministic():
    assert _snap() == _snap()
    assert all(v is False for v in _snap()["safety"].values())


def test_retry_time_does_not_change_signal_idempotency_identity():
    later_market = dict(MARKET, observed_at="2026-10-01T12:00:00Z")
    a = _snap("2026-10-01T12:00:00Z")
    b = build_t0_snapshot(
        signal=BASE_SIGNAL, captured_at_utc="2026-10-01T12:00:01Z",
        market_snapshot=later_market,
    )
    assert a["idempotency_key"] == b["idempotency_key"]


def test_future_market_snapshot_rejected():
    with pytest.raises(ValueError, match="future-dated"):
        build_t0_snapshot(signal=BASE_SIGNAL, captured_at_utc="2026-10-01T12:00:00Z",
                          market_snapshot=dict(MARKET, observed_at="2026-10-01T12:00:01Z"))


def test_future_public_context_rejected():
    with pytest.raises(ValueError, match="future-dated"):
        build_t0_snapshot(signal=BASE_SIGNAL, captured_at_utc="2026-10-01T12:00:00Z",
                          market_snapshot=MARKET,
                          public_context={"observed_at": "2026-10-01T12:00:01Z", "funding_rate": 0.0001})


def test_missing_features_are_not_backfilled():
    snap = build_t0_snapshot(signal=BASE_SIGNAL, captured_at_utc="2026-10-01T12:00:00Z")
    assert snap["public_context"]["open_interest"] == "UNAVAILABLE_AT_T0"
    assert snap["market"]["last_price"] == "UNAVAILABLE_AT_T0"


def test_simultaneous_signal_order_does_not_change_snapshot():
    peers = [
        {"candidate_id": "Z", "immutable_signal_key": "2", "direction": "LONG"},
        {"candidate_id": "A", "immutable_signal_key": "1", "direction": "SHORT"},
    ]
    a = build_t0_snapshot(signal=BASE_SIGNAL, captured_at_utc="2026-10-01T12:00:00Z",
                          market_snapshot=MARKET, simultaneous_signals=peers)
    b = build_t0_snapshot(signal=BASE_SIGNAL, captured_at_utc="2026-10-01T12:00:00Z",
                          market_snapshot=MARKET, simultaneous_signals=list(reversed(peers)))
    assert a == b


def test_sqlite_persistence_is_durably_idempotent_across_store_restart(tmp_path):
    path = tmp_path / "meta.db"
    first = append_t0_snapshot(EvidenceStore(str(path)), _snap())
    second = append_t0_snapshot(EvidenceStore(str(path)), _snap())
    assert first["inserted"] is True
    assert second["duplicate"] is True
    assert first["id"] == second["id"]
    assert len(EvidenceStore(str(path)).read_payloads("RADAR_META_T0_SNAPSHOT")) == 1


def test_store_without_append_once_fails_closed():
    class UnsafeStore:
        def append(self, *_args):
            raise AssertionError("must never use non-idempotent append")
    with pytest.raises(RuntimeError, match="IDEMPOTENCY_UNSUPPORTED"):
        append_t0_snapshot(UnsafeStore(), _snap())


def test_parent_dispatcher_output_is_identical_before_and_after_observation():
    from datetime import datetime, timezone
    signals = [
        BASE_SIGNAL,
        {"candidate_id": "BNB-LAUNCHPOOL-DEMAND-001", "immutable_signal_key": "bnb-001",
         "symbol": "BNB_USDT", "direction": "LONG", "entry_target_utc": "2026-10-01T12:00:00Z"},
    ]
    now = datetime(2026, 10, 1, 12, 0, 1, tzinfo=timezone.utc)
    before = arbitrate_due_signals(signals, now=now, global_slot_occupied=False)
    build_t0_snapshot(signal=before["winner"], captured_at_utc="2026-10-01T12:00:01Z",
                      market_snapshot=dict(MARKET, observed_at="2026-10-01T12:00:00Z"),
                      simultaneous_signals=signals)
    after = arbitrate_due_signals(signals, now=now, global_slot_occupied=False)
    assert before == after
