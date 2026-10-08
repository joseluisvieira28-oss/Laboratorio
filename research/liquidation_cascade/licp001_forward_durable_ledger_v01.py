#!/usr/bin/env python3
"""Durable LICP-001 forward receipt ledger.

Operational only. No exchange access and no scientific-parameter selection.
"""
from __future__ import annotations
import argparse, hashlib, json, tempfile
from pathlib import Path

CONFIG=Path("research/liquidation_cascade/LICP_001_TRIGGER_CONFIG_V0_1.json")
FREEZE_CUTOFF_MS=1791204237000  # 2026-10-05T12:43:57Z

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode()

def load_candidates(root):
    root=Path(root)
    files=[root] if root.is_file() else sorted(root.rglob("*.json"))
    rows=[]
    for p in files:
        try:j=json.loads(p.read_text())
        except Exception:continue
        if j.get("status")!="FORWARD_OBSERVATION":continue
        if j.get("live_trading") is not False:continue
        rows.append((p,j))
    return rows

def derive_episode_id(cfg_version,r):
    try:
        ignition_ts=int(r["meta"]["ignition"]["ignition_venue_ts"])
        pressure=str(r["pressure"])
    except Exception:
        return None
    raw=(cfg_version+"|"+str(ignition_ts)+"|"+pressure).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]

def normalize_legacy_ids(j,cfg_version):
    n=0
    for r in j.get("records",[]):
        if r.get("episode_id"):
            continue
        eid=derive_episode_id(cfg_version,r)
        if eid:
            r["episode_id"]=eid
            r["episode_id_reconstructed_legacy"]=True
            n+=1
    return n

def verify_receipt(j,cfg_sha,cfg_version):
    errs=[]
    if j.get("config_version")!=cfg_version:errs.append("CONFIG_VERSION_MISMATCH")
    if j.get("config_sha256")!=cfg_sha:errs.append("CONFIG_SHA_MISMATCH")
    try:
        if int(j.get("started_wall_ms",0)) < FREEZE_CUTOFF_MS:errs.append("PRE_FREEZE_RECEIPT")
        if int(j.get("ended_wall_ms",0)) < int(j.get("started_wall_ms",0)):errs.append("BAD_WALL_INTERVAL")
    except Exception:errs.append("BAD_WALL_TIME")
    normalize_legacy_ids(j,cfg_version)
    for i,r in enumerate(j.get("records",[])):
        if not r.get("episode_id"):errs.append("MISSING_EPISODE_ID_UNRECONSTRUCTABLE:"+str(i))
    return errs

def build(root,outdir):
    cfg=json.loads(CONFIG.read_text())
    cfg_sha=sha256_bytes(CONFIG.read_bytes())
    cfg_version=cfg["version"]
    candidates=load_candidates(root)
    accepted=[];rejected=[]

    for p,j in candidates:
        errs=verify_receipt(j,cfg_sha,cfg_version)
        if errs:rejected.append({"path":str(p),"errors":errs})
        else:accepted.append((p,j))

    accepted.sort(key=lambda x:(int(x[1]["started_wall_ms"]),str(x[0])))
    seen={};conflicts=[];total_records=0;legacy_ids=0
    for p,j in accepted:
        for r in j.get("records",[]):
            total_records+=1
            legacy_ids+=int(bool(r.get("episode_id_reconstructed_legacy")))
            eid=r["episode_id"];blob=sha256_bytes(canonical(r))
            if eid in seen and seen[eid]["sha256"]!=blob:
                conflicts.append({"episode_id":eid,"first":seen[eid],"conflict":{"path":str(p),"sha256":blob}})
            else:
                seen.setdefault(eid,{"path":str(p),"sha256":blob})

    gaps=[]
    for (_,a),(_,b) in zip(accepted,accepted[1:]):
        gap=int(b["started_wall_ms"])-int(a["ended_wall_ms"])
        if gap>0:gaps.append({"after_run_id":a.get("github_run_id"),"before_run_id":b.get("github_run_id"),"gap_ms":gap})

    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    rdir=outdir/"receipts";rdir.mkdir(exist_ok=True)
    for idx,(_,j) in enumerate(accepted,1):
        rid=j.get("github_run_id") or ("unknown-"+str(idx))
        attempt=j.get("github_run_attempt") or "1"
        (rdir/(f"{idx:04d}-{rid}-{attempt}.json")).write_text(json.dumps(j,indent=2,sort_keys=True)+"\n")

    status="BLOCKED_INTEGRITY_CONFLICT" if conflicts else "LEDGER_OK"
    summary={
      "schema":"licp001.forward_durable_ledger.v1",
      "status":status,
      "config_version":cfg_version,
      "config_sha256":cfg_sha,
      "accepted_receipts":len(accepted),
      "rejected_receipts":rejected,
      "raw_record_count":total_records,
      "unique_episode_ids":len(seen),
      "legacy_episode_ids_reconstructed":legacy_ids,
      "conflicts":conflicts,
      "observation_gaps":gaps,
      "eligible_started_after_ms":FREEZE_CUTOFF_MS,
      "science_changed":False
    }
    (outdir/"ledger_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    return summary

def self_test():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);cfg=json.loads(CONFIG.read_text());h=sha256_bytes(CONFIG.read_bytes())
        legacy={"family":"BTC_CONFIRMED","pressure":"SELL","meta":{"ignition":{"ignition_venue_ts":1800000000000}}}
        base={"status":"FORWARD_OBSERVATION","live_trading":False,"config_version":cfg["version"],"config_sha256":h,
              "started_wall_ms":FREEZE_CUTOFF_MS+1,"ended_wall_ms":FREEZE_CUTOFF_MS+1000,
              "github_run_id":"1","github_run_attempt":"1","records":[legacy]}
        (root/"a.json").write_text(json.dumps(base))
        b=json.loads(json.dumps(base));b["github_run_id"]="2";b["started_wall_ms"]=FREEZE_CUTOFF_MS+2000;b["ended_wall_ms"]=FREEZE_CUTOFF_MS+3000
        (root/"b.json").write_text(json.dumps(b))
        s=build(root,root/"out")
        assert s["status"]=="LEDGER_OK"
        assert s["unique_episode_ids"]==1
        assert s["legacy_episode_ids_reconstructed"]==2
        assert len(s["observation_gaps"])==1
    print("LICP001_DURABLE_LEDGER_SELFTEST_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root")
    ap.add_argument("--outdir")
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test:self_test();return
    if not a.root or not a.outdir:ap.error("--root and --outdir required")
    s=build(a.root,a.outdir)
    print(json.dumps(s,indent=2,sort_keys=True))
    if s["status"]!="LEDGER_OK":raise SystemExit(2)

if __name__=="__main__":main()
