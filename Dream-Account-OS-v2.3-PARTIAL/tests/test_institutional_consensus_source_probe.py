import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1] / "research" / "news_shock_v03_macro_consensus_source_gate"


class InstitutionalSourceProbeTests(unittest.TestCase):
    def test_selection_is_exactly_two_frozen_2021_events(self):
        receipt = json.loads((ROOT / "receipts/INSTITUTIONAL_PROBE_SELECTION_FREEZE.json").read_text())
        ids = [row["event_id"] for row in receipt["selected_events"]]
        self.assertEqual(ids, ["US_CPI_2021-01-13", "US_NFP_2021-01-08"])
        self.assertTrue(all("2021" in event_id for event_id in ids))

    def test_selection_matches_declared_lexicographic_rule(self):
        with (ROOT / "2021_EVENT_MANIFEST.csv").open() as fh:
            manifest = list(csv.DictReader(fh))
        expected = []
        for family in ("CPI", "EMPLOYMENT_SITUATION"):
            expected.append(min(r["event_id"] for r in manifest if r["event_family"] == family))
        receipt = json.loads((ROOT / "receipts/INSTITUTIONAL_PROBE_SELECTION_FREEZE.json").read_text())
        self.assertEqual([r["event_id"] for r in receipt["selected_events"]], expected)

    def test_matrix_uses_only_allowed_source_classes(self):
        allowed = {
            "CAPABLE_AND_AUDITABLE", "CAPABLE_BUT_ACCESS_UNAVAILABLE", "PARTIALLY_CAPABLE",
            "DOCUMENTATION_INSUFFICIENT", "NOT_POINT_IN_TIME_SAFE", "NOT_FIELD_COMPLETE", "REJECTED"
        }
        with (ROOT / "INSTITUTIONAL_SOURCE_MATRIX.csv").open() as fh:
            rows = list(csv.DictReader(fh))
        self.assertGreaterEqual(len(rows), 8)
        self.assertTrue({r["classification"] for r in rows} <= allowed)
        self.assertNotIn("CAPABLE_AND_AUDITABLE", {r["classification"] for r in rows})

    def test_no_consensus_values_or_outcome_columns_enter_probe(self):
        forbidden = {"btc", "eth", "return", "pnl", "price", "volume", "direction"}
        with (ROOT / "INSTITUTIONAL_SOURCE_MATRIX.csv").open() as fh:
            reader = csv.DictReader(fh)
            headers = {h.lower() for h in reader.fieldnames}
            rows = list(reader)
        self.assertFalse(headers & forbidden)
        self.assertFalse(any("consensus_value" in row for row in rows))

    def test_decision_is_exactly_d(self):
        text = (ROOT / "NEXT_SOURCE_GATE_DECISION.md").read_text()
        self.assertIn("D — NO DEFENSIBLE SOURCE IDENTIFIED", text)
        self.assertIn("SOURCE_BLOCKED", text)


if __name__ == "__main__":
    unittest.main()
