"""Synthetic-only tests: never open protected market outcomes."""
import unittest
from engine import (
    BOUNDARY, FIVE, H, fast_rebound, validate_signal,
    causal_first_5m_open, observed_quote_pair, normalized_parent_qty,
    six_hour_placebo_signal,
)


def signal(t=BOUNDARY, lag=1000):
    return {"symbol": "BTCUSDT", "side": "LONG",
            "bar_open_ms": t, "witness_ms": t+H+lag, "source_sha256": "a"*64}


def bars(t, n=48, op=100, hi=100.1, lo=99.9, cl=100):
    return [dict(t=t+i*FIVE, open=op, high=hi, low=lo, close=cl)
            for i in range(n)]


class FrozenContracts(unittest.TestCase):
    def test_boundary_and_timely_witness(self):
        self.assertEqual(BOUNDARY, 1792022400000)
        self.assertEqual(validate_signal(signal()), "PASS")
        self.assertEqual(validate_signal(signal(BOUNDARY-H)), "OUTSIDE_NEW_BOUNDARY")
        self.assertEqual(validate_signal(signal(lag=601000)), "NOT_TIMELY_AT_T0")
        x=signal(); x["source_sha256"]="X"; self.assertEqual(validate_signal(x),"SIGNAL_PROVENANCE_BLOCKED")

    def test_causal_entry_not_fictitious_hour_open(self):
        s=signal()
        self.assertEqual(causal_first_5m_open(s), BOUNDARY + H + FIVE)
        s["witness_ms"] += FIVE
        self.assertEqual(causal_first_5m_open(s), BOUNDARY + H + 2*FIVE)

    def test_funding_custody_blocks(self):
        s=signal(); t=causal_first_5m_open(s)
        self.assertEqual(fast_rebound(s,bars(t))["status"],"FUNDING_NOT_ATTESTED")

    def test_same_bar_stop_first(self):
        s=signal(); t=causal_first_5m_open(s)
        b=bars(t,1,op=100,hi=105,lo=90,cl=100)
        r=fast_rebound(s,b,funding_attested=True)
        self.assertEqual(r["exit_reason"],"STOP_FIRST")
        self.assertLess(r["net_pct"],0)

    def test_target_when_no_stop(self):
        s=signal(); t=causal_first_5m_open(s)
        b=bars(t,1,op=100,hi=103,lo=100,cl=102)
        r=fast_rebound(s,b,funding_attested=True)
        self.assertEqual(r["exit_reason"],"TARGET")
        self.assertGreater(r["net_pct"],0)
        self.assertLess(r["net_pct"],0.75)

    def test_negative_gap_worse_than_stop(self):
        s=signal(); t=causal_first_5m_open(s)
        b=bars(t,1,op=100,hi=100.05,lo=99.95,cl=100)
        b.append(dict(t=t+FIVE,open=95,high=96,low=94,close=95))
        r=fast_rebound(s,b,funding_attested=True)
        self.assertEqual(r["exit_reason"],"STOP_GAP")
        self.assertLess(r["net_pct"],-4)

    def test_unresolved_is_not_forced_win_or_loss(self):
        s=signal(); t=causal_first_5m_open(s)
        r=fast_rebound(s,bars(t,2),funding_attested=True)
        self.assertEqual(r["status"],"OPEN_UNRESOLVED")
        self.assertIsNone(r["net_pct"])

    def test_four_hour_expiry_at_last_bar(self):
        s=signal(); t=causal_first_5m_open(s)
        r=fast_rebound(s,bars(t),funding_attested=True)
        self.assertEqual(r["exit_reason"],"TIME_EXIT")
        self.assertEqual(r["exit_t"],t+4*H)
        self.assertLess(r["net_pct"],0)

    def test_gaps_and_broken_ohlc_block(self):
        s=signal(); t=causal_first_5m_open(s)
        b=bars(t,2); b[1]["t"]+=FIVE
        self.assertEqual(fast_rebound(s,b,funding_attested=True)["status"],"SOURCE_GAP_OR_BAD_OHLC")
        b=bars(t,1); b[0]["high"]=99
        self.assertEqual(fast_rebound(s,b,funding_attested=True)["status"],"SOURCE_GAP_OR_BAD_OHLC")

    def test_funding_is_not_zero_assumption(self):
        s=signal(); t=causal_first_5m_open(s)
        b=bars(t,48)
        base=fast_rebound(s,b,funding_attested=True)
        funded=fast_rebound(s,b,funding_attested=True,
                            funding_events=[{"t":t+2*H,"cash_fraction":-0.001}])
        self.assertAlmostEqual(funded["net_pct"],base["net_pct"]-0.1,places=8)
        bad=fast_rebound(s,b,funding_attested=True,
                         funding_events=[{"t":t-1,"cash_fraction":0.5}])
        self.assertEqual(bad["status"],"FUNDING_OUTSIDE_POSITION")

    def test_quote_comparison_requires_timestamps_and_depth(self):
        t=BOUNDARY+H+1000
        q=[{"t":t,"witnessed_at_ms":t+30,"venue":"MEXC",
            "ask":100,"bid":99.98,"depth_ask_usdt":1000},
           {"t":t+FIVE,"witnessed_at_ms":t+FIVE+20,"venue":"MEXC",
            "ask":99.5,"bid":99.48,"depth_ask_usdt":1000}]
        r=observed_quote_pair(t,q)
        self.assertEqual(r["status"],"SOURCE_ONLY_NO_FILL_PROOF")
        self.assertAlmostEqual(r["entry_improvement_bps_B_vs_A"],50)
        self.assertEqual(observed_quote_pair(t,q,notional_usdt=1100)["status"],
                         "QUOTE_OR_DEPTH_BLOCKED")
        q[1]["witnessed_at_ms"] += 5000
        self.assertEqual(observed_quote_pair(t,q)["status"],"QUOTE_OR_DEPTH_BLOCKED")

    def test_sizing_bounded_not_guaranteed_loss(self):
        x=normalized_parent_qty(10000,100)
        self.assertLessEqual(x["risk_fraction"],0.0025+1e-12)
        self.assertLessEqual(x["entry"]*x["qty"],2000)
        y=normalized_parent_qty(10000,100,active_planned_risk_fraction=0.004)
        self.assertLessEqual(y["risk_fraction"],0.001+1e-12)
        self.assertEqual(normalized_parent_qty(10000,100,
                         active_planned_risk_fraction=0.005)["qty"],0)

    def test_fixed_six_hour_placebo_no_retro_entry(self):
        s=signal()
        p=six_hour_placebo_signal(s)
        self.assertEqual(causal_first_5m_open(p)-causal_first_5m_open(s),6*H)
        self.assertEqual(p["control_type"],"FIXED_DELAY_6H_NOT_A_NEW_PARENT_SIGNAL")
        self.assertEqual(validate_signal(p),"PASS")


if __name__ == "__main__":
    unittest.main()
