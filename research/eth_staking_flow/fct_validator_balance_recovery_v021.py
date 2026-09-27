#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, time, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BASE="https://lab.ethpandaops.io/api/v1/mainnet/fct_validator_balance"
GENESIS=1606824023
EPOCH_SECONDS=384
START=date(2025,1,1)
END=date(2026,8,31)
LEGACY_RUN_ID=35387477455
OUT=Path("artifacts/fct_balance_v021")
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

def target_epoch_time(ds):
    d=date.fromisoformat(ds)
    midnight=int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp())
    e=(midnight-GENESIS+EPOCH_SECONDS-1)//EPOCH_SECONDS
    return int(e),int(GENESIS+e*EPOCH_SECONDS)

def get_json(url,timeout=60,attempts=7):
    last=None
    for a in range(1,attempts+1):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-fct-balance-v021/1.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                raw=r.read()
                return r.status,raw,json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raw=e.read()
            last=f"HTTP {e.code}: {raw[:500]!r}"
            if e.code not in (408,429,500,502,503,504):
                raise RuntimeError(last)
            time.sleep(min(30,2*a))
        except Exception as e:
            last=repr(e); time.sleep(min(30,2*a))
    raise RuntimeError(f"request failed after retries: {last}")

def extract_rows(obj):
    if not isinstance(obj,dict):
        raise RuntimeError(f"response not object: {type(obj).__name__}")
    if "error" in obj:
        raise RuntimeError(f"API error object: {obj!r}")
    rows=obj.get("fct_validator_balance")
    if rows is None:
        # Empty list responses may serialize as {}.
        rows=[]
    if not isinstance(rows,list):
        raise RuntimeError(f"unexpected row field type; keys={sorted(obj.keys())}")
    token=obj.get("next_page_token") or obj.get("nextPageToken") or ""
    return rows,str(token)

def count_status(epoch,target_unix,status):
    base_params={
      "validator_index_gte":0,
      "epoch_eq":epoch,
      "status_eq":status,
      "page_size":10000,
      "order_by":"validator_index,epoch_start_date_time",
    }
    token=""
    seen_tokens=set()
    seen=set()
    pages=0
    body_shas=[]
    while True:
        p=dict(base_params)
        if token: p["page_token"]=token
        url=BASE+"?"+urllib.parse.urlencode(p)
        http,raw,obj=get_json(url)
        if http!=200: raise RuntimeError(f"http {http}")
        rows,next_token=extract_rows(obj)
        pages+=1; body_shas.append(hashlib.sha256(raw).hexdigest())
        for r in rows:
            vi=r.get("validator_index")
            ep=r.get("epoch")
            ts=r.get("epoch_start_date_time")
            st=r.get("status")
            if vi is None or ep is None or ts is None:
                raise RuntimeError("null required row field")
            vi=int(vi); ep=int(ep); ts=int(ts)
            if ep!=epoch or ts!=target_unix or str(st)!=status:
                raise RuntimeError(f"row geometry/status mismatch: {ep} {ts} {st}")
            if vi in seen:
                raise RuntimeError(f"duplicate validator_index {vi}")
            seen.add(vi)
        if not next_token: break
        if next_token in seen_tokens: raise RuntimeError("repeated pagination token")
        seen_tokens.add(next_token); token=next_token
        if pages>50: raise RuntimeError("pagination runaway")
        time.sleep(0.12)
    return len(seen),{"pages":pages,"body_sha256s":body_shas,"unique_validators":len(seen)}

def read_date(ds,expected_epoch=None):
    epoch,target_unix=target_epoch_time(ds)
    if expected_epoch is not None and epoch!=expected_epoch:
        raise RuntimeError(f"{ds}: computed epoch {epoch} != expected {expected_epoch}")
    p,pm=count_status(epoch,target_unix,"pending_queued")
    a,am=count_status(epoch,target_unix,"active_exiting")
    return {
      "date":ds,"selected_epoch":epoch,"selected_unix_time":target_unix,
      "pending_queued_count":p,"active_exiting_count":a,"net_queue_count":p-a,
      "source":"XATU_CBT_FCT_VALIDATOR_BALANCE_EXACT_EPOCH_V0_2_1",
      "transport":{"pending_queued":pm,"active_exiting":am},
    }

def load_legacy(root=Path("legacy_artifacts")):
    files=sorted(root.rglob("queue_rep_*.json"))
    if len(files)!=20:
        raise RuntimeError(f"legacy monthly shard count {len(files)} != 20")
    recs={}
    for p in files:
        x=json.loads(p.read_text())
        for r in x.get("daily_source_records",[]):
            ds=str(r["date"])
            row={
              "date":ds,
              "selected_epoch":int(r["selected_epoch"]),
              "selected_unix_time":int(r["selected_unix_time"]),
              "pending_queued_count":int(r["pending_queued_count"]),
              "active_exiting_count":int(r["active_exiting_count"]),
              "net_queue_count":int(r["net_queue_count"]),
              "source":"LEGACY_XATU_CANONICAL_BEACON_VALIDATORS",
            }
            if ds in recs and recs[ds]!=row:
                raise RuntimeError(f"legacy conflicting duplicate {ds}")
            recs[ds]=row
    if len(recs)!=601:
        raise RuntimeError(f"legacy unique rows {len(recs)} != 601")
    if set(MISSING)&set(recs):
        raise RuntimeError("frozen missing date unexpectedly in legacy")
    return recs

receipt={
 "lab_id":"ETH-STAKING-FLOW-001",
 "stage":"V3_STAGEA_FCT_VALIDATOR_BALANCE_REMEDIATION_V0_2_1",
 "classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE",
 "source_only":True,
 "signal_evaluated":False,
 "market_prices_opened":False,
 "returns_opened":False,
 "pnl_opened":False,
 "source_after_2026_08_31_opened":False,
 "legacy_run_id":LEGACY_RUN_ID,
 "controls":[],
 "recovered_missing_dates":[],
}

try:
    legacy=load_legacy()
    controls_ok=True
    for ds,(ep,ts,pq,ae,nq) in CONTROLS.items():
        r=read_date(ds,ep)
        got=(r["selected_epoch"],r["selected_unix_time"],r["pending_queued_count"],r["active_exiting_count"],r["net_queue_count"])
        exp=(ep,ts,pq,ae,nq)
        r["expected"]={"epoch":ep,"unix":ts,"pending":pq,"exiting":ae,"net":nq}
        r["exact_control_pass"]=got==exp
        receipt["controls"].append(r)
        controls_ok=controls_ok and r["exact_control_pass"]
    receipt["control_exact_match_count"]=sum(1 for r in receipt["controls"] if r["exact_control_pass"])

    if not controls_ok:
        receipt["classification"]="SOURCE_PROVENANCE_FAILURE"
    else:
        recovered={}
        for ds,ep in MISSING.items():
            r=read_date(ds,ep)
            recovered[ds]=r
            receipt["recovered_missing_dates"].append(r)
        receipt["recovered_missing_date_count"]=len(recovered)

        combined=dict(legacy)
        for ds,r in recovered.items():
            if ds in combined: raise RuntimeError(f"splice collision {ds}")
            combined[ds]={k:r[k] for k in ("date","selected_epoch","selected_unix_time","pending_queued_count","active_exiting_count","net_queue_count","source")}

        expected=[]
        d=START
        while d<=END:
            expected.append(d.isoformat()); d+=timedelta(days=1)
        if sorted(combined)!=expected:
            raise RuntimeError("final 608-day date geometry mismatch")

        ledger=[combined[ds] for ds in expected]
        for r in ledger:
            ep,ts=target_epoch_time(r["date"])
            if r["selected_epoch"]!=ep or r["selected_unix_time"]!=ts:
                raise RuntimeError(f"final target geometry mismatch {r['date']}")

        canon=[{k:r[k] for k in ("date","selected_epoch","selected_unix_time","pending_queued_count","active_exiting_count","net_queue_count")} for r in ledger]
        series_sha=hashlib.sha256((json.dumps(canon,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
        receipt["observed_date_count"]=len(ledger)
        receipt["legacy_preserved_date_count"]=len(legacy)
        receipt["daily_series_sha256"]=series_sha
        receipt["classification"]="SOURCE_REPLICATION_PASS"

        (OUT/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_LEDGER_V0_2_1.json").write_text(
          json.dumps({"lab_id":"ETH-STAKING-FLOW-001","stage":"V3_STAGEA_SOURCE_LEDGER_V0_2_1","daily_series_sha256":series_sha,"records":ledger},indent=2,sort_keys=True)+"\n"
        )
except Exception as e:
    receipt["failure"]=f"{type(e).__name__}: {str(e)[:3000]}"

(OUT/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_2_1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":receipt["classification"],
 "failure":receipt.get("failure"),
 "control_exact_match_count":receipt.get("control_exact_match_count"),
 "recovered_missing_date_count":receipt.get("recovered_missing_date_count"),
 "legacy_preserved_date_count":receipt.get("legacy_preserved_date_count"),
 "observed_date_count":receipt.get("observed_date_count"),
 "daily_series_sha256":receipt.get("daily_series_sha256"),
},sort_keys=True))
raise SystemExit(0 if receipt["classification"]=="SOURCE_REPLICATION_PASS" else 2)
