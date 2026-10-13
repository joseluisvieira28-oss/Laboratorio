"""Strict synthetic 5m V5 causal invariants; no historical outcomes."""
import unittest
from unittest.mock import patch
from research.convex_8alt_5m_common_20261013 import native5m as m
from research.convex_multialt_4tf_20261013 import multialt_matrix as old
from research.convex_8alt_common_2023_25 import common_3yr as w

class Frozen5m(unittest.TestCase):
    def test_symbols_costs_window_immutable(self):
        self.assertEqual(len(m.ASSETS),8)
        self.assertEqual(m.TF,300000)
        self.assertEqual(m.COSTS,(("BASE",2),("STRESS",5)))
        w.apply_locked_3year_window()
        self.assertEqual((old.START,old.END,old.START_PRICE),(w.ECON_MS,w.END_MS,w.PRE_MS))
        self.assertEqual((old.base.STOP,old.base.TRAIL,old.base.ACTIVATE,old.base.FEE,old.base.PCT_NOTIONAL),
                         (.04,.12,.05,.0008,.20))

    def test_native_five_minute_causal_witness_cannot_fill_same_bar(self):
        start=w.ECON_MS
        bars={start+i*m.TF:{"t":start+i*m.TF,"open":100.0,"high":101.,
                             "low":99.,"close":100.,"volume":10.} for i in range(12)}
        bars[start+3*m.TF]["low"]=90.
        ordered=[bars[t] for t in sorted(bars)]
        signals=[True]+[False]*11
        w.apply_locked_3year_window()
        with patch.object(old.base,"END",start+12*m.TF),patch.object(old.src,"load_parent",
                          return_value=lambda _: (signals,[None]*12)):
            r=old.base.simulate(m.TF,ordered,bars,{},2,include_trades=True)
        self.assertEqual(r["closed_trades"],1)
        self.assertEqual(r["trades"][0]["open_t"],start+2*m.TF)
        self.assertEqual(r["trades"][0]["exit_reason"],"STOP_INTRABAR")
        self.assertLess(r["trades"][0]["net_pnl"],0)

    def test_funding_only_at_actual_future_settlement(self):
        start=w.ECON_MS
        bars={start+i*m.TF:{"t":start+i*m.TF,"open":100.,"high":100.5,
                             "low":99.5,"close":100.,"volume":1.} for i in range(12)}
        ordered=[bars[t] for t in sorted(bars)]
        signals=[True]+[False]*11
        w.apply_locked_3year_window()
        with patch.object(old.base,"END",start+12*m.TF),patch.object(old.src,"load_parent",
                          return_value=lambda _: (signals,[None]*12)):
            a=old.base.simulate(m.TF,ordered,bars,{},2)
            b=old.base.simulate(m.TF,ordered,bars,{start+3*m.TF:.01},2)
        self.assertLess(b["marked_return_pct"],a["marked_return_pct"])
        self.assertLess(b["funding_usdt"],0.)

    def test_no_new_production_venue_or_private_access(self):
        self.assertTrue(all(a.endswith("USDT") for a in m.ASSETS))
        self.assertNotIn("BTCUSDT",m.ASSETS)

if __name__=="__main__":
    unittest.main()
