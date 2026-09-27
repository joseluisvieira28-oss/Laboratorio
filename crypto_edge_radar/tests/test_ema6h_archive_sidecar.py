from __future__ import annotations

from datetime import datetime, timezone
import unittest
from urllib.error import HTTPError

from radar.ema6h_archive_sidecar import EMA6HArchiveRecoverySidecar


def ms(iso: str) -> int:
    return int(
        datetime.fromisoformat(
            iso.replace("Z", "+00:00")
        ).timestamp()
        * 1000
    )


class Receipt:
    checksum_verified = True


class FakeArchive:
    provider = "BINANCE_PUBLIC_DATA_KLINES_RECOVERY_V0.2"

    def __init__(self):
        self.availability_now_ms = None
        self.last_receipts = [Receipt(), Receipt()]


class FakeWatcher:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def run_once(self, *, now_ms):
        self.calls.append(now_ms)
        if self.error is not None:
            raise self.error
        return dict(self.result)


class ArchiveSidecarTests(unittest.TestCase):
    def test_uses_previous_utc_day_cutoff_not_same_day(self):
        archive = FakeArchive()
        watcher = FakeWatcher(
            result={
                "status": "OK",
                "new_boundaries": 2,
                "inserted_signals": 1,
                "inserted_resolutions": 0,
                "missing_boundaries": 0,
            }
        )
        sidecar = EMA6HArchiveRecoverySidecar(
            store=object(),
            archive=archive,
            watcher=watcher,
        )
        now_ms = ms("2026-09-27T19:45:00Z")
        state = sidecar.run_once(now_ms=now_ms)

        self.assertEqual(
            watcher.calls,
            [ms("2026-09-26T23:59:59.999Z")],
        )
        self.assertEqual(archive.availability_now_ms, now_ms)
        self.assertEqual(
            state["recovery_cutoff_signal_close_utc"],
            "2026-09-26T18:00:00Z",
        )
        self.assertFalse(state["same_day_recovery_allowed"])
        self.assertTrue(state["evidence_advanced"])
        self.assertEqual(state["new_boundaries"], 2)
        self.assertTrue(state["archive_all_checksums_verified"])
        self.assertFalse(state["science_changed"])

    def test_404_is_waiting_not_fabricated_recovery(self):
        archive = FakeArchive()
        error = HTTPError(
            "https://data.binance.vision/archive.zip",
            404,
            "not found",
            {},
            None,
        )
        watcher = FakeWatcher(error=error)
        sidecar = EMA6HArchiveRecoverySidecar(
            store=object(),
            archive=archive,
            watcher=watcher,
        )
        state = sidecar.run_once(
            now_ms=ms("2026-09-27T19:45:00Z")
        )
        self.assertEqual(
            state["status"],
            "WAITING_ARCHIVE_T_PLUS_1_PUBLICATION",
        )
        self.assertFalse(state["evidence_advanced"])
        self.assertEqual(state["http_status"], 404)

    def test_semantic_or_integrity_error_fails_closed(self):
        archive = FakeArchive()
        watcher = FakeWatcher(
            error=RuntimeError("CHECKSUM mismatch")
        )
        sidecar = EMA6HArchiveRecoverySidecar(
            store=object(),
            archive=archive,
            watcher=watcher,
        )
        state = sidecar.run_once(
            now_ms=ms("2026-09-27T19:45:00Z")
        )
        self.assertEqual(
            state["status"],
            "ARCHIVE_RECOVERY_FAIL_CLOSED",
        )
        self.assertFalse(state["evidence_advanced"])
        self.assertIn("CHECKSUM mismatch", state["error"])


if __name__ == "__main__":
    unittest.main()
