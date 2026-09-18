import unittest

from radar.dh03_12h_core import (
    ATR_LEN,
    LOOKBACK,
    MAX_HOLD_MS,
    MINUTE_MS,
    TWELVE_H_MS,
    Bar,
    SignalCandidate,
    aggregate_12h,
    atr_series,
    bind_exact_entry,
    latest_signal_candidate,
    resolve_minute_path,
)


class DH0312HCoreTests(unittest.TestCase):
    def test_15m_to_12h_requires_exact_48_bar_bucket(self):
        rows=[]
        for i in range(48):
            t=i*15*60*1000
            px=100+i*0.01
            rows.append(Bar(t,px,px+1,px-1,px+0.2,1.0))
        bars,incomplete=aggregate_12h(rows)
        self.assertEqual(incomplete,0)
        self.assertEqual(len(bars),1)
        self.assertEqual(bars[0].open_time,0)
        self.assertEqual(bars[0].open,rows[0].open)
        self.assertEqual(bars[0].close,rows[-1].close)

    def test_wilder_atr_seed_matches_phase5_definition(self):
        bars=[]
        close=100.0
        for i in range(ATR_LEN+3):
            op=close
            hi=op+2
            lo=op-1
            close=op+0.5
            bars.append(Bar(i*TWELVE_H_MS,op,hi,lo,close,1))
        atr=atr_series(bars,ATR_LEN)
        self.assertIsNone(atr[ATR_LEN-1])
        self.assertIsNotNone(atr[ATR_LEN])
        # Every true range is 3 in this synthetic series.
        self.assertAlmostEqual(atr[ATR_LEN],3.0,12)
        self.assertAlmostEqual(atr[ATR_LEN+1],3.0,12)

    def test_breakout_is_strict_close_above_prior_40_high(self):
        bars=[]
        for i in range(LOOKBACK+1):
            high=100.0
            close=99.0
            bars.append(Bar(i*TWELVE_H_MS,98,high,97,close,1))
        # Exact equality is not a breakout.
        equal=list(bars)
        equal[-1]=Bar(equal[-1].open_time,98,101,97,100.0,1)
        self.assertIsNone(latest_signal_candidate("BTCUSDT",equal))
        # Strictly above prior high is.
        above=list(bars)
        above[-1]=Bar(above[-1].open_time,98,101,97,100.01,1)
        c=latest_signal_candidate("BTCUSDT",above)
        self.assertIsNotNone(c)
        self.assertAlmostEqual(c.prior_high,100.0)

    def test_bind_entry_uses_signal_low_minus_quarter_atr_and_3r(self):
        c=SignalCandidate("BTCUSDT",10*TWELVE_H_MS,11*TWELVE_H_MS,90.0,8.0,100.0)
        s=bind_exact_entry(c,11*TWELVE_H_MS,100.0)
        self.assertAlmostEqual(s.stop,88.0)
        self.assertAlmostEqual(s.initial_risk_fraction,0.12)
        self.assertAlmostEqual(s.target,136.0)

    def test_same_minute_stop_and_target_ambiguity_is_stop_first(self):
        c=SignalCandidate("BTCUSDT",10*TWELVE_H_MS,11*TWELVE_H_MS,90.0,8.0,100.0)
        s=bind_exact_entry(c,11*TWELVE_H_MS,100.0)
        t=s.entry_open_time
        out=resolve_minute_path(
            s,
            [(t,100.0,140.0,80.0,110.0)],
            [],
        )
        self.assertTrue(out.resolved)
        self.assertEqual(out.exit_reason,"STOP_WINS_SAME_MINUTE_AMBIGUITY")
        self.assertEqual(out.exit_price,s.stop)

    def test_target_gap_is_capped_at_target(self):
        c=SignalCandidate("BTCUSDT",10*TWELVE_H_MS,11*TWELVE_H_MS,90.0,8.0,100.0)
        s=bind_exact_entry(c,11*TWELVE_H_MS,100.0)
        t=s.entry_open_time
        # First minute establishes exact entry; second gaps above target.
        out=resolve_minute_path(
            s,
            [
                (t,100.0,101.0,99.0,100.5),
                (t+MINUTE_MS,150.0,151.0,149.0,150.0),
            ],
            [],
        )
        self.assertTrue(out.resolved)
        self.assertEqual(out.exit_reason,"TARGET_GAP_CAPPED_AT_TARGET")
        self.assertEqual(out.exit_price,s.target)

    def test_gap_in_minute_path_fails_closed(self):
        c=SignalCandidate("BTCUSDT",10*TWELVE_H_MS,11*TWELVE_H_MS,90.0,8.0,100.0)
        s=bind_exact_entry(c,11*TWELVE_H_MS,100.0)
        t=s.entry_open_time
        out=resolve_minute_path(
            s,
            [
                (t,100.0,101.0,99.0,100.5),
                (t+2*MINUTE_MS,100.5,101.0,100.0,100.2),
            ],
            [],
        )
        self.assertFalse(out.resolved)
        self.assertEqual(out.exit_reason,"EXECUTION_PATH_UNRESOLVED_GAP")

    def test_time_exit_is_exact_deadline_minute_open(self):
        c=SignalCandidate("BTCUSDT",10*TWELVE_H_MS,11*TWELVE_H_MS,90.0,8.0,100.0)
        s=bind_exact_entry(c,11*TWELVE_H_MS,100.0)
        t=s.entry_open_time
        # Feed only entry and exact deadline: gap would fail before deadline, so build all minutes.
        mins=[]
        x=t
        while x<=t+MAX_HOLD_MS:
            mins.append((x,100.0,101.0,99.0,100.0))
            x+=MINUTE_MS
        out=resolve_minute_path(s,mins,[])
        self.assertTrue(out.resolved)
        self.assertEqual(out.exit_reason,"TIME_EXIT_EXACT_MINUTE_OPEN")
        self.assertEqual(out.exit_time,t+MAX_HOLD_MS)

    def test_funding_and_cost_formula_match_phase4(self):
        c=SignalCandidate("BTCUSDT",10*TWELVE_H_MS,11*TWELVE_H_MS,90.0,8.0,100.0)
        s=bind_exact_entry(c,11*TWELVE_H_MS,100.0)
        t=s.entry_open_time
        out=resolve_minute_path(
            s,
            [(t,100,101,99,100),(t+MINUTE_MS,100,136,99,135)],
            [(t,0.01),(t+30_000,0.001),(t+MINUTE_MS,0.002)],
        )
        self.assertTrue(out.resolved)
        # Funding at entry and exit timestamps are excluded; only the middle one counts.
        self.assertAlmostEqual(out.funding_return,-0.001,12)
        gross=(s.target-s.entry)/s.entry
        expected=(gross-0.001-0.002)/(s.initial_risk_fraction+0.002)
        self.assertAlmostEqual(out.base_net_r,expected,12)


if __name__=="__main__":
    unittest.main()
