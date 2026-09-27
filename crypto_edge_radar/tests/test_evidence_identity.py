from __future__ import annotations

import os
import tempfile
import unittest

from radar.evidence import EvidenceStore
from radar.evidence_identity import (
    IDENTITY_SCHEMA,
    build_evidence_identity,
    key_binding_sha256,
)


class EvidenceIdentityTests(unittest.TestCase):
    def test_identity_exposes_only_safe_equivalence_metadata(self):
        td = tempfile.TemporaryDirectory()
        try:
            store = EvidenceStore(os.path.join(td.name, "e.sqlite3"))
            a = store.append_once("TYPE_A", "key-a", {"secretish": "payload-a", "n": 1})
            b = store.append_once("TYPE_B", "key-b", {"secretish": "payload-b", "n": 2})
            identity = build_evidence_identity(store)

            self.assertEqual(identity["schema_version"], IDENTITY_SCHEMA)
            self.assertEqual(identity["status"], "VERIFIED")
            self.assertEqual(identity["event_count"], 2)
            self.assertEqual(identity["max_event_id"], 2)
            self.assertEqual(identity["key_count"], 2)
            self.assertEqual(identity["chain_head_sha256"], b["chain_sha256"])
            self.assertEqual(identity["sequence_last_value"], 2)
            self.assertTrue(identity["sequence_is_called"])
            self.assertTrue(identity["chain_verified"])
            self.assertFalse(identity["payloads_exposed"])
            self.assertFalse(identity["science_changed"])
            self.assertFalse(identity["database_mutation"])

            encoded = repr(identity)
            self.assertNotIn("payload-a", encoded)
            self.assertNotIn("payload-b", encoded)
            self.assertNotIn("secretish", encoded)
        finally:
            td.cleanup()

    def test_key_digest_is_order_independent_after_canonical_sort(self):
        rows = [
            ("TYPE_B", "z", 2),
            ("TYPE_A", "a", 1),
            ("TYPE_A", "β", 3),
        ]
        self.assertEqual(
            key_binding_sha256(rows),
            key_binding_sha256(list(reversed(rows))),
        )

    def test_key_digest_changes_when_binding_changes(self):
        base = [("TYPE_A", "a", 1), ("TYPE_B", "b", 2)]
        changed = [("TYPE_A", "a", 1), ("TYPE_B", "b", 3)]
        self.assertNotEqual(
            key_binding_sha256(base),
            key_binding_sha256(changed),
        )

    def test_empty_store_uses_genesis_and_zero_counts(self):
        td = tempfile.TemporaryDirectory()
        try:
            store = EvidenceStore(os.path.join(td.name, "e.sqlite3"))
            identity = build_evidence_identity(store)
            self.assertEqual(identity["event_count"], 0)
            self.assertEqual(identity["key_count"], 0)
            self.assertEqual(identity["max_event_id"], 0)
            self.assertEqual(identity["chain_head_sha256"], "0" * 64)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
