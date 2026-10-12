"""Synthetic unit tests only; no historical price outcomes or fills."""
import unittest
from first_touch import classify


class PathTests(unittest.TestCase):
    def setUp(self):
        self.case = dict(entry_ts=0, end_ts=3600000, step_seconds=3600,
                         entry_price=100, stop_price=95, target_price=120,
                         bars=[dict(ts=0, open=100, high=105, low=98, close=102)])

    def test_no_touch(self):
        self.assertEqual(classify(self.case), "NEITHER_TOUCHED")

    def test_target_first(self):
        self.case["bars"][0]["high"] = 121
        self.assertEqual(classify(self.case), "TARGET_FIRST_NO_FILL_GUARANTEE")

    def test_stop_first(self):
        self.case["bars"][0]["low"] = 94
        self.assertEqual(classify(self.case), "STOP_FIRST_NO_FILL_GUARANTEE")

    def test_same_bar_ambiguous(self):
        self.case["bars"][0].update(high=121, low=94)
        self.assertEqual(classify(self.case), "AMBIGUOUS_SAME_BAR")

    def test_gap_through_stop(self):
        self.case["bars"][0].update(open=93, high=99, low=90, close=96)
        self.assertEqual(classify(self.case), "STOP_GAP_FIRST_NO_FILL_GUARANTEE")

    def test_missing_interval(self):
        self.case["end_ts"] = 7200000
        self.assertEqual(classify(self.case), "MISSING_OR_PARTIAL_PATH")

    def test_invalid_ordered_levels(self):
        self.case["stop_price"] = 105
        self.assertEqual(classify(self.case), "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
