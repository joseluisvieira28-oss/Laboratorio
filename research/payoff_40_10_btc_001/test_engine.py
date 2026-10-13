"""Pure synthetic tests: NOT market results and do not prove edge."""
import unittest
from unittest.mock import patch
from datetime import datetime,timezone
import engine
import sources

T0=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp()*1000)

def fixture(n=240):
    b=[dict(t=T0+i*engine.HOUR,open=100.,high=100.,low=100.,close=100.,volume=100.) for i in range(n)]
    m={v["t"]:dict(open=100.,high=100.,low=100.,close=100.) for v in b}
    return b,m

def trial(b,m,signal,mode="PAYOFF",funding=None,fee=.0008,slip=0,begin=210,end=None):
    if end is None:end=len(b)-1
    with patch("engine.signals",return_value=signal):
        return engine.replay(b,funding or {},m,mode,fee,slip,
                             begin=T0+begin*engine.HOUR,end=T0+end*engine.HOUR)

class InvariantTests(unittest.TestCase):
    def test_target_and_stop_math(self):
        top,bottom=engine.nominal_bounds(100.)
        self.assertAlmostEqual(top,120.17614091273018,places=8)
        self.assertAlmostEqual(bottom,95.15612489991994,places=8)
        self.assertAlmostEqual(2*((1-.0008)*top/100-(1+.0008)),.40)
        self.assertAlmostEqual(2*((1-.0008)*bottom/100-(1+.0008)),-.10)

    def test_no_same_bar_entry_foreknowledge(self):
        b,m=fixture();sig=[False]*len(b);sig[210]=True
        b[211]["high"]=125.
        r=trial(b,m,sig)
        self.assertEqual(r["trades_closed"],1)
        self.assertEqual(r["trade_ledger"][0]["entry_t"],b[211]["t"])
        self.assertEqual(r["trade_ledger"][0]["reason"],"TARGET")
        self.assertAlmostEqual(r["trade_ledger"][0]["margin_net_return"],.40)

    def test_stop_and_target_one_bar_stop_first(self):
        b,m=fixture();sig=[False]*len(b);sig[210]=True
        b[211]["low"]=90.;b[211]["high"]=125.
        r=trial(b,m,sig)
        self.assertEqual(r["trade_ledger"][0]["reason"],"AMBIGUOUS_STOP_FIRST")

    def test_gap_can_exceed_stop_budget(self):
        b,m=fixture();sig=[False]*len(b);sig[210]=True
        b[212].update(open=90.,low=89.,high=100.,close=95.)
        r=trial(b,m,sig)
        self.assertEqual(r["trade_ledger"][0]["reason"],"STOP_GAP")
        self.assertLess(r["trade_ledger"][0]["margin_net_return"],-.10)

    def test_funding_paid_for_carried_position(self):
        b,m=fixture();sig=[False]*len(b);sig[210]=True
        b[214]["high"]=125.
        r=trial(b,m,sig,funding={b[212]["t"]:.001})
        self.assertEqual(r["funding_events"],1)
        self.assertLess(r["funding_cash_total"],0)
        self.assertLess(r["trade_ledger"][0]["margin_net_return"],.40)

    def test_new_entry_same_funding_timestamp_not_charged(self):
        b,m=fixture();sig=[False]*len(b);sig[210]=True
        b[211]["high"]=125.
        r=trial(b,m,sig,funding={b[211]["t"]:.001})
        self.assertEqual(r["funding_events"],0)

    def test_sixty_day_expiration_next_open(self):
        b,m=fixture(1800);sig=[False]*len(b);sig[210]=True
        r=trial(b,m,sig,end=1798)
        self.assertEqual(r["trade_ledger"][0]["reason"],"TIME_EXIT")
        self.assertEqual(r["trade_ledger"][0]["exit_t"]-r["trade_ledger"][0]["entry_t"],engine.EXPIRE)

    def test_historical_cutoff_open_not_counted_as_loss(self):
        b,m=fixture();sig=[False]*len(b);sig[210]=True
        r=trial(b,m,sig)
        self.assertEqual(r["trades_closed"],0)
        self.assertEqual(len(r["unresolved_at_cutoff"]),1)

    def test_parent_trailing_uses_completed_previous_bar(self):
        b,m=fixture();sig=[False]*len(b);sig[210]=True
        b[211].update(high=115.,close=110.)
        b[212].update(open=110.,high=112.,low=100.,close=100.)
        r=trial(b,m,sig,mode="PARENT")
        self.assertEqual(r["trade_ledger"][0]["reason"],"STOP_OR_TRAIL")
        self.assertAlmostEqual(r["trade_ledger"][0]["exit_fill"],115*.88)

    def test_gap_in_bars_fails_closed(self):
        b,m=fixture();sig=[False]*len(b);sig[210]=True
        del b[1]
        with self.assertRaisesRegex(ValueError,"HOURLY_SOURCE_GAP"):
            trial(b,m,sig)

    def test_funding_schema_fails_closed(self):
        self.assertEqual(
            sources.parse_funding("calc_time,funding_interval_hours,last_funding_rate\n1609459200000,8,0.00010\n"),
            {1609459200000:.0001})
        with self.assertRaisesRegex(ValueError,"UNKNOWN_FUNDING_HEADER"):
            sources.parse_funding("a,b,c\n1,2,3\n")

    def test_stress_fee_does_not_move_frozen_barriers(self):
        top,bottom=engine.nominal_bounds(100.)
        self.assertLess(2*((1-.001)*top/100-(1+.001)),.40)
        self.assertLess(2*((1-.001)*bottom/100-(1+.001)),-.10)

if __name__=="__main__":unittest.main()
