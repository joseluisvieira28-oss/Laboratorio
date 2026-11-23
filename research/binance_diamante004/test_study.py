#!/usr/bin/env python3
"""Pre-source deterministic tests of the frozen BINANCE-004 hypothesis (no network)."""
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from study import (ProspectiveStudy,visible_mid_bid10,buy_quote,sell_base,
                   bps_move,raw_age_ok,WINDOW_NS,HORIZON_NS,MIN_EVENTS_FOR_GO,
                   MIN_DAYS_FOR_GO,MAX_ENTRY_WAIT_NS)

def seeded():
    m=ProspectiveStudy()
    for s,b in m.books.items():
        b.status="SYNCED"
        b.last_update_id=100
        b.bids={D("99.99"):D("100"),D("99.98"):D("100")}
        b.asks={D("100.01"):D("100"),D("100.02"):D("100")}
        m.last_depth_ns[s]=0
    m._start(0)
    return m

def primary_window(model,idx=0,s="BTCUSDT",sell="9000",buy="1000",
                   depth_frames=2,valid_clock=True):
    item=model.buckets[s]
    item["sell_quote"]=D(sell)
    item["buy_quote"]=D(buy)
    item["depth_updates"]=depth_frames
    item["invalid_clock"]=0 if valid_clock else 1
    model.last_depth_ns[s]=(idx+1)*WINDOW_NS-100_000_000

class BookMath(unittest.TestCase):
    def test_book_mid(self):
        m=seeded()
        self.assertEqual(visible_mid_bid10(m.books["BTCUSDT"])["mid"],D("100"))
    def test_quote_walk_100(self):
        m=seeded();b=m.books["BTCUSDT"]
        units=buy_quote(b,D("100"))
        self.assertEqual(units,D("100")/D("100.01"))
        proceeds=sell_base(b,units)
        self.assertLess(proceeds,D("100"))
    def test_no_quotes_no_extrapolation(self):
        m=seeded()
        self.assertIsNone(buy_quote(m.books["BTCUSDT"],D("1000000")))
    def test_no_sell_liquidity(self):
        m=seeded()
        self.assertIsNone(sell_base(m.books["BTCUSDT"],D("1000000")))
    def test_no_mid_future_logic(self):
        self.assertEqual(bps_move(D("100"),D("100")),D(0))
    def test_requires_min_day_and_events(self):
        self.assertEqual(MIN_EVENTS_FOR_GO,200)
        self.assertEqual(MIN_DAYS_FOR_GO,20)

class AsOf(unittest.TestCase):
    def test_no_future_received_time(self):
        recv_ns=1795412915000*1_000_000
        self.assertTrue(raw_age_ok({"e":"depthUpdate","E":1795412914900},recv_ns))
        self.assertFalse(raw_age_ok({"e":"depthUpdate","E":1795412916101},recv_ns))
    def test_stale_depth_source_rejected(self):
        self.assertFalse(raw_age_ok({"e":"depthUpdate","E":1795412911900},
                                    1795412915000*1_000_000))
    def test_trade_age_requires_both_clocks(self):
        self.assertFalse(raw_age_ok({"e":"aggTrade","E":1795412914900,
                                     "T":1795412910000},1795412915000*1_000_000))
    def test_primary_rule_is_frozen(self):
        m=seeded();primary_window(m)
        m._advance(WINDOW_NS)
        primary=[e for e in m.events if e["kind"]=="PRIMARY" and e["symbol"]=="BTCUSDT"]
        self.assertEqual(len(primary),1)
        self.assertEqual(primary[0]["status"],"WAIT_ENTRY")
        self.assertEqual(m.windows[0]["pressure"],True)
        self.assertEqual(m.windows[0]["resilience_proxy"],True)
    def test_flow_control_not_relabelled_primary(self):
        m=seeded()
        primary_window(m)
        m.books["BTCUSDT"].bids[D("99.99")]=D("0.1");m.books["BTCUSDT"].bids[D("99.98")]=D("0.1")
        m._advance(WINDOW_NS)
        kinds=[e["kind"] for e in m.events if e["symbol"]=="BTCUSDT"]
        self.assertEqual(kinds,["FLOW_ONLY_CONTROL"])
    def test_no_trade_zero_control(self):
        m=seeded()
        m.buckets["BTCUSDT"]["sell_quote"]=D(0)
        m.buckets["BTCUSDT"]["buy_quote"]=D(0)
        m.last_depth_ns["BTCUSDT"]=WINDOW_NS-100_000_000
        m.buckets["BTCUSDT"]["depth_updates"]=2
        m._advance(WINDOW_NS)
        self.assertFalse(any(e["symbol"]=="BTCUSDT" and e["kind"]=="PRIMARY" for e in m.events))
    def test_stale_window_ignored(self):
        m=seeded();primary_window(m)
        m.last_depth_ns["BTCUSDT"]=0
        m._advance(WINDOW_NS)
        self.assertFalse(any(e["symbol"]=="BTCUSDT" and e["kind"]=="PRIMARY" for e in m.events))
    def test_clock_error_fails_window(self):
        m=seeded();primary_window(m,valid_clock=False)
        m._advance(WINDOW_NS)
        self.assertFalse(m.windows[0]["valid"])
    def test_first_frame_after_boundary_not_past_bucket(self):
        # A newly arrived aggregate cannot be inserted into a 30s interval already closed.
        m=seeded()
        for s in m.books:
            m.last_depth_ns[s]=WINDOW_NS-100_000_000
            m.buckets[s]["depth_updates"]=1
        m._advance(WINDOW_NS)
        self.assertEqual(m.windows[0]["sell_quote"],"0")
        m.buckets["BTCUSDT"]["sell_quote"]+=D(100000)
        self.assertEqual(m.windows[0]["sell_quote"],"0")
    def test_120_second_cooldown(self):
        m=seeded();primary_window(m)
        m._advance(WINDOW_NS)
        count=lambda:sum(e["kind"]=="PRIMARY" and e["symbol"]=="BTCUSDT" for e in m.events)
        self.assertEqual(count(),1)
        for idx in range(1,4):
            primary_window(m,idx=idx)
            m._advance((idx+1)*WINDOW_NS)
        self.assertEqual(count(),1)
        primary_window(m,idx=4)
        m._advance(5*WINDOW_NS)
        self.assertEqual(count(),2)
    def test_entry_requires_next_book(self):
        m=seeded();primary_window(m)
        m._advance(WINDOW_NS)
        e=next(e for e in m.events if e["kind"]=="PRIMARY")
        m._settle_quotes(e,m.books["BTCUSDT"],WINDOW_NS,1795412915000*1_000_000)
        self.assertEqual(e["status"],"WAIT_ENTRY")
        m._settle_quotes(e,m.books["BTCUSDT"],WINDOW_NS+1_000_000,1795412915000*1_000_000)
        self.assertEqual(e["status"],"WAIT_EXIT")
    def test_entry_timeout_censors(self):
        m=seeded();primary_window(m)
        m._advance(WINDOW_NS)
        e=next(e for e in m.events if e["kind"]=="PRIMARY")
        m._settle_quotes(e,m.books["BTCUSDT"],WINDOW_NS+MAX_ENTRY_WAIT_NS+1,1795412915000*1_000_000)
        self.assertEqual(e["status"],"CENSORED_LATE_ENTRY")
    def test_matured_net_less_than_gross(self):
        m=seeded();primary_window(m)
        m._advance(WINDOW_NS)
        e=next(e for e in m.events if e["kind"]=="PRIMARY")
        m._settle_quotes(e,m.books["BTCUSDT"],WINDOW_NS+1_000_000,1795412915000*1_000_000)
        m._settle_quotes(e,m.books["BTCUSDT"],WINDOW_NS+1_000_000+HORIZON_NS,1795412975000*1_000_000)
        self.assertEqual(e["status"],"MATURED_HYPOTHETICAL_NOT_FILLED")
        s=e["returns"]["1000"]
        self.assertLess(D(s["STRESS_5BPS_net_bps"]),D(s["BASE_2BPS_net_bps"]))
        self.assertLess(D(s["BASE_2BPS_net_bps"]),D(s["gross_bps"]))
    def test_single_session_never_go(self):
        m=seeded();primary_window(m);m._advance(WINDOW_NS)
        r=m.summary()
        self.assertFalse(r["economic_go"])
        self.assertFalse(r["trading_authorized"])
        self.assertEqual(r["real_fills"],0)

if __name__=="__main__":unittest.main()
