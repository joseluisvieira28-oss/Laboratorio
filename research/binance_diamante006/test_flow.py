#!/usr/bin/env python3
"""SYNTHETIC ONLY -- test original scientific decisions, not market results."""
import unittest
import datetime as dt
from flow_study import (T0, T_VALID, T_TEST, US, SYMBOLS, Trade, FlowStudy,
                        parse_agg_row,group_of,quote_net_bps,summarize,
                        bootstrap_cluster_lower)

def tx(ts,ident,price=100,qty=100,sell=True):
    return Trade(ts,ident,float(price),float(qty),sell)

def ev(day,kind="SELL_FLOW",score=5,symbol="BTCUSDT"):
    return {"symbol":symbol,"kind":kind,"cohort":"TEST","decision_date_utc":str(day),
            "status":"MATURED_NOT_FILLED","gross_bps":score+30,
            "base_net_bps":score+6,"stress_net_bps":score}

class ScientificTests(unittest.TestCase):
    def test_datetime_partitions(self):
        self.assertEqual(group_of(T0),"TRAIN")
        self.assertEqual(group_of(T_VALID-1),"TRAIN")
        self.assertEqual(group_of(T_VALID),"VALIDATION")
        self.assertEqual(group_of(T_TEST),"TEST")
    def test_spot_microsecond_2026(self):
        a=["12345","100.12","3.15","234","235",str(T0+50*US),"True","True"]
        t=parse_agg_row(a)
        self.assertTrue(t.buyer_maker)
        self.assertEqual(t.ts_us,T0+50*US)
        a[5]=str((T0+50*US)//1000)
        with self.assertRaisesRegex(ValueError,"MICROSECONDS"):
            parse_agg_row(a)
    def test_reversed_id_blocks(self):
        with self.assertRaisesRegex(ValueError,"NON_INCREASING"):
            parse_agg_row(["2","100","3","1","2",str(T0),"true","true"],previous_id=3)
    def test_bad_price_blocks(self):
        with self.assertRaisesRegex(ValueError,"PRICE"):
            parse_agg_row(["2","nan","3","1","2",str(T0),"true","true"])
    def test_flow_long_only_when_prior_window_closes(self):
        x=FlowStudy("BTCUSDT")
        x.ingest(tx(T0+5*US,1,100,100,True))
        self.assertEqual(len(x.active),0)
        x.ingest(tx(T0+31*US,2,100,1,False))
        self.assertEqual(x.active["SELL_FLOW"]["status"],"WAIT_EXIT")
        self.assertEqual(x.active["SELL_FLOW"]["decision_us"],T0+30*US)
        x.ingest(tx(T0+91*US,3,100.5,1,False))
        z=[e for e in x.events if e["kind"]=="SELL_FLOW"]
        self.assertEqual(len(z),1)
        self.assertEqual(z[0]["status"],"MATURED_NOT_FILLED")
        self.assertGreater(z[0]["stress_net_bps"],0)
    def test_late_entry_is_censored_not_hidden(self):
        x=FlowStudy("BTCUSDT")
        x.ingest(tx(T0+5*US,1))
        x.ingest(tx(T0+34*US,2))
        z=[e for e in x.events if e["kind"]=="SELL_FLOW"]
        self.assertEqual(len(z),1)
        self.assertEqual(z[0]["status"],"CENSORED_ENTRY_DELAY")
    def test_below_notional_has_no_signal(self):
        x=FlowStudy("BTCUSDT")
        x.ingest(tx(T0+5*US,1,100,1,True))
        x.ingest(tx(T0+31*US,2,100,1,True))
        self.assertNotIn("SELL_FLOW",x.active)
    def test_120second_cooldown(self):
        x=FlowStudy("BTCUSDT")
        for i in range(5):
            begin=T0+int((i*30+1)*US)
            x.ingest(tx(begin,i*2+1,100,100,True))
            x.ingest(tx(begin+int(30*US),i*2+2,100,1,False))
        # 120-sec spacing means no more than 2 signal decisions in ~150s
        self.assertLessEqual(sum(e["kind"]=="SELL_FLOW" for e in x.events)+int("SELL_FLOW" in x.active),2)
    def test_fee_stress_more_than_base(self):
        gross=100/100
        self.assertLess(quote_net_bps(100,100,5),quote_net_bps(100,100,2))
        self.assertLess(quote_net_bps(100,100,5),0)
    def test_bootstrap_requires_20_utc_days(self):
        self.assertIsNone(bootstrap_cluster_lower([ev(dt.date(2026,10,1))],reps=10))
    def test_synthetic_20day_200event_gate_only(self):
        rows=[]
        for i in range(20):
            day=dt.date(2026,9,30)+dt.timedelta(days=i)
            rows += [ev(day) for _ in range(10)]
            rows += [ev(day,"BASELINE",-5)]
        s=summarize(rows)
        self.assertTrue(s["economic_go_scientific_limited"])
        self.assertFalse(s["live_trading_go"])
        self.assertEqual(s["test_events"],200)
    def test_fewer_days_cannot_go(self):
        rows=[ev(dt.date(2026,10,1)) for _ in range(200)]
        rows += [ev(dt.date(2026,10,1),"BASELINE",-5)]
        s=summarize(rows)
        self.assertEqual(s["status"],"INCONCLUSIVE_INSUFFICIENT_OOS_SAMPLE")
    def test_zero_trade_is_not_simulated_loss(self):
        s=summarize([])
        self.assertIsNone(s["groups"]["TEST"]["SELL_FLOW"]["mean_stress_net_bps"])
        self.assertFalse(s["economic_go_scientific_limited"])
if __name__=="__main__":unittest.main()
