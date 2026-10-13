"""Public venue snapshot source guards: synthetic-only, no web or account."""
import unittest
from decimal import Decimal
from research.convex_sol_bnb_gates_v01 import mexc_public_feasibility as p

def spec():
    return {"symbol":"SOL_USDT","contractSize":Decimal("0.1"),
            "minVol":Decimal("1"),"maxVol":Decimal("10000"),
            "volUnit":Decimal("1"),"priceUnit":Decimal(".01")}

def depth(ts=1_800_000_000_000):
    return {"asks":[["100.10",23,12],["100.20",14,22]],
            "bids":[["100.00",30,45],["99.90",40,30]],
            "timestamp":ts}

def receipt(ts=1_800_000_000_000):
    return {"local_received_ms":ts+200,"request_latency_ms":500}

class PublicMEXC(unittest.TestCase):
    def test_unknown_scope_blocked(self):
        with self.assertRaisesRegex(ValueError,"OUT_OF_SCOPE_SYMBOL"):
            p.valid_symbol("BTC_USDT")
        with self.assertRaisesRegex(ValueError,"PUBLIC_GET_ONLY_SCOPE"):
            p.source_get("private","SOL_USDT")

    def test_contract_minimum_and_correct_third_depth_field(self):
        q=p.analyze_book(depth(),receipt(),"SOL_USDT",spec())
        self.assertGreater(q["public_spread_bps"],0)
        self.assertEqual(q["samples"][0]["required_contracts"],"10")
        self.assertEqual(q["samples"][0]["ask_book_contracts_visible"],"34")
        self.assertTrue(q["samples"][0]["visible_asks_cover_required_contracts"])
        self.assertFalse(q["samples"][1]["visible_asks_cover_required_contracts"])

    def test_book_depth_order_and_latency_fail_closed(self):
        r=receipt()
        for x in ({"asks":[[100,1],],"bids":[[99,1,2]],"timestamp":1_800_000_000_000},
                  {"asks":[[100,10,1]],"bids":[[101,10,1]],"timestamp":10_000}):
            with self.assertRaises(ValueError):
                p.analyze_book(x,r,"SOL_USDT",spec())
        with self.assertRaisesRegex(ValueError,"STALE_OR_CLOCK_SKEW"):
            p.analyze_book(depth(),{"local_received_ms":1_800_000_003_000,"request_latency_ms":500},"SOL_USDT",spec())
        with self.assertRaisesRegex(ValueError,"LATENCY_EXCESSIVE"):
            p.analyze_book(depth(),{"local_received_ms":1_800_000_000_100,"request_latency_ms":4000},"SOL_USDT",spec())

    def test_detail_fails_without_contract_size(self):
        item={"symbol":"SOL_USDT","minVol":1,"volUnit":1,"maxVol":1000,"priceUnit":".01"}
        with self.assertRaisesRegex(ValueError,"MISSING_OR_BAD_SPEC_contractSize"):
            p.extract_detail(item,"SOL_USDT")

    def test_funding_is_not_historical_settlement(self):
        x={"symbol":"SOL_USDT","fundingRate":"0.0001","fairPrice":101,
           "idxPrice":100,"timestamp":100_000,"nextSettleTime":200_000}
        d=p.validate_funding(x,"SOL_USDT",100_100)
        self.assertTrue(d["NOT_historical_funding_or_user_account"])
        with self.assertRaisesRegex(ValueError,"FUNDING_QUOTE_TIME_STALE"):
            p.validate_funding(x,"SOL_USDT",300_001)

if __name__=="__main__":unittest.main()
