import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from calendar_manifest import manifest_sha256
from pretarget_gate import validate_for_freeze
from protocol_builder import build_final_protocol

RULESET = json.loads(
    (MODULE_DIR / "H02_SCIENTIFIC_RULESET_V01.json").read_text(encoding="utf-8")
)
AUTHORITY = json.loads(
    (MODULE_DIR / "H02_DESIGN_FREEZE_AUTHORITY_V01.json").read_text(encoding="utf-8")
)


def synthetic_calendar():
    m = {
        "document_type": "MRCR_OFFICIAL_CALENDAR_MANIFEST_V01",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "calendar_year": 2027,
        "complete_official_calendar": True,
        "event_families": [
            "US_CPI",
            "US_EMPLOYMENT_SITUATION",
            "FOMC_STATEMENT",
        ],
        "official_sources": [{
            "authority": "SYNTHETIC_AUTHORITY",
            "source_url": "https://example.invalid/calendar",
            "retrieved_at_utc": "2026-12-01T00:00:00Z",
        }],
        "events": [{
            "event_id": "SYNTH-1",
            "event_family": "US_CPI",
            "scheduled_time_utc": "2027-01-01T13:30:00Z",
            "official_source_ref": 0,
        }],
        "manifest_sha256": None,
    }
    m["manifest_sha256"] = manifest_sha256(m)
    return m


class ProtocolBuilderTests(unittest.TestCase):
    def test_builds_target_locked_structurally_valid_protocol(self):
        protocol = build_final_protocol(
            ruleset=RULESET,
            calendar_manifest=synthetic_calendar(),
            implementation_head_sha="a" * 40,
            calendar_frozen_at_utc="2026-12-01T00:00:01Z",
            protocol_frozen_at_utc="2026-12-01T00:00:02Z",
            authority_receipt_sha256=AUTHORITY["receipt_sha256"],
        )
        result = validate_for_freeze(protocol)
        self.assertTrue(result.ready, result.blockers)
        self.assertTrue(protocol["governance"]["h02_authorized"])
        self.assertFalse(protocol["governance"]["target_observation_authorized"])
        self.assertEqual(protocol["decision_state"]["decision_clock_seconds"], 180)
        self.assertEqual(
            protocol["decision_state"]["depth_definition"],
            {"mode": "BPS_BAND", "value": 10},
        )
        self.assertEqual(protocol["outcome"]["future_horizon_seconds"], 900)

    def test_calendar_family_mutation_fails(self):
        calendar = synthetic_calendar()
        calendar["event_families"] = ["US_CPI"]
        calendar["manifest_sha256"] = manifest_sha256(calendar)
        with self.assertRaisesRegex(ValueError, "calendar event families"):
            build_final_protocol(
                ruleset=RULESET,
                calendar_manifest=calendar,
                implementation_head_sha="a" * 40,
                calendar_frozen_at_utc="2026-12-01T00:00:01Z",
                protocol_frozen_at_utc="2026-12-01T00:00:02Z",
                authority_receipt_sha256=AUTHORITY["receipt_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
