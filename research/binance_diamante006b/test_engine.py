#!/usr/bin/env python3
"""BINANCE006B 1s source/as-of/fee/OOS gates, SYNTHETIC ONLY (zero network)."""
import datetime as dt
import unittest
from engine import (US,T0,TV,TT,TE,KlineFlow,cohort,net_bps,parse_1s,
                    summarize,bootstrap_lower)

def candle(sec,close=100.0,quote=0.0,buy=0.0):
    return (T0+sec*US,close,quote,quote-buy)
def event(day,kind="SELL_FLOW",score=5):
    return {"symbol":"BTCUSDT","kind":kind,"cohort":"TEST","date":str(day),
            "status":"MATURED_NOT_EXECUTED","gross_bps":score+30,
            "base_net_bps":score+6,"stress_net_bps":score}
def csvrow(sec=0,taker_buy=0,quote=100):
    start=T0+sec*US
    return [str(start),"100","101","99","100","1",str(start+US-1),
            str(quote),"2","0.5",str(taker_buy),"0"]

class SourceAndTiming(unittest.TestCase):
    def test_frozen_30_30_30(self):
        self.assertEqual((TV-T0)//86400//US,30)
        self.assertEqual((TT-TV)//86400//US,30)
        self.assertEqual((TE-TT)//86400//US,30)
    def test_no_cross_split_training_leak(self):
        self.assertEqual(cohort(TV-1),"TRAIN")
        self.assertEqual(cohort(TV),"VALIDATION")
        self.assertEqual(cohort(TT),"TEST")
    def test_microsecond_kline_schema(self):
        bar=parse_1s(csvrow())
        self.assertEqual(bar[0],T0)
        self.assertEqual(bar[2],100)
        self.assertEqual(bar[3],100)
    def test_bad_ms_timestamp_fails(self):
        r=csvrow();r[0]=str(T0//1000)
        with self.assertRaisesRegex(ValueError,"MICROSECONDS"):
            parse_1s(r)
    def test_buy_quote_cannot_exceed_total(self):
        with self.assertRaisesRegex(ValueError,"EXCEEDS_TOTAL"):
            parse_1s(csvrow(taker_buy=101))
    def test_bad_ohlc_blocks(self):
        r=csvrow();r[2]="99"
        with self.assertRaisesRegex(ValueError,"OHLC"):
            parse_1s(r)
    def test_strict_no_missing_second(self):
        model=KlineFlow("BTCUSDT")
        model.ingest(candle(0))
        with self.assertRaisesRegex(ValueError,"MISSING"):
            model.ingest(candle(2))
    def test_30s_prior_only_and_exact_60s_after_entry(self):
        model=KlineFlow("BTCUSDT")
        for sec in range(92):
            # 30 original SELL-flow completed bars; all other bars zero volume
            price=100.5 if sec>=90 else 100
            model.ingest(candle(sec,price,quote=500 if sec<30 else 0))
            if sec==28:self.assertNotIn("SELL_FLOW",model.active)
        rows=[e for e in model.events if e["kind"]=="SELL_FLOW"]
        self.assertEqual(len(rows),1)
        e=rows[0]
        self.assertEqual(e["decision_us"],T0+30*US)
        self.assertEqual(e["entry_us"],T0+31*US)
        self.assertEqual(e["exit_us"],T0+91*US)
        self.assertEqual(e["status"],"MATURED_NOT_EXECUTED")
        self.assertGreater(e["stress_net_bps"],0)
    def test_zero_quote_no_sell_pressure(self):
        model=KlineFlow("BTCUSDT")
        for sec in range(31):model.ingest(candle(sec,100,0))
        self.assertEqual(len(model.active),0)
    def test_30s_low_quote_no_signal(self):
        model=KlineFlow("BTCUSDT")
        for sec in range(31):model.ingest(candle(sec,100,quote=1))
        self.assertNotIn("SELL_FLOW",model.active)
    def test_fee_cost_stress_lower(self):
        self.assertLess(net_bps(100,100,5),net_bps(100,100,2))
        self.assertLess(net_bps(100,100,5),0)
    def test_go_synthetic_only(self):
        rows=[]
        for d in range(20):
            date=dt.date(2026,9,30)+dt.timedelta(days=d)
            rows.extend([event(date) for _ in range(10)])
            rows.extend([event(date,"UNCONDITIONAL_BASELINE",-4)])
        r=summarize(rows)
        self.assertTrue(r["scientific_limited_go"])
        self.assertFalse(r["live_trading_authorized"])
        self.assertEqual(r["actual_orders"],0)
    def test_single_day_200_is_not_enough(self):
        rows=[event(dt.date(2026,10,1)) for _ in range(200)]
        r=summarize(rows)
        self.assertEqual(r["status"],"INCONCLUSIVE_INSUFFICIENT_TEST_SAMPLE")
    def test_absorption_not_covered(self):
        r=summarize([])
        self.assertFalse(r["L2_absorption_tested"])
        self.assertTrue(r["1s_close_not_executable_quote"])
if __name__=="__main__":unittest.main()
