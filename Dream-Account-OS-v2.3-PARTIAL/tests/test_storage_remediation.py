import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
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

    def test_prune_handles_gapped_row_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(f"{directory}/db.sqlite3")
            journal.record_snapshots([snap(i) for i in range(20)])
            journal.connection.execute("DELETE FROM normalized_snapshots WHERE id IN (4,18,19)")
            journal.connection.commit()
            result = journal.prune_normalized_snapshots(5)
            ids = [row[0] for row in journal.connection.execute("SELECT id FROM normalized_snapshots ORDER BY id")]
            self.assertEqual(ids, [14, 15, 16, 17, 20])
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

    def test_compaction_candidate_preserves_non_snapshot_tables_and_exact_newest_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.sqlite3"
            destination = root / "candidate.sqlite3"
            report_path = root / "report.json"
            journal = Journal(str(source))
            journal.record_scan("2026-01-01T00:00:00Z", "TEST", "PASS", "RANGE", {"x": 1})
            journal.record_signal("sig-1", "2026-01-01T00:00:00Z", "BTCUSDT", "SETUP", "A", {"y": 2})
            journal.record_snapshots([snap(i) for i in range(20)])
            journal.connection.execute("DELETE FROM normalized_snapshots WHERE id IN (4,18,19)")
            journal.connection.commit()
            source_ids = [row[0] for row in journal.connection.execute("SELECT id FROM normalized_snapshots ORDER BY id DESC LIMIT 5")]
            journal.close()
            expected_sha = hashlib.sha256(source.read_bytes()).hexdigest()

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/compact_rescue_database.py",
                    str(source),
                    str(destination),
                    "--max-snapshots",
                    "5",
                    "--report",
                    str(report_path),
                    "--expected-source-sha256",
                    expected_sha,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertTrue(report["source_unchanged"])
            self.assertTrue(report["expected_source_sha256_match"])
            self.assertEqual(report["expected_source_sha256"], expected_sha)
            self.assertEqual(report["source_nonempty_sidecars"], {})
            self.assertNotEqual(report["source_journal_mode"], "wal")
            self.assertEqual(report["candidate_snapshot_rows"], 5)
            self.assertEqual(report["non_snapshot_count_mismatches"], {})
            self.assertEqual(report["schema_mismatches"], {})

            candidate = sqlite3.connect(destination)
            candidate_ids = [row[0] for row in candidate.execute("SELECT id FROM normalized_snapshots ORDER BY id DESC")]
            self.assertEqual(candidate_ids, source_ids)
            self.assertEqual(candidate.execute("SELECT COUNT(*) FROM market_scans").fetchone()[0], 1)
            self.assertEqual(candidate.execute("SELECT COUNT(*) FROM signals").fetchone()[0], 1)
            self.assertEqual(candidate.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
            candidate.close()

    def test_compaction_rejects_wrong_expected_source_sha(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.sqlite3"
            destination = root / "candidate.sqlite3"
            journal = Journal(str(source))
            journal.record_snapshots([snap(i) for i in range(3)])
            journal.close()

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/compact_rescue_database.py",
                    str(source),
                    str(destination),
                    "--expected-source-sha256",
                    "0" * 64,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("source SHA-256 mismatch", completed.stderr + completed.stdout)
            self.assertFalse(destination.exists())

    def test_compaction_refuses_nonempty_wal_sidecar(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.sqlite3"
            destination = root / "candidate.sqlite3"
            journal = Journal(str(source))
            journal.record_snapshots([snap(i) for i in range(3)])
            journal.close()
            Path(str(source) + "-wal").write_bytes(b"not-a-stable-checkpoint")

            completed = subprocess.run(
                [sys.executable, "scripts/compact_rescue_database.py", str(source), str(destination)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("sidecar", completed.stderr + completed.stdout)
            self.assertFalse(destination.exists())

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
