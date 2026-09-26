from __future__ import annotations

import hashlib
import json
from unittest import TestCase

from radar.evidence import GENESIS_HASH
from radar.evidence_portability import (canonical_snapshot_sha, restore_snapshot, verify_preseeded_target_prefix, verify_snapshot)


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


    def test_preseeded_target_exact_equal_passes(self):
        source=make_snapshot()
        target=json.loads(json.dumps(source))
        r=verify_preseeded_target_prefix(source,target)
        self.assertEqual(r["classification"],"PRESEEDED_TARGET_EXACT_EQUAL")
        self.assertEqual(r["missing_event_suffix_count"],0)
        self.assertFalse(r["target_mutation"])

    def test_preseeded_target_exact_prefix_passes(self):
        source=make_snapshot()
        target=json.loads(json.dumps(source))
        target["events"]=target["events"][:1]
        target["event_keys"]=target["event_keys"][:1]
        target["event_count"]=1
        target["key_count"]=1
        target["chain_head_sha256"]=target["events"][0]["chain_sha256"]
        target["snapshot_sha256"]=canonical_snapshot_sha(target)
        r=verify_preseeded_target_prefix(source,target)
        self.assertEqual(r["classification"],"PRESEEDED_TARGET_EXACT_PREFIX")
        self.assertEqual(r["missing_event_suffix_count"],1)
        self.assertEqual(r["missing_key_suffix_count"],1)

    def test_preseeded_target_divergence_fails_closed(self):
        source=make_snapshot()
        target=json.loads(json.dumps(source))
        target["events"][1]["event_type"]="EVIL"
        target["events"][1]["payload_sha256"]=hashlib.sha256(target["events"][1]["payload_json"].encode()).hexdigest()
        material="|".join((target["events"][1]["prev_chain_sha256"],target["events"][1]["event_ts"],"EVIL",target["events"][1]["payload_sha256"]))
        target["events"][1]["chain_sha256"]=hashlib.sha256(material.encode()).hexdigest()
        target["chain_head_sha256"]=target["events"][1]["chain_sha256"]
        target["snapshot_sha256"]=canonical_snapshot_sha(target)
        with self.assertRaisesRegex(ValueError,"event divergence"):
            verify_preseeded_target_prefix(source,target)

    def test_preseeded_target_ahead_fails_closed(self):
        source=make_snapshot()
        target=json.loads(json.dumps(source))
        extra=dict(target["events"][-1])
        extra["id"]=3
        extra["event_ts"]="2026-09-22T00:00:03.000000Z"
        extra["prev_chain_sha256"]=target["events"][-1]["chain_sha256"]
        extra["chain_sha256"]=hashlib.sha256("|".join((extra["prev_chain_sha256"],extra["event_ts"],extra["event_type"],extra["payload_sha256"])).encode()).hexdigest()
        target["events"].append(extra)
        target["event_count"]=3
        target["chain_head_sha256"]=extra["chain_sha256"]
        target["snapshot_sha256"]=canonical_snapshot_sha(target)
        with self.assertRaisesRegex(ValueError,"ahead of source"):
            verify_preseeded_target_prefix(source,target)


if __name__=="__main__":
    import unittest
    unittest.main()
