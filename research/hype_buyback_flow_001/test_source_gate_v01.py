import importlib.util
from pathlib import Path
import unittest

source = Path(__file__).with_name("source_gate_v01.py")
spec = importlib.util.spec_from_file_location("source_gate_v01", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SourceOnlyGateTests(unittest.TestCase):
    def test_market_binding_cannot_be_guessed(self):
        meta = {"tokens": [{"name": "HYPE", "index": 150}, {"name": "USDC", "index": 0}],
                "universe": [{"name": "SOMETHING", "tokens": [12, 0]},
                             {"name": "@107", "tokens": [150, 0]}]}
        self.assertEqual(m.hype_pair(meta)["coin"], "@107")
        with self.assertRaises(ValueError):
            m.hype_pair({"tokens": [], "universe": []})

    def test_actual_buy_not_transfer_balance_or_revenue(self):
        rows = [
            {"coin": "@107", "side": "B", "time": 1700000000000, "tid": 1,
             "hash": "0x1", "px": "20", "sz": "5"},
            {"coin": "@107", "side": "B", "time": 1700000000000, "tid": 1,
             "hash": "0x1", "px": "20", "sz": "5"},
            {"coin": "@107", "side": "A", "time": 1700000001000, "tid": 2,
             "hash": "0x2", "px": "20", "sz": "4"},
            {"coin": "BTC", "side": "B", "time": 1700000001000, "tid": 3,
             "hash": "0x3", "px": "30000", "sz": "4"},
            {"coin": "@107", "side": "B", "time": 1700000002000,
             "hash": "0x4", "px": "20", "sz": "6"},
        ]
        r = m.audit_fills(rows, "@107")
        self.assertEqual(r["verified_hype_buys"], 1)
        self.assertEqual(r["hype_sells"], 1)
        self.assertEqual(r["other_markets"], 1)
        self.assertEqual(r["malformed"], 1)
        self.assertEqual(r["duplicate_tid_hash"], 1)
        self.assertEqual(r["HISTORICAL_COMPLETENESS"], "NOT_ESTABLISHED")

    def test_no_nonlist_response(self):
        with self.assertRaises(ValueError):
            m.audit_fills({"error": "rate limited"}, "@107")


if __name__ == "__main__":
    unittest.main()
