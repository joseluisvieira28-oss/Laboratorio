from __future__ import annotations

from unittest import TestCase

from radar.strategies.ema6h_50x200_regime_forward import (
    DAY_MS,FIFTEEN_MIN_MS,SIX_HOUR_MS,FIRST_ELIGIBLE_SIGNAL_CLOSE_MS,
    Candle,aggregate_15m_to_6h,detect_cross,ema_series,regime_bucket,regime_state,
    latest_certifiable_signal_close_ms
)

def candle(t,step,p,close=None):
    c=p if close is None else close
    return Candle(t,p,max(p,c)+1,min(p,c)-1,c,1.0,t+step-1)

class EMA6HRegimeMechanicsTests(TestCase):
    def test_exact_24x15m_aggregation(self):
        start=FIRST_ELIGIBLE_SIGNAL_CLOSE_MS-SIX_HOUR_MS
        rows=[candle(start+i*FIFTEEN_MIN_MS,FIFTEEN_MIN_MS,100+i*.01) for i in range(24)]
        bars,inc=aggregate_15m_to_6h(rows)
        self.assertEqual(inc,0);self.assertEqual(len(bars),1)
        self.assertEqual(bars[0].open_time,start)
        bars2,inc2=aggregate_15m_to_6h(rows[:-1])
        self.assertEqual(bars2,[]);self.assertEqual(inc2,1)

    def test_regime_three_state_classifier(self):
        start=DAY_MS*1000
        bull=[candle(start+i*DAY_MS,DAY_MS,100+i*.5,100+i*.5) for i in range(230)]
        sig=start+231*DAY_MS
        self.assertEqual(regime_state(bull,signal_close_ms=sig)["state"],"BULL_TREND")
        bear=[candle(start+i*DAY_MS,DAY_MS,300-i*.5,300-i*.5) for i in range(230)]
        self.assertEqual(regime_state(bear,signal_close_ms=sig)["state"],"BEAR_TREND")
        flat=[candle(start+i*DAY_MS,DAY_MS,100,100) for i in range(230)]
        self.assertEqual(regime_state(flat,signal_close_ms=sig)["state"],"TRANSITION_CHOP")
        self.assertEqual(regime_bucket("BULL_TREND",1),"TREND_ALIGNED")
        self.assertEqual(regime_bucket("BEAR_TREND",1),"COUNTER_REGIME")
        self.assertEqual(regime_bucket("TRANSITION_CHOP",-1),"TRANSITION_CHOP")

    def test_bull_cross_detected_without_parameter_search(self):
        start=FIRST_ELIGIBLE_SIGNAL_CLOSE_MS-202*SIX_HOUR_MS
        closes=[100.0]*200+[50.0,200.0]
        bars=[candle(start+i*SIX_HOUR_MS,SIX_HOUR_MS,c,c) for i,c in enumerate(closes)]
        signal_close=bars[-1].open_time+SIX_HOUR_MS
        sig=detect_cross("BTCUSDT",bars,signal_close_ms=signal_close)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction,1)

    def test_forward_boundary_requires_entry_15m_close(self):
        b=FIRST_ELIGIBLE_SIGNAL_CLOSE_MS
        self.assertIsNone(latest_certifiable_signal_close_ms(b+FIFTEEN_MIN_MS-1))
        self.assertEqual(latest_certifiable_signal_close_ms(b+FIFTEEN_MIN_MS),b)

if __name__=="__main__":
    import unittest;unittest.main()
