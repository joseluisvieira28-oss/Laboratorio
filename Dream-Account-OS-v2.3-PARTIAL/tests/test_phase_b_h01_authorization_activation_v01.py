from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.phase_b_h01_local_discovery_orchestrator_v01 import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RAW_DIR,
    expected_raw_paths,
    run_local_h01_discovery,
)
from research.phase_b_h01_mexc_discovery_access_v01 import (
    DEFAULT_AUTHORIZATION_PATH,
    FROZEN_UNIVERSE,
    validate_h01_discovery_access_request,
)


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "research" / "run_phase_b_h01_discovery_windows.bat"
ORCHESTRATOR = ROOT / "research" / "phase_b_h01_local_discovery_orchestrator_v01.py"


class PhaseBH01AuthorizationActivationTests(unittest.TestCase):
    def test_default_authorization_now_opens_exact_h01_discovery_preflight(self):
        self.assertTrue(DEFAULT_AUTHORIZATION_PATH.is_file())
        fingerprints = set()
        for symbol in FROZEN_UNIVERSE:
            receipt = validate_h01_discovery_access_request(
                symbol=symbol,
                start_month="2025-01",
                end_month="2025-08",
            )
            self.assertEqual(receipt.status, "PASS_H01_DISCOVERY_ACCESS_PREFLIGHT")
            self.assertTrue(receipt.authorization_verified)
            self.assertFalse(receipt.source_market_bytes_read)
            self.assertFalse(receipt.validation_2025_market_bytes_read)
            self.assertFalse(receipt.holdout_2026_market_bytes_read)
            fingerprints.add(receipt.authorization_fingerprint)
        self.assertEqual(len(fingerprints), 1)

    def test_validation_and_holdout_remain_physically_blocked_after_discovery_authorization(self):
        validation = validate_h01_discovery_access_request(
            symbol="BTCUSDT",
            start_month="2025-09",
            end_month="2025-12",
        )
        self.assertEqual(validation.status, "BLOCKED_H01_DISCOVERY_ACCESS")
        self.assertIn("H01_VALIDATION_2025_RANGE_BLOCKED", validation.reasons)
        self.assertFalse(validation.source_market_bytes_read)

        holdout = validate_h01_discovery_access_request(
            symbol="BTCUSDT",
            start_month="2026-01",
            end_month="2026-08",
        )
        self.assertEqual(holdout.status, "BLOCKED_H01_DISCOVERY_ACCESS")
        self.assertIn("H01_HOLDOUT_2026_RANGE_BLOCKED", holdout.reasons)
        self.assertFalse(holdout.source_market_bytes_read)

    def test_empty_download_directory_stops_before_h01_evaluation(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = run_local_h01_discovery(
                root / "downloads",
                raw_dir=root / "raw",
                output_dir=root / "output",
            )
            self.assertEqual(summary["status"], "H01_DISCOVERY_NOT_RUN_INTAKE_INCOMPLETE")
            self.assertEqual(summary["missing_count"], 48)
            self.assertFalse(summary["h01_evaluation_performed"])
            self.assertFalse(summary["validation_2025_access_performed"])
            self.assertFalse(summary["holdout_2026_access_performed"])
            self.assertFalse(summary["network_access_performed"])
            self.assertFalse(summary["exchange_mutation_performed"])
            self.assertFalse(summary["submitted_to_exchange"])

    def test_expected_raw_paths_are_exactly_six_symbols_times_eight_discovery_months(self):
        paths = expected_raw_paths("raw")
        self.assertEqual(len(paths), 48)
        names = tuple(path.name for path in paths)
        self.assertTrue(all("2025-01" in name or "2025-02" in name or "2025-03" in name or "2025-04" in name or "2025-05" in name or "2025-06" in name or "2025-07" in name or "2025-08" in name for name in names))
        self.assertFalse(any("2025-09" in name or "2025-10" in name or "2025-11" in name or "2025-12" in name for name in names))
        self.assertFalse(any("2026-" in name for name in names))

    def test_launcher_and_orchestrator_have_no_downloader_or_live_route(self):
        launcher = LAUNCHER.read_text(encoding="utf-8").lower()
        orchestrator = ORCHESTRATOR.read_text(encoding="utf-8").lower()
        forbidden = (
            "curl ",
            "invoke-webrequest",
            "requests.",
            "urllib",
            "websocket",
            "/api/v3/order",
            "subprocess",
        )
        for token in forbidden:
            self.assertNotIn(token, launcher)
            self.assertNotIn(token, orchestrator)
        self.assertIn("2025-01 through 2025-08 only", launcher)
        self.assertIn("validation 2025-09..12: locked", launcher)
        self.assertIn("holdout 2026: locked", launcher)


if __name__ == "__main__":
    unittest.main()
