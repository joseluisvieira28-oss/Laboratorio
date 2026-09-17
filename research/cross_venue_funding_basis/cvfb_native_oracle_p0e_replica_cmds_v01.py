#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, io, json, os, re, sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

FREEZE_PATH = Path(__file__).with_name("CVFB_NATIVE_ORACLE_PROVENANCE_P0E_REPLICA_CMDS_REQUESTER_PAYS_FREEZE_V0.1.json")
EXPECTED_FREEZE_GIT_BLOB_SHA = "3f4e3a43636ea9a17a1c9cbc60e25410bff6a6fe"
AUTH_AMENDMENT_PATH = Path(__file__).with_name("CVFB_NATIVE_ORACLE_PROVENANCE_P0E_REQUESTER_PAYS_AUTHORIZATION_V0.1.json")
RUNTIME_CONFIRMATION = "I_EXPLICITLY_AUTHORIZE_CVFB_P0E_REQUESTER_PAYS"
BUCKET = "hl-mainnet-node-data"
ROOT_PREFIX = "replica_cmds/"
DATE_TOKEN = "20240901"
TYPE_KEYS = {"type", "action", "variant", "kind"}
HIP3_MARKERS = ("perpdeploy", "setoracle", "hip3", "hip-3")

class ProbeBlocked(RuntimeError):
    pass

def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def load_freeze() -> Dict[str, Any]:
    data = FREEZE_PATH.read_bytes()
    got = git_blob_sha1(data)
    if got != EXPECTED_FREEZE_GIT_BLOB_SHA:
        raise ProbeBlocked(f"FREEZE_BLOB_MISMATCH expected={EXPECTED_FREEZE_GIT_BLOB_SHA} got={got}")
    x = json.loads(data)
    assert x["status"] == "FROZEN_PRE_EXECUTION_NOT_AUTHORIZED"
    assert x["scientific_design_changed"] is False
    assert x["parent_primary_remains_closed"] is True
    assert x["authorization_gate"]["requester_pays_charges_authorized"] is False
    assert x["authorization_gate"]["aws_credentials_authorized"] is False
    assert x["authorization_gate"]["execution_authorized"] is False
    assert x["official_source"]["bucket"] == BUCKET
    assert x["frozen_target"]["center_height"] == 280538302
    assert x["frozen_target"]["scan_height_start"] == 280538152
    assert x["frozen_target"]["scan_height_end"] == 280538452
    assert x["frozen_target"]["scan_block_count"] == 301
    assert x["economic_outcomes_authorized"] is False
    assert x["2026_authorized"] is False
    return x

def load_auth(runtime_confirmation: Optional[str]) -> Dict[str, Any]:
    if runtime_confirmation != RUNTIME_CONFIRMATION:
        raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: runtime confirmation missing")
    if os.environ.get("CVFB_P0E_REQUESTER_PAYS_AUTHORIZED") != "YES":
        raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: env authorization missing")
    if not AUTH_AMENDMENT_PATH.exists():
        raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: immutable authorization amendment missing")
    x = json.loads(AUTH_AMENDMENT_PATH.read_text())
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
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        raise ProbeBlocked("BLOCKED_NO_AUTHORIZATION: AWS credentials missing")
    return x

def make_s3():
    try:
        import boto3
    except Exception as exc:
        raise ProbeBlocked(f"TECHNICAL_BLOCKED: boto3 unavailable: {exc}") from exc
    return boto3.client("s3")

class Counter:
    def __init__(self, caps: Dict[str, int]):
        self.max = {"list": int(caps["max_list_requests"]), "head": int(caps["max_head_requests"]), "get": int(caps["max_get_requests"])}
        self.n = {"list": 0, "head": 0, "get": 0}
    def hit(self, kind: str):
        self.n[kind] += 1
        if self.n[kind] > self.max[kind]:
            raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_COMPLETENESS_CAP: {kind} request cap")

def s3_list(s3, c: Counter, **kw):
    c.hit("list")
    return s3.list_objects_v2(Bucket=BUCKET, RequestPayer="requester", **kw)

def s3_head(s3, c: Counter, key: str):
    c.hit("head")
    return s3.head_object(Bucket=BUCKET, Key=key, RequestPayer="requester")

def s3_get(s3, c: Counter, key: str) -> bytes:
    c.hit("get")
    return s3.get_object(Bucket=BUCKET, Key=key, RequestPayer="requester")["Body"].read()

def resolve_date_prefix(s3, c: Counter) -> str:
    root = s3_list(s3, c, Prefix=ROOT_PREFIX, Delimiter="/", MaxKeys=1000)
    if root.get("IsTruncated"):
        raise ProbeBlocked("TECHNICAL_BLOCKED_COST_OR_COMPLETENESS_CAP: root listing truncated")
    starts = sorted(p["Prefix"] for p in root.get("CommonPrefixes", []))
    if not starts:
        raise ProbeBlocked("TECHNICAL_BLOCKED_TARGET_DATE_NOT_FOUND: no start prefixes")
    matches = []
    for start in starts:
        p = f"{start}{DATE_TOKEN}/"
        r = s3_list(s3, c, Prefix=p, MaxKeys=1)
        if r.get("KeyCount", 0) > 0 or r.get("Contents"):
            matches.append(p)
    if len(matches) == 0:
        raise ProbeBlocked("TECHNICAL_BLOCKED_TARGET_DATE_NOT_FOUND")
    if len(matches) != 1:
        raise ProbeBlocked("TECHNICAL_BLOCKED_AMBIGUOUS_START_TIME_PREFIX")
    return matches[0]

def resolve_suffix(s3, c: Counter, date_prefix: str, center: int) -> str:
    token = str(center)
    r = s3_list(s3, c, Prefix=date_prefix + token, MaxKeys=20)
    hits = []
    for x in r.get("Contents", []):
        key = x["Key"]
        tail = key[len(date_prefix):]
        if not tail.startswith(token):
            continue
        suffix = tail[len(token):]
        if "/" in suffix:
            continue
        if suffix and not re.fullmatch(r"(?:\.[A-Za-z0-9_-]+)+", suffix):
            continue
        hits.append(suffix)
    if len(hits) != 1:
        raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_COMPLETENESS_CAP: center key count={len(hits)}")
    return hits[0]

def derive_keys(date_prefix: str, suffix: str, start: int, end: int) -> List[str]:
    return [f"{date_prefix}{h}{suffix}" for h in range(start, end + 1)]

def preflight(s3, c: Counter, keys: Sequence[str], caps: Dict[str, int]):
    total, metas = 0, []
    for key in keys:
        try:
            h = s3_head(s3, c, key)
        except Exception as exc:
            raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_COMPLETENESS_CAP: missing key {key}") from exc
        size = int(h.get("ContentLength", -1))
        if size < 0 or size > int(caps["max_single_object_bytes"]):
            raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_COMPLETENESS_CAP: object size={size} key={key}")
        total += size
        if total > int(caps["max_total_compressed_object_bytes"]):
            raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_COMPLETENESS_CAP: total bytes={total}")
        metas.append({"key": key, "content_length": size, "etag": str(h.get("ETag", "")).strip('"')})
    return total, metas

def decompress(data: bytes):
    if data[:4] == b"\x04\x22\x4d\x18":
        try:
            import lz4.frame
        except Exception as exc:
            raise ProbeBlocked(f"TECHNICAL_BLOCKED: lz4 unavailable: {exc}") from exc
        return lz4.frame.decompress(data), "lz4"
    return data, "raw"

def parse_records(data: bytes):
    body, comp = decompress(data)
    try:
        s = body.decode("utf-8").strip()
    except UnicodeDecodeError:
        s = None
    if s is not None:
        if not s:
            return [], comp + "+json"
        try:
            return [json.loads(s)], comp + "+json"
        except json.JSONDecodeError:
            try:
                return [json.loads(line) for line in s.splitlines() if line.strip()], comp + "+jsonl"
            except json.JSONDecodeError:
                pass
    try:
        import msgpack
        return list(msgpack.Unpacker(io.BytesIO(body), raw=False, strict_map_key=False)), comp + "+msgpack"
    except Exception as exc:
        raise ProbeBlocked(f"TECHNICAL_BLOCKED: unsupported frozen decoder set: {type(exc).__name__}") from exc

def walk(obj: Any, path: str, key_paths: set, labels: set, oracle_paths: set, oracle_labels: set):
    if isinstance(obj, dict):
        for k, v in obj.items():
            ks = str(k)
            p = f"{path}.{ks}" if path else ks
            key_paths.add(p)
            if "oracle" in ks.lower():
                oracle_paths.add(p)
            if ks.lower() in TYPE_KEYS and isinstance(v, str) and len(v) <= 160:
                labels.add(v)
                if "oracle" in v.lower():
                    oracle_labels.add(v)
            walk(v, p, key_paths, labels, oracle_paths, oracle_labels)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, path + "[]", key_paths, labels, oracle_paths, oracle_labels)

def hip3(s: str) -> bool:
    low = s.lower()
    return any(m in low for m in HIP3_MARKERS)

def run_probe(out: Path, confirmation: Optional[str]):
    freeze = load_freeze()
    load_auth(confirmation)
    caps = freeze["pre_download_cost_caps"]
    c = Counter(caps)
    s3 = make_s3()
    date_prefix = resolve_date_prefix(s3, c)
    suffix = resolve_suffix(s3, c, date_prefix, freeze["frozen_target"]["center_height"])
    keys = derive_keys(date_prefix, suffix, freeze["frozen_target"]["scan_height_start"], freeze["frozen_target"]["scan_height_end"])
    if len(keys) != 301:
        raise ProbeBlocked("TECHNICAL_BLOCKED: key count mismatch")
    total, metas = preflight(s3, c, keys, caps)
    key_paths, labels, oracle_paths, oracle_labels = set(), set(), set(), set()
    objects, decoders = [], set()
    for m in metas:
        raw = s3_get(s3, c, m["key"])
        if len(raw) != m["content_length"]:
            raise ProbeBlocked(f"TECHNICAL_BLOCKED_COST_OR_COMPLETENESS_CAP: length mismatch {m['key']}")
        records, decoder = parse_records(raw)
        decoders.add(decoder)
        for rec in records:
            walk(rec, "", key_paths, labels, oracle_paths, oracle_labels)
        objects.append({"key": m["key"], "content_length": m["content_length"], "sha256": sha256(raw), "record_count": len(records), "decoder": decoder})
    non_hip3_paths = sorted(p for p in oracle_paths if not hip3(p))
    non_hip3_labels = sorted(x for x in oracle_labels if not hip3(x))
    decision = "PASS_NATIVE_ORACLE_SCHEMA_CANDIDATE" if (non_hip3_paths or non_hip3_labels) else "FAIL_NO_NATIVE_ORACLE_SCHEMA_VISIBLE"
    result = {
        "schema_version": "0.1",
        "recovery_id": freeze["recovery_id"],
        "stage": freeze["stage"],
        "status": "COMPLETE",
        "decision": decision,
        "freeze_git_blob_sha": EXPECTED_FREEZE_GIT_BLOB_SHA,
        "authorization_amendment_sha256": sha256(AUTH_AMENDMENT_PATH.read_bytes()),
        "source": {"bucket": BUCKET, "date_prefix": date_prefix, "suffix": suffix, "center_height": freeze["frozen_target"]["center_height"], "block_count": len(keys), "compressed_bytes": total, "request_counts": c.n},
        "objects": objects,
        "schema": {
            "key_paths": sorted(key_paths),
            "action_type_variant_kind_labels": sorted(labels),
            "non_hip3_oracle_candidate_paths": non_hip3_paths,
            "non_hip3_oracle_candidate_labels": non_hip3_labels,
            "decoders_used": sorted(decoders),
        },
        "market_numeric_values_emitted": False,
        "raw_object_bodies_emitted": False,
        "economic_outcomes_computed": False,
        "primary_replication_reopened": False,
        "2026_opened": False,
        "live_trading_authorized": False,
        "merge_to_main_authorized": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result

def plan():
    x = load_freeze()
    return {"status": "PLAN_ONLY", "execution_authorized": False, "freeze_git_blob_sha": EXPECTED_FREEZE_GIT_BLOB_SHA, "target": x["frozen_target"], "caps": x["pre_download_cost_caps"], "source": x["official_source"], "authorization_gate": x["authorization_gate"]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--out", default="CVFB_NATIVE_ORACLE_PROVENANCE_P0E_RECEIPT_V0.1.json")
    ap.add_argument("--authorization-confirmation")
    a = ap.parse_args()
    if a.plan == a.execute:
        print("choose exactly one of --plan/--execute", file=sys.stderr)
        return 2
    try:
        r = plan() if a.plan else run_probe(Path(a.out), a.authorization_confirmation)
    except ProbeBlocked as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except AssertionError as exc:
        print(f"FREEZE_GUARD_FAIL: {exc}", file=sys.stderr)
        return 4
    print(json.dumps({"status": r.get("status"), "decision": r.get("decision"), "execution_authorized": r.get("execution_authorized"), "freeze_git_blob_sha": r.get("freeze_git_blob_sha")}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
