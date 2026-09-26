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
        self.database.statements.append(statement)
        if statement == "SET TRANSACTION READ ONLY":
            self.result = []
            return
        if statement.startswith("SELECT ID, EVENT_TS, EVENT_TYPE, PAYLOAD_JSON") and "LIMIT 0" in statement:
            self.result = []
            return
        if statement.startswith("SELECT EVENT_TYPE, EVENT_KEY, EVENT_ID") and "LIMIT 0" in statement:
            self.result = []
            return
        if statement == "SELECT LAST_VALUE FROM RADAR_EVENTS_ID_SEQ":
            self.result = [(len(self.database.rows) or 1,)]
            return
        if statement.startswith("CREATE TABLE") or statement.startswith("CREATE INDEX"):
            self.result = []
            return
        if "PG_ADVISORY_XACT_LOCK" in statement:
            self.result = [(None,)]
            return
        if statement.startswith("SELECT EVENT_ID FROM RADAR_EVENT_KEYS"):
            event_type, event_key = params
            event_id = self.database.keys.get((event_type, event_key))
            self.result = [(event_id,)] if event_id is not None else []
            return
        if statement.startswith("INSERT INTO RADAR_EVENT_KEYS"):
            event_type, event_key, event_id = params
            identity = (event_type, event_key)
            if identity in self.database.keys:
                raise AssertionError("duplicate fake postgres event key")
            self.database.keys[identity] = event_id
            self.result = []
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
        if statement.startswith("SELECT PAYLOAD_JSON FROM RADAR_EVENTS WHERE EVENT_TYPE"):
            event_type = params[0]
            self.result = [
                (row["payload_json"],)
                for row in self.database.rows
                if row["event_type"] == event_type
            ]
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
        self.keys = {}
        self.statements = []

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

    def test_postgres_append_once_is_idempotent(self):
        fake = FakePsycopg()
        with patch.object(evidence, "psycopg", fake):
            store = evidence.PostgresEvidenceStore("postgresql://example/test")
            first = store.append_once("TFG_FORWARD_SIGNAL", "BTC:123", {"value": 1})
            second = store.append_once("TFG_FORWARD_SIGNAL", "BTC:123", {"value": 999})
            self.assertTrue(first["inserted"])
            self.assertFalse(first["duplicate"])
            self.assertFalse(second["inserted"])
            self.assertTrue(second["duplicate"])
            self.assertEqual(first["id"], second["id"])
            self.assertEqual(len(fake.rows), 1)
            self.assertEqual(len(fake.keys), 1)
            ok, detail = store.verify_chain()
            self.assertTrue(ok, detail)

    def test_postgres_read_payloads_is_read_only_and_typed(self):
        fake = FakePsycopg()
        with patch.object(evidence, "psycopg", fake):
            store = evidence.PostgresEvidenceStore("postgresql://example/test")
            store.append("A", {"value": 1})
            store.append("B", {"value": 2})
            store.append("A", {"value": 3})
            self.assertEqual(store.read_payloads("A"), [{"value": 1}, {"value": 3}])
            self.assertEqual(len(fake.rows), 3)

    def test_postgres_detects_tampering(self):
        fake = FakePsycopg()
        with patch.object(evidence, "psycopg", fake):
            store = evidence.PostgresEvidenceStore("postgresql://example/test")
            store.append("A", {"value": 1})
            fake.rows[0]["payload_json"] = '{"value":999}'
            ok, detail = store.verify_chain()
            self.assertFalse(ok)
            self.assertIn("payload hash mismatch", detail)

    def test_preprovisioned_mode_performs_no_ddl(self):
        fake = FakePsycopg()
        with patch.object(evidence, "psycopg", fake):
            store = evidence.PostgresEvidenceStore(
                "postgresql://example/test",
                schema_preprovisioned=True,
            )
            self.assertEqual(store.backend, "postgres")
            self.assertTrue(
                any(x == "SET TRANSACTION READ ONLY" for x in fake.statements)
            )
            self.assertFalse(
                any(x.startswith("CREATE ") for x in fake.statements),
                fake.statements,
            )
            self.assertFalse(
                any(x.startswith("ALTER ") for x in fake.statements),
                fake.statements,
            )

    def test_factory_wires_preprovisioned_mode(self):
        fake = FakePsycopg()
        with patch.object(evidence, "psycopg", fake):
            store = evidence.build_evidence_store(
                "unused.sqlite3",
                "postgresql://example/test",
                schema_preprovisioned=True,
            )
            self.assertEqual(store.backend, "postgres")
            self.assertFalse(any(x.startswith("CREATE ") for x in fake.statements))

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
