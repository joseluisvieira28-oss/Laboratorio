import importlib.util
import unittest

spec = importlib.util.spec_from_file_location(
    "m", "absorption_failed_auction/engine.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(i, delta=0.10, vol=100.0, eff=0.50, ret=5.0, pocmig=1.0):
    close = 1790247600000 + (i + 1) * 300000
    return {
        "bar_open_ms": close - 300000,
        "bar_close_ms": close,
        "agg_delta_pct": delta,
        "agg_base_volume": vol,
        "ltf_path_efficiency": eff,
        "bar_return_bps": ret,
        "poc_migration_bps": pocmig,
        "poc_mid": 100.0,
        "vah": 101.0,
        "val": 99.0,
        "buy_imbalance_rows": 1,
        "sell_imbalance_rows": 1,
        "footprint_rows": 10,
        "ltf_intrabars": 5,
    }


class T(unittest.TestCase):
    def test_sensor_block(self):
        self.assertEqual(
            m.adjudicate([], "PASS_LIMITED")["classification"],
            "SENSOR_BLOCKED",
        )

    def test_source_block(self):
        self.assertEqual(
            m.adjudicate([], "PASS_STRONG", transport_coverage=0.98)["classification"],
            "SOURCE_BLOCKED",
        )

    def test_classifier_after_parent_open(self):
        rows = [row(i) for i in range(m.BASELINE + 1)]
        rows[-1] = row(
            m.BASELINE,
            delta=0.90,
            vol=1000.0,
            eff=0.01,
            ret=-1.0,
            pocmig=-1.0,
        )
        parent_pass = rows[m.BASELINE - 1]["bar_close_ms"]
        out = m.classify(rows, parent_pass)
        self.assertEqual(out[-1]["event_class"], "FAILED_AUCTION")

    def test_pre_open_bar_cannot_be_event(self):
        rows = [row(i) for i in range(m.BASELINE + 1)]
        rows[-1] = row(
            m.BASELINE,
            delta=0.90,
            vol=1000.0,
            eff=0.01,
            ret=-1.0,
            pocmig=-1.0,
        )
        out = m.classify(rows, rows[-1]["bar_close_ms"])
        self.assertEqual(out[-1]["event_class"], "PRE_OPEN_BASELINE_ONLY")

    def test_outcome_leak_rejected(self):
        rows = [row(i) for i in range(m.BASELINE + 1)]
        rows[-1]["R60"] = -10.0
        with self.assertRaises(m.LabError):
            m.classify(rows, rows[m.BASELINE - 1]["bar_close_ms"])

    def test_structure_invariant(self):
        r = row(0)
        r["poc_mid"] = 200
        with self.assertRaises(m.LabError):
            m.validate_structure(r)

    def test_insufficient(self):
        rows = [{
            "event_class": "FAILED_AUCTION",
            "utc_date": "2026-01-01",
            "R60": -1.0,
        }]
        self.assertEqual(
            m.adjudicate(rows, "PASS_STRONG")["classification"],
            "INSUFFICIENT_SAMPLE",
        )

    def test_wilson(self):
        self.assertGreater(m.wilson_lower(80, 100), 0.7)


if __name__ == "__main__":
    unittest.main()
