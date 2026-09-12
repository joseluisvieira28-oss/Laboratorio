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
    TradeObservation,
)
from microstructure_state_measurements_v01 import (  # noqa: E402
    MAX_SKEW_NS,
    MINUTE_NS,
    SECOND_NS,
    canonical_grid,
    classify_event_relative_window,
    event_control_comparison,
    nearest_rank_p90,
    realized_volatility_from_grid,
    resample_bbo_backward_asof,
    summarize_bbo_grid,
    summarize_trades,
)


def ident(venue="BINANCE_SPOT", symbol="BTCUSDT", asset="BTC", quote="USDT"):
    return MarketIdentity(venue, "SPOT", symbol, asset, quote)


def clk(ts, order):
    return ProvenanceClock(ts, 10_000 + order, 20_000 + order, order, f"{order % 16:x}" * 64)


def bbo(ts, order, bid=100.0, ask=101.0, bq=2.0, aq=3.0):
    return BBOObservation(ident(), clk(ts, order), bid, bq, ask, aq)


def trade(ts, order, price, qty, side):
    return TradeObservation(ident(), clk(ts, order), price, qty, order, side)


class TestMeasurementFreezeV01(unittest.TestCase):
    def test_half_open_event_windows(self):
        self.assertEqual(classify_event_relative_window(-30 * MINUTE_NS), "PRE_BASELINE")
        self.assertEqual(classify_event_relative_window(-1), "PRE_BASELINE")
        self.assertEqual(classify_event_relative_window(0), "PRIMARY_EVENT_STATE")
        self.assertEqual(classify_event_relative_window(30 * MINUTE_NS - 1), "PRIMARY_EVENT_STATE")
        self.assertEqual(classify_event_relative_window(30 * MINUTE_NS), "RECOVERY_STATE")
        self.assertIsNone(classify_event_relative_window(60 * MINUTE_NS))

    def test_canonical_grid_ceil_and_half_open(self):
        self.assertEqual(canonical_grid(1, 3 * SECOND_NS), (SECOND_NS, 2 * SECOND_NS))
        self.assertEqual(canonical_grid(SECOND_NS, 3 * SECOND_NS), (SECOND_NS, 2 * SECOND_NS))
        with self.assertRaises(SchemaViolation):
            canonical_grid(5, 5)

    def test_nearest_rank_p90_is_frozen(self):
        self.assertEqual(nearest_rank_p90(range(1, 11)), 9.0)
        self.assertEqual(nearest_rank_p90([5]), 5.0)
        self.assertIsNone(nearest_rank_p90([]))

    def test_resampler_never_uses_future_and_respects_two_seconds(self):
        rows = [
            bbo(0, 1),
            bbo(3 * SECOND_NS, 2, 101, 102),
        ]
        samples = resample_bbo_backward_asof(rows, start_ns=SECOND_NS, end_ns=5 * SECOND_NS)
        self.assertIs(samples[0], rows[0])
        self.assertIs(samples[1], rows[0])
        self.assertIs(samples[2], rows[1])
        self.assertIs(samples[3], rows[1])
        with self.assertRaises(SchemaViolation):
            resample_bbo_backward_asof(rows, start_ns=0, end_ns=SECOND_NS, max_skew_ns=SECOND_NS)

    def test_stale_grid_point_is_missing(self):
        rows = [bbo(0, 1)]
        samples = resample_bbo_backward_asof(rows, start_ns=3 * SECOND_NS, end_ns=4 * SECOND_NS)
        self.assertEqual(samples, (None,))

    def test_bbo_summary_uses_absolute_imbalance(self):
        samples = (
            bbo(0, 1, bid=100, ask=101, bq=9, aq=1),
            bbo(SECOND_NS, 2, bid=100, ask=102, bq=1, aq=9),
        )
        summary = summarize_bbo_grid(samples)
        self.assertEqual(summary.count, 2)
        self.assertAlmostEqual(summary.median_abs_top_imbalance, 0.8)
        self.assertGreater(summary.p90_spread_bps, summary.median_spread_bps)

    def test_realized_volatility_does_not_bridge_missingness(self):
        a = bbo(0, 1, bid=99.5, ask=100.5)
        b = bbo(SECOND_NS, 2, bid=100.5, ask=101.5)
        c = bbo(3 * SECOND_NS, 3, bid=101.5, ask=102.5)
        rv_contiguous = realized_volatility_from_grid((a, b))
        rv_gapped = realized_volatility_from_grid((a, None, c))
        self.assertIsNotNone(rv_contiguous)
        self.assertIsNone(rv_gapped)

    def test_trade_summary_and_absolute_flow(self):
        rows = [
            trade(0, 1, 100, 1, "BUY"),
            trade(1, 2, 100, 0.5, "SELL"),
        ]
        summary = summarize_trades(rows, window_minutes=30)
        self.assertEqual(summary.trade_count, 2)
        self.assertAlmostEqual(summary.base_quantity, 1.5)
        self.assertAlmostEqual(summary.quote_notional, 150.0)
        self.assertAlmostEqual(summary.absolute_normalized_signed_flow, 50.0 / 150.0)

    def test_unknown_trade_side_makes_flow_missing_not_inferred(self):
        rows = [trade(0, 1, 100, 1, None)]
        summary = summarize_trades(rows, window_minutes=30)
        self.assertIsNone(summary.absolute_normalized_signed_flow)

    def test_control_reference_requires_three_valid_controls(self):
        weak = event_control_comparison(12.0, [10.0, 11.0])
        self.assertIsNone(weak["control_median"])
        full = event_control_comparison(12.0, [10.0, 11.0, 9.0])
        self.assertEqual(full["control_median"], 10.0)
        self.assertEqual(full["difference"], 2.0)
        self.assertEqual(full["ratio"], 1.2)

    def test_no_directional_label_or_trading_authority_exposed(self):
        import microstructure_state_measurements_v01 as mod
        self.assertFalse(mod.TARGET_OBSERVATION_AUTHORIZED)
        self.assertEqual(mod.H02_STATUS, "NOT_AUTHORIZED")
        forbidden = {"entry", "stop", "take_profit", "position", "pnl", "win_rate", "directional_label"}
        self.assertTrue(forbidden.isdisjoint(set(dir(mod))))


if __name__ == "__main__":
    unittest.main()
