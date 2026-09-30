from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from radar.mexc_auth_readonly import MEXCCredentials
from scripts.mexc_triple_fishing_ready_v03 import build_readiness


class _FakePrivate:
    def position_mode(self):
        return 1

    def fee_details(self, symbol):
        return {"realTakerFee": 0.0008}

    def open_tpsl_orders(self):
        return []


class _FakePublic:
    def server_time_ms(self):
        return 1000.0

    def contract_row(self, symbol):
        return {
            "apiAllowed": True,
            "state": 0,
            "futureType": 1,
            "contractSize": 1.0,
            "minVol": 1.0,
            "volUnit": 1.0,
            "priceUnit": 0.1,
        }


class _FakeSlot:
    def __init__(self, path):
        self.path = path

    def current(self):
        return None


class TripleFishingReadinessV03Tests(unittest.TestCase):
    def _write_fixture(self, root: Path, checked_at: datetime) -> tuple[Path, Path]:
        overlay = root / "overlay.json"
        overlay.write_text(
            json.dumps(
                {
                    "overlay_id": "OPTIONS_V21_LOCAL_HASH_BOUND_PNL_CORRECTION_V0.1",
                    "entry_count": 4,
                }
            ),
            encoding="utf-8",
        )
        supervisor = root / "supervisor.json"
        supervisor.write_text(
            json.dumps(
                {
                    "version": "TRIPLE_FISHING_OPERATOR_V0.3",
                    "checked_at_utc": checked_at.isoformat().replace("+00:00", "Z"),
                    "source_state": {
                        "BNB-LAUNCHPOOL-DEMAND-001": {"status": "OK"},
                        "OPTIONS-SPOTPERP-001-V2.1": {
                            "status": "MISSED_ENTRY_WINDOW_NO_CHASE",
                            "watcher_status": "OK",
                        },
                        "HTF-DH03-12H-STANDALONE-FORWARD-V1": {
                            "status": "COLLECTING_LIVE",
                            "last_websocket_message_age_ms": 65,
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        return overlay, supervisor

    @patch("scripts.mexc_triple_fishing_ready_v03.GlobalSlotReservationV03", _FakeSlot)
    @patch("scripts.mexc_triple_fishing_ready_v03.MEXCFuturesPublicFeed", lambda timeout=10: _FakePublic())
    @patch("scripts.mexc_triple_fishing_ready_v03.MEXCFuturesAuthenticatedReadOnlyClient", lambda credentials: _FakePrivate())
    @patch(
        "scripts.mexc_triple_fishing_ready_v03.build_operator_risk_state",
        lambda **kwargs: {"pass": True, "blockers": [], "status": "PASS"},
    )
    @patch("scripts.mexc_triple_fishing_ready_v03.time.time_ns", side_effect=[1_000_000_000, 1_000_000_000])
    def test_concurrent_supervisor_update_after_readiness_start_is_not_false_stale(self, _time_ns):
        started = datetime(2026, 9, 30, 13, 26, 43, tzinfo=timezone.utc)
        supervisor_checked = started + timedelta(seconds=2)
        fresh_reference = supervisor_checked + timedelta(seconds=1)
        completed = fresh_reference + timedelta(milliseconds=250)
        ticks = iter([started, fresh_reference, completed])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            overlay, supervisor = self._write_fixture(root, supervisor_checked)
            result = build_readiness(
                credentials=MEXCCredentials("k", "s"),
                receipt_root=root / "receipts",
                correction_overlay=overlay,
                supervisor_state_path=supervisor,
                global_slot_path=root / "slot.json",
                kill_switch_path=root / "kill",
                now_fn=lambda: next(ticks),
            )

        self.assertTrue(result["pass"], result["blockers"])
        self.assertEqual(result["status"], "PASS_READY_TO_ARM")
        self.assertAlmostEqual(result["supervisor"]["age_seconds"], 1.0)
        self.assertNotIn("TRIPLE_SUPERVISOR_STATE_STALE", result["blockers"])

    @patch("scripts.mexc_triple_fishing_ready_v03.GlobalSlotReservationV03", _FakeSlot)
    @patch("scripts.mexc_triple_fishing_ready_v03.MEXCFuturesPublicFeed", lambda timeout=10: _FakePublic())
    @patch("scripts.mexc_triple_fishing_ready_v03.MEXCFuturesAuthenticatedReadOnlyClient", lambda credentials: _FakePrivate())
    @patch(
        "scripts.mexc_triple_fishing_ready_v03.build_operator_risk_state",
        lambda **kwargs: {"pass": True, "blockers": [], "status": "PASS"},
    )
    @patch("scripts.mexc_triple_fishing_ready_v03.time.time_ns", side_effect=[1_000_000_000, 1_000_000_000])
    def test_genuinely_future_supervisor_timestamp_still_fails_closed(self, _time_ns):
        started = datetime(2026, 9, 30, 13, 26, 43, tzinfo=timezone.utc)
        fresh_reference = started + timedelta(seconds=3)
        supervisor_checked = fresh_reference + timedelta(seconds=1)
        completed = fresh_reference + timedelta(milliseconds=250)
        ticks = iter([started, fresh_reference, completed])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            overlay, supervisor = self._write_fixture(root, supervisor_checked)
            result = build_readiness(
                credentials=MEXCCredentials("k", "s"),
                receipt_root=root / "receipts",
                correction_overlay=overlay,
                supervisor_state_path=supervisor,
                global_slot_path=root / "slot.json",
                kill_switch_path=root / "kill",
                now_fn=lambda: next(ticks),
            )

        self.assertFalse(result["pass"])
        self.assertIn("TRIPLE_SUPERVISOR_STATE_STALE", result["blockers"])
        self.assertLess(result["supervisor"]["age_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
