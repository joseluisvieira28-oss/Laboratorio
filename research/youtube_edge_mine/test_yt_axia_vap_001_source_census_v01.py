"""Synthetic outcome-blind mechanics for YT-AXIA-VAP-001 source feature."""
import unittest
from yt_axia_vap_001_source_census_v01 import (
    Blocked,bounded_ms,price_to_cents,price_bucket,local_peaks,qualifies_shape,load_freeze
)

def double_node():
    # 11 populated bins, peaks separated by 5 units, valley near zero.
    return {0:1,1:10,2:.5,3:.1,4:.2,5:.1,6:9,7:.5,8:1,9:2,10:1}

class SyntheticShape(unittest.TestCase):
    def test_price_cents_exact(self):
        self.assertEqual(price_to_cents("64000.01000000"),6400001)
    def test_finer_tick_rejected(self):
        with self.assertRaises(Blocked):price_to_cents("64000.00100000")
    def test_price_zero_rejected(self):
        with self.assertRaises(Blocked):price_to_cents("0.00000000")
    def test_1bp_grid_same_anchor(self):
        self.assertEqual(price_bucket(6000000,6000000),0)
    def test_grid_1bp_up(self):
        self.assertEqual(price_bucket(6000600,6000000),1)
    def test_grid_below_anchor_signed_floor(self):
        self.assertEqual(price_bucket(5999999,6000000),-1)
    def test_timestamp_2022_valid(self):
        self.assertEqual(bounded_ms("1641945600000"),1641945600000)
    def test_timestamp_2024_valid(self):
        self.assertEqual(bounded_ms("1723075200000"),1723075200000)
    def test_2025_microseconds_rejected(self):
        with self.assertRaises(Blocked):bounded_ms("1735689600010866")
    def test_two_peaks_finds(self):
        self.assertIn(1,local_peaks(double_node()))
        self.assertIn(6,local_peaks(double_node()))
    def test_two_peaks_pass(self):
        self.assertTrue(qualifies_shape(double_node(),100))
    def test_low_trade_count_blocks(self):
        self.assertFalse(qualifies_shape(double_node(),99))
    def test_narrow_width_blocks(self):
        self.assertFalse(qualifies_shape({0:3,1:2,2:3},200))
    def test_valley_high_blocks(self):
        z={i:4 for i in range(11)}
        z[1]=10;z[6]=9
        self.assertFalse(qualifies_shape(z,200))
    def test_peak_share_blocks(self):
        z=double_node()
        z[9]=250
        self.assertFalse(qualifies_shape(z,200))
    def test_adjacent_peaks_block(self):
        z={0:1,1:10,2:0.1,3:9,4:1,5:.2,6:.3,7:.4,8:.5}
        self.assertFalse(qualifies_shape(z,200,separation=4))
    def test_freeze_identity(self):
        f=load_freeze()
        self.assertEqual(f["lab_id"],"YT-AXIA-VAP-001")
        self.assertFalse(f["economic_outcomes_allowed"])
    def test_no_economic_result_fields(self):
        import inspect,yt_axia_vap_001_source_census_v01 as s
        source=inspect.getsource(s)
        self.assertNotIn("future_price",source)
        self.assertNotIn("calculate_pnl",source)
        self.assertNotIn("order_create",source)
if __name__=="__main__":unittest.main()
