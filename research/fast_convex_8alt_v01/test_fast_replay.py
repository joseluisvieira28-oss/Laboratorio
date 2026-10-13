"""Purely synthetic, before outcomes: time-travel, costs, exits, source guards."""
import unittest
from unittest.mock import patch
from research.fast_convex_8alt_v01 import fast_replay as r

STEP=r.old.M5
T=1672617600000  # 2023-01-02T00:00Z, aligned 1h and 5m

def bars(n,open_=100.):
    return {T+i*STEP:{"t":T+i*STEP,"open":open_,"high":open_+0.2,
                       "low":open_-0.2,"close":open_,"volume":1.}
            for i in range(n)}

def run(b,signal_at=None,timeout=8*r.old.HOUR,funding=None,slip=2):
    signal_at=signal_at if signal_at is not None else T+STEP
    with patch.object(r,"PERIOD_START",T),patch.object(r,"PERIOD_END",T+len(b)*STEP):
        return r.run_arm(b,funding or {},{signal_at},r.old.M5,timeout,slip)

class FastFrozenContracts(unittest.TestCase):
    def test_fixed_128_arms_and_eight_alts(self):
        self.assertEqual(r.ASSETS,("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
                                  "DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT"))
        self.assertEqual([x for x,_ in r.TIMEFRAMES],["5m","15m","30m","1h"])
        self.assertEqual([x for x,_ in r.HORIZONS],["FAST8H","FAST24H"])
        self.assertEqual(len(r.ASSETS)*len(r.TIMEFRAMES)*len(r.HORIZONS)*len(r.COSTS),128)
        self.assertEqual((r.TARGET,r.STOP,r.TAKER_FEE,r.RISK_NOTIONAL),(.012,.006,.0008,.2))
        self.assertEqual(r.PERIOD_START,r.common.ECON_MS)
        self.assertEqual(r.PERIOD_END,r.common.END_MS)

    def test_signal_entry_waits_one_extra_bar_after_close(self):
        b=bars(10)
        b[T+3*STEP]["low"]=98.
        result,ledger=run(b)
        self.assertEqual(result["closed_trades"],1)
        self.assertEqual(ledger[0]["entry_t"],T+2*STEP)
        self.assertEqual(ledger[0]["exit_t"],T+4*STEP)
        self.assertEqual(ledger[0]["reason"],"STOP_INTRABAR")

    def test_same_5m_bar_stop_and_target_prefers_loss(self):
        b=bars(10)
        b[T+2*STEP].update(high=103.,low=98.)
        result,ledger=run(b)
        self.assertEqual(ledger[0]["reason"],"STOP_INTRABAR")
        self.assertLess(ledger[0]["net_pnl"],0)

    def test_gap_exits_at_actual_open_timestamp_and_price(self):
        b=bars(10)
        b[T+3*STEP].update(open=98.,high=99.,low=97.)
        _,ledger=run(b)
        self.assertEqual(ledger[0]["exit_t"],T+3*STEP)
        self.assertEqual(ledger[0]["reason"],"STOP_OPEN_GAP")
        self.assertLess(ledger[0]["exit"],98.)

    def test_8h_timeout_before_intrabars_and_24h_unclosed(self):
        b=bars(115)
        cutoff=T+2*STEP+8*r.old.HOUR
        b[cutoff].update(high=105.,low=95.)
        short,led=run(b,timeout=8*r.old.HOUR)
        self.assertEqual(led[0]["exit_t"],cutoff)
        self.assertEqual(led[0]["reason"],"MAX_HOLD_OPEN")
        long,led24=run(b,timeout=24*r.old.HOUR)
        self.assertEqual(led24[0]["reason"],"STOP_INTRABAR")
        self.assertEqual(led24[0]["exit_t"],cutoff+STEP)

    def test_charge_funding_when_settlement_bar_exits_intrabar(self):
        b=bars(12)
        target=T+5*STEP
        b[target].update(high=100.4,low=98.0)
        base,lead=run(b)
        paid,ledger=run(b,funding={target:.001})
        self.assertLess(paid["funding_total_usdt"],0)
        self.assertLess(paid["closed_net_pnl_usdt"],base["closed_net_pnl_usdt"])
        self.assertLess(ledger[0]["funding"],0)

    def test_funding_not_charged_when_timeout_at_bar_open(self):
        b=bars(115)
        end=T+2*STEP+8*r.old.HOUR
        paid,_=run(b,funding={end:.005})
        self.assertEqual(paid["funding_total_usdt"],0)

    def test_stress_slippage_lowers_net_pnl_same_fixed_path(self):
        b=bars(10)
        b[T+3*STEP]["high"]=102.
        base,led=run(b,slip=2)
        stress,led2=run(b,slip=5)
        self.assertEqual(led[0]["reason"],"TARGET_INTRABAR")
        self.assertLess(stress["closed_net_pnl_usdt"],base["closed_net_pnl_usdt"])

    def test_false_high_trade_frequency_not_candidacy(self):
        a={"marked_return_pct":10.,"profit_factor":1.8,
           "annual_closed_trades":{"2023":2,"2024":2,"2025":2},
           "annual_closed_pnl_usdt":{"2023":500,"2024":500,"2025":500},
           "max_5m_low_model_dd_pct":-5,"approx_CAGR_3y_pct":12,
           "static_closed_pnl_without_top3_usdt":300}
        q=r.historical_gate(a,a)
        self.assertFalse(q["all_gates_descriptive_pass"])
        self.assertFalse(q["gates"]["TRADE_FREQUENCY_EACH_YEAR_52"])
        self.assertFalse(q["independent_OOS_promoted"])

if __name__=="__main__":
    unittest.main()
