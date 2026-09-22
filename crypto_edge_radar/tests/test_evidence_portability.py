from __future__ import annotations

import hashlib
import json
from unittest import TestCase

from radar.evidence import GENESIS_HASH
from radar.evidence_portability import canonical_snapshot_sha, restore_snapshot, verify_snapshot


def make_snapshot():
    events=[]
    prev=GENESIS_HASH
    for idx,(typ,payload) in enumerate((("A",{"x":1}),("B",{"x":2})),start=1):
        payload_json=json.dumps(payload,sort_keys=True,separators=(",",":"))
        payload_sha=hashlib.sha256(payload_json.encode()).hexdigest()
        ts=f"2026-09-22T00:00:0{idx}.000000Z"
        chain=hashlib.sha256("|".join((prev,ts,typ,payload_sha)).encode()).hexdigest()
        events.append({
            "id":idx,"event_ts":ts,"event_type":typ,
            "payload_json":payload_json,"payload_sha256":payload_sha,
            "prev_chain_sha256":prev,"chain_sha256":chain,
        })
        prev=chain
    snap={
        "events":events,
        "event_keys":[
            {"event_type":"A","event_key":"k1","event_id":1},
            {"event_type":"B","event_key":"k2","event_id":2},
        ],
        "event_count":2,"key_count":2,"chain_head_sha256":prev,
    }
    snap["snapshot_sha256"]=canonical_snapshot_sha(snap)
    return snap


class EvidencePortabilityTests(TestCase):
    def test_verified_snapshot_dry_run_mutates_nothing(self):
        s=make_snapshot()
        r=restore_snapshot(s,target_url="secret-target-url",apply=False)
        self.assertEqual(r["classification"],"DRY_RUN_VERIFIED_NO_TARGET_MUTATION")
        self.assertFalse(r["target_mutation"])
        self.assertFalse(r["secret_value_exposed"])
        self.assertEqual(r["event_count"],2)
        self.assertEqual(r["key_count"],2)

    def test_missing_target_is_explicit_auth_blocker(self):
        r=restore_snapshot(make_snapshot(),target_url="",apply=True)
        self.assertEqual(r["classification"],"AUTH_REQUIRED_NOT_EXECUTED")
        self.assertFalse(r["target_mutation"])

    def test_tampered_payload_fails_before_target_write(self):
        s=make_snapshot()
        s["events"][0]["payload_json"]='{"x":999}'
        with self.assertRaisesRegex(ValueError,"payload hash mismatch"):
            restore_snapshot(s,target_url="secret-target-url",apply=False)

    def test_broken_key_reference_fails_before_target_write(self):
        s=make_snapshot()
        s["event_keys"][0]["event_id"]=999
        with self.assertRaisesRegex(ValueError,"missing event"):
            verify_snapshot(s)

    def test_duplicate_key_fails(self):
        s=make_snapshot()
        s["event_keys"].append(dict(s["event_keys"][0]))
        s["key_count"]=3
        with self.assertRaisesRegex(ValueError,"duplicate event key"):
            verify_snapshot(s)


if __name__=="__main__":
    import unittest
    unittest.main()
