"""Synthetic unit safety for retrospective 1h policy translation. NO market outcomes."""
import importlib.util
import unittest
from types import SimpleNamespace
from pathlib import Path

p=Path(__file__).with_name("btc_parent_early_profit_historical.py")
spec=importlib.util.spec_from_file_location("btc_historical_shadow",p)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
H=3600000
START=1609459200000

def historical(changes=None,funding=None,fee=.0008,slip=.0002):
    # Candle start is 1 Jan 2021 UTC; signal only index1.
    candles=[
        (100,101,99,100),  # 0 prior
        (100,101,99,100),  # 1 signal at bar close
        (100,100.4,99,100),# 2 entry next OPEN
        (100,105,99,104.2),# 3 +1R confirmed-close signal
        (105,106,103,105), # 4 partial at next open
        (104,105,99,101),  # 5 remainder stop after partial
        (100,101,99,100),  # 6
        (100,101,99,100),  # 7
    ]
    for idx, values in (changes or {}).items():candles[idx]=values
    b=[dict(t=START+i*H,open=float(o),high=float(hi),low=float(lo),close=float(cl),volume=1000)
       for i,(o,hi,lo,cl) in enumerate(candles)]
    fake=SimpleNamespace(START=START, FINISH=b[-1]["t"],EQUITY0=10000.,
                         signals=lambda bars:[i==1 for i in range(len(bars))],
                         check_bars=lambda *args:None)
    marks={bar["t"]:{"open":bar["open"]} for bar in b}
    rates={START+i*H:val for i,val in (funding or {}).items()}
    return mod.replay_child(b,rates,marks,fee,slip,fake)

class BTCProfitHistoricalTests(unittest.TestCase):
    def test_profit_realized_only_at_next_open(self):
        a=historical()
        self.assertEqual(a["partial_50pct_count"],1)
        partial=[l for l in a["closed_leg_ledger"] if l["reason"]=="EARLY_HALF"]
        self.assertEqual(len(partial),1)
        self.assertEqual(partial[0]["exit_t"],START+4*H)
        self.assertGreater(partial[0]["net"],0)
        self.assertEqual(a["entries"],1)

    def test_stop_is_never_skipped_due_to_scheduled_partial(self):
        a=historical({4:(90,91,89,90)})
        self.assertEqual(a["partial_50pct_count"],0)
        self.assertEqual(a["exit_counts"].get("STOP_GAP"),1)

    def test_high_only_without_confirmed_close_does_not_trigger(self):
        a=historical({3:(100,110,99,103),4:(103,106,102,103)})
        self.assertEqual(a["partial_50pct_count"],0)

    def test_net_half_profit_gate_can_block_fill(self):
        # Gap down at next open; previous close had +1R.
        a=historical({4:(100.1,101,99.5,100.5)})
        self.assertEqual(a["partial_50pct_count"],0)

    def test_negative_funding_cannot_improve_partial_net(self):
        b=historical()
        a=historical(funding={3:.03})
        self.assertLess(a["funding_total"],b["funding_total"])
        self.assertLess(a["closed_equity"],b["closed_equity"])

    def test_conservative_initial_margin_r_is_positive(self):
        a=historical()
        self.assertGreater(a["partial_50pct_count"],0)
        self.assertGreater(a["paid_opening_fees"],0)
        self.assertGreater(a["paid_closing_fees"],0)

    def test_no_future_signal_or_same_bar_entry(self):
        a=historical({2:(100,105,99,105),3:(100,101,99,100)})
        partial=[l for l in a["closed_leg_ledger"] if l["reason"]=="EARLY_HALF"]
        self.assertEqual(partial,[])

    def test_profit_factor_and_cash_reconciliation(self):
        a=historical()
        legnet=sum(l["net"] for l in a["closed_leg_ledger"])
        self.assertAlmostEqual(a["closed_positions_net"],legnet,places=6)
        self.assertEqual(a["full_exit_count"],a["closed_positions"])
        self.assertFalse(a["open_position"])
        self.assertAlmostEqual(a["closed_equity"],a["capital"] + legnet,places=6)

if __name__=="__main__": unittest.main()
