from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import mexc_triple_fishing_operator_v03 as app


class SanitizedSupervisorFatalTests(unittest.TestCase):
    def _arguments(self, td: str) -> list[str]:
        root=Path(td)
        args=[
            "--receipt-root",str(root/"receipts"),
            "--armed-path",str(root/"armed.json"),
            "--kill-switch",str(root/"kill"),
            "--status-path",str(root/"engine.json"),
            "--global-slot-path",str(root/"slot.json"),
            "--supervisor-state",str(root/"supervisor.json"),
            "--bnb-state",str(root/"bnb.json"),
            "--options-db",str(root/"opt.db"),
            "--options-state",str(root/"options.json"),
            "--dh03-market-db",str(root/"market.db"),
            "--dh03-evidence-db",str(root/"evidence.db"),
            "--dh03-state",str(root/"dh03.json"),
        ]
        return ["mexc_triple_fishing_operator_v03.py",*args]

    def test_unavailable_credential_is_sanitized_and_preserves_slot(self):
        with tempfile.TemporaryDirectory() as td:
            marker=Path(td)/"slot.json"
            marker.write_text('{"synthetic_slot":"MUST_NOT_DELETE"}',encoding="utf-8")
            with patch.object(sys,"argv",self._arguments(td)), patch.object(
                app.MEXCCredentials,"from_env",
                side_effect=RuntimeError("PRIVATE_ACCOUNT_RESPONSE_MUST_NOT_APPEAR"),
            ):
                self.assertEqual(app.main(),61)
            self.assertEqual(marker.read_text(encoding="utf-8"),'{"synthetic_slot":"MUST_NOT_DELETE"}')
            fatal=Path(td)/"supervisor.json.fatal.json"
            evidence=fatal.read_text(encoding="utf-8")
            self.assertNotIn("PRIVATE_ACCOUNT_RESPONSE_MUST_NOT_APPEAR",evidence)
            receipt=json.loads(evidence)
            self.assertEqual(receipt["stage"],"LOAD_CREDENTIALS")
            self.assertEqual(receipt["error_type"],"RuntimeError")
            self.assertEqual(receipt["result"],"FAIL_CLOSED")

    def test_engine_init_error_stays_distinct(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(sys,"argv",self._arguments(td)), patch.object(
                app.MEXCCredentials,"from_env",return_value=object(),
            ), patch.object(
                app,"OperatorFuturesEngineV02",
                side_effect=OSError("SECRET_LOCAL_DISK_PATH_MUST_NOT_APPEAR"),
            ):
                self.assertEqual(app.main(),61)
            raw=(Path(td)/"supervisor.json.fatal.json").read_text(encoding="utf-8")
            self.assertNotIn("SECRET_LOCAL_DISK_PATH_MUST_NOT_APPEAR",raw)
            self.assertEqual(json.loads(raw)["stage"],"CONSTRUCT_ENGINE")

    def test_fatal_log_write_failure_cannot_resume(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(sys,"argv",self._arguments(td)), patch.object(
                app.MEXCCredentials,"from_env",
                side_effect=RuntimeError("synthetic"),
            ), patch.object(app,"_atomic_write",side_effect=OSError("read-only")):
                self.assertEqual(app.main(),61)


if __name__=="__main__":
    unittest.main()
