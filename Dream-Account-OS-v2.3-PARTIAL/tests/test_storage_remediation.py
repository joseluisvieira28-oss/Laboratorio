import os
import tempfile
import unittest
from unittest import mock

from dream_account.data_contract import DataQuality, NormalizedSnapshot
from dream_account.database import Journal
from dream_account.runtime_service import (
    FORCE_MAINTENANCE_ENV,
    MAX_OPERATIONAL_SNAPSHOTS,
    RESCUE_MIN_FREE_BYTES,
    RescueRequired,
    _maintenance_forced,
    _require_storage_headroom,
)


def snap(i: int) -> NormalizedSnapshot:
    return NormalizedSnapshot(
        f"2026-01-01T00:00:{i % 60:02d}+00:00",
        "MEXC",
        f"S{i:04d}USDT",
        "SPOT",
        100.0,
        99.9,
        100.1,
        0.2,
        10_000_000.0,
        data_quality=DataQuality.VERIFIED,
    )


class StorageRemediationTests(unittest.TestCase):
    def test_batch_snapshot_insert_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/db.sqlite3"
            journal = Journal(path)
            self.assertEqual(journal.record_snapshots([snap(i) for i in range(7)]), 7)
            journal.close()
            journal = Journal(path)
            self.assertEqual(journal.snapshot_storage_stats()["rows"], 7)
            journal.close()

    def test_prune_keeps_exact_newest_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(f"{directory}/db.sqlite3")
            journal.record_snapshots([snap(i) for i in range(20)])
            result = journal.prune_normalized_snapshots(5)
            ids = [row[0] for row in journal.connection.execute("SELECT id FROM normalized_snapshots ORDER BY id")]
            self.assertEqual(ids, [16, 17, 18, 19, 20])
            self.assertEqual(result["rows"], 5)
            self.assertEqual(result["deleted_rows"], 15)
            journal.close()

    def test_prune_keeps_exact_newest_rows_even_with_id_gaps(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(f"{directory}/db.sqlite3")
            journal.record_snapshots([snap(i) for i in range(10)])
            journal.connection.execute("DELETE FROM normalized_snapshots WHERE id IN (7, 8)")
            journal.connection.commit()
            result = journal.prune_normalized_snapshots(5)
            ids = [row[0] for row in journal.connection.execute("SELECT id FROM normalized_snapshots ORDER BY id")]
            self.assertEqual(ids, [4, 5, 6, 9, 10])
            self.assertEqual(result["rows"], 5)
            journal.close()

    def test_prune_does_not_touch_non_snapshot_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(f"{directory}/db.sqlite3")
            journal.record_scan("2026-01-01T00:00:00Z", "TEST", "PASS", "RANGE", {})
            journal.record_signal("sig-1", "2026-01-01T00:00:00Z", "BTCUSDT", "SETUP", "A", {})
            before = journal.counts()
            account_before = journal.connection.execute("SELECT * FROM account_state").fetchall()
            journal.record_snapshots([snap(i) for i in range(25)])
            journal.prune_normalized_snapshots(3)
            self.assertEqual(journal.counts(), before)
            self.assertEqual(journal.connection.execute("SELECT * FROM account_state").fetchall(), account_before)
            journal.close()

    def test_prune_rejects_invalid_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(f"{directory}/db.sqlite3")
            with self.assertRaises(ValueError):
                journal.prune_normalized_snapshots(0)
            journal.close()

    def test_operational_constants_are_capacity_only(self):
        self.assertEqual(MAX_OPERATIONAL_SNAPSHOTS, 500_000)
        self.assertEqual(RESCUE_MIN_FREE_BYTES, 128 * 1024 * 1024)

    def test_forced_maintenance_switch(self):
        with mock.patch.dict(os.environ, {FORCE_MAINTENANCE_ENV: "1"}, clear=False):
            self.assertTrue(_maintenance_forced())
            with self.assertRaises(RescueRequired):
                _require_storage_headroom()

    def test_disk_guard_fails_before_write(self):
        fake_usage = {"total_bytes": 1_000_000_000, "used_bytes": 950_000_000, "free_bytes": 50_000_000}
        with mock.patch("dream_account.runtime_service._disk_usage", return_value=fake_usage):
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(RescueRequired):
                    _require_storage_headroom()


if __name__ == "__main__":
    unittest.main()
