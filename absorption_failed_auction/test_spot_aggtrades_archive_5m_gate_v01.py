"""Synthetic-only canonical Binance spot source parser semantics checks."""
import unittest
from datetime import datetime,timezone
from spot_aggtrades_archive_5m_gate_v01 import to_ms,spot_aggressor_sign,spot_5m_close,BAR_MS

T=int(datetime(2026,10,3,0,0,tzinfo=timezone.utc).timestamp()*1000)
class SpotAggTradesSourceTests(unittest.TestCase):
    def test_seconds_to_ms(self):self.assertEqual(to_ms(T//1000),T)
    def test_ms_retained(self):self.assertEqual(to_ms(T),T)
    def test_us_to_ms(self):self.assertEqual(to_ms(T*1000),T)
    def test_ns_to_ms(self):self.assertEqual(to_ms(T*1_000_000),T)
    def test_buyer_maker_false_aggressor_buy(self):self.assertEqual(spot_aggressor_sign("false"),1)
    def test_buyer_maker_true_aggressor_sell(self):self.assertEqual(spot_aggressor_sign("True"),-1)
    def test_invalid_side_fails(self):
        with self.assertRaises(ValueError):spot_aggressor_sign("unknown")
    def test_utc_interval_on_boundary(self):self.assertEqual(spot_5m_close(T),T+BAR_MS)
    def test_utc_interval_just_before_boundary(self):self.assertEqual(spot_5m_close(T-1),T)
    def test_exact_first_minute(self):self.assertEqual(spot_5m_close(T+60_000),T+BAR_MS)
if __name__=="__main__":unittest.main()
