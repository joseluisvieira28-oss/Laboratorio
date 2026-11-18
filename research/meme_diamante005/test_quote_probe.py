"""Only synthetic data. No network calls, no orders."""
import unittest
import pathlib
import sys
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import raydium_quote_probe as q

MINT="EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"

class Tests(unittest.TestCase):
    def test_invalid_amounts(self):
        self.assertIsNone(q.int_amt("0"))
        self.assertIsNone(q.int_amt(None))
        self.assertEqual(q.int_amt("1234"),1234)
    def test_cohort_filter_does_not_sample_unknowns(self):
        with patch.object(q,"quote",side_effect=AssertionError("no quotes expected")):
            result=q.probe({"selection":[{"screen":{"status":"UNKNOWN"},"mint":MINT}]})
        self.assertEqual(result["quote_rows"],[])
        self.assertTrue(result["no_orders"])
    def test_cost_is_only_quote_proxy(self):
        outputs=[({"outputAmount":"9999999","otherAmountThreshold":"9949999"},{}),
                 ({"outputAmount":"48000000","otherAmountThreshold":"47760000"},{}),
                 ({"outputAmount":"47500000","otherAmountThreshold":"47262500"},{})]
        with patch.object(q,"quote",side_effect=outputs):
            with patch.object(q.time,"sleep"):
                r=q.probe({"selection":[{"screen":{"status":"SCREEN_PASS_ONLY"},
                                           "mint":MINT,"coingecko_id":"dogwifcoin"}]})
        self.assertEqual(r["quote_rows"][0]["status"],"COST_PROXIES_ONLY")
        self.assertAlmostEqual(r["quote_rows"][0]["instant_roundtrip_cost_pct"],4.)
        self.assertTrue(r["no_orders"])

if __name__=="__main__":unittest.main()
