#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

FREEZE_PATH = Path(__file__).with_name("CVFB_NATIVE_ORACLE_PROVENANCE_P0F_EXPLORER_BLOCKS_RAW_FREEZE_V0.1A.json")
AUTH_PATH = Path(__file__).with_name("CVFB_NATIVE_ORACLE_PROVENANCE_P0F_EXPLORER_BLOCKS_REQUESTER_PAYS_AUTHORIZATION_V0.1.json")
EXPECTED_FREEZE_GIT_BLOB_SHA = "3517c354b0ad6e7e79e7a85d0755127aa9c367ba"
RUNTIME_CONFIRMATION = "I_EXPLICITLY_AUTHORIZE_CVFB_P0F_EXPLORER_BLOCKS_REQUESTER_PAYS"
ENV_AUTH = "CVFB_P0F_EXPLORER_BLOCKS_REQUESTER_PAYS_AUTHORIZED"
BUCKET = "hl-mainnet-node-data"
TYPE_KEYS = {"type", "action", "variant", "kind"}
IDENTITY_CONTEXT_TOKENS = ("perpdeploy", "hip3", "hip-3", "deployer")

class ProbeBlocked(RuntimeError):
    pass

def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def normalized_git_blob_sha(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return git_blob_sha1(data)

def load_freeze() -> Dict[str, Any]:
    got = normalized_git_blob_sha(FREEZE_PATH)
    if got != EXPECTED_FREEZE_GIT_BLOB_SHA:
        raise ProbeBlocked(f"FREEZE_BLOB_MISMATCH expected={EXPECTED_FREEZE_GIT_BLOB_SHA} got={got}")
    x = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert x["status"] == "FROZEN_PRE_EXECUTION_NOT_AUTHORIZED"
    assert x["stage"] == "P0F_EXPLORER_BLOCKS_RAW_BOUNDED_REQUESTER_PAYS_SCHEMA_PROBE"
    assert x["parent_primary_remains_closed"] is True
    assert x["official_source"]["bucket"] == BUCKET
    assert x["official_source"]["prefix_family"] == "explorer_blocks"
    assert x["frozen_target"]["center_height"] == 280538302
    assert x["frozen_target"]["scan_height_start"] == 280538152
    assert x["frozen_target"]["scan_height_end"] == 280538452
    assert x["frozen_target"]["scan_block_count"] == 301
    assert len(x["deterministic_object_hypothesis"]["exact_keys"]) == 4
    assert x["economic_outcomes_authorized"] is False
    assert x["2026_authorized"] is False
    return x

def require_aws_credentials() -> None:
    try:
        import boto3
    except Exception as exc:
        raise ProbeBlocked(f"TECHNICAL_BLOCKED: boto3 unavailable: {exc}") from exc
    try:
        creds = boto3.Session().get_credentials()
        if creds is None:
            raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: AWS credentials unavailable")
        frozen = creds.get_frozen_credentials()
    except ProbeBlocked:
        raise
    except Exception as exc:
        raise ProbeBlocked(f"BLOCKED_NO_AUTHORIZATION: AWS credential resolution failed: {type(exc).__name__}") from exc
    if not frozen.access_key or not frozen.secret_key:
        raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: AWS credentials incomplete")

def load_auth(runtime_confirmation: Optional[str]) -> Dict[str, Any]:
    if runtime_confirmation != RUNTIME_CONFIRMATION:
        raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: runtime confirmation missing")
    if os.environ.get(ENV_AUTH) != "YES":
        raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: env authorization missing")
    if not AUTH_PATH.exists():
        raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: immutable P0F authorization amendment missing")
    x = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    required = {
        "status": "AUTHORIZED_BEFORE_FIRST_REQUESTER_PAYS_S3_REQUEST",
        "requester_pays_charges_authorized": True,
        "aws_credentials_authorized": True,
        "execution_authorized": True,
        "economic_outcomes_authorized": False,
        "primary_replication_reopened": False,
        "2026_authorized": False,
    }
    for k, v in required.items():
        if x.get(k) != v:
            raise ProbeBlocked(f"BLOCKED_NO_AUTHORIZATION: amendment {k} mismatch")
    if x.get("freeze_git_blob_sha") != EXPECTED_FREEZE_GIT_BLOB_SHA:
        raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: amendment freeze pin mismatch")
    if x.get("authorized_source") != "s3://hl-mainnet-node-data/explorer_blocks":
        raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: amendment source mismatch")
    require_aws_credentials()
    return x

def make_s3():
    import boto3
    return boto3.client("s3")

def decode_lz4_msgpack(data: bytes) -> List[Any]:
    try:
        import lz4.frame
        import msgpack
    except Exception as exc:
        raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_DECODER: dependency unavailable: {exc}") from exc
    if data[:4] != b"\x04\x22\x4d\x18":
        raise ProbeBlocked("TECHNICAL_BLOCKED_COST_OR_DECODER: expected LZ4 frame magic")
    try:
        body = lz4.frame.decompress(data)
        return list(msgpack.Unpacker(io.BytesIO(body), raw=False, strict_map_key=False))
    except Exception as exc:
        raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_DECODER: decode failed: {type(exc).__name__}") from exc

def walk(obj: Any, path: str, key_paths: set, labels: set, oracle_paths: set, oracle_labels: set, identity_markers: set):
    if isinstance(obj, dict):
        for k, v in obj.items():
            ks = str(k)
            p = f"{path}.{ks}" if path else ks
            key_paths.add(p)
            if "oracle" in ks.lower():
                oracle_paths.add(p)
            lowk = ks.lower()
            if any(t in lowk for t in IDENTITY_CONTEXT_TOKENS):
                identity_markers.add(p)
            if lowk in TYPE_KEYS and isinstance(v, str) and len(v) <= 200:
                labels.add(v)
                lv = v.lower()
                if "oracle" in lv:
                    oracle_labels.add(v)
                if any(t in lv for t in IDENTITY_CONTEXT_TOKENS):
                    identity_markers.add(v)
            walk(v, p, key_paths, labels, oracle_paths, oracle_labels, identity_markers)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, path + "[]", key_paths, labels, oracle_paths, oracle_labels, identity_markers)

def progress(msg: str) -> None:
    print(f"P0F_PROGRESS {msg}", file=sys.stderr, flush=True)

def run_probe(out: Path, confirmation: Optional[str]) -> Dict[str, Any]:
    progress("FREEZE_CHECK")
    freeze = load_freeze()
    progress("AUTH_CHECK")
    load_auth(confirmation)
    progress("AUTH_OK")
    caps = freeze["cost_and_completeness_caps"]
    keys = freeze["deterministic_object_hypothesis"]["exact_keys"]

    s3 = make_s3()
    metas = []
    total = 0

    # HEAD all exact frozen objects before any GET.
    for idx, key in enumerate(keys, start=1):
        progress(f"HEAD_{idx}_OF_{len(keys)}")
        try:
            h = s3.head_object(Bucket=BUCKET, Key=key, RequestPayer="requester")
        except Exception as exc:
            raise ProbeBlocked(f"TECHNICAL_BLOCKED_SOURCE_COVERAGE: missing_or_unreadable_key={key} error={type(exc).__name__}") from exc
        size = int(h.get("ContentLength", -1))
        if size < 0 or size > int(caps["max_single_object_bytes"]):
            raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_DECODER: single_object_bytes={size} key={key}")
        total += size
        if total > int(caps["max_total_compressed_object_bytes"]):
            raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_DECODER: total_compressed_bytes={total}")
        metas.append({"key": key, "content_length": size, "etag": str(h.get("ETag", "")).strip('"')})

    key_paths, labels, oracle_paths, oracle_labels, identity_markers = set(), set(), set(), set(), set()
    objects = []
    for idx, m in enumerate(metas, start=1):
        progress(f"GET_{idx}_OF_{len(metas)}")
        raw = s3.get_object(Bucket=BUCKET, Key=m["key"], RequestPayer="requester")["Body"].read()
        if len(raw) != m["content_length"]:
            raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_DECODER: length mismatch key={m['key']}")
        progress(f"DECODE_{idx}_OF_{len(metas)}")
        records = decode_lz4_msgpack(raw)
        for rec in records:
            walk(rec, "", key_paths, labels, oracle_paths, oracle_labels, identity_markers)
        objects.append({
            "key": m["key"],
            "content_length": m["content_length"],
            "sha256": sha256(raw),
            "record_count": len(records),
            "decoder": "lz4+msgpack",
        })

    decision = (
        "PASS_ORACLE_SCHEMA_CANDIDATE_REQUIRES_IDENTITY_AUDIT"
        if (oracle_paths or oracle_labels)
        else "FAIL_NO_ORACLE_SCHEMA_VISIBLE"
    )

    result = {
        "schema_version": "0.1A",
        "recovery_id": freeze["recovery_id"],
        "stage": freeze["stage"],
        "status": "COMPLETE",
        "decision": decision,
        "freeze_git_blob_sha": EXPECTED_FREEZE_GIT_BLOB_SHA,
        "authorization_amendment_sha256": sha256(AUTH_PATH.read_bytes()),
        "source": {
            "bucket": BUCKET,
            "exact_keys": keys,
            "object_count": len(objects),
            "compressed_bytes": total,
            "head_requests": len(metas),
            "get_requests": len(objects),
            "list_requests": 0,
        },
        "objects": objects,
        "schema": {
            "key_paths": sorted(key_paths),
            "action_type_variant_kind_labels": sorted(labels),
            "oracle_candidate_paths": sorted(oracle_paths),
            "oracle_candidate_labels": sorted(oracle_labels),
            "identity_context_markers": sorted(identity_markers),
        },
        "raw_object_bodies_emitted": False,
        "market_numeric_values_emitted": False,
        "oracle_numeric_values_emitted": False,
        "economic_outcomes_computed": False,
        "primary_replication_reopened": False,
        "2026_opened": False,
        "live_trading_authorized": False,
        "merge_to_main_authorized": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    progress("RECEIPT_WRITTEN")
    return result

def plan() -> Dict[str, Any]:
    x = load_freeze()
    return {
        "status": "PLAN_ONLY",
        "execution_authorized": False,
        "freeze_git_blob_sha": EXPECTED_FREEZE_GIT_BLOB_SHA,
        "target": x["frozen_target"],
        "exact_keys": x["deterministic_object_hypothesis"]["exact_keys"],
        "caps": x["cost_and_completeness_caps"],
        "authorization_gate": x["authorization_gate"],
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--out", default="CVFB_NATIVE_ORACLE_PROVENANCE_P0F_RECEIPT_V0.1A.json")
    ap.add_argument("--authorization-confirmation")
    a = ap.parse_args()
    if a.plan == a.execute:
        print("choose exactly one of --plan/--execute", file=sys.stderr)
        return 2
    try:
        r = plan() if a.plan else run_probe(Path(a.out), a.authorization_confirmation)
    except ProbeBlocked as exc:
        print(f"P0F_BLOCKED {exc}", file=sys.stderr, flush=True)
        if a.execute:
            blocked = {
                "schema_version": "0.1A",
                "stage": "P0F_EXPLORER_BLOCKS_RAW_BOUNDED_REQUESTER_PAYS_SCHEMA_PROBE",
                "status": "TECHNICAL_BLOCKED",
                "decision": str(exc).split(":", 1)[0],
                "detail": str(exc),
                "freeze_git_blob_sha": EXPECTED_FREEZE_GIT_BLOB_SHA,
                "raw_object_bodies_emitted": False,
                "market_numeric_values_emitted": False,
                "oracle_numeric_values_emitted": False,
                "economic_outcomes_computed": False,
                "primary_replication_reopened": False,
                "2026_opened": False,
                "live_trading_authorized": False,
                "merge_to_main_authorized": False,
            }
            try:
                p = Path(a.out)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                progress("BLOCKED_RECEIPT_WRITTEN")
            except Exception as write_exc:
                print(f"P0F_BLOCKED_RECEIPT_WRITE_FAILED {type(write_exc).__name__}", file=sys.stderr, flush=True)
        return 3
    except AssertionError as exc:
        print(f"FREEZE_GUARD_FAIL: {exc}", file=sys.stderr)
        return 4
    print(json.dumps({
        "status": r.get("status"),
        "decision": r.get("decision"),
        "execution_authorized": r.get("execution_authorized"),
        "freeze_git_blob_sha": r.get("freeze_git_blob_sha"),
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
