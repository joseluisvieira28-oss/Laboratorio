import unittest
from research.microstructure_scalping.cost_model_v01 import round_trip_fee_bps,taker_net_bps


class CostModelTests(unittest.TestCase):
    def test_mexc_api_taker_round_trip(self):
        self.assertEqual(round_trip_fee_bps("MEXC_API","taker","taker"),16.0)

    def test_bybit_reference_taker_round_trip(self):
        self.assertEqual(round_trip_fee_bps("BYBIT_VIP0_REF","taker","taker"),11.0)

    def test_net(self):
        self.assertEqual(taker_net_bps(20.0,"MEXC_API",2.0),2.0)


if __name__=="__main__":
    unittest.main()
