import sys
import unittest
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(RESEARCH))

from microstructure_state_schema_v01 import (  # noqa: E402
    BBOObservation,
    MarketIdentity,
    ProvenanceClock,
    SchemaViolation,
    backward_asof_align,
    dedupe_identical_hashes,
)


H1 = "1" * 64
H2 = "2" * 64
H3 = "3" * 64
H4 = "4" * 64


def identity(venue, symbol, canonical_asset, quote_asset):
    return MarketIdentity(
        venue=venue,
        market_type="SPOT",
        symbol=symbol,
        canonical_asset=canonical_asset,
        quote_asset=quote_asset,
    )


def clock(ts, order, h):
    return ProvenanceClock(
        exchange_ts_ns=ts,
        collector_wall_ns=10_000 + order,
        collector_monotonic_ns=20_000 + order,
        source_order=order,
        source_hash_sha256=h,
    )


def bbo(venue, symbol, asset, quote, ts, order, h, bid=100.0, ask=101.0):
    return BBOObservation(
        identity=identity(venue, symbol, asset, quote),
        clock=clock(ts, order, h),
        best_bid_price=bid,
        best_bid_quantity=2.0,
        best_ask_price=ask,
        best_ask_quantity=3.0,
    )


class TestMicrostructureStateSchemaV01(unittest.TestCase):
    def test_identity_scope_is_fail_closed(self):
        identity("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT").validate()
        with self.assertRaises(SchemaViolation):
            identity("BINANCE_SPOT", "SOLUSDT", "SOL", "USDT").validate()

    def test_bbo_metrics_are_mechanical(self):
        obs = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 1_000, 1, H1)
        self.assertAlmostEqual(obs.mid, 100.5)
        self.assertAlmostEqual(obs.spread, 1.0)
        self.assertAlmostEqual(obs.spread_bps, (1.0 / 100.5) * 10_000.0)

    def test_crossed_or_locked_book_fails_closed(self):
        with self.assertRaises(SchemaViolation):
            bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 1_000, 1, H1, bid=101.0, ask=101.0).validate()

    def test_backward_asof_never_uses_future(self):
        anchor = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 2_000, 10, H1)
        older = bbo("COINBASE_ADVANCED_SPOT", "BTC-USD", "BTC", "USD", 1_900, 20, H2)
        future = bbo("COINBASE_ADVANCED_SPOT", "BTC-USD", "BTC", "USD", 2_001, 21, H3)
        aligned = backward_asof_align(anchor, [future, older], max_skew_ns=500)
        self.assertIs(aligned.other, older)
        self.assertEqual(aligned.skew_ns, 100)

    def test_backward_asof_preserves_missingness_outside_skew(self):
        anchor = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 5_000, 10, H1)
        stale = bbo("COINBASE_ADVANCED_SPOT", "BTC-USD", "BTC", "USD", 1_000, 20, H2)
        aligned = backward_asof_align(anchor, [stale], max_skew_ns=500)
        self.assertIsNone(aligned.other)
        self.assertIsNone(aligned.skew_ns)

    def test_alignment_ignores_wrong_asset(self):
        anchor = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 2_000, 10, H1)
        eth = bbo("COINBASE_ADVANCED_SPOT", "ETH-USD", "ETH", "USD", 1_999, 20, H2)
        aligned = backward_asof_align(anchor, [eth], max_skew_ns=500)
        self.assertIsNone(aligned.other)

    def test_stable_tie_break_uses_source_order_not_price(self):
        anchor = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 2_000, 10, H1)
        c1 = bbo("COINBASE_ADVANCED_SPOT", "BTC-USD", "BTC", "USD", 1_999, 20, H2, bid=99.0, ask=100.0)
        c2 = bbo("COINBASE_ADVANCED_SPOT", "BTC-USD", "BTC", "USD", 1_999, 21, H3, bid=200.0, ask=201.0)
        aligned = backward_asof_align(anchor, [c1, c2], max_skew_ns=500)
        self.assertIs(aligned.other, c2)

    def test_identical_hash_duplicate_is_removed_stably(self):
        r1 = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 1_000, 1, H1)
        r1_dup = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 1_000, 1, H1)
        r2 = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 1_100, 2, H2)
        out = dedupe_identical_hashes([r1, r1_dup, r2])
        self.assertEqual(out, (r1, r2))

    def test_conflicting_payload_at_same_source_order_fails(self):
        r1 = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 1_000, 1, H1)
        conflict = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 1_000, 1, H4)
        with self.assertRaises(SchemaViolation):
            dedupe_identical_hashes([r1, conflict])

    def test_missing_exchange_time_cannot_anchor_alignment(self):
        anchor = BBOObservation(
            identity=identity("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT"),
            clock=clock(None, 1, H1),
            best_bid_price=100,
            best_bid_quantity=1,
            best_ask_price=101,
            best_ask_quantity=1,
        )
        candidate = bbo("COINBASE_ADVANCED_SPOT", "BTC-USD", "BTC", "USD", 999, 2, H2)
        with self.assertRaises(SchemaViolation):
            backward_asof_align(anchor, [candidate], max_skew_ns=500)

    def test_negative_skew_parameter_fails_closed(self):
        anchor = bbo("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT", 2_000, 10, H1)
        candidate = bbo("COINBASE_ADVANCED_SPOT", "BTC-USD", "BTC", "USD", 1_999, 20, H2)
        with self.assertRaises(SchemaViolation):
            backward_asof_align(anchor, [candidate], max_skew_ns=-1)


if __name__ == "__main__":
    unittest.main()
