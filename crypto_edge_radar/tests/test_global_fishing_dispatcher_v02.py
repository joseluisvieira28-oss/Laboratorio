from __future__ import annotations

from datetime import datetime, timezone
import unittest

from radar.global_fishing_dispatcher_v02 import arbitrate_due_signals


class GlobalFishingDispatcherV02Tests(unittest.TestCase):
    def signal(self, candidate, target, key=None):
        return {
            "candidate_id": candidate,
            "immutable_signal_key": key or candidate + ":sig",
            "entry_target_utc": target,
            "max_late_seconds": 2,
        }

    def test_existing_position_owns_slot(self):
        now = datetime(2026, 9, 29, 12, 0, 1, tzinfo=timezone.utc)
        out = arbitrate_due_signals(
            [self.signal("BNB", "2026-09-29T12:00:00Z")],
            now=now,
            global_slot_occupied=True,
        )
        self.assertEqual(out["status"], "GLOBAL_SLOT_OCCUPIED")
        self.assertIsNone(out["winner"])
        self.assertEqual(out["losers"][0]["reason"], "MISSED_CONFLICT_NO_CHASE")

    def test_earliest_target_wins(self):
        now = datetime(2026, 9, 29, 12, 0, 1, tzinfo=timezone.utc)
        out = arbitrate_due_signals(
            [
                self.signal("B", "2026-09-29T12:00:01Z"),
                self.signal("A", "2026-09-29T12:00:00Z"),
            ],
            now=now,
            global_slot_occupied=False,
        )
        self.assertEqual(out["winner_candidate_id"], "A")

    def test_lexical_tie_break_is_deterministic(self):
        now = datetime(2026, 9, 29, 12, 0, 1, tzinfo=timezone.utc)
        out = arbitrate_due_signals(
            [
                self.signal("CED1D", "2026-09-29T12:00:00Z"),
                self.signal("BNB", "2026-09-29T12:00:00Z"),
            ],
            now=now,
            global_slot_occupied=False,
        )
        self.assertEqual(out["winner_candidate_id"], "BNB")
        self.assertEqual(out["losers"][0]["candidate_id"], "CED1D")

    def test_late_signal_is_not_chased(self):
        now = datetime(2026, 9, 29, 12, 0, 5, tzinfo=timezone.utc)
        out = arbitrate_due_signals(
            [self.signal("BNB", "2026-09-29T12:00:00Z")],
            now=now,
            global_slot_occupied=False,
        )
        self.assertEqual(out["status"], "NO_DUE_SIGNAL")
        self.assertEqual(out["rejected"][0]["reason"], "MISSED_NO_CHASE")


    def test_nonfinite_lateness_is_rejected(self):
        now = datetime(2026, 9, 29, 13, 0, 0, tzinfo=timezone.utc)
        signal = self.signal("BNB", "2026-09-29T12:00:00Z")
        signal["max_late_seconds"] = "NaN"
        out = arbitrate_due_signals(
            [signal],
            now=now,
            global_slot_occupied=False,
        )
        self.assertIsNone(out["winner"])
        self.assertEqual(out["status"], "NO_DUE_SIGNAL")
        self.assertTrue(out["rejected"][0]["reason"].startswith("TIMING_INVALID:"))


if __name__ == "__main__":
    unittest.main()
