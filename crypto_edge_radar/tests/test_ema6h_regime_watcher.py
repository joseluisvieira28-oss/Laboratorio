from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from radar.evidence import EvidenceStore
from radar.ema6h_regime_watcher import EMA6HRegimeForwardWatcher
from radar.strategies.ema6h_50x200_regime_forward import (
    FIFTEEN_MIN_MS,SIX_HOUR_MS,FIRST_ELIGIBLE_SIGNAL_CLOSE_MS,
    Candle,CrossSignal,ForwardTrade
)

class FakeFeed:
    provider="BINANCE_SPOT_PUBLIC"
    def klines(self,*args,**kwargs):
        interval=args[1]
        if interval=="1d":
            return []
        start=kwargs["start_ms"];end=kwargs["end_ms"]
        out=[];t=start-(start%FIFTEEN_MIN_MS)
        while t<end:
            out.append(Candle(t,100,101,99,100,1,t+FIFTEEN_MIN_MS-1));t+=FIFTEEN_MIN_MS
        return out

class EMA6HRegimeWatcherTests(TestCase):
    def test_replay_safe_signal_and_boundary(self):
        b=FIRST_ELIGIBLE_SIGNAL_CLOSE_MS
        sig=CrossSignal("BTCUSDT",1,b-SIX_HOUR_MS,b,101,100,99,100)
        trade=ForwardTrade("BTCUSDT",1,b,b,100,b+6*SIX_HOUR_MS,"BULL_TREND","TREND_ALIGNED")
        with tempfile.TemporaryDirectory() as td:
            store=EvidenceStore(str(Path(td)/"e.sqlite3"))
            w=EMA6HRegimeForwardWatcher(store=store,feed=FakeFeed())
            with (
                patch("radar.ema6h_regime_watcher.latest_certifiable_signal_close_ms",return_value=b),
                patch("radar.ema6h_regime_watcher.regime_state",return_value={"state":"BULL_TREND"}),
                patch("radar.ema6h_regime_watcher.aggregate_15m_to_6h",return_value=([],0)),
                patch("radar.ema6h_regime_watcher.detect_cross",side_effect=lambda symbol,bars,signal_close_ms: sig if symbol=="BTCUSDT" else None),
                patch("radar.ema6h_regime_watcher.materialize_trade",return_value=trade),
            ):
                first=w.run_once(now_ms=b+FIFTEEN_MIN_MS)
                second=w.run_once(now_ms=b+FIFTEEN_MIN_MS)
            self.assertEqual(first["inserted_signals"],1)
            self.assertEqual(first["new_boundaries"],1)
            self.assertEqual(second["inserted_signals"],0)
            self.assertEqual(second["new_boundaries"],0)
            self.assertEqual(len(store.read_payloads("EMA6H_REGIME_FORWARD_SIGNAL")),1)
            self.assertEqual(len(store.read_payloads("EMA6H_REGIME_FORWARD_BOUNDARY")),1)
            ok,detail=store.verify_chain();self.assertTrue(ok,detail)

if __name__=="__main__":
    import unittest;unittest.main()
