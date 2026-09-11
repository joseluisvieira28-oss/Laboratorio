from __future__ import annotations

import ast
import json
from pathlib import Path
import tempfile
import unittest

from research.phase_b_h03_discovery_runner_v02 import (
    DEFAULT_AMENDMENT_PATH,
    EXPECTED_CLOSE_TIME_AMENDMENT_FINGERPRINT,
    _load_and_validate_amendment,
    run_h03_discovery,
)


class PhaseBH03DiscoveryRunnerV02Tests(unittest.TestCase):
    def test_exact_pre_outcome_amendment_is_bound(self) -> None:
        amendment = _load_and_validate_amendment()
        self.assertEqual(amendment["fingerprint"], EXPECTED_CLOSE_TIME_AMENDMENT_FINGERPRINT)
        self.assertFalse(amendment["authority_basis"]["first_outcome_evaluation_completed"])
        self.assertFalse(amendment["authority_basis"]["performance_metrics_inspected"])
        self.assertEqual(amendment["trigger"]["close_time_violations"], 22)
        self.assertEqual(amendment["amended_mapping"]["canonical_close_time"], "open_time + 900000 - 1")

    def test_empty_corpus_receipt_is_still_bound_to_amendment_without_market_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output = root / "receipt.json"
            receipt = run_h03_discovery(raw_root=root / "raw", output_path=output)
            self.assertEqual(receipt["status"], "H03_DISCOVERY_NOT_RUN_INTAKE_INCOMPLETE")
            self.assertEqual(receipt["close_time_adapter_amendment_fingerprint"], EXPECTED_CLOSE_TIME_AMENDMENT_FINGERPRINT)
            self.assertEqual(receipt["pre_outcome_close_time_anomalies_observed"], 22)
            self.assertFalse(receipt["market_data_bytes_opened"])
            self.assertFalse(receipt["outcome_evaluation_performed"])

    def test_tampered_amendment_fails_closed_before_delegation(self) -> None:
        raw = json.loads(DEFAULT_AMENDMENT_PATH.read_text(encoding="utf-8"))
        raw["locks"]["holdout_2026_authorized"] = True
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tampered.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(PermissionError):
                _load_and_validate_amendment(path)

    def test_v02_contains_no_network_or_exchange_mutation_primitive(self) -> None:
        source = Path(__file__).resolve().parents[1] / "research" / "phase_b_h03_discovery_runner_v02.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        forbidden_imports = {"requests", "urllib", "http", "socket", "websockets", "subprocess"}
        forbidden_calls = {"post", "put", "patch", "delete", "urlopen", "connect", "send"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn(alias.name.split(".")[0], forbidden_imports)
            elif isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or "").split(".")[0], forbidden_imports)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(node.func.attr.lower(), forbidden_calls)


if __name__ == "__main__":
    unittest.main()
