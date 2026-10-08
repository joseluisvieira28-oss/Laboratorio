"""Offline fatal-diagnostics tests. No exchange, credentials, or trading."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.mexc_triple_fishing_operator_v03 import (
    _write_fatal_receipt,
    main,
)


class FatalDiagnosticsTests(unittest.TestCase):
    def test_allowlisted_exception_class_only(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "live_state" / "triple.json"
            _write_fatal_receipt(state, "SUPERVISOR_LOOP", "RuntimeError")
            report = json.loads((state.parent / "TRIPLE_V03_FATAL_LAST.json").read_text())
            self.assertEqual(report["phase"], "SUPERVISOR_LOOP")
            self.assertEqual(report["exception_class"], "RuntimeError")
            self.assertEqual(report["exit_code"], 71)
            self.assertFalse(report["orders_created_by_diagnostic"])

    def test_unknown_error_name_is_redacted(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "live_state" / "triple.json"
            _write_fatal_receipt(state, "CREDENTIALS", "PRIVATE_API_SECRET_123")
            report = json.loads((state.parent / "TRIPLE_V03_FATAL_LAST.json").read_text())
            self.assertEqual(report["exception_class"], "OTHER_EXCEPTION")
            self.assertNotIn("PRIVATE_API_SECRET", json.dumps(report))

    def test_credential_init_failure_is_sanitized_and_fails(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "live_state" / "supervisor.json"
            fake_argv = [
                "mexc_triple_fishing_operator_v03.py",
                "--receipt-root", str(Path(td) / "receipts"),
                "--armed-path", str(Path(td) / "ARMED"),
                "--kill-switch", str(Path(td) / "KILL"),
                "--status-path", str(Path(td) / "engine.json"),
                "--global-slot-path", str(Path(td) / "slot.json"),
                "--supervisor-state", str(state),
                "--bnb-state", str(Path(td) / "bnb.json"),
                "--options-db", str(Path(td) / "options.sqlite"),
                "--options-state", str(Path(td) / "options.json"),
                "--dh03-market-db", str(Path(td) / "market.sqlite"),
                "--dh03-evidence-db", str(Path(td) / "evidence.sqlite"),
                "--dh03-state", str(Path(td) / "dh03.json"),
            ]
            with patch.object(sys, "argv", fake_argv), patch(
                "scripts.mexc_triple_fishing_operator_v03.MEXCCredentials.from_env",
                side_effect=RuntimeError("DO_NOT_LOG_FAKE_PRIVATE_TOKEN"),
            ):
                self.assertEqual(main(), 71)
            contents = (state.parent / "TRIPLE_V03_FATAL_LAST.json").read_text()
            self.assertNotIn("DO_NOT_LOG_FAKE_PRIVATE_TOKEN", contents)
            receipt = json.loads(contents)
            self.assertEqual(receipt["phase"], "CREDENTIALS")
            self.assertFalse((Path(td) / "ARMED").exists())
            self.assertFalse((Path(td) / "slot.json").exists())

    def test_diagnostics_write_failure_does_not_change_safety(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "live_state" / "supervisor.json"
            # Make the parent an ordinary file, so the diagnostic cannot write.
            state.parent.write_text("inert", encoding="utf-8")
            _write_fatal_receipt(state, "ENGINE_INIT", "OSError")
            self.assertFalse((Path(td) / "ARMED").exists())
            self.assertFalse((Path(td) / "slot.json").exists())


if __name__ == "__main__":
    unittest.main()
