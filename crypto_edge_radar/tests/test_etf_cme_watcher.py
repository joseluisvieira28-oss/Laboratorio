import tempfile
import unittest
from datetime import datetime, timezone

from radar.evidence import EvidenceStore
from radar.etf_cme_watcher import ETFCMEPublicSignalWatcher, MISSED_EVENT, SIGNAL_EVENT
from radar.strategies.etf_cme_instflow_001 import CFTCObservation


PREVIOUS = CFTCObservation("2026-09-01", 1000, 400, 300)
CURRENT = CFTCObservation("2026-09-08", 1000, 450, 300)


def source(**_kwargs):
    return PREVIOUS, CURRENT


def ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


class ETFCMEPublicSignalWatcherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EvidenceStore(self.tmp.name + "/evidence.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_due_persists_once_and_restart_is_idempotent(self):
        first = ETFCMEPublicSignalWatcher(store=self.store, source=source).run_once(
            now_ms=ms("2026-09-16T00:00:00Z")
        )
        restarted = ETFCMEPublicSignalWatcher(store=self.store, source=source).run_once(
            now_ms=ms("2026-09-16T00:00:01Z")
        )
        self.assertEqual(first["status"], "SIGNAL_OBSERVED")
        self.assertTrue(first["signal_evidence_inserted"])
        self.assertFalse(restarted["signal_evidence_inserted"])
        self.assertEqual(len(self.store.read_payloads(SIGNAL_EVENT)), 1)

    def test_late_start_records_missed_without_signal_reconstruction(self):
        result = ETFCMEPublicSignalWatcher(store=self.store, source=source).run_once(
            now_ms=ms("2026-09-16T00:01:00Z")
        )
        self.assertEqual(result["status"], "MISSED_EXPECTED_OBSERVATION_NO_CHASE")
        self.assertEqual(len(self.store.read_payloads(SIGNAL_EVENT)), 0)
        self.assertEqual(len(self.store.read_payloads(MISSED_EVENT)), 1)

    def test_source_outage_fails_closed_without_evidence_fabrication(self):
        def broken(**_kwargs):
            raise RuntimeError("source down")

        result = ETFCMEPublicSignalWatcher(store=self.store, source=broken).run_once(
            now_ms=ms("2026-09-16T00:00:00Z")
        )
        self.assertEqual(result["status"], "FAIL_CLOSED")
        self.assertEqual(result["source_status"], "SOURCE_UNAVAILABLE")
        self.assertEqual(len(self.store.read_payloads(SIGNAL_EVENT)), 0)

    def test_before_window_is_source_observation_not_forward_signal(self):
        result = ETFCMEPublicSignalWatcher(store=self.store, source=source).run_once(
            now_ms=ms("2026-09-15T12:00:00Z")
        )
        self.assertEqual(result["status"], "WAITING_INFORMATION_SAFE_TIME")
        self.assertEqual(len(self.store.read_payloads(SIGNAL_EVENT)), 0)


if __name__ == "__main__":
    unittest.main()
