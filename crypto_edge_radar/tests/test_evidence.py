from contextlib import closing
import os
import sqlite3
import tempfile
import unittest

from radar.evidence import EvidenceStore


class EvidenceTests(unittest.TestCase):
    def test_chain_verifies_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "evidence.sqlite3")
            store = EvidenceStore(path)
            store.append("A", {"value": 1})
            store.append("B", {"value": 2})
            ok, detail = store.verify_chain()
            self.assertTrue(ok, detail)

            # sqlite3.Connection context commits/rolls back but does not
            # necessarily close the OS file handle. Windows requires explicit
            # closure before TemporaryDirectory cleanup.
            with closing(sqlite3.connect(path)) as conn:
                with conn:
                    conn.execute(
                        "UPDATE events SET payload_json = ? WHERE id = 1",
                        ('{"value":999}',),
                    )
            ok, detail = store.verify_chain()
            self.assertFalse(ok)
            self.assertIn("mismatch", detail)


if __name__ == "__main__":
    unittest.main()
