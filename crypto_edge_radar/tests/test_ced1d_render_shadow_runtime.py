from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from radar.evidence import EvidenceStore
from radar.ced1d_render_shadow_runtime import (
    CED1DRenderShadowRunner,
    CED1DRenderShadowRuntimeError,
    RECEIPT_EVENT,
    LEDGER_EVENT,
    FAILURE_EVENT,
    _validate_complete_result,
    latest_mature_signal_day,
    retryable_latest_archive_404,
)


def ms(y, m, d, hh=0, mm=0):
    return int(datetime(y, m, d, hh, mm, tzinfo=timezone.utc).timestamp() * 1000)


class CED1DRenderShadowRuntimeTests(TestCase):
    def test_readiness_gate_does_not_open_outcomes_early(self):
        self.assertIsNone(latest_mature_signal_day(date(2026, 9, 22)))
        self.assertIsNone(latest_mature_signal_day(date(2026, 9, 24)))
        self.assertEqual(latest_mature_signal_day(date(2026, 9, 25)), date(2026, 9, 22))

    def test_waiting_path_never_invokes_subprocess(self):
        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(os.path.join(td, "e.sqlite3"))
            runner = CED1DRenderShadowRunner(store=store)
            with patch("radar.ced1d_render_shadow_runtime.subprocess.run") as run:
                result = runner.run_once(now_ms=ms(2026, 9, 24, 23, 59))
            run.assert_not_called()
            self.assertEqual(result["status"], "WAITING_SOURCE_READINESS")
            self.assertFalse(result["retrospective_backfill"])
            self.assertFalse(result["orders_created"])
            self.assertFalse(result["exchange_mutation_performed"])

    def test_pre_migration_ledger_row_is_rejected(self):
        receipt = {
            "status": "SHADOW_COLLECTION_COMPLETE",
            "candidate": "CED1D-0031",
            "first_eligible_signal_day": "2026-09-22",
            "first_eligible_signal_completion": "2026-09-23T00:00:00Z",
            "through_signal_day": "2026-09-22",
            "governance": {
                "pre_boundary_performance_backfill": False,
                "live_trading": False,
                "orders": False,
                "wallets": False,
                "exchange_mutation": False,
                "authenticated_trading_endpoints": False,
                "parameter_changes": False,
                "merge_main": False,
            },
        }
        with self.assertRaisesRegex(
            CED1DRenderShadowRuntimeError, "PRE_MIGRATION_EVENT_FORBIDDEN"
        ):
            _validate_complete_result(
                receipt,
                [{"event_id": "CED1D-0031:2026-09-21", "signal_day": "2026-09-21"}],
                date(2026, 9, 22),
            )

    def test_latest_archive_pending_is_retryable_and_not_persisted_as_failure(self):
        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(os.path.join(td, "e.sqlite3"))
            runner = CED1DRenderShadowRunner(store=store)

            latest_url = (
                "https://data.binance.vision/data/futures/um/daily/"
                "klines/AVAXUSDT/1m/AVAXUSDT-1m-2026-09-24.zip"
            )

            def fake_run(cmd, **kwargs):
                out = Path(cmd[cmd.index("--output") + 1])
                out.mkdir(parents=True)
                receipt = {
                    "document_id": "CED1D_0031_RENDER_SHADOW_RECEIPT_V0.3",
                    "status": "SHADOW_COLLECTION_FAIL_CLOSED",
                    "candidate": "CED1D-0031",
                    "through_signal_day": "2026-09-22",
                    "error": (
                        "GateError:FETCH_FAIL:HTTPError:HTTP Error 404: Not Found:"
                        + latest_url
                    ),
                }
                (out / "CED1D_0031_RENDER_SHADOW_RECEIPT_V0.3.json").write_text(
                    json.dumps(receipt)
                )
                class P:
                    returncode = 1
                    stderr = "collector fail-closed"
                return P()

            with patch(
                "radar.ced1d_render_shadow_runtime.subprocess.run",
                side_effect=fake_run,
            ):
                result = runner.run_once(now_ms=ms(2026, 9, 25, 0, 10))

            self.assertEqual(result["status"], "WAITING_SOURCE_ARCHIVE")
            self.assertTrue(result["retryable_source_archive_pending"])
            self.assertEqual(result["latest_required_path_day"], "2026-09-24")
            self.assertEqual(len(store.read_payloads(FAILURE_EVENT)), 0)
            self.assertEqual(len(store.read_payloads(RECEIPT_EVENT)), 0)
            self.assertEqual(len(store.read_payloads(LEDGER_EVENT)), 0)

    def test_earlier_archive_404_remains_fail_closed_not_retryable(self):
        receipt = {
            "status": "SHADOW_COLLECTION_FAIL_CLOSED",
            "error": (
                "GateError:FETCH_FAIL:HTTPError:HTTP Error 404: Not Found:"
                "https://data.binance.vision/data/futures/um/daily/"
                "klines/AVAXUSDT/1m/AVAXUSDT-1m-2026-09-20.zip"
            ),
        }
        self.assertFalse(
            retryable_latest_archive_404(receipt, date(2026, 9, 22))
        )

    def test_successful_fake_run_persists_once_and_replays_without_reexecution(self):
        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(os.path.join(td, "e.sqlite3"))
            runner = CED1DRenderShadowRunner(store=store)

            def fake_run(cmd, **kwargs):
                out = Path(cmd[cmd.index("--output") + 1])
                out.mkdir(parents=True)
                receipt = {
                    "document_id": "CED1D_0031_RENDER_SHADOW_RECEIPT_V0.3",
                    "status": "SHADOW_COLLECTION_COMPLETE",
                    "candidate": "CED1D-0031",
                    "first_eligible_signal_day": "2026-09-22",
                    "first_eligible_signal_completion": "2026-09-23T00:00:00Z",
                    "through_signal_day": "2026-09-22",
                    "source": [],
                    "metrics": {"routing": "SHADOW_ACCUMULATING"},
                    "fingerprint": "synthetic",
                    "governance": {
                        "pre_boundary_performance_backfill": False,
                        "warmup_input_only": True,
                        "warmup_valid_observation_semantics": True,
                        "live_trading": False,
                        "orders": False,
                        "wallets": False,
                        "exchange_mutation": False,
                        "authenticated_trading_endpoints": False,
                        "parameter_changes": False,
                        "notional_per_leg_usdt": 100,
                        "merge_main": False,
                    },
                }
                (out / "CED1D_0031_RENDER_SHADOW_RECEIPT_V0.3.json").write_text(
                    json.dumps(receipt)
                )
                (out / "CED1D_0031_RENDER_SHADOW_LEDGER_V0.3.csv").write_text(
                    "event_id,signal_day,status\n"
                    "CED1D-0031:2026-09-22,2026-09-22,NO_SIGNAL\n"
                )
                class P:
                    returncode = 0
                    stderr = ""
                return P()

            with patch(
                "radar.ced1d_render_shadow_runtime.subprocess.run",
                side_effect=fake_run,
            ) as run:
                first = runner.run_once(now_ms=ms(2026, 9, 25, 0, 10))
                second = runner.run_once(now_ms=ms(2026, 9, 25, 0, 11))

            self.assertEqual(run.call_count, 1)
            self.assertEqual(first["status"], "SHADOW_COLLECTION_COMPLETE")
            self.assertEqual(first["inserted_events"], 1)
            self.assertEqual(second["status"], "ALREADY_PERSISTED")
            self.assertEqual(len(store.read_payloads(RECEIPT_EVENT)), 1)
            self.assertEqual(len(store.read_payloads(LEDGER_EVENT)), 1)


if __name__ == "__main__":
    import unittest
    unittest.main()
