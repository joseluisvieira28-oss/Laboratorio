from __future__ import annotations

import json
import multiprocessing as mp
from pathlib import Path
import tempfile
import unittest

from radar.global_slot_reservation_v03 import (
    GlobalSlotReservationError,
    GlobalSlotReservationV03,
)


def _claim_worker(path: str, candidate: str, signal: str, oid: str, queue) -> None:
    result = GlobalSlotReservationV03(path).claim(
        candidate_id=candidate,
        signal_identity=signal,
        external_oid=oid,
    )
    queue.put(result["claim_status"])


class GlobalSlotReservationV03Tests(unittest.TestCase):
    def test_two_processes_cannot_both_claim_slot(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "GLOBAL_POSITION_SLOT_V03.json")
            ctx = mp.get_context("spawn")
            queue = ctx.Queue()
            p1 = ctx.Process(target=_claim_worker, args=(path, "A", "A:1", "oid-a", queue))
            p2 = ctx.Process(target=_claim_worker, args=(path, "B", "B:1", "oid-b", queue))
            p1.start()
            p2.start()
            p1.join(10)
            p2.join(10)
            self.assertEqual(p1.exitcode, 0)
            self.assertEqual(p2.exitcode, 0)
            statuses = sorted([queue.get(timeout=2), queue.get(timeout=2)])
            self.assertEqual(statuses, ["CLAIMED", "OCCUPIED_BY_OTHER_SIGNAL"])

    def test_same_owner_recovers_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "slot.json"
            first = GlobalSlotReservationV03(path).claim(
                candidate_id="OPTIONS",
                signal_identity="OPTIONS:2026-09-30",
                external_oid="oid-1",
            )
            second = GlobalSlotReservationV03(path).claim(
                candidate_id="OPTIONS",
                signal_identity="OPTIONS:2026-09-30",
                external_oid="oid-1",
            )
            self.assertEqual(first["claim_status"], "CLAIMED")
            self.assertEqual(second["claim_status"], "RECOVERED_EXISTING_OWNER")

    def test_no_automatic_expiry(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "slot.json"
            GlobalSlotReservationV03(path).claim(
                candidate_id="BNB",
                signal_identity="BNB:1",
                external_oid="oid-bnb",
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["reserved_at_utc"] = "2020-01-01T00:00:00Z"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = GlobalSlotReservationV03(path).claim(
                candidate_id="DH03",
                signal_identity="DH03:1",
                external_oid="oid-dh03",
            )
            self.assertEqual(out["claim_status"], "OCCUPIED_BY_OTHER_SIGNAL")

    def test_release_requires_owner_and_terminal_reason(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "slot.json"
            slot = GlobalSlotReservationV03(path)
            slot.claim(candidate_id="A", signal_identity="A:1", external_oid="oid")
            with self.assertRaises(GlobalSlotReservationError):
                slot.release(signal_identity="B:1", reason="POST_TRADE_RECONCILIATION_CONFIRMED")
            with self.assertRaises(GlobalSlotReservationError):
                slot.release(signal_identity="A:1", reason="TIMEOUT")
            self.assertIsNotNone(slot.current())
            out = slot.release(
                signal_identity="A:1",
                reason="POST_TRADE_RECONCILIATION_CONFIRMED",
            )
            self.assertEqual(out["release_status"], "RELEASED")
            self.assertIsNone(slot.current())


if __name__ == "__main__":
    unittest.main()
