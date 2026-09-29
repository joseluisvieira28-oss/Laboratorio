import os
import unittest
from dataclasses import dataclass
from unittest import mock

from dream_account.execution_mexc_readonly import SpotAccount, SpotBalance, SpotOrder, SpotTrade
from dream_account.execution_mexc_reconciliation_probe import (
    CANONICAL_SPOT_SYMBOLS,
    ReadOnlyReconciliationBlocked,
    load_guarded_client_from_env,
    run_reconciliation,
)


@dataclass
class FakeClient:
    daos_order: bool = False
    daos_trade: bool = False
    skew: int = 120

    def sync_clock(self):
        return self.skew

    def account(self):
        return SpotAccount(
            account_type="SPOT",
            can_trade=True,
            can_withdraw=True,
            can_deposit=True,
            permissions=("SPOT",),
            balances=(
                SpotBalance("BTC", "0.1", "0"),
                SpotBalance("USDT", "100", "0"),
            ),
        )

    def open_orders(self, symbol):
        if self.daos_order and symbol == CANONICAL_SPOT_SYMBOLS[0]:
            return (
                SpotOrder(
                    symbol=symbol,
                    order_id="1",
                    client_order_id="DAOS-test",
                    status="NEW",
                    side="BUY",
                    order_type="LIMIT",
                    price="1",
                    original_quantity="1",
                    executed_quantity="0",
                    cumulative_quote_quantity="0",
                    created_time_ms=None,
                    updated_time_ms=None,
                ),
            )
        return ()

    def recent_trades(self, symbol, *, limit=100, order_id=None):
        if self.daos_trade and symbol == CANONICAL_SPOT_SYMBOLS[-1]:
            return (
                SpotTrade(
                    symbol=symbol,
                    trade_id="2",
                    order_id="3",
                    client_order_id="DAOS-fill",
                    price="1",
                    quantity="1",
                    quote_quantity="1",
                    commission="0",
                    commission_asset="USDT",
                    time_ms=1,
                    is_buyer=True,
                    is_maker=False,
                ),
            )
        return ()


class MEXCReconciliationProbeTests(unittest.TestCase):
    def test_clean_reconciliation_is_sanitized(self):
        report = run_reconciliation(FakeClient())
        payload = report.sanitized_dict()
        self.assertEqual(payload["status"], "PASS_CLEAN")
        self.assertEqual(payload["symbols_queried"], 10)
        self.assertEqual(payload["daos_open_order_count"], 0)
        self.assertEqual(payload["daos_recent_trade_count"], 0)
        self.assertNotIn("BTC", str(payload))
        self.assertNotIn("USDT", str(payload))
        self.assertNotIn("order_id", payload)
        self.assertNotIn("price", payload)
        self.assertEqual(payload["exchange_mutation_routes"], 0)

    def test_daos_exchange_footprint_blocks_shadow_gate(self):
        report = run_reconciliation(FakeClient(daos_order=True, daos_trade=True))
        self.assertEqual(report.status, "DIVERGENCE_BLOCKED")
        self.assertEqual(report.daos_open_order_count, 1)
        self.assertEqual(report.daos_recent_trade_count, 1)

    def test_large_clock_skew_blocks(self):
        with self.assertRaises(ReadOnlyReconciliationBlocked):
            run_reconciliation(FakeClient(skew=6000))

    def test_env_requires_two_explicit_safety_gates(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ReadOnlyReconciliationBlocked):
                load_guarded_client_from_env(client_factory=lambda a, b: object())
        with mock.patch.dict(
            os.environ,
            {
                "MEXC_READONLY_SCOPE_ATTESTED": "1",
                "MEXC_READONLY_RECONCILE_ENABLE": "1",
                "MEXC_READONLY_ACCESS_KEY": "a",
                "MEXC_READONLY_SECRET_KEY": "b",
            },
            clear=True,
        ):
            self.assertIsNotNone(load_guarded_client_from_env(client_factory=lambda a, b: object()))


if __name__ == "__main__":
    unittest.main()
