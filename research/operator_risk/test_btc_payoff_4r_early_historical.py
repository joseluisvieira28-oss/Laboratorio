"""Synthetic BTC PAYOFF 4R historical partial tests. No source market or private trading."""
import importlib.util,unittest
from pathlib import Path
from types import SimpleNamespace

f=Path(__file__).with_name("btc_payoff_4r_early_historical.py")
spec=importlib.util.spec_from_file_location("btcpayoff4r_hist_test",f)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
HOUR=3_600_000
START=1583020800000


def scenario(edit=None,funding=None):
    v=[(100,101,99,100),
       (100,101,99,100),
       (100,101,99,100),
       (100,107,99,105.5),
       (106,108,104,106),
       (100,101,99,100),
       (100,101,99,100)]
    for i,z in (edit or {}).items():v[i]=z
    b=[dict(t=START+i*HOUR,open=float(o),high=float(hi),
             low=float(lo),close=float(cl),volume=1000)
       for i,(o,hi,lo,cl) in enumerate(v)]
    p=SimpleNamespace(
        START=START,FINISH=b[-1]["t"],EXPIRE=100*HOUR,
        EQUITY0=10000.0,LEV=2,MAINT_PROXY=.005,
        signals=lambda market:[i==1 for i in range(len(market))],
        nominal_bounds=lambda fill:(fill*1.20,fill*.95),
    )
    marks={bar["t"]:{"open":bar["open"],"low":bar["low"]} for bar in b}
    rates={START+i*HOUR:float(v) for i,v in (funding or {}).items()}
    return mod.child_replay(b,rates,marks,p,.0008,.0002)


class FourRHistTests(unittest.TestCase):
    def test_half_when_confirmed_close_and_next_open(self):
        d=scenario()
        self.assertEqual(d["realized_50pct_count"],1)
        partial=[x for x in d["closed_exit_leg_ledger"] if x["reason"]=="EARLY_HALF"]
        self.assertEqual(len(partial),1)
        self.assertEqual(partial[0]["exit_t"],START+4*HOUR)
        self.assertGreater(partial[0]["net"],0)

    def test_stop_gap_bypasses_early_half(self):
        d=scenario(edit={4:(90,93,88,89)})
        self.assertEqual(d["realized_50pct_count"],0)
        self.assertEqual(d["exit_reasons"].get("STOP_GAP"),1)

    def test_high_without_close_cannot_trigger_half(self):
        d=scenario(edit={3:(100,108,99,103)})
        self.assertEqual(d["realized_50pct_count"],0)

    def test_partial_net_under_funding_cost_refused(self):
        d=scenario(funding={3:.04})
        self.assertEqual(d["realized_50pct_count"],0)
        self.assertLess(d["signed_funding_total"],0)

    def test_original_target_and_stop_ambiguity_stop_first(self):
        d=scenario(edit={3:(100,130,90,100)})
        self.assertEqual(d["exit_reasons"].get("STOP_FIRST"),1)

    def test_original_4r_full_target_exit(self):
        d=scenario(edit={3:(100,125,99,122)})
        self.assertEqual(d["exit_reasons"].get("TARGET"),1)
        self.assertEqual(d["realized_50pct_count"],0)

    def test_no_same_bar_entry_or_optimistic_fill(self):
        d=scenario()
        self.assertTrue(all(x["entry_t"]==START+2*HOUR for x in d["closed_exit_leg_ledger"]))
        self.assertTrue(all(x["exit_t"]>START+2*HOUR for x in d["closed_exit_leg_ledger"]))

    def test_fee_cash_ledger_reconciles(self):
        d=scenario()
        self.assertFalse(d["unresolved_at_cutoff"])
        self.assertAlmostEqual(d["closed_equity_usdt"],
                               d["capital"]+sum(x["net"] for x in d["closed_exit_leg_ledger"]),
                               places=5)

    def test_costed_model_never_claims_live_bbo_or_oos(self):
        d=scenario()
        self.assertTrue(d["historical_BBO_not_available"])
        self.assertFalse(d["independent_OOS"])
        self.assertFalse(d["real_broker_ACK"])


if __name__=="__main__":unittest.main()
