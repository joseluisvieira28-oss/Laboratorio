from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from research.phase_b_mexc_download_intake_v01 import intake_downloads


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "phase_b_mexc_download_intake_v01.py"
LAUNCHER = ROOT / "research" / "intake_phase_b_mexc_downloads_windows.bat"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


class PhaseBMEXCDownloadIntakeTests(unittest.TestCase):
    def test_present_files_copy_and_missing_months_are_reported_without_p00(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            downloads = root / "downloads"
            dest = root / "raw"
            downloads.mkdir()
            feb = downloads / "BTC_USDT-Min15-2023-02-01.csv"
            feb.write_text("header\nfixture\n", encoding="utf-8")

            result = intake_downloads(downloads, dest, symbol="BTCUSDT", start_month="2023-02", end_month="2023-03")

            self.assertEqual(result.status, "INCOMPLETE_INTAKE")
            self.assertEqual(result.copied_count, 1)
            self.assertEqual(result.missing_count, 1)
            self.assertEqual(result.conflict_count, 0)
            self.assertFalse(result.p00_evaluation_performed)
            self.assertFalse(result.network_access_performed)
            self.assertFalse(result.exchange_mutation_performed)
            self.assertEqual((dest / feb.name).read_bytes(), feb.read_bytes())

    def test_same_hash_is_idempotently_already_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            downloads = root / "downloads"
            dest = root / "raw"
            downloads.mkdir()
            dest.mkdir()
            name = "BTC_USDT-Min15-2023-02-01.csv"
            (downloads / name).write_bytes(b"same")
            (dest / name).write_bytes(b"same")

            result = intake_downloads(downloads, dest, symbol="BTCUSDT", start_month="2023-02", end_month="2023-02")

        self.assertEqual(result.status, "PASS_INTAKE_COMPLETE")
        self.assertEqual(result.already_present_count, 1)
        self.assertEqual(result.copied_count, 0)

    def test_destination_hash_conflict_blocks_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            downloads = root / "downloads"
            dest = root / "raw"
            downloads.mkdir()
            dest.mkdir()
            name = "BTC_USDT-Min15-2023-02-01.csv"
            source = downloads / name
            target = dest / name
            source.write_bytes(b"official")
            target.write_bytes(b"existing-different")
            before = _sha256(target)

            result = intake_downloads(downloads, dest, symbol="BTCUSDT", start_month="2023-02", end_month="2023-02")
            after = _sha256(target)

        self.assertEqual(result.status, "BLOCKED_INTAKE")
        self.assertEqual(result.conflict_count, 1)
        self.assertIn("DESTINATION_HASH_CONFLICT", result.reasons)
        self.assertEqual(before, after)

    def test_2025_is_blocked_before_source_directory_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = intake_downloads(root / "missing", root / "raw", symbol="BTCUSDT", start_month="2025-01", end_month="2025-01")
        self.assertEqual(result.status, "BLOCKED_INTAKE")
        self.assertIn("INTAKE_RANGE_OUTSIDE_PRE_2025_DISCOVERY_BOUNDARY", result.reasons)
        self.assertEqual(result.months, ())

    def test_source_has_no_network_or_p00_evaluator_wiring(self):
        text = SOURCE.read_text(encoding="utf-8").lower()
        for forbidden in (
            "phase_b_research_evaluator_v01",
            "derive_signal_geometries",
            "simulate_outcome",
            "import requests",
            "import urllib",
            "import websockets",
            "import socket",
            "api.mexc.com",
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
        ):
            self.assertNotIn(forbidden, text)

    def test_windows_launcher_is_offline_intake_only(self):
        text = LAUNCHER.read_text(encoding="utf-8").lower()
        self.assertIn('set "pythonpath=%project_root%\\src;%project_root%;%pythonpath%"', text)
        self.assertIn("research.phase_b_mexc_download_intake_v01", text)
        self.assertIn("local_data\\discovery_raw", text)
        self.assertNotIn("phase_b_research_evaluator_v01", text)
        self.assertNotIn("api.mexc.com", text)
        self.assertNotIn("invoke-webrequest", text)
        self.assertGreaterEqual(text.count("no p00 evaluation was run"), 2)


if __name__ == "__main__":
    unittest.main()
