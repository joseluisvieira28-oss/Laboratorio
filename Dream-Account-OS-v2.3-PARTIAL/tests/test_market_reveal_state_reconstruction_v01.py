import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from decision_boundary import rfc3339_to_ns
from order_book import BookMetrics
from source_adapters import parse_coinbase_market_trade
from state_reconstruction import (
    TimedBookMetrics,
    aggregate_aggressive_flow,
    reconstruct_state,
)


def book_metrics(mid, spread, depth, sequence):
    mid = Decimal(str(mid))
    spread = Decimal(str(spread))
    half = spread / Decimal("2")
    return BookMetrics(
        best_bid=mid - half,
        best_ask=mid + half,
        mid=mid,
        spread_abs=spread,
        spread_bps=(spread / mid) * Decimal("10000"),
        bid_depth_quote=Decimal(str(depth)) / Decimal("2"),
        ask_depth_quote=Decimal(str(depth)) / Decimal("2"),
        total_depth_quote=Decimal(str(depth)),
        sequence_last=sequence,
    )


class StateReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.anchor = rfc3339_to_ns("2026-01-01T00:00:00Z")
        self.t1 = rfc3339_to_ns("2026-01-01T00:00:01Z")
        self.decision = rfc3339_to_ns("2026-01-01T00:00:02Z")
        self.books = [
            TimedBookMetrics(
                timestamp_ns=self.anchor,
                metrics=book_metrics("100", "2", "1000", 10),
            ),
            TimedBookMetrics(
                timestamp_ns=self.t1,
                metrics=book_metrics("102", "4", "700", 11),
            ),
            TimedBookMetrics(
                timestamp_ns=self.decision,
                metrics=book_metrics("101", "3", "800", 12),
            ),
        ]
        self.trades = [
            parse_coinbase_market_trade({
                "trade_id": "1",
                "product_id": "BTC-USD",
                "price": "100",
                "size": "1",
                "side": "SELL",
                "time": "2026-01-01T00:00:00.500Z",
            }),
            parse_coinbase_market_trade({
                "trade_id": "2",
                "product_id": "BTC-USD",
                "price": "101",
                "size": "0.5",
                "side": "BUY",
                "time": "2026-01-01T00:00:01.500Z",
            }),
        ]

    def test_flow_summary_uses_aggressor_semantics(self):
        flow = aggregate_aggressive_flow(
            self.trades,
            venue="COINBASE_ADVANCED_SPOT",
            native_symbol="BTC-USD",
            anchor_ns=self.anchor,
            decision_ns=self.decision,
        )
        self.assertEqual(flow.buy_trade_count, 1)
        self.assertEqual(flow.sell_trade_count, 1)
        self.assertEqual(flow.buy_notional, Decimal("100"))
        self.assertEqual(flow.sell_notional, Decimal("50.5"))

    def test_reconstructs_retracement_and_liquidity_state(self):
        out = reconstruct_state(
            venue="COINBASE_ADVANCED_SPOT",
            native_symbol="BTC-USD",
            anchor_ns=self.anchor,
            decision_ns=self.decision,
            book_observations=self.books,
            trades=self.trades,
        )
        self.assertEqual(out.pre_book_sequence, 10)
        self.assertEqual(out.decision_book_sequence, 12)
        self.assertEqual(out.feature_trade_count, 2)
        self.assertAlmostEqual(out.state["retracement_fraction"], 0.5)
        self.assertAlmostEqual(out.state["spread_vs_pre"], 1.5)
        self.assertAlmostEqual(out.state["spread_vs_max_to_decision"], 0.75)
        self.assertAlmostEqual(out.state["depth_vs_pre"], 0.8)
        self.assertAlmostEqual(out.state["bid_depth_vs_pre"], 0.8)
        self.assertAlmostEqual(out.state["ask_depth_vs_pre"], 0.8)
        self.assertGreater(out.state["pre_spread_bps"], 0.0)
        self.assertGreater(out.state["displacement_in_pre_spreads"], 0.0)

    def test_future_trade_is_rejected_not_silently_used(self):
        contaminated = list(self.trades)
        contaminated.append(
            parse_coinbase_market_trade({
                "trade_id": "future",
                "product_id": "BTC-USD",
                "price": "999",
                "size": "999",
                "side": "SELL",
                "time": "2026-01-01T00:00:03Z",
            })
        )
        with self.assertRaises(ValueError):
            reconstruct_state(
                venue="COINBASE_ADVANCED_SPOT",
                native_symbol="BTC-USD",
                anchor_ns=self.anchor,
                decision_ns=self.decision,
                book_observations=self.books,
                trades=contaminated,
            )

    def test_future_book_state_is_rejected(self):
        contaminated = list(self.books)
        contaminated.append(
            TimedBookMetrics(
                timestamp_ns=rfc3339_to_ns("2026-01-01T00:00:03Z"),
                metrics=book_metrics("999", "1", "999999", 13),
            )
        )
        with self.assertRaises(ValueError):
            reconstruct_state(
                venue="COINBASE_ADVANCED_SPOT",
                native_symbol="BTC-USD",
                anchor_ns=self.anchor,
                decision_ns=self.decision,
                book_observations=contaminated,
                trades=self.trades,
            )


if __name__ == "__main__":
    unittest.main()
