from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from radar import forward_web


class QuiesceStore:
    backend = "postgres"

    def verify_chain(self):
        return True, "verified 1035 events via postgres"


class QuiesceRuntime:
    last = None

    def __init__(self, *, settings):
        self.settings = settings
        self.store = QuiesceStore()
        self.etf_cme_exact_scheduler = MagicMock()
        self.run_cycle = MagicMock()
        self.run_loop = MagicMock()
        self._state = {}
        QuiesceRuntime.last = self

    def _set_state(self, state):
        self._state = dict(state)

    def state(self):
        return dict(self._state)


class FakeServer:
    def __init__(self, *_args, **_kwargs):
        self.served = False
        self.closed = False

    def serve_forever(self):
        self.served = True
        return

    def server_close(self):
        self.closed = True


class QuiesceModeTests(unittest.TestCase):
    def test_quiesce_starts_no_scientific_worker_and_performs_no_cycle(self):
        settings = MagicMock()
        settings.http_timeout = 10

        with patch.dict(
            os.environ,
            {
                "RADAR_EVIDENCE_WRITES_QUIESCED": "true",
                "RADAR_BACKUP_LOG_EMIT_ON_START": "false",
                "RADAR_BACKUP_JSON_LOG_EMIT_ON_START": "false",
            },
            clear=False,
        ), patch.object(
            forward_web.Settings,
            "from_env",
            return_value=settings,
        ), patch.object(
            forward_web,
            "ForwardShadowRuntime",
            QuiesceRuntime,
        ), patch.object(
            forward_web,
            "ThreadingHTTPServer",
            FakeServer,
        ), patch.object(
            forward_web.threading,
            "Thread",
        ) as thread_cls:
            rc = forward_web.serve_forward_shadow(
                port=8787,
                interval=60.0,
            )

        self.assertEqual(rc, 0)
        runtime = QuiesceRuntime.last
        self.assertIsNotNone(runtime)
        runtime.run_cycle.assert_not_called()
        runtime.run_loop.assert_not_called()
        runtime.etf_cme_exact_scheduler.run_loop.assert_not_called()
        thread_cls.assert_not_called()

        state = runtime.state()
        self.assertEqual(state["health"], "OK")
        self.assertEqual(state["mode"], "EVIDENCE_WRITES_QUIESCED")
        self.assertTrue(state["maintenance_quiesce"])
        self.assertTrue(state["evidence_chain_ok"])
        self.assertIn("1035 events", state["evidence_chain_detail"])
        self.assertFalse(state["authenticated_exchange_api_used"])
        self.assertFalse(state["orders_created"])
        self.assertFalse(state["exchange_mutation_performed"])
        self.assertFalse(state["live_capital_enabled"])


if __name__ == "__main__":
    unittest.main()
