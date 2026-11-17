import datetime as dt
import unittest
import study as s
class TestFundingTiming(unittest.TestCase):
    def test_utc_week_anchor(self):
        self.assertTrue(s.dtstr(s.ANCHOR).startswith("2024-09-02T02:00:00"))
        self.assertEqual(s.timeweek(s.ANCHOR),s.ANCHOR)
        self.assertEqual(s.timeweek(s.ANCHOR-3600000),s.ANCHOR-s.WEEK)
    def test_roundtrip_taker_and_slippage(self):
        self.assertAlmostEqual(s.COST(0),0.0019)
        self.assertAlmostEqual(s.COST(.0002),0.0027)
        self.assertAlmostEqual(2*(s.B_MAKER+s.H_MAKER),.0007)
    def test_prediction_no_current_week_access(self):
        prior=[{"spread_b_minus_h":-.0012}]
        future={"spread_b_minus_h":+.005}
        self.assertEqual(s.choose("prev_week_sign",prior,future,.0027),-1)
        self.assertEqual(s.choose("prev_week_fee_gate",prior,future,.0027),0)
        self.assertEqual(s.choose("shortBN_longHL_fixed",prior,future,.0027),1)
    def test_standalone_shock_already_in_percent(self):
        row={"direction":1,"funding_net":-.0027,"funding_gross":0.0000,
            "fee_and_slippage":.0027,"basis_price_proxy":0.0001,
            "worst_leg_adverse_pct":-25.0}
        self.assertEqual(s.eval_trades([row])["worst_standalone_leg_intraweek_pct"],-25.0)
    def test_sign_zeros(self):
        self.assertEqual(s.sign(0),0)
        self.assertEqual(s.sign(-.00001),-1)
        self.assertEqual(s.sign(.00001),1)
if __name__=="__main__":unittest.main()
