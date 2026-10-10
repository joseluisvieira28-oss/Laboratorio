"""Offline evidence-only regression checks; no exchange calls."""
import unittest

from radar.three_gate_audit_v01 import audit_three_gates


class ThreeGateAuditTest(unittest.TestCase):
    def test_empty_fails_closed(self):
        result = audit_three_gates("EXAMPLE", {})
        self.assertEqual(result["status"], "NO_GO__EVIDENCE_INCOMPLETE")
        self.assertFalse(result["automatic_live_authorization"])
        self.assertEqual(set(result["blockers"]), {"science", "economics", "execution"})

    def test_ordinary_forward_cannot_promote(self):
        evidence = {
            "candidate_id": "EXAMPLE",
            "science": {"verdict": "FORWARD_INSUFFICIENT"},
            "economics": {
                "route_status": "PUBLIC_EXECUTION_SAMPLE_READY_FOR_AUDIT",
                "independent_forward_net_expectancy_bps": -25.229662455,
            },
            "execution": {"historical_gap_review": "CURRENT_BUCKET_CONTINUOUS"},
        }
        result = audit_three_gates("EXAMPLE", evidence)
        self.assertEqual(result["gates"], {
            "science": "BLOCKED", "economics": "BLOCKED", "execution": "BLOCKED"
        })
        self.assertIn("HISTORICAL_RUNTIME_GAPS_NOT_RECONCILED", result["blockers"]["execution"])

    def test_identity_is_frozen(self):
        result = audit_three_gates("OTHER", {"candidate_id": "EXAMPLE"})
        self.assertIn("CANDIDATE_IDENTITY_NOT_BOUND", result["blockers"]["science"])

    def test_non_finite_results_are_blocked(self):
        for bad in (float("nan"), float("inf"), -1.0, None):
            evidence = {"candidate_id": "EXAMPLE", "economics": {
                "independent_forward_net_expectancy_bps": bad}}
            self.assertEqual(audit_three_gates("EXAMPLE", evidence)["gates"]["economics"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
