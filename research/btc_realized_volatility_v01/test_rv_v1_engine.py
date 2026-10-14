"""Synthetic QA only. DO NOT use market outcomes to change rules."""
import datetime as dt
import unittest
from rv_v1_engine import HOUR, START, SourceBlocked, ts_ms, features, replay


class RVFrozenTests(unittest.TestCase):
    def test_timestamp_ms_us_and_invalid(self):
        self.assertEqual(ts_ms(START), START)
        self.assertEqual(ts_ms(START*1000), START)
        with self.assertRaises(SourceBlocked):
            ts_ms(START*1000+17)
        with self.assertRaises(SourceBlocked):
            ts_ms(100)

    def test_features_only_completed_bars(self):
        start = START - 132*4*HOUR
        hrs=[]
        for i in range(140*4):
            t=start+i*HOUR
            price=20000+5*i+7*(i%4==3)
            hrs.append((t,price,price+40,price-40,price+10))
        dec=features(hrs)
        self.assertTrue(dec)
        first=list(dec)[0]
        self.assertEqual(first % (4*HOUR), 0)
        self.assertTrue(all(set(d["signals"])=={"EMA50_BENCH","EMA50_RV_FILTER","RV_EXPANSION_ENTRY"} for d in dec.values()))
        with self.assertRaises(SourceBlocked):
            features(hrs[1:])

    def test_next_hour_entry_and_gap_stop_with_funding(self):
        h0=(START, 100.,102.,99.,101.)
        h1=(START+HOUR,95.,97.,90.,92.)
        d={START:{"signals":{"EMA50_BENCH":True,"EMA50_RV_FILTER":False,
                             "RV_EXPANSION_ENTRY":False},"close_below":False}}
        result, trades=replay([h0,h1],{START+HOUR:(0.001,None)},d,"EMA50_BENCH",.0002)
        self.assertEqual(result["closed"],1)
        tr=trades[0]
        self.assertEqual(tr["reason"],"STOP")
        self.assertEqual(tr["opened"],START)
        self.assertLess(tr["exit"],95)
        self.assertLess(tr["funding"],0)
        self.assertGreater(tr["entry_fee"],0)
        self.assertGreater(tr["exit_fee"],0)
        self.assertAlmostEqual(tr["net"],(tr["exit"]-tr["entry"])*tr["quantity"]
                               -tr["entry_fee"]-tr["exit_fee"]+tr["funding"],places=6)

    def test_no_new_entry_until_confirmed_four_hour_decision(self):
        h=[(START+i*HOUR,100,101,99,100) for i in range(4)]
        d={START+4*HOUR:{"signals":{"EMA50_BENCH":True,"EMA50_RV_FILTER":True,
                                "RV_EXPANSION_ENTRY":True},"close_below":False}}
        r,t=replay(h,{},d,"EMA50_BENCH",.0002)
        self.assertEqual(r["closed"],0)
        self.assertFalse(r["open_position"])

    def test_long_funding_credit_when_rate_negative(self):
        h=[(START,100,101,99,100),(START+HOUR,100,101,99,100)]
        d={START:{"signals":{"EMA50_BENCH":True,"EMA50_RV_FILTER":False,
                              "RV_EXPANSION_ENTRY":False},"close_below":False}}
        r,t=replay(h,{START+HOUR:(-0.001,None)},d,"EMA50_BENCH",.0002)
        self.assertGreater(r["funding_total"],0)
        self.assertTrue(r["open_position"])

    def test_stop_is_live_in_same_entry_hour(self):
        h=[(START,100,101,90,95)]
        d={START:{"signals":{"EMA50_BENCH":True,"EMA50_RV_FILTER":False,
                               "RV_EXPANSION_ENTRY":False},"close_below":False}}
        r,trades=replay(h,{},d,"EMA50_BENCH",.0002)
        self.assertEqual(r["closed"],1)
        self.assertEqual(trades[0]["reason"],"STOP_SAME_HOUR")
        self.assertFalse(r["open_position"])

    def test_ema_exit_at_next_open(self):
        h=[(START,100,101,99,100),(START+HOUR,104,105,103,104)]
        d={START:{"signals":{"EMA50_BENCH":True,"EMA50_RV_FILTER":False,
                              "RV_EXPANSION_ENTRY":False},"close_below":False},
           START+HOUR:{"signals":{"EMA50_BENCH":False,"EMA50_RV_FILTER":False,
                                  "RV_EXPANSION_ENTRY":False},"close_below":True}}
        r,t=replay(h,{},d,"EMA50_BENCH",.0002)
        self.assertEqual(t[0]["reason"],"EMA50")
        self.assertAlmostEqual(t[0]["exit"],104*(1-.0002))


if __name__=="__main__":
    unittest.main()
