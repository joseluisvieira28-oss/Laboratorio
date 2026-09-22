from __future__ import annotations

import hashlib
import json
import os
import tempfile
from unittest import TestCase

from radar.evidence import EvidenceStore
from radar.private_evidence_backup import build_private_evidence_snapshot, emit_snapshot_log_chunks


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


    def test_log_chunks_roundtrip(self):
        import base64, contextlib, gzip, io
        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(os.path.join(td, "e.sqlite3"))
            store.append_once("A", "k1", {"x": 1})
            store.append_once("B", "k2", {"x": 2})
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                header = emit_snapshot_log_chunks(store, chunk_chars=1000)
            lines = buf.getvalue().splitlines()
            chunks = [line.split(" ", 2)[2] for line in lines if line.startswith("RADAR_BACKUP_CHUNK ")]
            packed = base64.b64decode("".join(chunks), validate=True)
            raw = gzip.decompress(packed)
            snap = json.loads(raw)
            self.assertEqual(snap["event_count"], 2)
            self.assertTrue(snap["chain_verified"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), header["snapshot_sha256"])
            self.assertEqual(hashlib.sha256(packed).hexdigest(), header["gzip_sha256"])

if __name__ == "__main__":
    import unittest
    unittest.main()
