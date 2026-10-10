import importlib.util
from pathlib import Path
import unittest

source = Path(__file__).with_name("source_gate_v01.py")
spec = importlib.util.spec_from_file_location("source_gate_v01", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ctx_source = Path(__file__).with_name("source_retention_liquidity_v013.py")
ctx_spec = importlib.util.spec_from_file_location("source_retention_liquidity_v013", ctx_source)
ctx_m = importlib.util.module_from_spec(ctx_spec)
ctx_spec.loader.exec_module(ctx_m)


class SourceOnlyGateTests(unittest.TestCase):
    def test_official_af_address_length_contract(self):
        self.assertEqual(len(m.AF), 42)
        self.assertEqual(m.AF, ctx_m.AF)
        self.assertEqual(m.AF, "0x" + "fe" * 20)

    def test_spot_context_uses_explicit_market_index_not_universe_offset(self):
        ctx = [{"coin": "@"+str(i), "dayNtlVlm": "0.0"} for i in range(108)]
        ctx[107]["dayNtlVlm"] = "39000000.0"
        meta = {"tokens": [{"name":"HYPE","index":150}, {"name":"USDC","index":0}],
                "universe":[{"name":"@105","tokens":[15,0],"index":105},
                            {"name":"@107","tokens":[150,0],"index":107}]}
        verified = ctx_m.market_binding([meta, ctx])
        self.assertEqual(verified["universe_index"], 1)
        self.assertEqual(verified["spot_market_index"], 107)
        self.assertEqual(verified["dayNtlVlm"], "39000000.0")
        ctx[107]["coin"] = "@106"
        with self.assertRaises(ValueError):
            ctx_m.market_binding([meta, ctx])

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
