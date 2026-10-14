"""Hermetic validation of first-cycle diagnostics; no credentials or network."""
from __future__ import annotations

import io
import json
import threading
import unittest
from unittest.mock import patch

from radar import first_cycle_diagnostics as diag


def receipts(text):
    result = []
    for line in text.splitlines():
        if line.startswith(diag._LOG_PREFIX):
            result.append(json.loads(line[len(diag._LOG_PREFIX):]))
    return result


class FirstCycleDiagnosticsTests(unittest.TestCase):
    def test_success_runs_scientific_operation_exactly_once(self):
        calls = []
        sentinel = {"health": "DEGRADED_FAIL_CLOSED", "sentinel": object()}

        def operation():
            calls.append(1)
            return sentinel

        output = io.StringIO()
        with patch.object(diag.sys, "stderr", output):
            actual = diag.run_with_first_cycle_diagnostics(
                operation, interval_seconds=10.0
            )
        self.assertIs(actual, sentinel)
        self.assertEqual(calls, [1])
        trace = receipts(output.getvalue())
        self.assertEqual([x["kind"] for x in trace], [
            "FIRST_CYCLE_STARTED", "FIRST_CYCLE_FINISHED"
        ])
        self.assertEqual(trace[-1]["health"], "DEGRADED_FAIL_CLOSED")

    def test_blocking_operation_emits_bounded_progress_without_modifying_result(self):
        output = io.StringIO()
        expected = {"health": "OK", "unchanged": True}
        marker = "PRIVATE_KEY=must_never_be_logged"
        secret_argument = marker
        entered = threading.Event()
        release = threading.Event()

        def operation():
            secret_local = secret_argument
            self.assertEqual(secret_local, marker)
            entered.set()
            self.assertTrue(release.wait(3))
            return expected

        with patch.object(diag.sys, "stderr", output), patch.object(
            diag, "_radar_stack",
            return_value=[{"file": "ced1d_render_shadow_runtime.py",
                           "function": "run_once", "line": 120}],
        ):
            def release_when_started():
                self.assertTrue(entered.wait(2))
                self.assertTrue(self._wait_for_trace(output, "FIRST_CYCLE_STILL_RUNNING"))
                release.set()

            helper = threading.Thread(target=release_when_started, daemon=True)
            helper.start()
            try:
                result = diag.run_with_first_cycle_diagnostics(
                    operation, interval_seconds=0.01
                )
            finally:
                release.set()
                helper.join(timeout=3)

        self.assertIs(result, expected)
        trace = receipts(output.getvalue())
        active = [r for r in trace if r["kind"] == "FIRST_CYCLE_STILL_RUNNING"]
        self.assertTrue(active)
        self.assertEqual(active[0]["radar_stack"][0]["file"],
                         "ced1d_render_shadow_runtime.py")
        self.assertNotIn(marker, output.getvalue())
        self.assertIn("FIRST_CYCLE_FINISHED", [r["kind"] for r in trace])

    @staticmethod
    def _wait_for_trace(output, kind):
        import time
        until = time.monotonic() + 1.0
        while time.monotonic() < until:
            if kind in output.getvalue():
                return True
            time.sleep(0.01)
        return False

    def test_exception_type_only_and_original_exception_is_preserved(self):
        output = io.StringIO()
        def failed():
            raise RuntimeError("PASSWORD=never_print_this")

        with patch.object(diag.sys, "stderr", output):
            with self.assertRaisesRegex(RuntimeError, "PASSWORD="):
                diag.run_with_first_cycle_diagnostics(
                    failed, interval_seconds=10.0
                )
        trace = receipts(output.getvalue())
        self.assertEqual(trace[-1]["kind"], "FIRST_CYCLE_FAILED")
        self.assertEqual(trace[-1]["exception_type"], "RuntimeError")
        self.assertNotIn("never_print_this", output.getvalue())

    def test_base_exception_is_not_swallowed(self):
        with patch.object(diag.sys, "stderr", io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                diag.run_with_first_cycle_diagnostics(
                    lambda: (_ for _ in ()).throw(KeyboardInterrupt()),
                    interval_seconds=10.0,
                )

    def test_non_dict_return_is_not_modified(self):
        with patch.object(diag.sys, "stderr", io.StringIO()):
            self.assertEqual(diag.run_with_first_cycle_diagnostics(
                lambda: 17, interval_seconds=10.0), 17)

    def test_invalid_interval_does_not_call_operation(self):
        invoked = []
        with self.assertRaises(ValueError):
            diag.run_with_first_cycle_diagnostics(
                lambda: invoked.append(True), interval_seconds=0)
        self.assertEqual(invoked, [])

    def test_only_package_frames_or_placeholder_no_local_values(self):
        stack = diag._radar_stack(threading.get_ident())
        self.assertGreaterEqual(len(stack), 1)
        self.assertLessEqual(len(stack), 8)
        for frame in stack:
            self.assertEqual(set(frame), {"file", "function", "line"})
            self.assertNotIn("/", frame["file"])
            self.assertNotIn("\\", frame["file"])

    def test_logger_failure_does_not_change_return_value(self):
        class BrokenStderr:
            def write(self, value):
                raise BrokenPipeError()
            def flush(self):
                raise BrokenPipeError()

        with patch.object(diag.sys, "stderr", BrokenStderr()):
            self.assertEqual(diag.run_with_first_cycle_diagnostics(
                lambda: "safe", interval_seconds=10.0), "safe")


if __name__ == "__main__":
    unittest.main()
