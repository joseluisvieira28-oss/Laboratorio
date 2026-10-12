import unittest
from datetime import datetime, timezone
from source_window_recovery import phase_at

class ClockTests(unittest.TestCase):
    def check(self, iso, expected):
        self.assertEqual(phase_at(datetime.fromisoformat(iso)), expected)
    def test_summer_entry(self): self.check("2026-10-12T13:01:00+00:00", "ENTRY")
    def test_summer_exit(self): self.check("2026-10-12T15:01:00+00:00", "EXIT")
    def test_dst_mismatch_week(self): self.check("2026-10-26T13:01:00+00:00", "ENTRY")
    def test_winter_entry(self): self.check("2026-11-02T14:01:00+00:00", "ENTRY")
    def test_late(self): self.check("2026-10-12T13:11:00+00:00", "OUTSIDE_FROZEN_WINDOWS")
    def test_early(self): self.check("2026-10-12T12:59:00+00:00", "OUTSIDE_FROZEN_WINDOWS")
    def test_weekend(self): self.check("2026-10-11T13:01:00+00:00", "NONTRADING_DAY")
    def test_naive_rejected(self):
        with self.assertRaises(ValueError): phase_at(datetime(2026,10,12,13,1))

if __name__ == "__main__": unittest.main()
