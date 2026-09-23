#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, re, sys
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_MANIFEST_SHA256="767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3"
EXPECTED_OBJECTS=8400
EXPECTED_BYTES=8975275014

def hash_file(p: Path):
    h256=hashlib.sha256(); hmd5=hashlib.md5(); n=0
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""):
            n+=len(b); h256.update(b); hmd5.update(b)
    return h256.hexdigest(), hmd5.hexdigest(), n

def key_hour(key: str):
    m=re.fullmatch(r"market_data/(\d{8})/(\d{1,2})/l2Book/BTC\.lz4",key)
    if not m:
        raise RuntimeError(f"unexpected RAW path: {key}")
    d=datetime.strptime(m.group(1),"%Y%m%d").replace(tzinfo=timezone.utc)
    return d.replace(hour=int(m.group(2)))

def main():
    base=Path.home()/"Desktop"/"L2R_2025_BTC_VALIDATION_LOCAL"
    raw=base/"HL_L2R_2025_BTC_RAW_V0_1"
    ev=base/"_EVIDENCE_2025_VALIDATION_V0_1"
    ev.mkdir(parents=True,exist_ok=True)
    out=ev/"L2_RESILIENCY_001_2025_BTC_RAW_MANIFEST_V0_1.csv"
    if not raw.exists():
        raise SystemExit(f"RAW root missing: {raw}")

    files=list(raw.rglob("BTC.lz4"))
    total_bytes=sum(p.stat().st_size for p in files)
    print(f"RAW count={len(files)} bytes={total_bytes}",flush=True)
    if len(files)!=EXPECTED_OBJECTS or total_bytes!=EXPECTED_BYTES:
        raise SystemExit(f"FAIL CLOSED corpus shape {len(files)}/{total_bytes}")

    rows=[]
    for i,p in enumerate(files,1):
        rel=p.relative_to(raw)
        key=rel.as_posix()
        key_hour(key)  # validates path grammar
        sha,md5,n=hash_file(p)
        rows.append({
            "key":key,
            "status":"VERIFIED_EXISTING",
            "content_length":n,
            "etag":md5,
            "sha256":sha,
            "md5":md5,
            "local_relpath":str(rel),
        })
        if i%250==0 or i==len(files):
            print(f"manifest hashing {i}/{len(files)}",flush=True)

    rows.sort(key=lambda r:key_hour(r["key"]))
    fields=["key","status","content_length","etag","sha256","md5","local_relpath"]
    with out.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    sha=hashlib.sha256(out.read_bytes()).hexdigest()
    print("MANIFEST",out)
    print("MANIFEST_SHA256",sha)
    if sha!=EXPECTED_MANIFEST_SHA256:
        raise SystemExit(f"FAIL CLOSED manifest hash mismatch {sha}")
    print("MANIFEST_TECHNICAL_EQUIVALENCE_BINDING_PASS")

if __name__=="__main__":
    main()
