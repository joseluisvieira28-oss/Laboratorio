import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod
t=load("trail_exit", "exit_logic.py")
g=load("convex_mexc_source", "source_probe.py")

class IntakeTests(unittest.TestCase):
    def test_three_frozen_mexc_assets_only(self):
        self.assertEqual(g.SYMBOLS,("ETH_USDT","SOL_USDT","BNB_USDT"))
        self.assertNotIn("BTC_USDT",g.SYMBOLS)
    def test_gateway_original_synthetic_suite(self):
        g.selftest()
    def test_initial_stop_and_nonlatched(self):
        p=t.at_entry(100)
        self.assertAlmostEqual(p.active_stop,96)
        x=t.after_closed_hour(p,candle_open=100,candle_high=120,candle_low=98,candle_close=110)
        self.assertEqual(x["action"],"HOLD")
        self.assertAlmostEqual(x["next_state"].active_stop,105.6)
        p=x["next_state"]
        # 105.6 old stop executes despite close below activation threshold.
        x=t.after_closed_hour(p,candle_open=110,candle_high=111,candle_low=104,candle_close=104)
        self.assertEqual(x["action"],"STOP_EXIT")
        self.assertAlmostEqual(x["exit_raw"],105.6)
    def test_deactivation_without_intrabar_stop(self):
        p=t.at_entry(100)
        x=t.after_closed_hour(p,candle_open=100,candle_high=120,candle_low=98,candle_close=104)
        self.assertAlmostEqual(x["next_state"].active_stop,96)
        self.assertAlmostEqual(x["next_state"].observed_peak,120)
        x=t.after_closed_hour(x["next_state"],candle_open=104,candle_high=110,candle_low=102,candle_close=106)
        self.assertAlmostEqual(x["next_state"].active_stop,105.6)
    def test_newly_generated_stop_applies_next_candle(self):
        p=t.at_entry(100)
        x=t.after_closed_hour(p,candle_open=100,candle_high=140,candle_low=97,candle_close=120)
        self.assertEqual(x["action"],"HOLD")
        self.assertAlmostEqual(x["next_state"].active_stop,123.2)
    def test_gap_below_stop(self):
        x=t.after_closed_hour(t.at_entry(100),candle_open=90,candle_high=110,candle_low=89,candle_close=100)
        self.assertEqual((x["action"],x["exit_raw"]),("STOP_GAP_EXIT",90))
    def test_invalid_ohlc_fails(self):
        with self.assertRaises(ValueError):
            t.after_closed_hour(t.at_entry(100),candle_open=100,candle_high=90,candle_low=99,candle_close=100)
    def test_no_order_authority(self):
        self.assertFalse(t.no_order_authority())

if __name__=="__main__":unittest.main()
