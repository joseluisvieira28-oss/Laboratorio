import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dream_account.data_contract import DataQuality, NormalizedSnapshot
from dream_account.database import Journal

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compact_rescue_database import build_candidate, sha256
from gate_f_replace import perform_gate_f


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


class GateFRecoveryTests(unittest.TestCase):
    def _source(self, root: Path) -> Path:
        source = root / "dream_account.sqlite3"
        journal = Journal(str(source))
        journal.record_snapshots([snap(i) for i in range(20)])
        journal.record_scan("2026-01-01T00:00:00Z", "TEST", "PASS", "RANGE", {"x": 1})
        journal.close()
        return source

    def _expected_candidate_hash(self, source: Path, root: Path, cap: int) -> str:
        candidate = root / "expected.sqlite3"
        report = build_candidate(source, candidate, cap, expected_source_sha256=sha256(source))
        self.assertEqual(report["status"], "PASS")
        value = sha256(candidate)
        candidate.unlink()
        return value

    def test_gate_f_replaces_source_with_validated_compact_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._source(root)
            source_sha = sha256(source)
            candidate_sha = self._expected_candidate_hash(source, root, 5)
            result = perform_gate_f(
                source=source,
                candidate=root / "candidate.sqlite3",
                report_path=root / "report.json",
                install_path=root / ".installing.sqlite3",
                marker_path=root / "GATE_F_IN_PROGRESS.json",
                receipt_path=root / "GATE_F_RECOVERY_RECEIPT.json",
                max_snapshots=5,
                expected_source_sha=source_sha,
                expected_candidate_sha=candidate_sha,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertTrue(result["production_replacement_performed"])
            self.assertEqual(sha256(source), candidate_sha)
            self.assertFalse((root / "GATE_F_IN_PROGRESS.json").exists())
            self.assertTrue((root / "GATE_F_RECOVERY_RECEIPT.json").exists())
            connection = sqlite3.connect(source)
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM normalized_snapshots").fetchone()[0], 5)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM market_scans").fetchone()[0], 1)
            connection.close()

    def test_candidate_hash_mismatch_stops_before_source_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._source(root)
            source_sha = sha256(source)
            with self.assertRaises(RuntimeError):
                perform_gate_f(
                    source=source,
                    candidate=root / "candidate.sqlite3",
                    report_path=root / "report.json",
                    install_path=root / ".installing.sqlite3",
                    marker_path=root / "GATE_F_IN_PROGRESS.json",
                    receipt_path=root / "GATE_F_RECOVERY_RECEIPT.json",
                    max_snapshots=5,
                    expected_source_sha=source_sha,
                    expected_candidate_sha="0" * 64,
                )
            self.assertTrue(source.exists())
            self.assertEqual(sha256(source), source_sha)
            self.assertFalse((root / "GATE_F_IN_PROGRESS.json").exists())

    def test_gate_f_is_idempotent_after_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._source(root)
            source_sha = sha256(source)
            candidate_sha = self._expected_candidate_hash(source, root, 5)
            kwargs = dict(
                source=source,
                candidate=root / "candidate.sqlite3",
                report_path=root / "report.json",
                install_path=root / ".installing.sqlite3",
                marker_path=root / "GATE_F_IN_PROGRESS.json",
                receipt_path=root / "GATE_F_RECOVERY_RECEIPT.json",
                max_snapshots=5,
                expected_source_sha=source_sha,
                expected_candidate_sha=candidate_sha,
            )
            first = perform_gate_f(**kwargs)
            second = perform_gate_f(**kwargs)
            self.assertEqual(first["status"], "PASS")
            self.assertEqual(second["status"], "PASS_ALREADY_INSTALLED")
            self.assertFalse(second["production_replacement_performed"])
            self.assertEqual(sha256(source), candidate_sha)


if __name__ == "__main__":
    unittest.main()
