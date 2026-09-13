from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path

from research.phase_b_h03_discovery_runner_v01 import (
    DEFAULT_AUTHORIZATION_PATH,
    EXPECTED_AUTHORIZATION_FINGERPRINT,
    EXPECTED_MANIFEST_FINGERPRINT,
    _load_and_validate_authorization,
    run_h03_discovery,
)


class PhaseBH03DiscoveryRunnerTests(unittest.TestCase):
    def test_frozen_authorization_is_exact_and_future_routes_remain_locked(self) -> None:
        auth = _load_and_validate_authorization(DEFAULT_AUTHORIZATION_PATH)
        self.assertEqual(auth["fingerprint"], EXPECTED_AUTHORIZATION_FINGERPRINT)
        self.assertEqual(auth["required_bindings"]["manifest_fingerprint"], EXPECTED_MANIFEST_FINGERPRINT)
        self.assertTrue(auth["market_data_access_authorized"])
        self.assertTrue(auth["network_download_authorized"])
        self.assertTrue(auth["offline_evaluation_authorized"])
        self.assertFalse(auth["mexc_validation_2025_09_through_2025_12_authorized"])
        self.assertFalse(auth["holdout_2026_authorized"])
        self.assertFalse(auth["exchange_mutation_authorized"])
        self.assertFalse(auth["live_trading_authorized"])
        self.assertFalse(auth["main_merge_authorized"])
        self.assertFalse(auth["render_deploy_authorized"])
        self.assertFalse(auth["cross_exchange_backfill_for_h02_authorized"])

    def test_empty_local_corpus_stops_before_any_market_bytes_are_opened(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output = root / "receipt.json"
            receipt = run_h03_discovery(root / "raw", output, DEFAULT_AUTHORIZATION_PATH)
            self.assertEqual(receipt["status"], "H03_DISCOVERY_NOT_RUN_INTAKE_INCOMPLETE")
            self.assertEqual(receipt["missing_file_count"], 8760)
            self.assertFalse(receipt["market_data_bytes_opened"])
            self.assertFalse(receipt["outcome_evaluation_performed"])
            self.assertFalse(receipt["mexc_validation_2025_accessed"])
            self.assertFalse(receipt["holdout_2026_accessed"])
            self.assertTrue(output.is_file())

    def test_runner_contains_no_network_or_exchange_mutation_primitive(self) -> None:
        source = Path(__file__).resolve().parents[1] / "research" / "phase_b_h03_discovery_runner_v01.py"
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

    def test_authorization_fingerprint_tamper_fails_closed_before_data(self) -> None:
        original = json.loads(DEFAULT_AUTHORIZATION_PATH.read_text(encoding="utf-8"))
        original["holdout_2026_authorized"] = True
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tampered.json"
            path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaises(PermissionError):
                _load_and_validate_authorization(path)


if __name__ == "__main__":
    unittest.main()
