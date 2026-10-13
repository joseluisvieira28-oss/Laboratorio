"""All synthetic fixed two-sided quote depth correctness checks."""
import unittest
from decimal import Decimal
from research.convex_sol_bnb_gates_v01 import two_sided_book_12 as d

class BothSideDepth(unittest.TestCase):
    def test_two_sided_100_possible_2000_not_and_fee_hurdle(self):
        spec={"symbol":"SOL_USDT","contractSize":Decimal(".1"),
              "minVol":Decimal("1"),"volUnit":Decimal("1"),
              "maxVol":Decimal("10000"),"priceUnit":Decimal(".01")}
        raw={"timestamp":1791910884000,"version":100,"asks":[[107.25,10000,15],[107.26,10000,20]],
             "bids":[[107.24,10000,11],[107.23,10000,40]]}
        source={"local_received_ms":1791910884100,"request_latency_ms":90,
                "sha256_raw_response":"a"*64}
        x=d.detail_snapshot(spec,raw,source)
        self.assertTrue(x["probes"][0]["two_sided_book_depth_sufficient"])
        self.assertFalse(x["probes"][1]["two_sided_book_depth_sufficient"])
        self.assertGreater(x["hurdle_base_bps_approx"],20)
        self.assertGreater(x["hurdle_stress_bps_approx"],x["hurdle_base_bps_approx"])
        with self.assertRaisesRegex(ValueError,"NOT_A_NEW_PUBLIC_BOOK_VERSION"):
            d.detail_snapshot(spec,raw,source,previous=100)

    def test_vwap_uses_contract_quantity_third_element_not_order_count(self):
        levels=[{"price":Decimal("100"),"number_of_orders":Decimal("100000"),
                 "contracts":Decimal("2")}]
        self.assertIsNone(d.vwap(levels,Decimal("5"),Decimal(".1")))
        self.assertEqual(d.vwap(levels,Decimal("2"),Decimal(".1")),Decimal("100"))

if __name__=="__main__":unittest.main()
