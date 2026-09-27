#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, time, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

GENESIS=1606824023
EPOCH_SECONDS=384
START=date(2025,1,1)
END=date(2026,8,31)
LEGACY_RUN_ID=35387477455
DAILY="https://lab.ethpandaops.io/api/v1/mainnet/fct_validator_count_by_entity_by_status_daily"
TRANS="https://lab.ethpandaops.io/api/v1/mainnet/dim_validator_status"
OUT=Path("artifacts/daily_transition_v022")
OUT.mkdir(parents=True,exist_ok=True)

CONTROLS={
 "2025-02-24":(347738,1740355415,0,5,-5),
 "2025-03-02":(349088,1740873815,0,0,0),
 "2025-10-17":(400613,1760659415,48,55209,-55161),
}
MISSING={
 "2025-02-25":347963,"2025-02-26":348188,"2025-02-27":348413,
 "2025-02-28":348638,"2025-03-01":348863,"2025-10-18":400838,"2025-10-19":401063,
}

def geometry(ds):
    d=date.fromisoformat(ds)
    m=int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp())
    x=(m-GENESIS)/EPOCH_SECONDS
    floor_e=math.floor(x); target_e=math.ceil(x)
    return floor_e, GENESIS+floor_e*EPOCH_SECONDS, target_e, GENESIS+target_e*EPOCH_SECONDS

def get_json(url,timeout=45,attempts=7):
    last=None
    for a in range(1,attempts+1):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-daily-transition-v022/1.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                raw=r.read()
                return r.status,raw,json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raw=e.read()
            last=f"HTTP {e.code}: {raw[:500]!r}"
            if e.code not in (408,429,500,502,503,504):
                raise RuntimeError(last)
            time.sleep(min(20,2*a))
        except Exception as e:
            last=repr(e); time.sleep(min(20,2*a))
    raise RuntimeError(f"request failed after retries: {last}")

def fetch_all(base,params,row_key,max_pages=100):
    out=[]; token=""; seen=set(); pages=0; body_shas=[]
    while True:
        p=dict(params)
        if token: p["page_token"]=token
        url=base+"?"+urllib.parse.urlencode(p)
        http,raw,obj=get_json(url)
        if http!=200: raise RuntimeError(f"http {http}")
        if not isinstance(obj,dict) or "error" in obj:
            raise RuntimeError(f"bad API object {obj!r}")
        rows=obj.get(row_key)
        if rows is None: rows=[]
        if not isinstance(rows,list): raise RuntimeError(f"bad rows field {row_key}")
        out.extend(rows); pages+=1; body_shas.append(hashlib.sha256(raw).hexdigest())
        nxt=obj.get("next_page_token") or obj.get("nextPageToken") or ""
        if not nxt: break
        if nxt in seen: raise RuntimeError("repeated page token")
        seen.add(nxt); token=str(nxt)
        if pages>=max_pages: raise RuntimeError("pagination cap exceeded")
        time.sleep(0.08)
    return out,{"pages":pages,"body_sha256s":body_shas}

def daily_count(ds,status):
    rows,meta=fetch_all(DAILY,{
      "day_start_date_eq":ds,"status_eq":status,"page_size":10000
    },"fct_validator_count_by_entity_by_status_daily",10)
    total=0
    for r in rows:
        if str(r.get("day_start_date"))!=ds or str(r.get("status"))!=status:
            raise RuntimeError(f"daily filter leakage {ds} {status}")
        total+=int(r.get("validator_count",0))
    meta["row_count"]=len(rows); meta["summed_validator_count"]=total
    return total,meta

def transitions_at(epoch,target_unix):
    rows,meta=fetch_all(TRANS,{
      "validator_index_gte":0,"epoch_eq":epoch,"page_size":10000,"order_by":"validator_index,status"
    },"dim_validator_status",20)
    by_vi={}
    for r in rows:
        vi=int(r["validator_index"])
        ep=int(r["epoch"]); ts=int(r["epoch_start_date_time"]); st=str(r["status"])
        if ep!=epoch or ts!=target_unix or not st:
            raise RuntimeError(f"transition geometry mismatch vi={vi}")
        by_vi.setdefault(vi,set()).add(st)
    bad={vi:sorted(v) for vi,v in by_vi.items() if len(v)!=1}
    if bad: raise RuntimeError(f"multiple new statuses same epoch: {list(bad.items())[:10]}")
    transitions=[(vi,next(iter(sts))) for vi,sts in sorted(by_vi.items())]
    meta["transition_validator_count"]=len(transitions)
    meta["new_status_counts"]={}
    for _,st in transitions: meta["new_status_counts"][st]=meta["new_status_counts"].get(st,0)+1
    return transitions,meta

def prior_status(vi,target_epoch):
    rows,meta=fetch_all(TRANS,{
      "validator_index_eq":vi,"page_size":100
    },"dim_validator_status",5)
    candidates=[]
    for r in rows:
        if int(r["validator_index"])!=vi: raise RuntimeError("validator filter leakage")
        ep=int(r["epoch"]); st=str(r["status"])
        if ep<target_epoch: candidates.append((ep,st))
    if not candidates: return None,meta
    maxep=max(ep for ep,_ in candidates)
    sts=sorted({st for ep,st in candidates if ep==maxep})
    if len(sts)!=1: raise RuntimeError(f"ambiguous prior status vi={vi} epoch={maxep} statuses={sts}")
    return sts[0],meta

def reconstruct(ds,expected_target_epoch=None):
    floor_e,floor_ts,target_e,target_ts=geometry(ds)
    if target_e!=floor_e+1: raise RuntimeError(f"{ds}: geometry not one-epoch bridge")
    if expected_target_epoch is not None and target_e!=expected_target_epoch:
        raise RuntimeError(f"{ds}: target epoch {target_e} != expected {expected_target_epoch}")

    pq,pqm=daily_count(ds,"pending_queued")
    ae,aem=daily_count(ds,"active_exiting")
    trs,trm=transitions_at(target_e,target_ts)

    ptarget=pq; atarget=ae
    audit=[]
    for vi,new in trs:
        prev,pm=prior_status(vi,target_e)
        if prev=="pending_queued": ptarget-=1
        if prev=="active_exiting": atarget-=1
        if new=="pending_queued": ptarget+=1
        if new=="active_exiting": atarget+=1
        audit.append({"validator_index":vi,"previous_status":prev,"new_status":new})

    if ptarget<0 or atarget<0: raise RuntimeError("negative reconstructed count")
    return {
      "date":ds,
      "floor_epoch":floor_e,"floor_unix_time":floor_ts,
      "selected_epoch":target_e,"selected_unix_time":target_ts,
      "floor_pending_queued_count":pq,"floor_active_exiting_count":ae,
      "pending_queued_count":ptarget,"active_exiting_count":atarget,"net_queue_count":ptarget-atarget,
      "target_transition_count":len(trs),
      "transition_audit":audit,
      "transport":{"daily_pending":pqm,"daily_exiting":aem,"target_transitions":trm},
      "source":"XATU_CBT_DAILY_PLUS_EXACT_TARGET_TRANSITIONS_V0_2_2",
    }

def load_legacy(root=Path("legacy_artifacts")):
    files=sorted(root.rglob("queue_rep_*.json"))
    if len(files)!=20: raise RuntimeError(f"legacy shard file count {len(files)} !=20")
    recs={}
    for p in files:
        x=json.loads(p.read_text())
        for r in x.get("daily_source_records",[]):
            ds=str(r["date"])
            row={k:r[k] for k in ("date","selected_epoch","selected_unix_time","pending_queued_count","active_exiting_count","net_queue_count")}
            row["selected_epoch"]=int(row["selected_epoch"]); row["selected_unix_time"]=int(row["selected_unix_time"])
            row["pending_queued_count"]=int(row["pending_queued_count"]); row["active_exiting_count"]=int(row["active_exiting_count"]); row["net_queue_count"]=int(row["net_queue_count"])
            row["source"]="LEGACY_XATU_CANONICAL_BEACON_VALIDATORS"
            if ds in recs and recs[ds]!=row: raise RuntimeError(f"legacy conflict {ds}")
            recs[ds]=row
    if len(recs)!=601: raise RuntimeError(f"legacy rows {len(recs)} !=601")
    if set(MISSING)&set(recs): raise RuntimeError("missing date unexpectedly in legacy")
    return recs

receipt={
 "lab_id":"ETH-STAKING-FLOW-001",
 "stage":"V3_STAGEA_DAILY_PLUS_TRANSITION_REMEDIATION_V0_2_2",
 "classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE",
 "source_only":True,"signal_evaluated":False,"market_prices_opened":False,
 "returns_opened":False,"pnl_opened":False,"source_after_2026_08_31_opened":False,
 "legacy_run_id":LEGACY_RUN_ID,"controls":[],"recovered_missing_dates":[]
}
try:
    legacy=load_legacy()
    controls_ok=True
    for ds,(ep,ts,pq,ae,nq) in CONTROLS.items():
        r=reconstruct(ds,ep)
        got=(r["selected_epoch"],r["selected_unix_time"],r["pending_queued_count"],r["active_exiting_count"],r["net_queue_count"])
        exp=(ep,ts,pq,ae,nq)
        r["expected"]={"epoch":ep,"unix":ts,"pending":pq,"exiting":ae,"net":nq}
        r["exact_control_pass"]=got==exp
        receipt["controls"].append(r); controls_ok=controls_ok and r["exact_control_pass"]
    receipt["control_exact_match_count"]=sum(1 for r in receipt["controls"] if r["exact_control_pass"])

    if not controls_ok:
        receipt["classification"]="SOURCE_PROVENANCE_FAILURE"
    else:
        recovered={}
        for ds,ep in MISSING.items():
            r=reconstruct(ds,ep); recovered[ds]=r; receipt["recovered_missing_dates"].append(r)
        receipt["recovered_missing_date_count"]=len(recovered)

        combined=dict(legacy)
        for ds,r in recovered.items():
            combined[ds]={k:r[k] for k in ("date","selected_epoch","selected_unix_time","pending_queued_count","active_exiting_count","net_queue_count","source")}

        expected=[]; d=START
        while d<=END: expected.append(d.isoformat()); d+=timedelta(days=1)
        if sorted(combined)!=expected: raise RuntimeError("final date geometry mismatch")
        ledger=[combined[ds] for ds in expected]
        for r in ledger:
            _,_,ep,ts=geometry(r["date"])
            if r["selected_epoch"]!=ep or r["selected_unix_time"]!=ts:
                raise RuntimeError(f"final target mismatch {r['date']}")
        canon=[{k:r[k] for k in ("date","selected_epoch","selected_unix_time","pending_queued_count","active_exiting_count","net_queue_count")} for r in ledger]
        sha=hashlib.sha256((json.dumps(canon,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
        receipt["legacy_preserved_date_count"]=len(legacy)
        receipt["observed_date_count"]=len(ledger)
        receipt["daily_series_sha256"]=sha
        receipt["classification"]="SOURCE_REPLICATION_PASS"
        (OUT/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_LEDGER_V0_2_2.json").write_text(
          json.dumps({"lab_id":"ETH-STAKING-FLOW-001","stage":"V3_STAGEA_SOURCE_LEDGER_V0_2_2","daily_series_sha256":sha,"records":ledger},indent=2,sort_keys=True)+"\n"
        )
except Exception as e:
    receipt["failure"]=f"{type(e).__name__}: {str(e)[:3000]}"

(OUT/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_2_2.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":receipt["classification"],"failure":receipt.get("failure"),
 "control_exact_match_count":receipt.get("control_exact_match_count"),
 "recovered_missing_date_count":receipt.get("recovered_missing_date_count"),
 "legacy_preserved_date_count":receipt.get("legacy_preserved_date_count"),
 "observed_date_count":receipt.get("observed_date_count"),
 "daily_series_sha256":receipt.get("daily_series_sha256"),
},sort_keys=True))
raise SystemExit(0 if receipt["classification"]=="SOURCE_REPLICATION_PASS" else 2)
