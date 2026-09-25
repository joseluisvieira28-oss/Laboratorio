from __future__ import annotations

import unittest
from pathlib import Path

from scripts.mexc_execution_readiness_audit_v01 import summarize_manifest_registry


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "execution" / "CANDIDATE_EXECUTION_MANIFESTS_V1.json"


class ExecutionReadinessAuditTests(unittest.TestCase):
    def test_eight_candidates_are_accounted_for(self) -> None:
        result = summarize_manifest_registry(MANIFESTS)
        self.assertEqual(result["candidate_count"], 8)
        self.assertTrue(result["deny_by_default"])

    def test_only_options_has_ready_local_arming_lane(self) -> None:
        result = summarize_manifest_registry(MANIFESTS)
        ready = [
            row for row in result["candidates"]
            if row["category"] == "READY_FOR_LOCAL_ARMING"
        ]
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0]["candidate_id"], "OPTIONS-SPOTPERP-001-V2.1")
        self.assertEqual(ready[0]["ready_routes"], ["LONG"])

    def test_bnb_and_ced1d_are_prebuilt_but_locked(self) -> None:
        result = summarize_manifest_registry(MANIFESTS)
        by_id = {row["candidate_id"]: row for row in result["candidates"]}
        self.assertEqual(by_id["BNB-LAUNCHPOOL-DEMAND-001"]["category"], "ENGINEERING_PREBUILT_LOCKED")
        self.assertEqual(by_id["CED1D-0031"]["category"], "ENGINEERING_PREBUILT_LOCKED")


if __name__ == "__main__":
    unittest.main()
