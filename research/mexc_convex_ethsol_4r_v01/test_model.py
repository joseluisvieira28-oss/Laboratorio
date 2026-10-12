"""Synthetic invariant tests only; NEVER use outcomes from a price archive."""
import unittest
from decimal import Decimal
from unittest.mock import patch

import model


def tick(at, bid=100, ask=100.1, mark=None, book_offset=10):
    x = {"received_ms": at, "book_ms": at - book_offset,
         "bid": bid, "ask": ask}
    if mark is not None:
        x["mark_price"] = mark
    return x


class TestPreregisteredMath(unittest.TestCase):
    def test_fee_only_reference_is_exact_four_to_one(self):
        b = model.barriers_from_entry(100)
        stop = model.fee_only_return_per_initial_notional(100, b["stop_bid"])
        target = model.fee_only_return_per_initial_notional(100, b["target_bid"])
        self.assertEqual(stop, Decimal("-0.041568"))
        self.assertEqual(target, -4 * stop)
        self.assertGreater(b["target_bid"], Decimal(116))

    def test_exit_fee_on_actual_exit_notional(self):
        r = model.net_usdt(1, 100, 120, funding_cash="-0.4",
                           extra_slippage_cash="0.1")
        self.assertEqual(r["gross_usdt"], Decimal("20"))
        self.assertEqual(r["entry_fee_usdt"], Decimal("0.0800"))
        self.assertEqual(r["exit_fee_usdt"], Decimal("0.0960"))
        self.assertEqual(r["net_usdt"], Decimal("19.3240"))

    def test_negative_slippage_rejected(self):
        with self.assertRaises(ValueError):
            model.net_usdt(1, 100, 102, extra_slippage_cash=-1)

    def test_risk_rounding_never_forces_min_lot(self):
        r = model.risk_limited_contracts(500, 50, 1, "0.1", "0.1", 100)
        self.assertEqual(r["status"], "HYPOTHETICAL_SIZE_PASS")
        self.assertEqual(r["contracts"], "0.6")
        self.assertLessEqual(Decimal(r["planned_stop_risk_usdt"]), Decimal("1.25"))
        block = model.risk_limited_contracts(500, 50, 1, "1", "1", 100)
        self.assertEqual(block["status"], "LOT_LIMIT_BLOCKED")

    def test_aggregate_budget_prevents_second_entry(self):
        r = model.risk_limited_contracts(500, 50, 1, "0.1", "0.1", 100,
                                         current_open_planned_risk_usdt="2.50")
        self.assertEqual(r["status"], "AGGREGATE_RISK_BLOCKED")

    def test_nonpositive_equity_rejected(self):
        with self.assertRaises(ValueError):
            model.risk_limited_contracts(0, 100, 1, 1, 1, 1)


class TestCausalQuotePath(unittest.TestCase):
    def test_target_first(self):
        events = [tick(11000, 101, 101.1),
                  tick(12000, 117, 117.1)]
        r = model.observed_first_touch(10000, 100, events)
        self.assertEqual(r["status"], "TARGET_BID_TOUCH_NO_FILL_GUARANTEE")

    def test_stop_first(self):
        events = [tick(11000, 99, 99.1),
                  tick(12000, 95.0, 95.1)]
        r = model.observed_first_touch(10000, 100, events)
        self.assertEqual(r["status"], "STOP_BID_TOUCH_NO_FILL_GUARANTEE")

    def test_missing_between_observations_invalidates_path(self):
        r = model.observed_first_touch(10000, 100,
                                      [tick(11000), tick(42000, 130, 130.1)])
        self.assertEqual(r["status"], "PATH_UNIDENTIFIABLE")
        self.assertEqual(r["reason"], "UNOBSERVED_QUOTE_GAP")

    def test_stale_quote_does_not_gain_4R(self):
        r = model.observed_first_touch(10000, 100,
                                      [tick(11000, 130, 130.1, book_offset=3000)])
        self.assertEqual(r["status"], "PATH_UNIDENTIFIABLE")

    def test_missing_mark_blocks_leverage(self):
        r = model.observed_first_touch(10000, 100, [tick(11000, 120, 121)],
                                       leverage=10)
        self.assertEqual(r["status"], "LIQUIDATION_UNIDENTIFIABLE")

    def test_mark_liquidation_before_target(self):
        r = model.observed_first_touch(10000, 100,
                                      [tick(11000, 100, 100.1, mark=90)],
                                      leverage=10, liquidation_mark_price=95)
        self.assertEqual(r["status"], "MARK_LIQUIDATION_TOUCH_NO_FILL_GUARANTEE")

    def test_stop_and_mark_same_tick_is_ambiguous(self):
        r = model.observed_first_touch(10000, 100,
                                      [tick(11000, 95, 95.1, mark=90)],
                                      leverage=10, liquidation_mark_price=95)
        self.assertEqual(r["status"], "AMBIGUOUS_LIQUIDATION_ORDER")

    def test_duplicate_clock_rejected(self):
        r = model.observed_first_touch(10000, 100, [tick(11000), tick(11000, 120, 121)])
        self.assertEqual(r["status"], "PATH_UNIDENTIFIABLE")

    def test_timeout_requires_observed_bid(self):
        with patch.object(model, "MAX_HOLD_MS", 1200):
            r = model.observed_first_touch(10000, 100,
                                          [tick(11000), tick(12000)])
            self.assertEqual(r["status"],
                             "TIME_LIMIT_BID_REFERENCE_NO_FILL_GUARANTEE")

    def test_no_ticks_is_not_profitable_close(self):
        r = model.observed_first_touch(10000, 100, [])
        self.assertEqual(r["status"], "OPEN_NO_VERDICT")
        self.assertFalse(r["scoreable_closed_trade"])


if __name__ == "__main__":
    unittest.main()
