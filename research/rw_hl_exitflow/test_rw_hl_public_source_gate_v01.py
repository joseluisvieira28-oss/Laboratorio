"""Synthetic-only Hyperliquid G1 source and firewall tests."""
import unittest
from unittest.mock import patch
import rw_hl_public_source_gate_v01 as src

def sample():
    rows=[{"name":x} for x in ("BTC","ETH","SOL","XRP","DOGE")]
    ctx=[{"openInterest":"100.5","markPx":"1.26","funding":"-0.00002",
          "dayNtlVlm":"230000"} for _ in rows]
    return [{"universe":rows},ctx]

class Sources(unittest.TestCase):
    def test_valid_market_join(self):
        x=src.parse_public_market(sample())
        self.assertEqual(x["valid_public_markets"],5)
    def test_oi_zero_valid(self):
        d=sample();d[1][0]["openInterest"]="0"
        self.assertEqual(src.parse_public_market(d)["valid_public_markets"],5)
    def test_negative_oi_block(self):
        d=sample();d[1][0]["openInterest"]="-1"
        with self.assertRaises(src.Blocked):src.parse_public_market(d)
    def test_invalid_mark_block(self):
        d=sample();d[1][0]["markPx"]="0"
        with self.assertRaises(src.Blocked):src.parse_public_market(d)
    def test_metadata_duplicate_block(self):
        d=sample();d[0]["universe"][1]["name"]="BTC"
        with self.assertRaises(src.Blocked):src.parse_public_market(d)
    def test_missing_alignment_block(self):
        d=sample();d[1].pop()
        with self.assertRaises(src.Blocked):src.parse_public_market(d)
    def test_delisted_skipped(self):
        d=sample();d[0]["universe"][0]["isDelisted"]=True
        with self.assertRaises(src.Blocked):src.parse_public_market(d)
    def test_zero_funding_is_number(self):
        d=sample();d[1][0]["funding"]="0"
        self.assertEqual(src.parse_public_market(d)["valid_public_markets"],5)
    def test_null_not_numeric(self):
        with self.assertRaises(src.Blocked):src.numeric(None,"OI")
    def test_nan_funding_rejected(self):
        d=sample();d[1][0]["funding"]="nan"
        with self.assertRaises(src.Blocked):src.parse_public_market(d)
    def test_user_endpoint_never_called(self):
        with self.assertRaises(src.Blocked):
            src.public_info({"type":"userFills","user":"anything"})
    def test_only_exact_old_funding_probe_allowed(self):
        with self.assertRaises(src.Blocked):
            src.public_info({"type":"fundingHistory","coin":"BTC","startTime":1})
    def test_canonical_immutable_deterministic(self):
        self.assertEqual(src.canon({"x":1,"y":2}),src.canon({"y":2,"x":1}))
    def test_no_order_endpoints(self):
        self.assertEqual(src.API,"https://api.hyperliquid.xyz/info")

if __name__=="__main__":unittest.main()
