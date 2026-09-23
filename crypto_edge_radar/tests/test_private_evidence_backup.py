from __future__ import annotations

import hashlib
import json
import os
import tempfile
from unittest import TestCase

from radar.evidence import EvidenceStore
from radar.private_evidence_backup import build_private_evidence_snapshot


class PrivateEvidenceBackupTests(TestCase):
    def test_sqlite_snapshot_is_complete_read_only_and_chain_verified(self):
        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(os.path.join(td, "e.sqlite3"))
            store.append_once("A", "k1", {"x": 1})
            store.append_once("B", "k2", {"x": 2})
            before = store.verify_chain()

            snap = build_private_evidence_snapshot(store)

            after = store.verify_chain()
            self.assertEqual(before, after)
            self.assertEqual(snap["event_count"], 2)
            self.assertEqual(snap["key_count"], 2)
            self.assertTrue(snap["chain_verified"])
            self.assertFalse(snap["database_mutation"])
            self.assertFalse(snap["secret_values_included"])
            self.assertEqual(snap["event_type_counts"], {"A": 1, "B": 1})
            self.assertEqual(snap["events"][0]["id"], 1)
            self.assertEqual(snap["events"][1]["id"], 2)

            raw = json.dumps(
                {"events": snap["events"], "event_keys": snap["event_keys"]},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), snap["snapshot_sha256"])


if __name__ == "__main__":
    import unittest
    unittest.main()
