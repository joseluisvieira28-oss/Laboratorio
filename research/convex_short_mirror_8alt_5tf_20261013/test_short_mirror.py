"""Synthetic only: verify direction mirror, order timing, funding sign, gap and stop reset."""
import unittest
from unittest.mock import patch
from research.convex_short_mirror_8alt_5tf_20261013 import short_mirror as m
from research.convex_multialt_4tf_20261013 import multialt_matrix as old

BASE_T=1672531200000

def market(n=24):
    return {BASE_T+i*m.FIVE:{"t":BASE_T+i*m.FIVE,"open":100.,
            "high":100.4,"low":99.6,"close":100.,"volume":10.} for i in range(n)}

def play(data,signal_idx=0,*,funding=None,tf=m.FIVE,slip=2):
    n=len(data)
    bars=[data[t] for t in sorted(data)]
    signal=[i==signal_idx for i in range(n)]
    return m.simulate_short(tf,bars,data,funding or {},slip,
                            include_trades=True,start=BASE_T,end=BASE_T+n*m.FIVE,
                            forced_signals=signal)

class MirrorShortTests(unittest.TestCase):
    def test_frozen_80_models_and_original_risk(self):
        self.assertEqual(len(m.ASSETS),8)
        self.assertEqual([v for _,v in m.TFS],[300000,900000,1800000,3600000,14400000])
        self.assertEqual(m.COSTS,(("BASE",2),("STRESS",5)))
        self.assertEqual((m.STOP,m.TRAIL,m.ACTIVATE,m.FEE,m.EXPOSURE),(.04,.12,.05,.0008,.2))
        self.assertEqual(len(m.ASSETS)*len(m.TFS)*len(m.COSTS),80)

    def test_short_signal_extreme_high_in_bear_regime(self):
        # A high Z-score by itself is not sufficient: bearish SMA is required.
        closes=[130.]*180+[100.]*24+[110.]
        bars=[{"t":BASE_T+i*m.FIVE,"open":closes[i],"high":closes[i],
               "low":closes[i],"close":closes[i],"volume":10.} for i in range(len(closes))]
        real=old.src.load_parent()
        globals()["sma"]=real.__globals__["sma"]
        globals()["stdev"]=real.__globals__["stdev"]
        def fake_parent(bars):
            return [False]*len(bars),[{"rsi":81,"z":3.1,"vol_flag":False} for _ in bars]
        with patch.object(old.src,"load_parent",return_value=fake_parent):
            signals=m.mirror_short_signals(bars)
        self.assertTrue(signals[-1])
        self.assertFalse(signals[-2])
        bars[-1]["close"]=170.;bars[-1]["high"]=170.;bars[-1]["open"]=170.;bars[-1]["low"]=170.
        with patch.object(old.src,"load_parent",return_value=fake_parent):
            self.assertFalse(m.mirror_short_signals(bars)[-1])

    def test_short_entry_after_one_full_post_close_bar_and_adverse_exit_high(self):
        bars=market()
        bars[BASE_T+3*m.FIVE]["high"]=110.
        res=play(bars)
        self.assertEqual(res["entries"],1)
        self.assertEqual(res["closed_trades"],1)
        tr=res["trades"][0]
        self.assertEqual(tr["open_t"],BASE_T+2*m.FIVE)
        self.assertEqual(tr["close_t"],BASE_T+4*m.FIVE)
        self.assertEqual(tr["exit_reason"],"STOP_INTRABAR")
        self.assertLess(tr["net_pnl"],0)
        self.assertLess(tr["entry_price"],100)
        self.assertGreater(tr["exit_price"],100)

    def test_short_funding_is_reverse_of_long(self):
        bars=market()
        a=play(bars)
        b=play(bars,funding={BASE_T+3*m.FIVE:0.01})
        c=play(bars,funding={BASE_T+3*m.FIVE:-0.01})
        self.assertGreater(b["marked_return_pct"],a["marked_return_pct"])
        self.assertLess(c["marked_return_pct"],a["marked_return_pct"])
        self.assertGreater(b["funding_usdt"],0)
        self.assertLess(c["funding_usdt"],0)

    def test_nonlatched_trail_weakens_when_profitable_short_rebounds(self):
        bars=market()
        entry=BASE_T+2*m.FIVE
        bars[entry].update(high=100.4,low=89.,close=94.)
        bars[entry+m.FIVE].update(open=94.,high=99.,low=94.,close=98.)
        bars[entry+2*m.FIVE].update(open=98.,high=102.,low=97.,close=100.)
        bars[entry+3*m.FIVE].update(open=100.,high=105.,low=99.,close=104.)
        result=play(bars)
        self.assertEqual(result["closed_trades"],1)
        self.assertEqual(result["trades"][0]["close_t"],entry+4*m.FIVE)
        self.assertEqual(result["trades"][0]["exit_reason"],"STOP_INTRABAR")

    def test_short_gap_uses_observed_worse_open_and_stress_degrades(self):
        bars=market()
        bars[BASE_T+3*m.FIVE].update(open=120.,high=121.,low=119.,close=120.)
        a=play(bars,slip=2)
        b=play(bars,slip=5)
        self.assertEqual(a["trades"][0]["exit_reason"],"STOP_OPEN_GAP")
        self.assertLess(a["trades"][0]["notional_return_pct"],-19)
        self.assertLess(b["marked_return_pct"],a["marked_return_pct"])

    def test_short_terminal_open_is_marked_not_fake_closed(self):
        r=play(market())
        self.assertTrue(r["end_position_open"])
        self.assertEqual(r["closed_trades"],0)
        self.assertEqual(r["fees_usdt"],10000*.2*.0008)

if __name__=="__main__":
    unittest.main()
