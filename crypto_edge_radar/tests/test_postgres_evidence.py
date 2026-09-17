import unittest
from unittest.mock import patch

from radar import evidence


class FakeCursor:
    def __init__(self, database):
        self.database = database
        self.result = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        statement = " ".join(sql.split()).upper()
        if statement.startswith("CREATE TABLE") or statement.startswith("CREATE INDEX"):
            self.result = []
            return
        if "PG_ADVISORY_XACT_LOCK" in statement:
            self.result = [(None,)]
            return
        if statement.startswith("SELECT CHAIN_SHA256 FROM RADAR_EVENTS"):
            if self.database.rows:
                self.result = [(self.database.rows[-1]["chain_sha256"],)]
            else:
                self.result = []
            return
        if statement.startswith("INSERT INTO RADAR_EVENTS"):
            event_ts, event_type, payload_json, payload_sha, prev_hash, chain_sha = params
            event_id = len(self.database.rows) + 1
            self.database.rows.append(
                {
                    "id": event_id,
                    "event_ts": event_ts,
                    "event_type": event_type,
                    "payload_json": payload_json,
                    "payload_sha256": payload_sha,
                    "prev_chain_sha256": prev_hash,
                    "chain_sha256": chain_sha,
                }
            )
            self.result = [(event_id,)]
            return
        if statement.startswith("SELECT ID, EVENT_TS, EVENT_TYPE, PAYLOAD_JSON"):
            self.result = [
                (
                    row["id"],
                    row["event_ts"],
                    row["event_type"],
                    row["payload_json"],
                    row["payload_sha256"],
                    row["prev_chain_sha256"],
                    row["chain_sha256"],
                )
                for row in self.database.rows
            ]
            return
        raise AssertionError(f"unexpected SQL in fake postgres: {statement}")

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return list(self.result)


class FakeConnection:
    def __init__(self, database):
        self.database = database

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return FakeCursor(self.database)


class FakePsycopg:
    def __init__(self):
        self.rows = []

    def connect(self, database_url, connect_timeout=5):
        if not database_url.startswith("postgresql://"):
            raise OSError("invalid test database URL")
        return FakeConnection(self)


class BrokenPsycopg:
    def connect(self, *_args, **_kwargs):
        raise OSError("synthetic postgres unavailable")


class PostgresEvidenceTests(unittest.TestCase):
    def test_postgres_append_and_chain_verify(self):
        fake = FakePsycopg()
        with patch.object(evidence, "psycopg", fake):
            store = evidence.PostgresEvidenceStore("postgresql://example/test")
            first = store.append("A", {"value": 1})
            second = store.append("B", {"value": 2})
            self.assertEqual(first["backend"], "postgres")
            self.assertEqual(second["prev_chain_sha256"], first["chain_sha256"])
            ok, detail = store.verify_chain()
            self.assertTrue(ok)
            self.assertIn("2 events via postgres", detail)

    def test_postgres_detects_tampering(self):
        fake = FakePsycopg()
        with patch.object(evidence, "psycopg", fake):
            store = evidence.PostgresEvidenceStore("postgresql://example/test")
            store.append("A", {"value": 1})
            fake.rows[0]["payload_json"] = '{"value":999}'
            ok, detail = store.verify_chain()
            self.assertFalse(ok)
            self.assertIn("payload hash mismatch", detail)

    def test_postgres_initialization_fails_closed(self):
        with patch.object(evidence, "psycopg", BrokenPsycopg()):
            with self.assertRaisesRegex(RuntimeError, "postgres evidence initialization failed"):
                evidence.PostgresEvidenceStore("postgresql://example/test")

    def test_factory_keeps_sqlite_fallback_without_remote_url(self):
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmp:
            store = evidence.build_evidence_store(os.path.join(tmp, "radar.sqlite3"), None)
            self.assertEqual(store.backend, "sqlite")
            receipt = store.append("A", {"value": 1})
            self.assertEqual(receipt["backend"], "sqlite")
            ok, _ = store.verify_chain()
            self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
