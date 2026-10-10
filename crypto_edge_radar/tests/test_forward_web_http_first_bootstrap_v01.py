"""Regression: bind PUBLIC_SHADOW_ONLY HTTP before slow CED1D first run.

All tests are hermetic. No exchange, network, credentials, orders, capital, or
database mutations occur in this fixture.
"""
import os
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from radar import forward_web


class HttpFirstBootstrapTest(unittest.TestCase):
    def test_public_port_serves_while_initial_evidence_cycle_is_blocked(self):
        server_started = threading.Event()
        server_stop = threading.Event()
        server_closed = threading.Event()
        cycle_entered = threading.Event()
        cycle_release = threading.Event()
        result = {}
        failures = []
        instances = []

        class FakeServer:
            def __init__(self, address, handler):
                self.address = address
                self.handler = handler
                instances.append(self)

            def serve_forever(self):
                server_started.set()
                server_stop.wait(timeout=8)

            def shutdown(self):
                server_stop.set()

            def server_close(self):
                server_closed.set()

        class FakeRuntime:
            def __init__(self, settings):
                self.settings = settings
                self.store = SimpleNamespace(backend="synthetic")
                self.exact_worker_started = False

            def state(self):
                return {
                    "mode": "PUBLIC_SHADOW_ONLY",
                    "health": "STARTING",
                    "authenticated_exchange_api_used": False,
                    "exchange_mutation_performed": False,
                    "orders_created": False,
                    "live_capital_enabled": False,
                }

            def run_cycle(self):
                cycle_entered.set()
                if not cycle_release.wait(timeout=8):
                    raise RuntimeError("synthetic cycle timed out")
                # No workers are allowed until this preflight has completed.
                return {"persistence_watchdog": {"writes_allowed": False}}

        def runner():
            try:
                result["code"] = forward_web.serve_forward_shadow(port=0, interval=30)
            except Exception as exc:
                failures.append(type(exc).__name__)

        with (
            patch.object(forward_web.Settings, "from_env", return_value=SimpleNamespace()),
            patch.object(forward_web, "ForwardShadowRuntime", FakeRuntime),
            patch.object(forward_web, "ThreadingHTTPServer", FakeServer),
            patch.dict(os.environ, {
                "RADAR_EVIDENCE_WRITES_QUIESCED": "false",
                "RADAR_BACKUP_LOG_EMIT_ON_START": "false",
                "RADAR_BACKUP_JSON_LOG_EMIT_ON_START": "false",
                "RADAR_SUPABASE_POOLER_PROBE_ON_START": "false",
                "RADAR_EMA6H_RENDER_SOURCE_PROBE_ON_START": "false",
            }),
        ):
            thread = threading.Thread(target=runner, daemon=True)
            thread.start()
            try:
                self.assertTrue(cycle_entered.wait(4), "Initial scientific cycle was not entered")
                self.assertTrue(server_started.is_set(),
                                "HTTP should be accepting during slow initial CED1D cycle")
                self.assertEqual(instances[0].handler.runtime.state()["health"], "STARTING")
                self.assertTrue(thread.is_alive(), "Slow-cycle fixture should be blocked")
                self.assertFalse(instances[0].handler.runtime.state()["orders_created"])
            finally:
                cycle_release.set()
                server_stop.set()
                thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertTrue(server_closed.is_set())
        self.assertEqual(failures, [])
        self.assertEqual(result.get("code"), 0)


if __name__ == "__main__":
    unittest.main()
