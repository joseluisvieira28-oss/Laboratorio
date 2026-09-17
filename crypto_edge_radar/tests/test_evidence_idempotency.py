from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
import unittest

from radar.evidence import EvidenceStore


class EvidenceIdempotencyTests(unittest.TestCase):
    def test_same_type_and_key_is_appended_only_once(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "evidence.sqlite3"
            store = EvidenceStore(str(db))

            first = store.append_once("TFG_SIGNAL", "BTCUSDT:123", {"value": 1})
            second = store.append_once("TFG_SIGNAL", "BTCUSDT:123", {"value": 999})

            self.assertTrue(first["inserted"])
            self.assertFalse(first["duplicate"])
            self.assertFalse(second["inserted"])
            self.assertTrue(second["duplicate"])
            self.assertEqual(first["id"], second["id"])

            with sqlite3.connect(db) as conn:
                event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                key_count = conn.execute("SELECT COUNT(*) FROM event_keys").fetchone()[0]
            self.assertEqual(event_count, 1)
            self.assertEqual(key_count, 1)
            self.assertEqual(store.verify_chain(), (True, "verified 1 events via sqlite"))

    def test_same_key_is_allowed_for_different_event_types(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(str(Path(td) / "evidence.sqlite3"))
            a = store.append_once("TFG_SIGNAL", "BTCUSDT:123", {"phase": "signal"})
            b = store.append_once("TFG_RESOLUTION", "BTCUSDT:123", {"phase": "resolution"})
            self.assertTrue(a["inserted"])
            self.assertTrue(b["inserted"])
            self.assertNotEqual(a["id"], b["id"])
            ok, detail = store.verify_chain()
            self.assertTrue(ok, detail)

    def test_empty_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(str(Path(td) / "evidence.sqlite3"))
            with self.assertRaises(ValueError):
                store.append_once("TFG_SIGNAL", "", {"value": 1})


if __name__ == "__main__":
    unittest.main()
