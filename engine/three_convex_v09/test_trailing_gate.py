import unittest
from engine.three_convex_v09.trailing_gate import calc_v5_trail,TrailHalt

def g(close=100,peak=100,previous=96,confirmed=True):
    return calc_v5_trail(actual_fill=100,completed_tf_close=close,
                         peak_5m_high_so_far=peak,previous_broker_stop=previous,
                         price_tick=".01",closed_tf_confirmed=confirmed)

class TrailTests(unittest.TestCase):
    def test_no_trigger_keeps_initial(self):
        z=g()
        self.assertEqual(z["action"],"KEEP")
        self.assertFalse(z["activation_on_completed_tf_close"])
        self.assertFalse(z["real_broker_amend_allowed"])
    def test_at_exact_five_pct_high_below_trailing_threshold_keeps_initial(self):
        self.assertEqual(g(close=105,peak=105)["action"],"KEEP")
    def test_high_peak_and_close_above_activation_tightens(self):
        z=g(close=110,peak=114)
        self.assertEqual(z["action"],"TIGHTEN")
        self.assertEqual(z["proposed_broker_stop_tick_floor"],"100.32")
    def test_deactivation_explicitly_weakens_original(self):
        z=g(close=104,peak=114,previous="100.32")
        self.assertEqual(z["action"],"WEAKEN")
        self.assertTrue(z["protective_weaken_requested"])
        self.assertFalse(z["live_go"])
    def test_reactivation_after_weakening_tightens(self):
        self.assertEqual(g(close=107,peak=114,previous=96)["action"],"TIGHTEN")
    def test_incomplete_bar_rejected(self):
        with self.assertRaisesRegex(TrailHalt,"INCOMPLETE"):
            g(confirmed=False)
    def test_previous_stop_must_be_readback_positive(self):
        with self.assertRaisesRegex(TrailHalt,"INVALID_PRICE_GEOMETRY"):
            g(previous=0)
    def test_peak_less_than_close_rejected(self):
        with self.assertRaisesRegex(TrailHalt,"INVALID_PRICE_GEOMETRY"):
            g(close=110,peak=105)
    def test_nonfinite_market_rejected(self):
        with self.assertRaisesRegex(TrailHalt,"BAD_PEAK"):
            g(peak="NaN")
    def test_tick_floor_is_not_round_nearest(self):
        z=calc_v5_trail(actual_fill=101.03,completed_tf_close=107,
            peak_5m_high_so_far=113.03,previous_broker_stop=96.98,
            price_tick=".10",closed_tf_confirmed=True)
        self.assertEqual(z["proposed_broker_stop_tick_floor"],"99.4")
if __name__=="__main__": unittest.main()
