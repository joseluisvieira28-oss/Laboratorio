import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from calendar_manifest import manifest_sha256, validate_calendar_manifest


TEMPLATE = MODULE_DIR / "OFFICIAL_CALENDAR_MANIFEST_TEMPLATE_V01.json"


class CalendarManifestTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_template_fails_closed(self):
        ready, blockers = validate_calendar_manifest(self.template)
        self.assertFalse(ready)
        self.assertIn("COMPLETE_OFFICIAL_CALENDAR_FALSE", blockers)
        self.assertIn("OFFICIAL_SOURCES_MISSING", blockers)
        self.assertIn("EVENTS_MISSING", blockers)

    def _complete_synthetic(self):
        m = copy.deepcopy(self.template)
        m["complete_official_calendar"] = True
        m["event_families"] = ["SYNTHETIC_EVENT"]
        m["official_sources"] = [{
            "authority": "SYNTHETIC_AUTHORITY",
            "source_url": "https://example.invalid/calendar",
            "retrieved_at_utc": "2099-01-01T00:00:00Z"
        }]
        m["events"] = [{
            "event_id": "SYNTH-2099-01-01",
            "event_family": "SYNTHETIC_EVENT",
            "scheduled_time_utc": "2099-01-01T00:00:00Z",
            "official_source_ref": 0
        }]
        m["manifest_sha256"] = manifest_sha256(m)
        return m

    def test_complete_synthetic_manifest_passes(self):
        m = self._complete_synthetic()
        ready, blockers = validate_calendar_manifest(m)
        self.assertTrue(ready, blockers)

    def test_duplicate_event_ids_fail(self):
        m = self._complete_synthetic()
        m["events"].append(dict(m["events"][0]))
        m["manifest_sha256"] = manifest_sha256(m)
        ready, blockers = validate_calendar_manifest(m)
        self.assertFalse(ready)
        self.assertIn("DUPLICATE_EVENT_ID", blockers)

    def test_mutation_after_hash_fails(self):
        m = self._complete_synthetic()
        m["events"][0]["scheduled_time_utc"] = "2099-01-01T00:01:00Z"
        ready, blockers = validate_calendar_manifest(m)
        self.assertFalse(ready)
        self.assertIn("MANIFEST_SHA256_MISMATCH", blockers)


if __name__ == "__main__":
    unittest.main()
