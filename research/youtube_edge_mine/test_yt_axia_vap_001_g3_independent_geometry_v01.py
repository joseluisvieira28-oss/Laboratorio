"""Synthetic G3 source quality / phase / matched-strata tests. Zero market data."""
import unittest
from yt_axia_vap_001_g3_independent_geometry_v01 import (
    load_freeze,bin_price,by_grid,cell_key,evaluate_day
)

class Geometry(unittest.TestCase):
    def test_freeze_dates_disjoint(self):
        f=load_freeze()
        self.assertFalse(set(f["independent_source_days"])&set(f["preceding_discovery_days_excluded"]))
    def test_unshifted_matches_one_bp(self):
        self.assertEqual(bin_price(6000600,6000000,False),1)
    def test_shift_phase_half_bp(self):
        self.assertEqual(bin_price(6000450,6000000,False),0)
        self.assertEqual(bin_price(6000450,6000000,True),1)
    def test_negative_bin_floor(self):
        self.assertEqual(bin_price(5999900,6000000,False),-1)
    def test_reaggregation_conserves_volume(self):
        v={6000000:1,6000010:2,6000300:3,6000600:4}
        self.assertEqual(sum(by_grid(v,6000000,False).values()),10)
        self.assertEqual(sum(by_grid(v,6000000,True).values()),10)
    def test_poc_coarse_state(self):
        bins={-5:1,-1:15,2:2,9:1}
        key=cell_key(bins,5,10)
        self.assertEqual(key[1],"SELL")
        self.assertEqual(key[2],"NARROW")
    def test_source_classification_does_not_depend_on_future(self):
        b={"anchor":6000000,"price_vol":{6000000:1,6000600:10,6001200:.5,6001800:.1,
            6002400:.2,6003000:.1,6003600:9,6004200:.5,6004800:1,6005400:2,6006000:1},
           "n":120,"buy":30,"sell":3}
        z=evaluate_day("2022-06-16",{1655337600000:b},20261009)
        self.assertEqual(z["primary_signal_bars"],1)
        self.assertEqual(z["eligible_control_bars"],0)
        self.assertEqual(z["placebo_shuffled_total"],8)
    def test_empty_market_bar_not_trade(self):
        z=evaluate_day("2023-12-15",{1702598400000:{
            "anchor":6000000,"price_vol":{6000000:1},"n":1,"buy":1,"sell":0}},20261009)
        self.assertEqual(z["insufficient_profile_bars"],1)
        self.assertEqual(z["primary_signal_bars"],0)
    def test_shuffled_deterministic(self):
        x={i*600:float(i%7+1) for i in range(30)}
        bar={"anchor":6000000,"price_vol":{6000000+k:v for k,v in x.items()},
            "n":350,"buy":3,"sell":7}
        a=evaluate_day("2024-04-19",{1713484800000:bar},23)
        b=evaluate_day("2024-04-19",{1713484800000:bar},23)
        self.assertEqual(a,b)
    def test_missing_price_bin_one_valid_range(self):
        p={6000000:1,6006000:1,6012000:1}
        self.assertEqual(sum(by_grid(p,6000000).values()),3)
if __name__=="__main__":unittest.main()
