import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).parents[1] / "research" / "news_shock_v03_macro_consensus_source_gate" / "validate_event.py"
SPEC = importlib.util.spec_from_file_location("validate_event", MODULE)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def record(release="2024-03-12T12:30:00Z", published="2024-03-12T12:00:00Z"):
    fields = ["headline_cpi_mom", "headline_cpi_yoy", "core_cpi_mom", "core_cpi_yoy"]
    evidence = []
    observations = []
    for field in fields:
        for role in ("actual_first_release", "consensus"):
            eid = f"{field}-{role}"
            evidence.append({
                "evidence_id": eid,
                "published_at_utc": published if role == "consensus" else release,
                "temporal_proof": "PRE_T0_DIRECT" if role == "consensus" else "UNRESOLVED",
            })
            observations.append({"field": field, "role": role, "value": 0.1, "evidence_id": eid})
    return {
        "event_id": "US_CPI_2024-03-12",
        "event_family": "CPI",
        "release_timezone": "America/New_York",
        "scheduled_release_utc": release,
        "cutoff_utc": release,
        "evidence": evidence,
        "observations": observations,
    }


class SourceGateTests(unittest.TestCase):
    def test_valid_edt_record_passes(self):
        self.assertEqual(mod.validate_event(record()), [])

    def test_valid_est_record_passes(self):
        self.assertEqual(mod.validate_event(record("2024-01-11T13:30:00Z", "2024-01-10T20:00:00Z")), [])

    def test_post_release_consensus_fails(self):
        errors = mod.validate_event(record(published="2024-03-12T12:30:01Z"))
        self.assertIn("CONSENSUS_NOT_STRICTLY_PRE_T0", errors)

    def test_equal_t0_consensus_fails(self):
        errors = mod.validate_event(record(published="2024-03-12T12:30:00Z"))
        self.assertIn("CONSENSUS_NOT_STRICTLY_PRE_T0", errors)

    def test_fixed_offset_dst_error_fails_clock(self):
        errors = mod.validate_event(record(release="2024-03-12T13:30:00Z"))
        self.assertIn("RELEASE_CLOCK_NOT_0830_ET", errors)

    def test_2026_is_blocked(self):
        r = record("2026-03-12T12:30:00Z", "2026-03-11T20:00:00Z")
        r["event_id"] = "US_CPI_2026-03-12"
        self.assertIn("OUT_OF_SCOPE_BLOCKED", mod.validate_event(r))

    def test_missing_is_not_zero(self):
        r = record()
        r["observations"][0]["value"] = None
        self.assertIn("MISSING_VALUE_NOT_COMPLETE", mod.validate_event(r))

    def test_duplicate_field_role_fails(self):
        r = record()
        r["observations"].append(dict(r["observations"][0]))
        self.assertIn("DUPLICATE_OBSERVATION", mod.validate_event(r))

    def test_post_t0_temporal_label_cannot_pass(self):
        r = record()
        for e in r["evidence"]:
            if e["evidence_id"].endswith("consensus"):
                e["temporal_proof"] = "POST_T0_ONLY"
                break
        self.assertIn("CONSENSUS_TEMPORAL_PROOF_INVALID", mod.validate_event(r))


if __name__ == "__main__":
    unittest.main()
