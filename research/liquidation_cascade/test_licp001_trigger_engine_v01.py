import json,tempfile,unittest
from research.liquidation_cascade.licp001_trigger_engine_v01 import (
    load_config,bybit_pressure,side_concentration,aggregate_burst
)

class TriggerEngineTests(unittest.TestCase):
    def test_unfrozen_config_refuses_to_load(self):
        with tempfile.NamedTemporaryFile("w+",suffix=".json") as f:
            json.dump({"status":"UNFROZEN"},f);f.flush()
            with self.assertRaisesRegex(PermissionError,"NOT_FROZEN"):
                load_config(f.name)

    def test_bybit_side_normalization(self):
        self.assertEqual(bybit_pressure("Buy"),"SELL")
        self.assertEqual(bybit_pressure("Sell"),"BUY")

    def test_side_concentration(self):
        self.assertAlmostEqual(side_concentration(90,10),.8)

    def test_burst_is_strictly_trailing(self):
        events=[
          {"source":"bybit","symbol":"BTCUSDT","venue_ts":1000,"pressure":"SELL","notional":10},
          {"source":"bybit","symbol":"BTCUSDT","venue_ts":2000,"pressure":"SELL","notional":20},
          {"source":"bybit","symbol":"BTCUSDT","venue_ts":3000,"pressure":"BUY","notional":5},
        ]
        b=aggregate_burst(events,"bybit","BTCUSDT",3000,2000)
        self.assertEqual(b.total_notional,25)
        self.assertEqual(b.pressure,"SELL")

if __name__=="__main__":unittest.main()
