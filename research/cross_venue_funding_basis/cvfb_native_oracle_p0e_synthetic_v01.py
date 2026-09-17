#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "cvfb_native_oracle_p0e_replica_cmds_v01.py"
spec = importlib.util.spec_from_file_location("p0e", RUNNER)
p0e = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(p0e)


def test_freeze_pin_and_target():
    x = p0e.load_freeze()
    assert x["frozen_target"]["center_height"] == 280538302
    assert x["frozen_target"]["scan_block_count"] == 301
    assert x["authorization_gate"]["execution_authorized"] is False


def test_derive_exact_301_keys():
    keys = p0e.derive_keys("replica_cmds/start/20240901/", ".rmp.lz4", 280538152, 280538452)
    assert len(keys) == 301
    assert keys[0].endswith("280538152.rmp.lz4")
    assert keys[-1].endswith("280538452.rmp.lz4")


def test_raw_json_and_jsonl():
    recs, dec = p0e.parse_records(json.dumps({"type": "bookAction", "nested": {"oracleState": "SUPPRESSED"}}).encode())
    assert dec == "raw+json" and len(recs) == 1
    body = b'{"type":"a"}\n{"type":"b"}\n'
    recs, dec = p0e.parse_records(body)
    assert dec == "raw+jsonl" and len(recs) == 2


def test_lz4_json():
    import lz4.frame
    raw = json.dumps({"kind": "oracleCandidate", "value": 123}).encode()
    recs, dec = p0e.parse_records(lz4.frame.compress(raw))
    assert dec == "lz4+json" and len(recs) == 1


def test_msgpack_and_lz4_msgpack():
    import lz4.frame
    import msgpack
    raw = msgpack.packb({"type": "alpha"}, use_bin_type=True) + msgpack.packb({"type": "beta"}, use_bin_type=True)
    recs, dec = p0e.parse_records(raw)
    assert dec == "raw+msgpack" and len(recs) == 2
    recs2, dec2 = p0e.parse_records(lz4.frame.compress(raw))
    assert dec2 == "lz4+msgpack" and len(recs2) == 2


def test_schema_extraction_and_hip3_guard():
    key_paths, labels, oracle_paths, oracle_labels = set(), set(), set(), set()
    obj = {
        "outer": {
            "nativeOracleEnvelope": {"type": "validatorOraclePublish", "px": 999},
            "hip3": {"action": "perpDeploy.setOracle"},
        }
    }
    p0e.walk(obj, "", key_paths, labels, oracle_paths, oracle_labels)
    assert "outer.nativeOracleEnvelope" in oracle_paths
    assert "validatorOraclePublish" in oracle_labels
    assert p0e.hip3("perpDeploy.setOracle") is True
    assert p0e.hip3("validatorOraclePublish") is False


def test_unauthorized_execution_blocks_before_s3():
    os.environ.pop("CVFB_P0E_REQUESTER_PAYS_AUTHORIZED", None)
    try:
        p0e.load_auth(None)
    except p0e.ProbeBlocked as exc:
        assert "BLOCKED_NO_AUTHORIZATION" in str(exc)
    else:
        raise AssertionError("authorization guard unexpectedly passed")


def main():
    tests = [
        test_freeze_pin_and_target,
        test_derive_exact_301_keys,
        test_raw_json_and_jsonl,
        test_lz4_json,
        test_msgpack_and_lz4_msgpack,
        test_schema_extraction_and_hip3_guard,
        test_unauthorized_execution_blocks_before_s3,
    ]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"P0E_SYNTHETIC_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
