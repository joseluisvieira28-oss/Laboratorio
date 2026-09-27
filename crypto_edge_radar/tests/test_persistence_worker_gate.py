from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from radar import forward_web


class FailClosedRuntime:
    last = None

    def __init__(self, *, settings):
        self.settings = settings
        self.store = MagicMock()
        self.etf_cme_exact_scheduler = MagicMock()
        self.run_loop = MagicMock()
        self._state = {}
        FailClosedRuntime.last = self

    def run_cycle(self):
        state = {
            "health": "DEGRADED_FAIL_CLOSED",
            "mode": "PERSISTENCE_ROUTE_FAIL_CLOSED",
            "persistence_watchdog": {
                "classification": "FAIL_CLOSED_PERSISTENCE_ROUTE",
                "pass": False,
                "writes_allowed": False,
            },
        }
        self._state = dict(state)
        return state

    def state(self):
        return dict(self._state)


class FakeServer:
    def __init__(self, *_args, **_kwargs):
        self.served = False

    def serve_forever(self):
        self.served = True
        return

    def server_close(self):
        return


class PersistenceWorkerGateTests(unittest.TestCase):
    def test_fail_closed_persistence_state_starts_no_worker_threads(self):
        settings = MagicMock()
        settings.http_timeout = 10

        with patch.dict(
            os.environ,
            {
                "RADAR_EVIDENCE_WRITES_QUIESCED": "false",
                "RADAR_BACKUP_LOG_EMIT_ON_START": "false",
                "RADAR_BACKUP_JSON_LOG_EMIT_ON_START": "false",
                "RADAR_SUPABASE_POOLER_PROBE_ON_START": "false",
            },
            clear=False,
        ), patch.object(
            forward_web.Settings,
            "from_env",
            return_value=settings,
        ), patch.object(
            forward_web,
            "ForwardShadowRuntime",
            FailClosedRuntime,
        ), patch.object(
            forward_web,
            "ThreadingHTTPServer",
            FakeServer,
        ), patch.object(
            forward_web.threading,
            "Thread",
        ) as thread_cls:
            rc = forward_web.serve_forward_shadow(port=8787, interval=30.0)

        self.assertEqual(rc, 0)
        runtime = FailClosedRuntime.last
        self.assertIsNotNone(runtime)
        self.assertEqual(
            runtime.state()["mode"],
            "PERSISTENCE_ROUTE_FAIL_CLOSED",
        )
        runtime.run_loop.assert_not_called()
        runtime.etf_cme_exact_scheduler.run_loop.assert_not_called()
        thread_cls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
