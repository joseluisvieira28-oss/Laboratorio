from __future__ import annotations

import unittest

from dream_account.execution_mexc_readonly import (
    ReadOnlyReconciliationSnapshot,
    SpotAccount,
    SpotBalance,
    SpotOrder,
    SpotTrade,
)
from dream_account.execution_readonly_reconcile import (
    LAB_CLIENT_ORDER_PREFIX,
    ReconciliationVerdict,
    assess_shadow_exchange_state,
)


def account(account_type="SPOT"):
    return SpotAccount(
        account_type=account_type,
        can_trade=True,
        can_withdraw=True,
        can_deposit=True,
        permissions=("SPOT",),
        balances=(SpotBalance("USDT", "56", "0"),),
    )


def order(client_order_id="manual-1", order_id="1"):
    return SpotOrder(
        symbol="BTCUSDT",
        order_id=order_id,
        client_order_id=client_order_id,
        status="NEW",
        side="BUY",
        order_type="LIMIT",
        price="60000",
        original_quantity="0.001",
        executed_quantity="0",
        cumulative_quote_quantity="0",
        created_time_ms=1,
        updated_time_ms=1,
    )


def trade(client_order_id="manual-1", trade_id="t1"):
    return SpotTrade(
        symbol="BTCUSDT",
        trade_id=trade_id,
        order_id="1",
        client_order_id=client_order_id,
        price="60000",
        quantity="0.001",
        quote_quantity="60",
        commission="0.006",
        commission_asset="USDT",
        time_ms=1,
        is_buyer=True,
        is_maker=False,
    )


def snapshot(*, open_orders=(), queried_order=None, trades=(), skew=0, account_type="SPOT"):
    return ReadOnlyReconciliationSnapshot(
        symbol="BTCUSDT",
        observed_local_time_ms=1_000_000,
        mexc_server_time_ms=1_000_000 + skew,
        clock_skew_ms=skew,
        account=account(account_type),
        open_orders=tuple(open_orders),
        queried_order=queried_order,
        recent_trades=tuple(trades),
    )


class GateKReadOnlyReconciliationTests(unittest.TestCase):
    def test_manual_exchange_activity_does_not_impersonate_lab(self):
        report = assess_shadow_exchange_state(
            snapshot(open_orders=(order("manual-123"),), trades=(trade("manual-123"),))
        )
        self.assertEqual(report.verdict, ReconciliationVerdict.CLEAR)
        self.assertEqual(report.lab_open_order_ids, ())
        self.assertEqual(report.lab_trade_ids, ())

    def test_lab_prefixed_open_order_is_hard_divergence(self):
        report = assess_shadow_exchange_state(
            snapshot(open_orders=(order(LAB_CLIENT_ORDER_PREFIX + "abc", "ord-1"),))
        )
        self.assertEqual(report.verdict, ReconciliationVerdict.DIVERGENCE)
        self.assertIn("unexpected_lab_exchange_order", report.reasons)
        self.assertEqual(report.lab_open_order_ids, ("ord-1",))

    def test_lab_prefixed_fill_is_hard_divergence(self):
        report = assess_shadow_exchange_state(
            snapshot(trades=(trade(LAB_CLIENT_ORDER_PREFIX + "abc", "deal-1"),))
        )
        self.assertEqual(report.verdict, ReconciliationVerdict.DIVERGENCE)
        self.assertIn("unexpected_lab_exchange_fill", report.reasons)
        self.assertEqual(report.lab_trade_ids, ("deal-1",))

    def test_queried_order_is_included_without_duplicate(self):
        same = order(LAB_CLIENT_ORDER_PREFIX + "abc", "ord-1")
        report = assess_shadow_exchange_state(snapshot(open_orders=(same,), queried_order=same))
        self.assertEqual(report.lab_open_order_ids, ("ord-1",))

    def test_large_clock_skew_blocks_even_without_exchange_footprint(self):
        report = assess_shadow_exchange_state(snapshot(skew=5001))
        self.assertEqual(report.verdict, ReconciliationVerdict.BLOCKED)
        self.assertIn("clock_skew_exceeds_gate", report.reasons)

    def test_non_spot_account_blocks(self):
        report = assess_shadow_exchange_state(snapshot(account_type="FUTURES"))
        self.assertEqual(report.verdict, ReconciliationVerdict.BLOCKED)
        self.assertIn("unexpected_account_type", report.reasons)

    def test_account_can_trade_flag_is_not_treated_as_key_write_permission(self):
        report = assess_shadow_exchange_state(snapshot())
        self.assertEqual(report.verdict, ReconciliationVerdict.CLEAR)
        self.assertNotIn("can_trade", ",".join(report.reasons))
        self.assertNotIn("can_withdraw", ",".join(report.reasons))

    def test_report_fingerprint_is_stable(self):
        one = assess_shadow_exchange_state(snapshot())
        two = assess_shadow_exchange_state(snapshot())
        self.assertEqual(one.fingerprint(), two.fingerprint())
        self.assertEqual(len(one.fingerprint()), 64)


if __name__ == "__main__":
    unittest.main()
