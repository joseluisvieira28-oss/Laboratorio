from __future__ import annotations

import hashlib
import json
import unittest
from unittest.mock import patch

from radar import sequence_finalization as sf
from radar.evidence import GENESIS_HASH


def make_snapshot(n: int = 3):
    events = []
    keys = []
    prev = GENESIS_HASH
    for idx in range(1, n + 1):
        payload_json = json.dumps({"i": idx}, sort_keys=True, separators=(",", ":"))
        payload_sha = hashlib.sha256(payload_json.encode()).hexdigest()
        event_ts = f"2026-09-27T00:00:{idx:02d}.000000Z"
        event_type = "TEST"
        chain_sha = hashlib.sha256(
            "|".join((prev, event_ts, event_type, payload_sha)).encode()
        ).hexdigest()
        events.append({
            "id": idx,
            "event_ts": event_ts,
            "event_type": event_type,
            "payload_json": payload_json,
            "payload_sha256": payload_sha,
            "prev_chain_sha256": prev,
            "chain_sha256": chain_sha,
        })
        keys.append({
            "event_type": event_type,
            "event_key": f"k{idx}",
            "event_id": idx,
        })
        prev = chain_sha
    snapshot = {
        "events": events,
        "event_keys": keys,
        "event_count": len(events),
        "key_count": len(keys),
        "chain_head_sha256": prev,
    }
    from radar.evidence_portability import canonical_snapshot_sha
    snapshot["snapshot_sha256"] = canonical_snapshot_sha(snapshot)
    return snapshot


class FakeTarget:
    def __init__(self, source, sequence_last):
        self.events = [dict(x) for x in source["events"]]
        self.keys = [dict(x) for x in source["event_keys"]]
        self.sequence_last = sequence_last
        self.sequence_called = True
        self.setvals = []

    def connect(self, *_args, **_kwargs):
        return FakeConnection(self)


class FakeConnection:
    def __init__(self, target):
        self.target = target

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return FakeCursor(self.target)


class FakeCursor:
    def __init__(self, target):
        self.target = target
        self.result = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        statement = " ".join(sql.split()).upper()
        if statement == "SET TRANSACTION READ ONLY":
            self.result = []
            return
        if "PG_ADVISORY_XACT_LOCK" in statement:
            self.result = [(None,)]
            return
        if statement.startswith(
            "SELECT ID,EVENT_TS,EVENT_TYPE,PAYLOAD_JSON,PAYLOAD_SHA256,"
        ):
            self.result = [
                (
                    x["id"], x["event_ts"], x["event_type"], x["payload_json"],
                    x["payload_sha256"], x["prev_chain_sha256"], x["chain_sha256"],
                )
                for x in self.target.events
            ]
            return
        if statement.startswith(
            "SELECT EVENT_TYPE,EVENT_KEY,EVENT_ID FROM RADAR_EVENT_KEYS"
        ):
            rows = sorted(
                self.target.keys,
                key=lambda x: (x["event_type"], x["event_key"]),
            )
            self.result = [
                (x["event_type"], x["event_key"], x["event_id"])
                for x in rows
            ]
            return
        if statement == "SELECT LAST_VALUE,IS_CALLED FROM RADAR_EVENTS_ID_SEQ":
            self.result = [
                (self.target.sequence_last, self.target.sequence_called)
            ]
            return
        if statement.startswith("SELECT SETVAL("):
            value = int(params[0])
            self.target.sequence_last = value
            self.target.sequence_called = True
            self.target.setvals.append(value)
            self.result = [(value,)]
            return
        raise AssertionError(f"unexpected SQL: {statement}")

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return list(self.result)


class SequenceFinalizationTests(unittest.TestCase):
    def test_missing_target_url_is_auth_required(self):
        result = sf.finalize_target_sequence(
            make_snapshot(3),
            target_url="",
            apply=False,
        )
        self.assertEqual(result["classification"], "AUTH_REQUIRED_NOT_EXECUTED")
        self.assertFalse(result["sequence_mutation"])

    def test_dry_run_exact_rows_sequence_behind_mutates_nothing(self):
        source = make_snapshot(3)
        target = FakeTarget(source, sequence_last=2)
        before_events = [dict(x) for x in target.events]
        before_keys = [dict(x) for x in target.keys]
        with patch.object(sf, "psycopg", target):
            result = sf.finalize_target_sequence(
                source,
                target_url="postgresql://admin-target",
                apply=False,
            )
        self.assertEqual(
            result["classification"],
            "DRY_RUN_TARGET_ROWS_EXACT__SEQUENCE_FINALIZATION_REQUIRED",
        )
        self.assertEqual(target.setvals, [])
        self.assertEqual(target.events, before_events)
        self.assertEqual(target.keys, before_keys)

    def test_apply_changes_only_sequence_after_exact_row_reverification(self):
        source = make_snapshot(3)
        target = FakeTarget(source, sequence_last=2)
        before_events = [dict(x) for x in target.events]
        before_keys = [dict(x) for x in target.keys]
        with patch.object(sf, "psycopg", target):
            result = sf.finalize_target_sequence(
                source,
                target_url="postgresql://admin-target",
                apply=True,
            )
        self.assertEqual(result["classification"], "TARGET_SEQUENCE_FINALIZED_EXACT")
        self.assertEqual(target.setvals, [3])
        self.assertEqual(target.sequence_last, 3)
        self.assertEqual(target.events, before_events)
        self.assertEqual(target.keys, before_keys)
        self.assertFalse(result["target_mutation"])
        self.assertTrue(result["sequence_mutation"])
        self.assertFalse(result["cutover_authorized"])

    def test_divergent_target_fails_closed_without_setval(self):
        source = make_snapshot(3)
        target = FakeTarget(source, sequence_last=2)
        target.events[1]["payload_json"] = '{"i":999}'
        with patch.object(sf, "psycopg", target):
            with self.assertRaisesRegex(ValueError, "payload hash mismatch"):
                sf.finalize_target_sequence(
                    source,
                    target_url="postgresql://admin-target",
                    apply=True,
                )
        self.assertEqual(target.setvals, [])

    def test_already_exact_sequence_is_noop(self):
        source = make_snapshot(3)
        target = FakeTarget(source, sequence_last=3)
        with patch.object(sf, "psycopg", target):
            result = sf.finalize_target_sequence(
                source,
                target_url="postgresql://admin-target",
                apply=True,
            )
        self.assertEqual(result["classification"], "TARGET_SEQUENCE_ALREADY_EXACT")
        self.assertEqual(target.setvals, [])
        self.assertFalse(result["sequence_mutation"])


if __name__ == "__main__":
    unittest.main()
