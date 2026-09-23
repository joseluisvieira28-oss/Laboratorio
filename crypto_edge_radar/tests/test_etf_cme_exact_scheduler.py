from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone

from radar.evidence import EvidenceStore
from radar.etf_cme_exact_scheduler import (
    BOUNDARY_AS_OF_DATE,
    ETFCMEExactRuntimeScheduler,
    PREARM_EVENT,
)
from radar.etf_cme_watcher import ETFCMEPublicSignalWatcher, MISSED_EVENT, SIGNAL_EVENT
from radar.strategies.etf_cme_instflow_001 import CFTCObservation


def ms(value: str) -> int:
    return int(
        datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000
    )


def source_for(current_as_of: str):
    current = CFTCObservation(current_as_of, 1000, 450, 300)
    previous = CFTCObservation("2026-09-15" if current_as_of > "2026-09-15" else "2026-09-08", 1000, 400, 300)

    def _source(**_kwargs):
        return previous, current

    return _source


class ETFCMEExactRuntimeSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EvidenceStore(self.tmp.name + "/evidence.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def _scheduler(self, current_as_of: str):
        watcher = ETFCMEPublicSignalWatcher(
            store=self.store,
            source=source_for(current_as_of),
        )
        return ETFCMEExactRuntimeScheduler(watcher=watcher)

    def test_boundary_is_strict_and_old_miss_cannot_be_prearmed(self):
        scheduler = self._scheduler("2026-09-15")
        discovery = scheduler.discover(now_ms=ms("2026-09-23T04:00:00Z"))
        self.assertEqual(discovery["current_as_of_date"], BOUNDARY_AS_OF_DATE)

        state = scheduler.prearm(
            discovery,
            observed_ms=ms("2026-09-23T04:00:00Z"),
        )
        self.assertEqual(
            state["status"], "WAITING_NEW_CFTC_AS_OF_AFTER_BOUNDARY"
        )
        self.assertEqual(self.store.read_payloads(PREARM_EVENT), [])
        self.assertEqual(self.store.read_payloads(SIGNAL_EVENT), [])

    def test_future_report_prearms_inside_existing_60_second_window(self):
        scheduler = self._scheduler("2026-09-22")
        now_ms = ms("2026-09-29T23:59:30Z")
        discovery = scheduler.discover(now_ms=now_ms)
        self.assertEqual(discovery["target_utc"], "2026-09-30T00:00:00Z")

        state = scheduler.prearm(discovery, observed_ms=now_ms)
        self.assertEqual(state["status"], "PREARMED_FOR_EXACT_TARGET")
        self.assertEqual(len(self.store.read_payloads(PREARM_EVENT)), 1)
        self.assertEqual(self.store.read_payloads(SIGNAL_EVENT), [])

    def test_exact_target_uses_existing_watcher_and_persists_once(self):
        scheduler = self._scheduler("2026-09-22")
        discovery = scheduler.discover(now_ms=ms("2026-09-29T23:59:30Z"))
        scheduler.prearm(
            discovery,
            observed_ms=ms("2026-09-29T23:59:30Z"),
        )

        first = scheduler.attempt_exact(now_ms=ms("2026-09-30T00:00:00Z"))
        second = scheduler.attempt_exact(now_ms=ms("2026-09-30T00:00:01Z"))

        self.assertEqual(first["watcher_status"], "SIGNAL_OBSERVED")
        self.assertTrue(first["signal_evidence_inserted"])
        self.assertFalse(second["signal_evidence_inserted"])
        self.assertEqual(len(self.store.read_payloads(SIGNAL_EVENT)), 1)
        self.assertEqual(len(self.store.read_payloads(MISSED_EVENT)), 0)

    def test_late_after_two_seconds_stays_missed_no_chase(self):
        scheduler = self._scheduler("2026-09-22")
        state = scheduler.attempt_exact(now_ms=ms("2026-09-30T00:00:03Z"))

        self.assertEqual(
            state["watcher_status"], "MISSED_EXPECTED_OBSERVATION_NO_CHASE"
        )
        self.assertFalse(state["signal_evidence_inserted"])
        self.assertTrue(state["missed_evidence_inserted"])
        self.assertEqual(len(self.store.read_payloads(SIGNAL_EVENT)), 0)
        self.assertEqual(len(self.store.read_payloads(MISSED_EVENT)), 1)


if __name__ == "__main__":
    unittest.main()
