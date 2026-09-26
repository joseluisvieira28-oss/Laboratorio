import unittest
from research.liquidation_cascade.freeze_licp001_trigger_v01 import extract,freeze

GOOD_HASH="0"*64

def receipt(decision="CALIBRATION_SAMPLE",eligible=True):
    def d(p75=10,p95=20):
        return {"notional":{"p75":p75,"p95":p95},"side_concentration":{"p75":.8}}
    r={"decision":decision,"bursts":{
      "bybit":{"BTCUSDT":{"bursts":{"5000":d(100,200)}},
               "ETHUSDT":{"bursts":{"5000":d(30,40)}},
               "SOLUSDT":{"bursts":{"5000":d(50,60)}}},
      "binance":{"BTCUSDT":{"bursts":{"5000":d(70,80)}}}
    }}
    if eligible:
        r["eligibility"]={
          "span_days":7.0,
          "bybit_events":250,
          "bybit_btc_events":50,
          "uptime_pct":95.0,
          "clock_regressions":0,
          "raw_event_log_sha256":GOOD_HASH,
        }
    return r

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

    def test_short_sample_without_eligibility_refuses(self):
        with self.assertRaisesRegex(ValueError,"ELIGIBILITY_NOT_PROVEN"):
            extract(receipt(eligible=False))

    def test_under_seven_days_refuses(self):
        r=receipt();r["eligibility"]["span_days"]=6.99
        with self.assertRaisesRegex(ValueError,"span_days"):
            extract(r)

    def test_event_count_floor_refuses(self):
        r=receipt();r["eligibility"]["bybit_events"]=249
        with self.assertRaisesRegex(ValueError,"bybit_events"):
            extract(r)

    def test_btc_event_floor_refuses(self):
        r=receipt();r["eligibility"]["bybit_btc_events"]=49
        with self.assertRaisesRegex(ValueError,"bybit_btc_events"):
            extract(r)

    def test_uptime_floor_refuses(self):
        r=receipt();r["eligibility"]["uptime_pct"]=94.99
        with self.assertRaisesRegex(ValueError,"uptime_pct"):
            extract(r)

    def test_clock_regression_refuses(self):
        r=receipt();r["eligibility"]["clock_regressions"]=1
        with self.assertRaisesRegex(ValueError,"clock_regressions"):
            extract(r)

    def test_exact_quantile_mapping(self):
        c=freeze(cfg(),receipt(),"x.json")
        self.assertEqual(c["btc_ignition"]["notional_threshold"],200)
        self.assertEqual(c["btc_ignition"]["side_concentration_threshold"],.8)
        self.assertEqual(c["binance_confirmation"]["notional_threshold"],70)
        self.assertEqual(c["alt_propagation"]["notional_thresholds"]["ETHUSDT"],40)
        self.assertEqual(c["alt_propagation"]["notional_thresholds"]["SOLUSDT"],60)
        self.assertEqual(c["status"],"FROZEN")
        self.assertEqual(c["calibration_eligibility"]["span_days"],7.0)

if __name__=="__main__":unittest.main()
