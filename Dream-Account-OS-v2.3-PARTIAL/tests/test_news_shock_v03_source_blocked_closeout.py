import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1] / "research" / "news_shock_v03_macro_consensus_source_gate"


class SourceBlockedCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.marker = json.loads((ROOT / "SOURCE_BLOCKED.marker").read_text())

    def test_terminal_state_is_source_blocked_not_a_hypothesis_result(self):
        self.assertEqual(self.marker["status"], "SOURCE_BLOCKED")
        self.assertEqual(
            self.marker["hypothesis_result"],
            "NOT_TESTED_CRITICAL_INPUT_NOT_DEFENSIBLY_ESTABLISHED",
        )
        self.assertEqual(
            self.marker["v0_2_status"], "SCIENTIFICALLY_VALID_DESCRIPTIVE_RESULT"
        )

    def test_reopen_sample_is_exactly_the_frozen_pair(self):
        events = self.marker["reopen_condition"]["frozen_events"]
        self.assertEqual(
            [event["event_id"] for event in events],
            ["US_CPI_2021-01-13", "US_NFP_2021-01-08"],
        )
        self.assertTrue(self.marker["reopen_condition"]["reuse_same_events_first"])

    def test_reopen_fields_are_exact_and_complete(self):
        events = self.marker["reopen_condition"]["frozen_events"]
        self.assertEqual(
            events[0]["required_fields"],
            [
                "headline_mom_consensus",
                "headline_yoy_consensus",
                "core_mom_consensus",
                "core_yoy_consensus",
            ],
        )
        self.assertEqual(
            events[1]["required_fields"],
            [
                "payrolls_consensus",
                "unemployment_consensus",
                "ahe_mom_consensus",
                "ahe_yoy_consensus",
            ],
        )

    def test_reopen_evidence_requirements_are_exact(self):
        self.assertEqual(
            self.marker["reopen_condition"]["required_evidence_per_field"],
            [
                "consensus_value",
                "timestamp_or_vintage_strictly_before_t0",
                "timezone",
                "event_identifier",
                "provenance",
                "immutable_version_or_audit_trail",
            ],
        )
        self.assertTrue(self.marker["reopen_condition"]["all_fields_required"])
        self.assertTrue(
            self.marker["reopen_condition"]["all_requirements_required_per_field"]
        )

    def test_reference_is_the_frozen_remote_head(self):
        self.assertEqual(
            self.marker["reference_branch"],
            "news-shock-v03-institutional-source-probe",
        )
        self.assertEqual(
            self.marker["reference_commit"],
            "4460415c0c89e6b1b1edf39291f8bf1cf22c7c72",
        )

    def test_closeout_contains_required_terminal_language(self):
        closeout = (ROOT / "NEWS_SHOCK_V03_SOURCE_BLOCKED_CLOSEOUT.md").read_text()
        self.assertIn("V0.2: SCIENTIFICALLY VALID DESCRIPTIVE RESULT", closeout)
        self.assertIn("V0.3: SOURCE_BLOCKED", closeout)
        self.assertIn("FORMALLY CLOSED — SOURCE_BLOCKED", closeout)
        self.assertIn("hypothesis was not tested", closeout)

    def test_closeout_hash_manifest_matches_files(self):
        manifest = ROOT / "receipts" / "SOURCE_BLOCKED_CLOSEOUT_HASH_MANIFEST.csv"
        rows = manifest.read_text().splitlines()[1:]
        self.assertEqual(len(rows), 2)
        for row in rows:
            relative_path, expected = row.split(",")
            actual = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
