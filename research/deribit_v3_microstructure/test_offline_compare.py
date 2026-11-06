"""Offline V3 safety and arithmetic tests. Run with unittest discovery."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import offline_compare

class OfflineCompareTests(unittest.TestCase):
    def test_replay_is_not_forward_or_live(self):
        result = offline_compare.compute()
        self.assertEqual(result["forward_v3_count"], 0)
        self.assertFalse(result["live_go"])
        self.assertFalse(result["all_in_pnl_available"])
        self.assertEqual(result["historic_attempts"], 3)
        self.assertEqual(result["historic_technical_valid"], 2)
        self.assertEqual(result["historic_v2_gate_pass"], 0)
        self.assertTrue(all(r["net_pnl"] is None for r in result["rows"]))

    def test_friction_reconciles_without_fee_split_guess(self):
        result = offline_compare.compute()
        for row in result["rows"]:
            if row["technical_valid"]:
                from decimal import Decimal as D
                self.assertEqual(D(row["v2_roundtrip_friction_usdc"]),
                                 D(row["full_spread_usdc"]) + D(row["four_trading_fees_usdc"]))
                self.assertIsNone(row["hold_to_expiry_entry_cost_usdc"])
                self.assertGreaterEqual(D(row["stress_50pct_spread_widening_pct"]),
                                        D(row["stress_25pct_spread_widening_pct"]))

    def test_no_network_calls(self):
        import socket
        with patch.object(socket.socket, "connect", side_effect=AssertionError("NETWORK_FORBIDDEN")):
            offline_compare.compute()

if __name__ == "__main__":
    unittest.main()
