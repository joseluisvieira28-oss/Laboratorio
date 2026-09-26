import unittest
from research.liquidation_cascade.freeze_licp001_trigger_v01 import extract,freeze

def receipt(decision="CALIBRATION_SAMPLE"):
    def d(p75=10,p95=20):
        return {"notional":{"p75":p75,"p95":p95},"side_concentration":{"p75":.8}}
    return {"decision":decision,"bursts":{
      "bybit":{"BTCUSDT":{"bursts":{"5000":d(100,200)}},
               "ETHUSDT":{"bursts":{"5000":d(30,40)}},
               "SOLUSDT":{"bursts":{"5000":d(50,60)}}},
      "binance":{"BTCUSDT":{"bursts":{"5000":d(70,80)}}}
    }}

def cfg():
    return {"status":"UNFROZEN","source_calibration_receipt":None,
      "btc_ignition":{"notional_threshold":None,"side_concentration_threshold":None},
      "binance_confirmation":{"notional_threshold":None},
      "oi_confirmation":{"enabled":False},
      "alt_propagation":{"notional_thresholds":{"ETHUSDT":None,"SOLUSDT":None}}}

class FreezeTests(unittest.TestCase):
    def test_sparse_refuses(self):
        with self.assertRaisesRegex(ValueError,"NOT_SUFFICIENT"):
            extract(receipt("CALIBRATION_SPARSE"))

    def test_exact_quantile_mapping(self):
        c=freeze(cfg(),receipt(),"x.json")
        self.assertEqual(c["btc_ignition"]["notional_threshold"],200)
        self.assertEqual(c["btc_ignition"]["side_concentration_threshold"],.8)
        self.assertEqual(c["binance_confirmation"]["notional_threshold"],70)
        self.assertEqual(c["alt_propagation"]["notional_thresholds"]["ETHUSDT"],40)
        self.assertEqual(c["alt_propagation"]["notional_thresholds"]["SOLUSDT"],60)
        self.assertEqual(c["status"],"FROZEN")

if __name__=="__main__":unittest.main()
