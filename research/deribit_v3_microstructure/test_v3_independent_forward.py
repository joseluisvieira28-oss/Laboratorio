"""No-market tests for the independent quote evidence auditor."""
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest

import v3_forward_audit as audit_forward
import test_collector


class ForwardAuditTests(unittest.TestCase):
    def generate(self, root):
        case = test_collector.CollectorTests()
        attempt, receipt = case.run_attempt(root)
        self.assertTrue(receipt["prospective_v3"])
        return attempt

    def test_independent_valid_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = self.generate(tmp)
            result = audit_forward.audit(attempt)
            self.assertEqual(result["status"], "INDEPENDENT_FORWARD_QUOTE_AUDIT_PASS")
            self.assertEqual(result["source_hashes"], 4)
            self.assertIsNone(result["net_pnl"])

    def test_tampered_raw_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = self.generate(tmp)
            (attempt / "put.json").write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "RAW_SOURCE_HASH"):
                audit_forward.audit(attempt)

    def test_bad_decision_window_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = self.generate(tmp)
            path = attempt / "receipt.json"
            r = json.loads(path.read_text())
            r["decision_at"] = "2026-11-06T08:10:00+00:00"
            path.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError, "DECISION_WINDOW"):
                audit_forward.audit(attempt)

    def test_trading_or_net_pnl_contamination_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = self.generate(tmp)
            path = attempt / "receipt.json"
            r = json.loads(path.read_text())
            r["net_pnl"] = 1.0
            path.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError, "TRADING_OR_FEE_CONTAMINATION"):
                audit_forward.audit(attempt)

    def test_changed_collector_or_precommit_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = self.generate(tmp)
            path = attempt / "receipt.json"
            r = json.loads(path.read_text())
            r["collector_hash"] = "0" * 64
            path.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError, "COLLECTOR_CHANGED"):
                audit_forward.audit(attempt)

    def test_synthetic_diagnostic_not_forward(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = test_collector.CollectorTests()
            attempt, receipt = case.run_attempt(tmp, mode="controlled_observation")
            self.assertFalse(receipt["prospective_v3"])
            with self.assertRaisesRegex(ValueError, "NOT_ACCEPTED_FORWARD"):
                audit_forward.audit(attempt)

if __name__ == "__main__":
    unittest.main()
