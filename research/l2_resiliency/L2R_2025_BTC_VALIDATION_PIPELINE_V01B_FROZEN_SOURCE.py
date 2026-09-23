#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
import math
import os
import random
import re
import shutil
import struct
import sys
import time
import zipfile
from collections import Counter, defaultdict, deque
from pathlib import Path

import boto3
import lz4.frame
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

LAB_ID = "L2-RESILIENCY-001"
PROTOCOL = "INDEPENDENT_2025_VALIDATION_HOLDOUT_PROTOCOL_V0.1"
YEAR = 2025
BUCKET = "hyperliquid-archive"
ASSET = "BTC"
EXPECTED_HOURS = 365 * 24
MIN_HOURLY_COVERAGE_PCT = 95.0
MIN_ELIGIBLE_DAYS = 300
HORIZONS_MS = (1000, 5000, 15000, 60000)
CELLS = (
    ("R1_Y5", 1000, 5000),
    ("R1_Y15", 1000, 15000),
    ("R1_Y60", 1000, 60000),
    ("R5_Y15", 5000, 15000),
    ("R5_Y60", 5000, 60000),
    ("R15_Y60", 15000, 60000),
)
MAX_LATENESS_NS = 1_100_000_000
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260919
READ_CHUNK = 1024 * 1024
CANONICAL_MANIFEST_SHA256 = "767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3"
CANONICAL_PRESENT_OBJECTS = 8400
CANONICAL_COMPRESSED_BYTES = 8975275014
SOURCE_CLOCK_AMENDMENT = "SOURCE_CLOCK_NORMALIZATION_AMENDMENT_V0.1B"
KEY_RE = re.compile(r"^market_data/(2025\d{4})/([0-9]|1[0-9]|2[0-3])/l2Book/BTC\.lz4$")
ISO_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?Z?$")

class PipelineFailure(RuntimeError):
    pass

def default_base() -> Path:
    return Path.home() / "Desktop" / "L2R_2025_BTC_VALIDATION_LOCAL"

def raw_root(base: Path) -> Path:
    return base / "HL_L2R_2025_BTC_RAW_V0_1"

def evidence_root(base: Path) -> Path:
    return base / "_EVIDENCE_2025_VALIDATION_V0_1"

def row_local_path(base: Path, row) -> Path:
    # Technical portability only: canonical manifest was authored on Windows.
    rel = str(row["local_relpath"]).replace("\\", "/")
    return raw_root(base) / Path(*rel.split("/"))

def ensure_dirs(base: Path):
    raw_root(base).mkdir(parents=True, exist_ok=True)
    evidence_root(base).mkdir(parents=True, exist_ok=True)

def s3_client():
    cfg = Config(
        retries={"max_attempts": 10, "mode": "adaptive"},
        connect_timeout=30,
        read_timeout=180,
        max_pool_connections=32,
    )
    return boto3.client("s3", config=cfg)

def all_2025_keys():
    start = dt.datetime(YEAR, 1, 1, tzinfo=dt.timezone.utc)
    for i in range(EXPECTED_HOURS):
        t = start + dt.timedelta(hours=i)
        yield f"market_data/{t:%Y%m%d}/{t.hour}/l2Book/{ASSET}.lz4"

def key_hour(key: str) -> dt.datetime:
    m = KEY_RE.fullmatch(key)
    if not m:
        raise PipelineFailure(f"illegal/protected key: {key}")
    ymd, hs = m.groups()
    x = dt.datetime.strptime(ymd + f"{int(hs):02d}", "%Y%m%d%H").replace(tzinfo=dt.timezone.utc)
    if x.year != YEAR:
        raise PipelineFailure(f"protected year key: {key}")
    return x

def key_bounds_ns(key: str):
    x = key_hour(key)
    s = int(x.timestamp()) * 1_000_000_000
    return s, s + 3_600_000_000_000

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 * READ_CHUNK), b""):
            h.update(b)
    return h.hexdigest()

def hashes_file(path: Path):
    h256 = hashlib.sha256()
    hmd5 = hashlib.md5()
    total = 0
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 * READ_CHUNK), b""):
            total += len(b)
            h256.update(b)
            hmd5.update(b)
    return h256.hexdigest(), hmd5.hexdigest(), total

def ordinary_etag(etag: str) -> bool:
    e = str(etag).strip().strip('"').lower()
    return len(e) == 32 and "-" not in e and all(c in "0123456789abcdef" for c in e)

def inventory_one(key: str):
    c = s3_client()
    try:
        r = c.head_object(Bucket=BUCKET, Key=key, RequestPayer="requester")
        return {
            "key": key,
            "status": "PRESENT",
            "content_length": int(r["ContentLength"]),
            "etag": str(r.get("ETag", "")).strip().strip('"').lower(),
            "last_modified": r.get("LastModified").isoformat() if r.get("LastModified") else "",
            "error": "",
        }
    except ClientError as e:
        code = str(e.response.get("Error", {}).get("Code", ""))
        status = int(e.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0) or 0)
        if code in {"404", "NoSuchKey", "NotFound"} or status == 404:
            return {"key": key, "status": "MISSING", "content_length": 0, "etag": "", "last_modified": "", "error": ""}
        return {"key": key, "status": "ERROR", "content_length": 0, "etag": "", "last_modified": "", "error": f"{code}:{str(e)[:500]}"}
    except Exception as e:
        return {"key": key, "status": "ERROR", "content_length": 0, "etag": "", "last_modified": "", "error": f"{type(e).__name__}:{str(e)[:500]}"}

def credentials_preflight():
    """Fail fast on expired AWS login/session before issuing thousands of archive requests."""
    try:
        boto3.client("sts", config=Config(retries={"max_attempts": 2, "mode": "standard"})).get_caller_identity()
        return True
    except Exception as e:
        msg = f"{type(e).__name__}: {str(e)}"
        if "LoginRefreshRequired" in msg or "expired" in msg.lower() or "credentials" in msg.lower():
            raise PipelineFailure("SOURCE_AUTH_BLOCKED: AWS session is not valid. Run 'aws login' in PowerShell, then rerun this V0.1.1 package.")
        raise PipelineFailure(f"SOURCE_AUTH_BLOCKED: AWS credential preflight failed: {msg[:1000]}")

def stage_inventory(base: Path, workers: int):
    ev = evidence_root(base)
    inv_csv = ev / "L2_RESILIENCY_001_2025_BTC_SOURCE_INVENTORY_V0_1.csv"
    receipt = ev / "L2_RESILIENCY_001_2025_BTC_SOURCE_INVENTORY_RECEIPT_V0_1.json"
    keys = list(all_2025_keys())
    keyset = set(keys)

    prior = {}
    resume_errors = []
    if inv_csv.exists():
        try:
            with inv_csv.open("r", encoding="utf-8-sig", newline="") as f:
                old = list(csv.DictReader(f))
            if len(old) == EXPECTED_HOURS and {r.get("key","") for r in old} == keyset:
                for r in old:
                    st = str(r.get("status","")).upper()
                    if st in {"PRESENT","MISSING"}:
                        prior[r["key"]] = {
                            "key":r["key"],"status":st,
                            "content_length":int(r.get("content_length") or 0),
                            "etag":str(r.get("etag") or ""),
                            "last_modified":str(r.get("last_modified") or ""),
                            "error":"",
                        }
                    else:
                        resume_errors.append(r["key"])
            else:
                prior = {}
                resume_errors = []
        except Exception:
            prior = {}
            resume_errors = []

    if prior:
        probe_keys = [k for k in keys if k not in prior]
        print(f"\n[1/4] SOURCE INVENTORY RESUME V0.1.1 — reusing {len(prior):,} resolved keys; probing {len(probe_keys):,} unresolved/error keys")
    else:
        probe_keys = keys
        print("\n[1/4] SOURCE INVENTORY V0.1.1 — 8,760 hourly keys, HEAD only")

    if probe_keys:
        credentials_preflight()

    rows = list(prior.values())
    abort_auth = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(workers * 4, 24))) as ex:
        futs = {ex.submit(inventory_one, k): k for k in probe_keys}
        done = 0
        for fut in concurrent.futures.as_completed(futs):
            r = fut.result()
            rows.append(r)
            done += 1
            if r.get("status") == "ERROR":
                err = str(r.get("error",""))
                if "LoginRefreshRequired" in err or "session has expired" in err.lower():
                    abort_auth = err
            if done % 250 == 0 or done == len(probe_keys):
                print(f"  inventory probe {done:,}/{len(probe_keys):,}", flush=True)

    # If auth died during the probe, preserve all new resolved evidence and fail explicitly.
    by_key = {r["key"]: r for r in rows}
    rows = [by_key.get(k, {"key":k,"status":"ERROR","content_length":0,"etag":"","last_modified":"","error":"UNRESOLVED"}) for k in keys]
    rows.sort(key=lambda r: key_hour(r["key"]))

    with inv_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["key","status","content_length","etag","last_modified","error"])
        w.writeheader(); w.writerows(rows)

    counts = Counter(r["status"] for r in rows)
    coverage = 100.0 * counts["PRESENT"] / EXPECTED_HOURS
    total_bytes = sum(int(r["content_length"]) for r in rows if r["status"] == "PRESENT")
    errors = [r for r in rows if r["status"] == "ERROR"]

    if abort_auth:
        classification = "SOURCE_AUTH_BLOCKED"
    else:
        classification = (
            "SOURCE_INVENTORY_PASS"
            if not errors and coverage >= MIN_HOURLY_COVERAGE_PCT
            else "SOURCE_INVENTORY_ERROR" if errors else "VALIDATION_BLOCKED_SOURCE_COVERAGE"
        )

    obj = {
        "schema_version":"0.1.1","lab_id":LAB_ID,"year":YEAR,
        "classification":classification,
        "expected_hours":EXPECTED_HOURS,
        "present_hours":counts["PRESENT"],
        "missing_hours":counts["MISSING"],
        "error_hours":counts["ERROR"],
        "coverage_pct":coverage,
        "min_required_coverage_pct":MIN_HOURLY_COVERAGE_PCT,
        "present_compressed_bytes":total_bytes,
        "inventory_csv_sha256":sha256_file(inv_csv),
        "resume_reused_resolved_keys":len(prior),
        "resume_probed_keys":len(probe_keys),
        "source":"Hyperliquid official requester-pays S3 archive",
        "outcomes_computed":False,
        "access_2026":False,
    }
    receipt.write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(f"  present={counts['PRESENT']:,} missing={counts['MISSING']:,} errors={counts['ERROR']:,} coverage={coverage:.6f}%")
    print(f"  classification={classification}")
    if classification != "SOURCE_INVENTORY_PASS":
        make_bundle(base)
        if classification == "SOURCE_AUTH_BLOCKED":
            raise PipelineFailure("SOURCE_AUTH_BLOCKED: run 'aws login' in PowerShell, then rerun the same V0.1.1 package. Resolved inventory evidence has been preserved.")
        raise PipelineFailure(classification)
    return rows, obj

def local_path_for(base: Path, key: str) -> Path:
    return raw_root(base) / Path(*key.split("/"))

def download_one(args):
    base_str, row = args
    base = Path(base_str)
    key = row["key"]
    size = int(row["content_length"])
    etag = str(row["etag"]).lower()
    path = local_path_for(base, key)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and path.stat().st_size == size:
        sha, md5, actual = hashes_file(path)
        if actual == size and (not ordinary_etag(etag) or md5 == etag):
            return {"key":key,"status":"VERIFIED_EXISTING","content_length":size,"etag":etag,"sha256":sha,"md5":md5,"local_relpath":str(path.relative_to(raw_root(base)))}

    c = s3_client()
    part = path.with_suffix(path.suffix + ".part")
    if part.exists():
        part.unlink()
    h256 = hashlib.sha256(); hmd5 = hashlib.md5(); total = 0
    try:
        r = c.get_object(Bucket=BUCKET, Key=key, RequestPayer="requester")
        body = r["Body"]
        try:
            with part.open("wb") as f:
                while True:
                    b = body.read(8 * READ_CHUNK)
                    if not b: break
                    f.write(b)
                    total += len(b)
                    h256.update(b); hmd5.update(b)
        finally:
            body.close()
        if total != size:
            raise PipelineFailure(f"download size mismatch {key}: {total}!={size}")
        sha = h256.hexdigest(); md5 = hmd5.hexdigest()
        if ordinary_etag(etag) and md5 != etag:
            raise PipelineFailure(f"ETag/MD5 mismatch {key}")
        os.replace(part, path)
        return {"key":key,"status":"DOWNLOADED_VERIFIED","content_length":size,"etag":etag,"sha256":sha,"md5":md5,"local_relpath":str(path.relative_to(raw_root(base)))}
    except Exception:
        if part.exists():
            part.unlink()
        raise

def stage_acquisition(base: Path, inv_rows, workers: int):
    ev = evidence_root(base)
    manifest = ev / "L2_RESILIENCY_001_2025_BTC_RAW_MANIFEST_V0_1.csv"
    receipt = ev / "L2_RESILIENCY_001_2025_BTC_BODY_ACQUISITION_RECEIPT_V0_1.json"
    present = [r for r in inv_rows if r["status"] == "PRESENT"]

    print("\n[2/4] RAW BODY ACQUISITION — requester-pays GET")
    print("  Existing verified files are reused; interrupted .part files are discarded.")
    out = []
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(workers * 2, 8))) as ex:
        futs = {ex.submit(download_one, (str(base), r)): r["key"] for r in present}
        done = 0
        for fut in concurrent.futures.as_completed(futs):
            key = futs[fut]
            try:
                out.append(fut.result())
            except Exception as e:
                failed.append({"key":key,"error":f"{type(e).__name__}:{str(e)[:1000]}"})
            done += 1
            if done % 250 == 0 or done == len(present):
                print(f"  acquisition {done:,}/{len(present):,} | failed={len(failed)}", flush=True)

    out.sort(key=lambda r: key_hour(r["key"]))
    with manifest.open("w", encoding="utf-8-sig", newline="") as f:
        fields=["key","status","content_length","etag","sha256","md5","local_relpath"]
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(out)

    ok = len(out) == len(present) and not failed
    obj = {
        "schema_version":"0.1","lab_id":LAB_ID,"year":YEAR,
        "classification":"SOURCE_BODY_ACQUISITION_PASS" if ok else "SOURCE_BODY_ACQUISITION_FAIL_CLOSED",
        "present_objects_expected":len(present),
        "objects_verified":len(out),
        "failed_objects":len(failed),
        "failure_sample":failed[:20],
        "compressed_bytes_verified":sum(int(r["content_length"]) for r in out),
        "manifest_sha256":sha256_file(manifest),
        "outcomes_computed":False,
        "access_2026":False,
    }
    receipt.write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(f"  classification={obj['classification']} | objects={len(out):,} | failed={len(failed)}")
    if not ok:
        make_bundle(base)
        raise PipelineFailure(obj["classification"])
    return out, obj

def parse_env_ns(s: str) -> int:
    if not isinstance(s, str):
        raise PipelineFailure("envelope time not string")
    m=ISO_RE.fullmatch(s.strip())
    if not m:
        raise PipelineFailure(f"invalid envelope time: {s}")
    base, frac = m.groups()
    d=dt.datetime.strptime(base,"%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    ns=((frac or "")+"000000000")[:9]
    return int(d.timestamp())*1_000_000_000 + int(ns)

def finite_num(v, name):
    if isinstance(v, bool):
        raise PipelineFailure(f"boolean {name}")
    try: x=float(v)
    except Exception as e: raise PipelineFailure(f"non-numeric {name}") from e
    if not math.isfinite(x):
        raise PipelineFailure(f"non-finite {name}")
    return x

def extract_state(obj):
    if not isinstance(obj, dict) or "time" not in obj or "ver_num" not in obj or "raw" not in obj:
        raise PipelineFailure("missing top-level time/ver_num/raw")
    if isinstance(obj.get("ver_num"), bool) or not isinstance(obj.get("ver_num"), int):
        raise PipelineFailure("ver_num not int")
    raw=obj["raw"]
    if not isinstance(raw, dict) or raw.get("channel")!="l2Book":
        raise PipelineFailure("wrong raw/channel")
    data=raw.get("data")
    if not isinstance(data, dict) or data.get("coin")!="BTC":
        raise PipelineFailure("wrong data/coin")
    payload=data.get("time")
    if isinstance(payload,bool) or not isinstance(payload,int):
        raise PipelineFailure("payload time not int")
    levels=data.get("levels")
    if not isinstance(levels,list) or len(levels)!=2:
        raise PipelineFailure("levels not two sides")
    bids, asks = levels
    if len(bids)<5 or len(asks)<5:
        raise PipelineFailure("fewer than five levels")
    bid_px=[]; ask_px=[]; bid_sz5=[]; ask_sz5=[]
    for side, pxs, szs in ((bids,bid_px,bid_sz5),(asks,ask_px,ask_sz5)):
        for i,lvl in enumerate(side):
            if not isinstance(lvl,dict):
                raise PipelineFailure("level not object")
            p=finite_num(lvl.get("px"),"px")
            s=finite_num(lvl.get("sz"),"sz")
            n=lvl.get("n")
            if p<=0 or s<0 or isinstance(n,bool) or not isinstance(n,int) or n<0:
                raise PipelineFailure("invalid level fields")
            pxs.append(p)
            if i<5: szs.append(s)
    if not all(bid_px[i]>bid_px[i+1] for i in range(4)):
        raise PipelineFailure("bid top5 ordering")
    if not all(ask_px[i]<ask_px[i+1] for i in range(4)):
        raise PipelineFailure("ask top5 ordering")
    if bid_px[0]>=ask_px[0]:
        raise PipelineFailure("locked/crossed book")
    return {
        "payload_ms":payload,
        "bid_best":bid_px[0],"ask_best":ask_px[0],
        "bid_prices_all":tuple(bid_px),"ask_prices_all":tuple(ask_px),
        "bid_depth5":sum(bid_sz5),"ask_depth5":sum(ask_sz5),
        "mid":(bid_px[0]+ask_px[0])/2.0,
        "bid_levels":len(bids),"ask_levels":len(asks),
    }

def build_segments(rows):
    ordered=sorted(rows,key=lambda r:key_hour(r["key"]))
    out=[]; cur=[]; prev=None
    for r in ordered:
        h=key_hour(r["key"])
        if prev is None or h == prev + dt.timedelta(hours=1):
            cur.append(r)
        else:
            out.append(cur); cur=[r]
        prev=h
    if cur: out.append(cur)
    return out

def schema_segment(args):
    sid, rows, base_str = args
    base=Path(base_str)
    totals=Counter()
    obj_rows=[]
    stale_rows=[]
    future_rows=[]
    last_env=None
    last_payload=None
    min_bid=10**9; min_ask=10**9

    for row in rows:
        key=row["key"]
        path=row_local_path(base,row)
        start_ns,end_ns=key_bounds_ns(key)
        expected_size=int(row["content_length"])
        expected_sha=row["sha256"].lower()
        expected_md5=row["md5"].lower()
        expected_etag=row["etag"].lower()
        h256=hashlib.sha256(); hmd5=hashlib.md5(); actual=0
        dec=lz4.frame.LZ4FrameDecompressor()
        pending=b""; ri=0; obj_records=0; obj_stale=0; obj_equal=0; obj_future=0

        def proc(line):
            nonlocal last_env,last_payload,ri,obj_records,obj_stale,obj_equal,obj_future,min_bid,min_ask
            ri+=1; obj_records+=1; totals["records"]+=1
            o=json.loads(line)
            env=parse_env_ns(o["time"])
            if not (start_ns<=env<end_ns):
                raise PipelineFailure(f"{key}: envelope outside key hour")
            st=extract_state(o)
            min_bid=min(min_bid,st["bid_levels"]); min_ask=min(min_ask,st["ask_levels"])
            p=st["payload_ms"]
            if last_env is not None and env < last_env:
                raise PipelineFailure(f"{key}: envelope backwards")
            future = p*1_000_000 > env
            last_env=env
            if future:
                totals["future_clock_skew"]+=1; obj_future+=1
            if last_payload is not None and p < last_payload:
                totals["stale"]+=1; obj_stale+=1
                stale_rows.append({
                    "segment_id":sid,"key":key,"record_index_1based":ri,
                    "envelope_ns":env,"payload_ms":p,
                    "last_accepted_payload_ms":last_payload,
                    "rewind_ms":last_payload-p
                })
                if future:
                    future_rows.append({
                        "segment_id":sid,"key":key,"record_index_1based":ri,
                        "envelope_ns":env,"payload_ms":p,
                        "future_ahead_ns":p*1_000_000-env,
                        "normalization_action":"STALE_QUARANTINED_NO_WATERMARK_ADVANCE"
                    })
                return
            if last_payload is not None and p == last_payload:
                totals["equal"]+=1; obj_equal+=1
            if future:
                future_rows.append({
                    "segment_id":sid,"key":key,"record_index_1based":ri,
                    "envelope_ns":env,"payload_ms":p,
                    "future_ahead_ns":p*1_000_000-env,
                    "normalization_action":"ACCEPTED_ENVELOPE_ORDER_NO_WATERMARK_ADVANCE"
                })
            else:
                last_payload=p
            totals["accepted"]+=1

        with path.open("rb") as f:
            while True:
                b=f.read(READ_CHUNK)
                if not b: break
                actual+=len(b); h256.update(b); hmd5.update(b)
                out=dec.decompress(b)
                if not out: continue
                pending+=out
                parts=pending.split(b"\n"); pending=parts.pop()
                for line in parts:
                    if line.strip(): proc(line)
        if pending.strip(): proc(pending)
        if not dec.eof:
            raise PipelineFailure(f"{key}: incomplete LZ4")
        if actual!=expected_size or h256.hexdigest()!=expected_sha or hmd5.hexdigest()!=expected_md5:
            raise PipelineFailure(f"{key}: byte/hash binding mismatch")
        if ordinary_etag(expected_etag) and expected_md5 != expected_etag:
            raise PipelineFailure(f"{key}: ETag/MD5 mismatch")
        totals["objects"]+=1
        obj_rows.append({
            "segment_id":sid,"key":key,"status":"PASS",
            "records":obj_records,"stale_late_payload":obj_stale,
            "equal_payload_timestamp":obj_equal,"future_payload_clock_skew":obj_future,
        })

    return {
        "segment_id":sid,"start_key":rows[0]["key"],"end_key":rows[-1]["key"],"hours":len(rows),
        "totals":dict(totals),"objects":obj_rows,"stale":stale_rows,"future":future_rows,
        "min_bid_levels":min_bid,"min_ask_levels":min_ask,
    }

def stage_schema(base: Path, manifest_rows, workers: int):
    ev=evidence_root(base)
    receipt=ev/"L2_RESILIENCY_001_2025_SCHEMA_NORMALIZED_RECEIPT_V0_1.json"
    obj_csv=ev/"L2_RESILIENCY_001_2025_SCHEMA_OBJECT_AUDIT_V0_1.csv"
    stale_csv=ev/"L2_RESILIENCY_001_2025_STALE_LATE_PAYLOAD_LEDGER_V0_1B.csv"
    future_csv=ev/"L2_RESILIENCY_001_2025_FUTURE_PAYLOAD_NORMALIZATION_LEDGER_V0_1B.csv"
    segments=build_segments(manifest_rows)
    print(f"\n[3/4] FULL SOURCE/SCHEMA AUDIT — segments={len(segments)}")

    results=[]
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=max(1,min(workers,4))) as ex:
            futs=[ex.submit(schema_segment,(i+1,seg,str(base))) for i,seg in enumerate(segments)]
            for fut in concurrent.futures.as_completed(futs):
                r=fut.result(); results.append(r)
                print(f"  segment {r['segment_id']} PASS | records={r['totals'].get('records',0):,} stale={r['totals'].get('stale',0):,}", flush=True)
    except Exception as e:
        obj={"schema_version":"0.1","lab_id":LAB_ID,"year":YEAR,
             "classification":"SOURCE_SCHEMA_FAIL_CLOSED","failure":f"{type(e).__name__}: {str(e)[:2000]}",
             "outcomes_computed":False,"access_2026":False}
        receipt.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        make_bundle(base)
        raise PipelineFailure(obj["classification"])

    results.sort(key=lambda r:r["segment_id"])
    totals=Counter(); all_obj=[]; all_stale=[]; all_future=[]
    min_bid=min(r["min_bid_levels"] for r in results)
    min_ask=min(r["min_ask_levels"] for r in results)
    for r in results:
        totals.update(r["totals"]); all_obj+=r["objects"]; all_stale+=r["stale"]; all_future+=r["future"]

    with obj_csv.open("w",encoding="utf-8-sig",newline="") as f:
        fields=["segment_id","key","status","records","stale_late_payload","equal_payload_timestamp","future_payload_clock_skew"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(all_obj)
    with stale_csv.open("w",encoding="utf-8-sig",newline="") as f:
        fields=["segment_id","key","record_index_1based","envelope_ns","payload_ms","last_accepted_payload_ms","rewind_ms"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(all_stale)
    with future_csv.open("w",encoding="utf-8-sig",newline="") as f:
        fields=["segment_id","key","record_index_1based","envelope_ns","payload_ms","future_ahead_ns","normalization_action"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(all_future)

    obj={
        "schema_version":"0.1","lab_id":LAB_ID,"year":YEAR,
        "classification":"SOURCE_SCHEMA_NORMALIZED_PASS",
        "objects":int(totals["objects"]),
        "records":int(totals["records"]),
        "accepted_states":int(totals["accepted"]),
        "stale_late_payload":int(totals["stale"]),
        "equal_payload_timestamp":int(totals["equal"]),
        "future_payload_clock_skew":int(totals["future_clock_skew"]),
        "source_clock_amendment":SOURCE_CLOCK_AMENDMENT,
        "segments":len(results),
        "min_bid_levels_global":min_bid,
        "min_ask_levels_global":min_ask,
        "object_audit_sha256":sha256_file(obj_csv),
        "stale_ledger_sha256":sha256_file(stale_csv),
        "future_clock_ledger_sha256":sha256_file(future_csv),
        "outcomes_computed":False,
        "access_2026":False,
    }
    receipt.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"  SOURCE_SCHEMA_NORMALIZED_PASS | objects={totals['objects']:,} records={totals['records']:,} stale={totals['stale']:,}")
    return results, obj

def anchor_date(env_ns: int):
    return dt.datetime.fromtimestamp(env_ns//1_000_000_000,tz=dt.timezone.utc).date().isoformat()

def add_daily(daily,key,response,rr,side):
    v=daily.setdefault(key,[0,0.0,0.0,0,0.0,0,0.0])
    v[0]+=1; v[1]+=response; v[2]+=rr
    if side=="ASK": v[3]+=1; v[4]+=response
    else: v[5]+=1; v[6]+=response

def validation_segment(args):
    sid, rows, base_str = args
    base=Path(base_str)
    last_env=None; last_payload=None; prev_state=None
    totals=Counter()
    timing_avail=Counter(); timing_late=Counter(); timing_end=Counter()
    active={}; queues={h:deque() for h in HORIZONS_MS}; eid_next=0
    daily={}; cell_counts={c[0]:Counter() for c in CELLS}

    def finalize_event(ev):
        pre=ev["pre_depth"]
        for cell,rh,yh in CELLS:
            cc=cell_counts[cell]; cc["anchors_total"]+=1
            if pre<=0:
                cc["zero_pre_depth"]+=1; continue
            r=ev["h"].get(rh); y=ev["h"].get(yh)
            if r is None or y is None:
                cc["timing_missing"]+=1; continue
            depth_r=r["ask_depth5"] if ev["side"]=="ASK" else r["bid_depth5"]
            rr=depth_r/pre
            group="WEAK" if depth_r<pre else "STRONG"
            response=ev["direction"]*10000.0*(y["mid"]/r["mid"]-1.0)
            cc["valid"]+=1; cc[group.lower()]+=1
            cc[f"{group.lower()}_sum_response"]+=response
            cc[f"{group.lower()}_sum_rr"]+=rr
            add_daily(daily,(ev["date"],cell,group),response,rr,ev["side"])

    def resolve(eid,h,state,why=None):
        ev=active[eid]
        if h in ev["resolved"]: raise PipelineFailure("double horizon")
        ev["resolved"].add(h)
        if state is None:
            ev["h"][h]=None
            if why=="late": timing_late[h]+=1
            elif why=="end": timing_end[h]+=1
            else: raise PipelineFailure("unknown missing type")
        else:
            ev["h"][h]={"mid":state["mid"],"bid_depth5":state["bid_depth5"],"ask_depth5":state["ask_depth5"]}
            timing_avail[h]+=1
        if len(ev["resolved"])==len(HORIZONS_MS):
            finalize_event(ev); del active[eid]

    def resolve_due(env,state):
        for h in HORIZONS_MS:
            q=queues[h]
            while q and q[0][0] <= env:
                target,eid=q.popleft()
                late=env-target
                if late<=MAX_LATENESS_NS: resolve(eid,h,state)
                else: resolve(eid,h,None,"late")

    def create_event(env,side,pre_depth):
        nonlocal eid_next
        eid=eid_next; eid_next+=1
        ev={"date":anchor_date(env),"side":side,"direction":1.0 if side=="ASK" else -1.0,
            "pre_depth":pre_depth,"h":{},"resolved":set()}
        active[eid]=ev
        for h in HORIZONS_MS: queues[h].append((env+h*1_000_000,eid))

    def consume(env,st):
        nonlocal prev_state
        resolve_due(env,st)
        if prev_state is not None:
            totals["eligible_transitions"]+=1
            aw=st["ask_best"]>prev_state["ask_best"]
            bw=st["bid_best"]<prev_state["bid_best"]
            if aw and bw:
                totals["ambiguous"]+=1
            elif aw:
                if any(p==prev_state["ask_best"] for p in st["ask_prices_all"]):
                    raise PipelineFailure("prior ask still present")
                totals["ask_sweeps"]+=1; create_event(env,"ASK",prev_state["ask_depth5"])
            elif bw:
                if any(p==prev_state["bid_best"] for p in st["bid_prices_all"]):
                    raise PipelineFailure("prior bid still present")
                totals["bid_sweeps"]+=1; create_event(env,"BID",prev_state["bid_depth5"])
            else:
                totals["non_sweep"]+=1
        prev_state=st

    for row in rows:
        key=row["key"]; path=row_local_path(base,row)
        start_ns,end_ns=key_bounds_ns(key)
        dec=lz4.frame.LZ4FrameDecompressor(); pending=b""

        def proc(line):
            nonlocal last_env,last_payload
            totals["records"]+=1
            o=json.loads(line); env=parse_env_ns(o["time"])
            if not (start_ns<=env<end_ns): raise PipelineFailure("envelope outside key hour")
            st=extract_state(o); p=st["payload_ms"]
            if last_env is not None and env<last_env: raise PipelineFailure("envelope backwards")
            future = p*1_000_000>env
            last_env=env
            if future: totals["future_clock_skew"]+=1
            if last_payload is not None and p<last_payload:
                totals["stale"]+=1; return
            if last_payload is not None and p==last_payload: totals["equal"]+=1
            if not future: last_payload=p
            totals["accepted"]+=1; consume(env,st)

        with path.open("rb") as f:
            while True:
                b=f.read(READ_CHUNK)
                if not b: break
                out=dec.decompress(b)
                if not out: continue
                pending+=out
                parts=pending.split(b"\n"); pending=parts.pop()
                for line in parts:
                    if line.strip(): proc(line)
        if pending.strip(): proc(pending)
        if not dec.eof: raise PipelineFailure("incomplete LZ4")

    for h in HORIZONS_MS:
        while queues[h]:
            _,eid=queues[h].popleft(); resolve(eid,h,None,"end")
    if active: raise PipelineFailure("active events remain")

    serial=[]
    for (date,cell,group),v in daily.items():
        serial.append({"date":date,"cell":cell,"group":group,"n":v[0],"sum_response_bps":v[1],"sum_rr":v[2],
                       "ask_n":v[3],"ask_sum_response_bps":v[4],"bid_n":v[5],"bid_sum_response_bps":v[6]})
    return {
        "segment_id":sid,"totals":dict(totals),
        "timing_available":{str(h):int(timing_avail[h]) for h in HORIZONS_MS},
        "timing_missing_late":{str(h):int(timing_late[h]) for h in HORIZONS_MS},
        "timing_missing_end":{str(h):int(timing_end[h]) for h in HORIZONS_MS},
        "cell_counts":{k:dict(v) for k,v in cell_counts.items()},
        "daily":serial,
    }

def percentile_type7(vals,q):
    if not vals: return None
    a=sorted(vals)
    if len(a)==1: return float(a[0])
    pos=(len(a)-1)*q; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi: return float(a[lo])
    w=pos-lo
    return float(a[lo]*(1-w)+a[hi]*w)

def bootstrap_mean_ci(values):
    if not values: return None,None
    rng=random.Random(BOOTSTRAP_SEED); n=len(values); boots=[]
    for _ in range(BOOTSTRAP_REPS):
        s=0.0
        for __ in range(n): s+=values[rng.randrange(n)]
        boots.append(s/n)
    return percentile_type7(boots,.025), percentile_type7(boots,.975)

def stage_validation(base: Path, manifest_rows, schema_receipt, workers: int):
    ev=evidence_root(base)
    receipt=ev/"L2_RESILIENCY_001_VALIDATION_2025_RECEIPT_V0_1.json"
    cell_csv=ev/"L2_RESILIENCY_001_VALIDATION_2025_CELL_SUMMARY_V0_1.csv"
    daily_csv=ev/"L2_RESILIENCY_001_VALIDATION_2025_DAILY_CELL_STATS_V0_1.csv"
    side_csv=ev/"L2_RESILIENCY_001_VALIDATION_2025_SIDE_DIAGNOSTICS_V0_1.csv"
    month_csv=ev/"L2_RESILIENCY_001_VALIDATION_2025_MONTHLY_DIAGNOSTICS_V0_1.csv"
    segments=build_segments(manifest_rows)

    print("\n[4/4] INDEPENDENT 2025 VALIDATION — frozen outcomes")
    results=[]
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=max(1,min(workers,4))) as ex:
            futs=[ex.submit(validation_segment,(i+1,seg,str(base))) for i,seg in enumerate(segments)]
            for fut in concurrent.futures.as_completed(futs):
                r=fut.result(); results.append(r)
                t=r["totals"]
                print(f"  segment {r['segment_id']} | sweeps={t.get('ask_sweeps',0)+t.get('bid_sweeps',0):,} ambiguous={t.get('ambiguous',0):,}",flush=True)
    except Exception as e:
        obj={"schema_version":"0.1","lab_id":LAB_ID,"year":YEAR,
             "classification":"VALIDATION_TECHNICAL_FAIL_CLOSED",
             "failure":f"{type(e).__name__}: {str(e)[:2000]}",
             "access_2026":False,"pnl_computed":False,"live_trading":False}
        receipt.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        make_bundle(base)
        raise PipelineFailure(obj["classification"])

    results.sort(key=lambda r:r["segment_id"])
    totals=Counter(); timing_av=Counter(); timing_late=Counter(); timing_end=Counter()
    merged_daily={}; merged_cells={c[0]:Counter() for c in CELLS}
    for r in results:
        totals.update(r["totals"])
        for h in HORIZONS_MS:
            timing_av[h]+=int(r["timing_available"][str(h)])
            timing_late[h]+=int(r["timing_missing_late"][str(h)])
            timing_end[h]+=int(r["timing_missing_end"][str(h)])
        for cell,d in r["cell_counts"].items(): merged_cells[cell].update(d)
        for d in r["daily"]:
            key=(d["date"],d["cell"],d["group"])
            m=merged_daily.setdefault(key,[0,0.0,0.0,0,0.0,0,0.0])
            m[0]+=int(d["n"]); m[1]+=float(d["sum_response_bps"]); m[2]+=float(d["sum_rr"])
            m[3]+=int(d["ask_n"]); m[4]+=float(d["ask_sum_response_bps"])
            m[5]+=int(d["bid_n"]); m[6]+=float(d["bid_sum_response_bps"])

    with daily_csv.open("w",encoding="utf-8-sig",newline="") as f:
        fields=["date","cell","group","n","mean_response_bps","mean_rr","ask_n","ask_mean_response_bps","bid_n","bid_mean_response_bps"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for key in sorted(merged_daily):
            date,cell,group=key; v=merged_daily[key]
            w.writerow({"date":date,"cell":cell,"group":group,"n":v[0],
                        "mean_response_bps":f"{v[1]/v[0]:.12f}" if v[0] else "",
                        "mean_rr":f"{v[2]/v[0]:.12f}" if v[0] else "",
                        "ask_n":v[3],"ask_mean_response_bps":f"{v[4]/v[3]:.12f}" if v[3] else "",
                        "bid_n":v[5],"bid_mean_response_bps":f"{v[6]/v[5]:.12f}" if v[5] else ""})

    cell_rows=[]; contrast_by_date=defaultdict(dict)
    for cell,rh,yh in CELLS:
        weak={}; strong={}
        for (date,c,g),v in merged_daily.items():
            if c!=cell or not v[0]: continue
            mean=v[1]/v[0]
            (weak if g=="WEAK" else strong)[date]=mean
        dates=sorted(set(weak)&set(strong))
        cont=[weak[d]-strong[d] for d in dates]
        for d in dates: contrast_by_date[d][cell]=weak[d]-strong[d]
        point=sum(cont)/len(cont) if cont else None
        lo,hi=bootstrap_mean_ci(cont)
        cc=merged_cells[cell]; wn=int(cc["weak"]); sn=int(cc["strong"])
        row={
            "cell":cell,"replenishment_ms":rh,"outcome_ms":yh,
            "anchors_total":int(cc["anchors_total"]),
            "zero_pre_depth":int(cc["zero_pre_depth"]),
            "timing_missing":int(cc["timing_missing"]),
            "valid":int(cc["valid"]),"weak_n":wn,"strong_n":sn,
            "eligible_days":len(dates),
            "weak_event_mean_response_bps":float(cc["weak_sum_response"])/wn if wn else None,
            "strong_event_mean_response_bps":float(cc["strong_sum_response"])/sn if sn else None,
            "weak_event_mean_rr":float(cc["weak_sum_rr"])/wn if wn else None,
            "strong_event_mean_rr":float(cc["strong_sum_rr"])/sn if sn else None,
            "daily_contrast_bps":point,
            "bootstrap_ci95_low_bps":lo,"bootstrap_ci95_high_bps":hi,
            "positive_contrast":bool(point is not None and point>0),
            "sample_viable":len(dates)>=MIN_ELIGIBLE_DAYS,
        }
        cell_rows.append(row)

    with cell_csv.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cell_rows[0].keys())); w.writeheader(); w.writerows(cell_rows)

    with side_csv.open("w",encoding="utf-8-sig",newline="") as f:
        fields=["cell","group","side","n","mean_response_bps"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for cell,_,_ in CELLS:
            for group in ("WEAK","STRONG"):
                vals=[v for (d,c,g),v in merged_daily.items() if c==cell and g==group]
                for side,ni,si in (("ASK",3,4),("BID",5,6)):
                    n=sum(v[ni] for v in vals); s=sum(v[si] for v in vals)
                    w.writerow({"cell":cell,"group":group,"side":side,"n":n,"mean_response_bps":f"{s/n:.12f}" if n else ""})

    global_daily=[]
    for date in sorted(contrast_by_date):
        vals=list(contrast_by_date[date].values())
        if vals: global_daily.append((date,sum(vals)/len(vals),len(vals)))
    global_values=[x[1] for x in global_daily]
    global_effect=sum(global_values)/len(global_values) if global_values else None
    glo,ghi=bootstrap_mean_ci(global_values)

    monthly=defaultdict(list)
    for d,v,nc in global_daily: monthly[d[:7]].append(v)
    with month_csv.open("w",encoding="utf-8-sig",newline="") as f:
        fields=["month","eligible_days","global_mean_contrast_bps","positive_days","positive_day_pct"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for m in sorted(monthly):
            vals=monthly[m]; pos=sum(x>0 for x in vals)
            w.writerow({"month":m,"eligible_days":len(vals),"global_mean_contrast_bps":sum(vals)/len(vals),
                        "positive_days":pos,"positive_day_pct":100*pos/len(vals)})

    positive_cells=sum(r["positive_contrast"] for r in cell_rows)
    pos_by_r={str(rh):any(r["replenishment_ms"]==rh and r["positive_contrast"] for r in cell_rows) for rh in (1000,5000,15000)}
    source_coverage=100.0*len(manifest_rows)/EXPECTED_HOURS
    sample_viable=len(global_values)>=MIN_ELIGIBLE_DAYS and all(r["sample_viable"] for r in cell_rows)
    support={
        "global_effect_positive":bool(global_effect is not None and global_effect>0),
        "global_ci_low_positive":bool(glo is not None and glo>0),
        "at_least_4_of_6_cells_positive":positive_cells>=4,
        "each_R_has_positive_cell":all(pos_by_r.values()),
        "source_coverage_viable":source_coverage>=MIN_HOURLY_COVERAGE_PCT,
        "sample_viable":sample_viable,
    }
    if source_coverage < MIN_HOURLY_COVERAGE_PCT:
        classification="VALIDATION_BLOCKED_SOURCE_COVERAGE"
    elif not sample_viable:
        classification="VALIDATION_INSUFFICIENT_SAMPLE"
    elif all(support.values()):
        classification="VALIDATION_PASS"
    else:
        classification="VALIDATION_FAIL_NO_PROMOTION"

    obj={
        "schema_version":"0.1","lab_id":LAB_ID,"year":YEAR,
        "classification":classification,"protocol":PROTOCOL,"source_clock_amendment":SOURCE_CLOCK_AMENDMENT,
        "source_coverage_pct":source_coverage,
        "global_primary":{"eligible_days":len(global_values),"effect_bps":global_effect,
                          "bootstrap_ci95_low_bps":glo,"bootstrap_ci95_high_bps":ghi,
                          "positive_cells":positive_cells,"positive_by_replenishment_horizon":pos_by_r,
                          "support_gate":support},
        "cells":cell_rows,
        "totals":{"records":int(totals["records"]),"accepted_states":int(totals["accepted"]),
                  "stale_late_payload":int(totals["stale"]),"equal_payload_timestamp":int(totals["equal"]),
                   "future_payload_clock_skew":int(totals["future_clock_skew"]),
                  "eligible_transitions":int(totals["eligible_transitions"]),"ask_sweeps":int(totals["ask_sweeps"]),
                  "bid_sweeps":int(totals["bid_sweeps"]),"sweep_total":int(totals["ask_sweeps"]+totals["bid_sweeps"]),
                  "ambiguous":int(totals["ambiguous"])},
        "timing":{str(h):{"available":int(timing_av[h]),"missing_late":int(timing_late[h]),"missing_segment_end":int(timing_end[h])} for h in HORIZONS_MS},
        "evidence_sha256":{"cell_summary":sha256_file(cell_csv),"daily_stats":sha256_file(daily_csv),
                           "side_diagnostics":sha256_file(side_csv),"monthly_diagnostics":sha256_file(month_csv)},
        "firewalls":{"access_2026":False,"pnl_computed":False,"trading_costs_computed":False,
                     "sharpe_computed":False,"leverage_computed":False,"live_trading":False,
                     "exchange_mutation":False,"main_merge":False,"deployment":False},
        "post_outcome_rule":"NO RESCUE / NO RETUNING. Exact V0.1 validation verdict is immutable."
    }
    receipt.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("\n=== FINAL 2025 VALIDATION VERDICT ===")
    print("classification:",classification)
    print("source coverage:",f"{source_coverage:.6f}%")
    print("global effect bps:",global_effect)
    print("global 95% CI:",(glo,ghi))
    print("eligible days:",len(global_values))
    print("positive cells:",f"{positive_cells}/6")
    print("positive by R:",pos_by_r)
    for r in cell_rows:
        print(r["cell"],"| days",r["eligible_days"],"| contrast",r["daily_contrast_bps"],"| CI",(r["bootstrap_ci95_low_bps"],r["bootstrap_ci95_high_bps"]))
    return obj

def make_bundle(base: Path):
    ev=evidence_root(base)
    bundle=base/"L2_RESILIENCY_001_2025_VALIDATION_EVIDENCE_V0_1.zip"
    wanted=[]
    if ev.exists():
        for p in ev.iterdir():
            if p.is_file() and p.suffix.lower() in {".json",".csv",".txt"}:
                wanted.append(p)
    with zipfile.ZipFile(bundle,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(wanted):
            z.write(p,arcname=p.name)
    return bundle

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",default=str(default_base()))
    ap.add_argument("--workers",type=int,default=4)
    ap.add_argument("--offline-existing-corpus",action="store_true",help="Use canonical existing local manifest/raw corpus; no AWS/network stages.")
    args=ap.parse_args()
    base=Path(args.base).resolve()
    ensure_dirs(base)

    print("="*82)
    print("L2-RESILIENCY-001 — INDEPENDENT 2025 VALIDATION PIPELINE V0.1.1")
    print("="*82)
    print("Official Hyperliquid requester-pays BTC l2Book, full calendar 2025 only")
    print("WARNING: requester-pays S3 download charges may apply to your AWS account.")
    print("2026 FORBIDDEN | NO PNL | NO COSTS | NO SHARPE | NO LIVE TRADING")
    print("NO POST-OUTCOME RETUNING")
    print("Base:",base)
    print()

    try:
        if args.offline_existing_corpus:
            manifest=evidence_root(base)/"L2_RESILIENCY_001_2025_BTC_RAW_MANIFEST_V0_1.csv"
            if not manifest.exists(): raise PipelineFailure(f"canonical manifest missing: {manifest}")
            if sha256_file(manifest)!=CANONICAL_MANIFEST_SHA256: raise PipelineFailure("canonical manifest SHA mismatch")
            with manifest.open("r",encoding="utf-8-sig",newline="") as f: manifest_rows=list(csv.DictReader(f))
            if len(manifest_rows)!=CANONICAL_PRESENT_OBJECTS: raise PipelineFailure("canonical object count mismatch")
            if sum(int(r["content_length"]) for r in manifest_rows)!=CANONICAL_COMPRESSED_BYTES: raise PipelineFailure("canonical byte total mismatch")
            print("[1-2/4] OFFLINE CANONICAL SOURCE BINDING PASS — no AWS/network")
        else:
            inv_rows,inv_receipt=stage_inventory(base,args.workers)
            manifest_rows,acq_receipt=stage_acquisition(base,inv_rows,args.workers)
        schema_results,schema_receipt=stage_schema(base,manifest_rows,args.workers)
        validation=stage_validation(base,manifest_rows,schema_receipt,args.workers)
        bundle=make_bundle(base)
        print("\nEvidence bundle:",bundle)
        print("Evidence bundle SHA256:",sha256_file(bundle))
        print("Upload ONLY this ZIP to ChatGPT.")
        return 0
    except (NoCredentialsError,PartialCredentialsError) as e:
        obj={"classification":"SOURCE_AUTH_BLOCKED","failure":str(e),"outcomes_computed":False,"access_2026":False}
        p=evidence_root(base)/"L2_RESILIENCY_001_2025_PIPELINE_FAILURE_V0_1.json"
        p.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")
        bundle=make_bundle(base)
        print("\nSOURCE_AUTH_BLOCKED — AWS credentials not available to boto3.")
        print("Evidence bundle:",bundle)
        return 2
    except Exception as e:
        p=evidence_root(base)/"L2_RESILIENCY_001_2025_PIPELINE_FAILURE_V0_1.json"
        if not p.exists():
            p.write_text(json.dumps({"classification":"PIPELINE_FAIL_CLOSED","failure":f"{type(e).__name__}: {str(e)[:3000]}",
                                     "access_2026":False},indent=2)+"\n",encoding="utf-8")
        bundle=make_bundle(base)
        print("\nFAIL-CLOSED:",type(e).__name__,str(e))
        print("Evidence bundle:",bundle)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
