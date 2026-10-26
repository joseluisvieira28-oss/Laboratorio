import unittest
from science_gate_v032 import evaluate

def fixture():
    entries = []
    for n in range(319):
        entries.append({"asset": "BTCUSDT" if n < 25 else "SOLUSDT",
                        "month": "2022-02", "timeframe": "1d",
                        "zip_sha256": "a"*64, "checksum_matches": True,
                        "status": "PASS"})
    for idx in range(8):
        entries[25+idx]["status"] = "FAIL_CLOSED"
        entries[25+idx]["error"] = "INCOMPLETE_MONTH"
    return {"archive_pairs": 319, "passed": 311, "failed": 8,
            "holdout_access": False, "manifest": entries}

class TestGate(unittest.TestCase):
    def test_source_fail(self):
        result = evaluate(fixture())
        self.assertEqual(result["status"], "SOURCE_INCOMPLETE_FAIL_CLOSED")
        self.assertEqual(result["historical_pnl"], "NOT_REPORTED")
        self.assertEqual(result["incomplete_archives"], 8)

    def test_clean_source_does_not_mean_profit(self):
        source = fixture()
        for entry in source["manifest"]:
            entry["status"] = "PASS"
        source["passed"] = 319
        source["failed"] = 0
        result = evaluate(source)
        self.assertIn("NOT_ECONOMIC_CERTIFICATION", result["status"])
        self.assertEqual(result["live_trading"], "NO_GO")

    def test_holdout(self):
        source = fixture()
        source["holdout_access"] = True
        with self.assertRaises(ValueError):
            evaluate(source)

    def test_bad_hash(self):
        source = fixture()
        source["manifest"][0]["zip_sha256"] = "bad"
        with self.assertRaises(ValueError):
            evaluate(source)

    def test_wrong_archive_count(self):
        source = fixture()
        source["manifest"].pop()
        with self.assertRaises(ValueError):
            evaluate(source)

    def test_mutated_count(self):
        source = fixture()
        source["passed"] = 319
        with self.assertRaises(ValueError):
            evaluate(source)

    def test_bad_checksum(self):
        source = fixture()
        source["manifest"][0]["checksum_matches"] = False
        with self.assertRaises(ValueError):
            evaluate(source)

    def test_future_date(self):
        source = fixture()
        source["manifest"][0]["month"] = "2026-10"
        with self.assertRaises(ValueError):
            evaluate(source)

if __name__ == '__main__':
    unittest.main()
