from __future__ import annotations
import unittest
from datetime import date,datetime,timezone
from unittest.mock import patch
from scripts.mexc_options_v21_signal_bridge_v03 import build_execution_signal,radar_healthy,OptionsExecutionBridgeError

class DummyOptions:
    def trades(self,**kwargs): return [object()]
class DummyBTC:
    def daily(self,**kwargs): return [object()]

class BridgeTests(unittest.TestCase):
    def _radar(self):
        return {"build_id":"v0.14.4-win-cirv-eight-motor","registry_version":"3.7","registry":{"focus_loaded":8,"focus_expected":8}}
    def test_radar_8_of_8_required(self):
        self.assertTrue(radar_healthy(self._radar()))
        bad=self._radar(); bad["registry"]["focus_loaded"]=7
        self.assertFalse(radar_healthy(bad))
    @patch("scripts.mexc_options_v21_signal_bridge_v03.latest_complete_signal_day",return_value=date(2026,9,24))
    @patch("scripts.mexc_options_v21_signal_bridge_v03.build_daily_skew",return_value={"valid":True,"position":-1,"skew":-2.5})
    @patch("scripts.mexc_options_v21_signal_bridge_v03.rv20_and_weight",return_value={"rv20":0.02,"expanding_median_rv20":0.015,"weight":0.75})
    @patch("scripts.mexc_options_v21_signal_bridge_v03.exact_daily_open_if_available",return_value=85000.0)
    def test_short_signal_materializes_inside_30s(self,*_):
        out=build_execution_signal(now=datetime(2026,9,25,0,0,10,tzinfo=timezone.utc),options_feed=DummyOptions(),btc_feed=DummyBTC(),radar_state=self._radar())
        self.assertEqual(out["signal_direction"],"SHORT")
        self.assertEqual(out["entry_target_utc"],"2026-09-25T00:00:00Z")
        self.assertEqual(out["exit_target_utc"],"2026-09-26T00:00:00Z")
        self.assertEqual(out["materialization_latency_seconds"],10.0)
        self.assertFalse(out["scientific_promotion_credit_from_execution_translation"])
    @patch("scripts.mexc_options_v21_signal_bridge_v03.latest_complete_signal_day",return_value=date(2026,9,24))
    def test_after_30s_is_no_chase(self,*_):
        with self.assertRaises(OptionsExecutionBridgeError):
            build_execution_signal(now=datetime(2026,9,25,0,0,31,tzinfo=timezone.utc),options_feed=DummyOptions(),btc_feed=DummyBTC(),radar_state=self._radar())

if __name__=="__main__": unittest.main()
