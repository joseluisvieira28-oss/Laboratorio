#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, time, urllib.error, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BASE="https://lodestar-mainnet.chainsafe.io"
GENESIS=1606824023
EPOCH_SECONDS=384
START=date(2025,1,1)
END=date(2026,8,31)
LEGACY_RUN_ID=35387477455
OUT=Path("artifacts/chainsafe_v023")
OUT.mkdir(parents=True,exist_ok=True)

CONTROLS={
 "2025-02-24":(347738,11127616,0,5,-5),
 "2025-03-02":(349088,11170816,0,0,0),
 "2025-10-17":(400613,12819616,48,55209,-55161),
}
MISSING={
 "2025-02-25":(347963,11134816),
 "2025-02-26":(348188,11142016),
 "2025-02-27":(348413,11149216),
 "2025-02-28":(348638,11156416),
 "2025-03-01":(348863,11163616),
 "2025-10-18":(400838,12826816),
 "2025-10-19":(401063,12834016),
}
RETRYABLE={408,425,429,500,502,503,504}
BACKOFF=[5,10,20,30,30]

def get_json(url):
    last=None
    attempts=[]
    for i in range(6):
        t0=time.time()
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-chainsafe-v023/1.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=120) as r:
                raw=r.read()
                attempts.append({"attempt":i+1,"http_status":r.status,"body_bytes":len(raw),"body_sha256":hashlib.sha256(raw).hexdigest(),"elapsed_s":round(time.time()-t0,3)})
                return json.loads(raw),attempts
        except urllib.error.HTTPError as e:
            raw=e.read()
            attempts.append({"attempt":i+1,"http_status":e.code,"body_bytes":len(raw),"body_sha256":hashlib.sha256(raw).hexdigest(),"elapsed_s":round(time.time()-t0,3),"error_prefix":raw[:300].decode("utf-8","replace")})
            last=f"HTTP {e.code}"
            if e.code not in RETRYABLE: break
        except Exception as e:
            attempts.append({"attempt":i+1,"http_status":None,"elapsed_s":round(time.time()-t0,3),"error":repr(e)})
            last=repr(e)
        if i<5:
            time.sleep(BACKOFF[i])
    raise RuntimeError(json.dumps({"url":url,"last":last,"attempts":attempts},sort_keys=True))

def status_count(slot,status):
    url=f"{BASE}/eth/v1/beacon/states/{slot}/validators?status={status}"
    obj,attempts=get_json(url)
    if not isinstance(obj,dict) or not isinstance(obj.get("data"),list):
        raise RuntimeError(f"bad beacon response shape {slot} {status}")
    rows=obj["data"]
    for r in rows:
        if str(r.get("status"))!=status:
            raise RuntimeError(f"status filter leakage {slot} {status}")
    return len(rows),{
      "url":url,"attempts":attempts,"row_count":len(rows),
      "execution_optimistic":obj.get("execution_optimistic"),
      "finalized":obj.get("finalized"),
    }

def read_date(ds,epoch,slot):
    pq,pqm=status_count(slot,"pending_queued")
    time.sleep(2)
    ae,aem=status_count(slot,"active_exiting")
    ts=GENESIS+epoch*EPOCH_SECONDS
    return {
      "date":ds,"selected_epoch":epoch,"selected_unix_time":ts,
      "pending_queued_count":pq,"active_exiting_count":ae,"net_queue_count":pq-ae,
      "source":"CHAINSAFE_LODESTAR_HISTORICAL_BEACON_STATE_V0_2_3",
      "transport":{"pending_queued":pqm,"active_exiting":aem},
    }

def load_legacy(root=Path("legacy_artifacts")):
    files=sorted(root.rglob("queue_rep_*.json"))
    if len(files)!=20: raise RuntimeError(f"legacy files {len(files)} !=20")
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
    if set(MISSING)&set(recs): raise RuntimeError("missing date in legacy")
    return recs

receipt={
 "lab_id":"ETH-STAKING-FLOW-001","stage":"V3_STAGEA_CHAINSAFE_SERIAL_RETRY_V0_2_3",
 "classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE",
 "source_only":True,"signal_evaluated":False,"market_prices_opened":False,
 "returns_opened":False,"pnl_opened":False,"source_after_2026_08_31_opened":False,
 "legacy_run_id":LEGACY_RUN_ID,"controls":[],"recovered_missing_dates":[]
}
try:
    legacy=load_legacy()
    controls_ok=True
    for ds,(ep,slot,pq,ae,nq) in CONTROLS.items():
        r=read_date(ds,ep,slot)
        exp=(ep,GENESIS+ep*EPOCH_SECONDS,pq,ae,nq)
        got=(r["selected_epoch"],r["selected_unix_time"],r["pending_queued_count"],r["active_exiting_count"],r["net_queue_count"])
        r["expected"]={"epoch":ep,"unix":exp[1],"pending":pq,"exiting":ae,"net":nq}
        r["exact_control_pass"]=got==exp
        receipt["controls"].append(r); controls_ok=controls_ok and r["exact_control_pass"]
        time.sleep(2)
    receipt["control_exact_match_count"]=sum(1 for r in receipt["controls"] if r["exact_control_pass"])
    if not controls_ok:
        receipt["classification"]="SOURCE_PROVENANCE_FAILURE"
    else:
        recovered={}
        for ds,(ep,slot) in MISSING.items():
            r=read_date(ds,ep,slot); recovered[ds]=r; receipt["recovered_missing_dates"].append(r); time.sleep(2)
        receipt["recovered_missing_date_count"]=len(recovered)

        combined=dict(legacy)
        for ds,r in recovered.items():
            combined[ds]={k:r[k] for k in ("date","selected_epoch","selected_unix_time","pending_queued_count","active_exiting_count","net_queue_count","source")}
        expected=[]; d=START
        while d<=END: expected.append(d.isoformat()); d+=timedelta(days=1)
        if sorted(combined)!=expected: raise RuntimeError("final date geometry mismatch")
        ledger=[combined[ds] for ds in expected]
        canon=[{k:r[k] for k in ("date","selected_epoch","selected_unix_time","pending_queued_count","active_exiting_count","net_queue_count")} for r in ledger]
        sha=hashlib.sha256((json.dumps(canon,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
        receipt["legacy_preserved_date_count"]=len(legacy)
        receipt["observed_date_count"]=len(ledger)
        receipt["daily_series_sha256"]=sha
        receipt["classification"]="SOURCE_REPLICATION_PASS"
        (OUT/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_LEDGER_V0_2_3.json").write_text(
          json.dumps({"lab_id":"ETH-STAKING-FLOW-001","stage":"V3_STAGEA_SOURCE_LEDGER_V0_2_3","daily_series_sha256":sha,"records":ledger},indent=2,sort_keys=True)+"\n"
        )
except Exception as e:
    msg=str(e)
    receipt["failure"]=f"{type(e).__name__}: {msg[:12000]}"

(OUT/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_2_3.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":receipt["classification"],"failure":receipt.get("failure"),
 "control_exact_match_count":receipt.get("control_exact_match_count"),
 "recovered_missing_date_count":receipt.get("recovered_missing_date_count"),
 "legacy_preserved_date_count":receipt.get("legacy_preserved_date_count"),
 "observed_date_count":receipt.get("observed_date_count"),
 "daily_series_sha256":receipt.get("daily_series_sha256")
},sort_keys=True))
raise SystemExit(0 if receipt["classification"]=="SOURCE_REPLICATION_PASS" else 2)
