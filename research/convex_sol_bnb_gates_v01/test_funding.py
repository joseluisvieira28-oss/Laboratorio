"""Zero-outcome tests of frozen public funding page, no live network."""
import unittest
from research.convex_sol_bnb_gates_v01 import exact_funding_mark as e

def item(symbol,t,r="0.0001",p="123.456"):
    return {"symbol":symbol,"fundingTime":t,"fundingRate":r,"markPrice":p}

class FundingMarkContracts(unittest.TestCase):
    def test_symbol_time_mark_rate(self):
        t=e.START
        x=e.parse_funding_record(item("SOLUSDT",t),"SOLUSDT")
        self.assertEqual(x[0],t)
        self.assertAlmostEqual(x[1]["mark"],123.456)
        self.assertEqual(e.PAIRS["SOLUSDT"][0],"1h")
        self.assertEqual(e.PAIRS["BNBUSDT"][0],"4h")

    def test_fail_no_mark_and_other_symbol(self):
        for p in ("",None,0,"nan",-1):
            with self.subTest(mark=p),self.assertRaises(ValueError):
                e.parse_funding_record(item("BNBUSDT",e.START,p=p),"BNBUSDT")
        with self.assertRaisesRegex(ValueError,"WRONG_SYMBOL"):
            e.parse_funding_record(item("SOLUSDT",e.START),"BNBUSDT")

    def test_outside_window_blocked(self):
        for t in (e.START-1,e.END,e.END+1):
            with self.subTest(t=t),self.assertRaises(ValueError):
                e.parse_funding_record(item("BNBUSDT",t),"BNBUSDT")

    def test_pagination_completed_with_unique_order(self):
        def getter(symbol,start):
            data=[item(symbol,e.START),item(symbol,e.START+e.engine.HOUR)] if start==e.START else []
            return data,{"source":"synthetic"}
        old=e.EXPECTED_SETTLEMENTS
        e.EXPECTED_SETTLEMENTS=2
        try:
            got,pages=e.collect_full_api("SOLUSDT",getter)
            self.assertEqual(len(got),2)
            self.assertEqual(len(pages),1)
        finally:e.EXPECTED_SETTLEMENTS=old

    def test_duplicate_timestamp_block(self):
        def getter(symbol,start):
            return [item(symbol,e.START),item(symbol,e.START)],{"source":"synthetic"}
        with self.assertRaisesRegex(ValueError,"NONCAUSAL_DUPLICATE"):
            e.collect_full_api("SOLUSDT",getter)

    def test_missing_observation_is_blocked(self):
        def getter(symbol,start):
            return [item(symbol,e.START)],{"source":"synthetic"}
        with self.assertRaisesRegex(ValueError,"COVERAGE_MISMATCH"):
            e.collect_full_api("SOLUSDT",getter)

    def test_mark_rate_reweighting_identity(self):
        market=100.
        mark=102.
        rate=.0001
        new_rate=rate*mark/market
        qty=7.
        self.assertAlmostEqual(-qty*market*new_rate,-qty*mark*rate)
        self.assertAlmostEqual(new_rate,.000102)

if __name__=="__main__":unittest.main()
