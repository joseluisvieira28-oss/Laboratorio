from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from radar.evidence import EvidenceStore
from radar.ema6h_regime_metrics import evaluate_ema6h_regime_forward

class EMA6HRegimeMetricsTests(TestCase):
    def test_metrics_never_auto_promote(self):
        with tempfile.TemporaryDirectory() as td:
            s=EvidenceStore(str(Path(td)/"e.sqlite3"))
            for i in range(10):
                key=f"k{i}"
                trade={"symbol":"BTCUSDT","direction":1,"signal_close_ms":i,"entry_open_ms":i,"entry":100.0,"exit_open_ms":i+1,
                       "regime_state":"BULL_TREND","regime_bucket":"TREND_ALIGNED"}
                s.append_once("EMA6H_REGIME_FORWARD_SIGNAL",key,{"event_key":key,"paper_trade":trade})
                s.append_once("EMA6H_REGIME_FORWARD_RESOLUTION",key,{"event_key":key,"paper_trade":trade,"outcome":{"base_net_bps":10.0,"stress_net_bps":6.0}})
            m=evaluate_ema6h_regime_forward(s)
            self.assertEqual(m["classification"],"REGIME_MECHANISM_REVIEW_ELIGIBLE")
            self.assertFalse(m["automatic_promotion"])
            self.assertFalse(m["live_trading_authorized"])
            self.assertEqual(m["by_regime_bucket"]["TREND_ALIGNED"]["n"],10)

if __name__=="__main__":
    import unittest;unittest.main()
