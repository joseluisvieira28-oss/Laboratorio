from __future__ import annotations

import hashlib
import json
import unittest
from unittest.mock import patch

from radar import evidence_portability as ep
from radar.evidence import GENESIS_HASH


def make_snapshot(n: int = 3):
    events = []
    keys = []
    prev = GENESIS_HASH
    for idx in range(1, n + 1):
        payload_json = json.dumps(
            {"i": idx},
            sort_keys=True,
            separators=(",", ":"),
        )
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
    snapshot["snapshot_sha256"] = ep.canonical_snapshot_sha(snapshot)
    return snapshot


class FakeTarget:
    def __init__(self, source, prefix_count, sequence_last=None):
        self.events = [dict(x) for x in source["events"][:prefix_count]]
        self.keys = [
            dict(x)
            for x in source["event_keys"]
            if int(x["event_id"]) <= prefix_count
        ]
        self.sequence_last = (
            prefix_count if sequence_last is None else sequence_last
        )
        self.sequence_called = prefix_count > 0
        self.mutations = []

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

        if statement.startswith("INSERT INTO RADAR_EVENTS"):
            (
                event_id, event_ts, event_type, payload_json, payload_sha,
                prev_chain, chain_sha,
            ) = params
            self.target.mutations.append(("event", int(event_id)))
            self.target.events.append({
                "id": int(event_id),
                "event_ts": event_ts,
                "event_type": event_type,
                "payload_json": payload_json,
                "payload_sha256": payload_sha,
                "prev_chain_sha256": prev_chain,
                "chain_sha256": chain_sha,
            })
            self.result = []
            return

        if statement.startswith("INSERT INTO RADAR_EVENT_KEYS"):
            event_type, event_key, event_id = params
            self.target.mutations.append(("key", int(event_id)))
            self.target.keys.append({
                "event_type": event_type,
                "event_key": event_key,
                "event_id": int(event_id),
            })
            self.result = []
            return

        raise AssertionError(f"unexpected SQL: {statement}")

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return list(self.result)


class PrefixReconciliationTests(unittest.TestCase):
    def test_exact_prefix_dry_run_mutates_nothing(self):
        source = make_snapshot(3)
        target = FakeTarget(source, 2)
        with patch.object(ep, "psycopg", target):
            result = ep.reconcile_target_prefix(
                source,
                target_url="postgresql://target",
                apply=False,
            )
        self.assertEqual(result["classification"], "DRY_RUN_TARGET_EXACT_PREFIX")
        self.assertTrue(result["exact_prefix"])
        self.assertEqual(result["missing_event_count"], 1)
        self.assertEqual(result["missing_key_count"], 1)
        self.assertEqual(target.mutations, [])

    def test_divergent_existing_event_fails_closed_before_write(self):
        source = make_snapshot(3)
        target = FakeTarget(source, 2)
        target.events[1]["payload_json"] = '{"i":999}'
        with patch.object(ep, "psycopg", target):
            with self.assertRaisesRegex(ValueError, "payload hash mismatch"):
                ep.reconcile_target_prefix(
                    source,
                    target_url="postgresql://target",
                    apply=True,
                )
        self.assertEqual(target.mutations, [])

    def test_sequence_drift_fails_closed_before_write(self):
        source = make_snapshot(3)
        target = FakeTarget(source, 2, sequence_last=7)
        with patch.object(ep, "psycopg", target):
            result = ep.reconcile_target_prefix(
                source,
                target_url="postgresql://target",
                apply=True,
            )
        self.assertEqual(
            result["classification"],
            "TARGET_PREFIX_FAIL_CLOSED_NO_MUTATION",
        )
        self.assertIn(
            "TARGET_SEQUENCE_NOT_ALIGNED_TO_PREFIX_MAX_ID",
            result["reasons"],
        )
        self.assertEqual(target.mutations, [])

    def test_apply_appends_only_missing_rows_and_leaves_sequence_unmodified(self):
        source = make_snapshot(3)
        target = FakeTarget(source, 2)
        with patch.object(ep, "psycopg", target):
            result = ep.reconcile_target_prefix(
                source,
                target_url="postgresql://target",
                apply=True,
            )
        self.assertEqual(
            result["classification"],
            "TARGET_DELTA_ROWS_VERIFIED__SEQUENCE_FINALIZATION_REQUIRED",
        )
        self.assertEqual(result["inserted_event_count"], 1)
        self.assertEqual(result["inserted_key_count"], 1)
        self.assertTrue(result["target_rows_exact_after_reconcile"])
        self.assertTrue(result["sequence_finalization_required"])
        self.assertEqual(result["required_sequence_last_value"], 3)
        self.assertEqual(target.sequence_last, 2)
        self.assertEqual(target.mutations, [("event", 3), ("key", 3)])
        self.assertFalse(result["cutover_authorized"])

    def test_already_exact_target_is_noop(self):
        source = make_snapshot(3)
        target = FakeTarget(source, 3)
        with patch.object(ep, "psycopg", target):
            result = ep.reconcile_target_prefix(
                source,
                target_url="postgresql://target",
                apply=True,
            )
        self.assertEqual(
            result["classification"],
            "TARGET_ALREADY_EXACT__SEQUENCE_ALIGNED",
        )
        self.assertEqual(result["inserted_event_count"], 0)
        self.assertEqual(result["inserted_key_count"], 0)
        self.assertFalse(result["sequence_finalization_required"])
        self.assertEqual(target.mutations, [])


if __name__ == "__main__":
    unittest.main()
