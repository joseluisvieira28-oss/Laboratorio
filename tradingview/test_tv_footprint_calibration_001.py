import importlib.util
import unittest

spec = importlib.util.spec_from_file_location(
    "cal", "tradingview/tv_footprint_calibration_001.py"
)
cal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cal)


class FootprintCalibrationTests(unittest.TestCase):
    def test_strong_gate(self):
        tv = []
        agg = []
        for i in range(cal.MIN_MATCHED_BARS):
            t = cal.FORWARD_START_MS + i * cal.BAR_MS
            d = float((i % 17) - 8)
            base = 100.0 + (i % 5)
            agg.append({
                "bar_open_ms": t,
                "bar_close_ms": t + cal.BAR_MS,
                "agg_base_volume": base,
                "agg_buy_volume": 0.0,
                "agg_sell_volume": 0.0,
                "agg_trade_count": 1,
                "agg_delta": d,
                "agg_delta_pct": d / base,
            })
            tv.append({
                "bar_open_ms": t,
                "bar_close_ms": t + cal.BAR_MS,
                "tv_total_volume": base * 1.001,
                "tv_buy_volume": 0.0,
                "tv_sell_volume": 0.0,
                "tv_delta": d * 0.95,
                "tv_delta_pct": d / base,
                "ltf_path_efficiency": 0.5,
                "ltf_signed_volume_pct": 0.0,
                "volume_z": 0.0,
                "bar_return_bps": 0.0,
            })
        result = cal.calibrate(tv, agg)
        self.assertEqual(result["classification"], "PASS_STRONG")
        self.assertGreater(result["delta_spearman"], 0.99)

    def test_insufficient_sample(self):
        t = cal.FORWARD_START_MS
        tv = [{"bar_open_ms": t, "tv_total_volume": 100.0, "tv_delta": 1.0}]
        agg = [{"bar_open_ms": t, "agg_base_volume": 100.0, "agg_delta": 1.0}]
        result = cal.calibrate(tv, agg)
        self.assertEqual(result["classification"], "INSUFFICIENT_SAMPLE")

    def test_epoch_parse(self):
        self.assertEqual(cal._to_ms("1758702000000"), 1758702000000)
        self.assertEqual(cal._to_ms("1758702000"), 1758702000000)


if __name__ == "__main__":
    unittest.main()
