import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from radar.forward_web import ForwardShadowRuntime


class DH03BackgroundRuntimeTests(unittest.TestCase):
    def _runtime(self):
        r=object.__new__(ForwardShadowRuntime)
        r._lock=threading.Lock()
        r.store=SimpleNamespace(backend="postgres")
        r._dh03_thread=None
        r._dh03_last_attempt_day=None
        r._dh03_state={
            "status":"STARTING",
            "strategy_id":"HTF-DH03-12H-STANDALONE-FORWARD-V1",
        }
        return r

    def test_starts_once_per_runtime_day_and_reuses_state(self):
        r=self._runtime()
        calls=[]
        def fake_run(*,persist=True):
            calls.append(persist)
            return {
                "status":"WAITING_FIRST_ELIGIBLE_ARCHIVE_DAY",
                "strategy_id":"HTF-DH03-12H-STANDALONE-FORWARD-V1",
                "mode":"PUBLIC_ARCHIVE_SHADOW_ONLY",
                "latest_archive_day":"2026-09-17",
                "evidence_backend":"postgres",
                "live_capital_enabled":False,
                "orders_created":False,
            }
        with patch("radar.forward_web.run_dh03_archive_shadow",side_effect=fake_run):
            first=r._maybe_start_dh03(runtime_day="2026-09-18")
            self.assertEqual(first["status"],"RUNNING")
            r._dh03_thread.join(timeout=2)
            self.assertFalse(r._dh03_thread.is_alive())
            second=r._maybe_start_dh03(runtime_day="2026-09-18")
            self.assertEqual(second["status"],"WAITING_FIRST_ELIGIBLE_ARCHIVE_DAY")
            time.sleep(0.02)
            self.assertEqual(calls,[True])

    def test_worker_failure_is_fail_closed(self):
        r=self._runtime()
        with patch("radar.forward_web.run_dh03_archive_shadow",side_effect=RuntimeError("synthetic")):
            r._maybe_start_dh03(runtime_day="2026-09-18")
            r._dh03_thread.join(timeout=2)
            state=r._dh03_state
            self.assertEqual(state["status"],"FAIL_CLOSED")
            self.assertFalse(state["live_capital_enabled"])
            self.assertFalse(state["orders_created"])
            self.assertIn("RuntimeError:synthetic",state["error"])


if __name__=="__main__":
    unittest.main()
