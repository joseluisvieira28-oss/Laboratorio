#!/usr/bin/env python3
from __future__ import annotations
import bisect, hashlib, json, time, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

LAB_ID="ETH-STAKING-FLOW-001"
GENESIS=1606824023
EPOCH_SECONDS=384
START_DATE=date(2025,1,1)
END_DATE=date(2026,8,31)
MIN_EPOCH=335588
MAX_EPOCH=472163
LEGACY_RUN_ID=35387477455
BASE="https://lab.ethpandaops.io/api/v1/mainnet"

MISSING={
 "2025-02-25":347963,"2025-02-26":348188,"2025-02-27":348413,
 "2025-02-28":348638,"2025-03-01":348863,"2025-10-18":400838,"2025-10-19":401063,
}
CONTROLS={
 "2025-02-24":(347738,1740355415,0,5,-5),
 "2025-03-02":(349088,1740873815,0,0,0),
 "2025-10-17":(400613,1760659415,48,55209,-55161),
}
OUTDIR=Path("artifacts/cbt_v020")
OUTDIR.mkdir(parents=True,exist_ok=True)

def utc_midnight(d: date) -> int:
    return int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp())

def target_epoch_time(d: date):
    ts=utc_midnight(d)
    e=(ts-GENESIS + EPOCH_SECONDS-1)//EPOCH_SECONDS
    return int(e), int(GENESIS+e*EPOCH_SECONDS)

def daterange(a: date,b: date):
    d=a
    while d<=b:
        yield d
        d+=timedelta(days=1)

def get_json(url, timeout=60, attempts=8):
    last=None
    for attempt in range(1,attempts+1):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-cbt-v020/1.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                raw=r.read()
                return r.status, raw, json.loads(raw)
        except urllib.error.HTTPError as e:
            raw=e.read()
            last=f"HTTP {e.code}: {raw[:500]!r}"
            if e.code not in (408,429,500,502,503,504):
                raise RuntimeError(last)
            retry=e.headers.get("Retry-After")
            delay=float(retry) if retry and retry.isdigit() else min(30,2*attempt)
            time.sleep(delay)
        except Exception as e:
            last=repr(e)
            time.sleep(min(30,2*attempt))
    raise RuntimeError(f"request failed after retries: {last}")

def qurl(params):
    return BASE+"/dim_validator_status?"+urllib.parse.urlencode(params)

def extract_rows(obj):
    if not isinstance(obj,dict):
        raise RuntimeError(f"API response not object: {type(obj).__name__}")
    rows=obj.get("dim_validator_status")
    if not isinstance(rows,list):
        raise RuntimeError(f"transition row array missing; keys={sorted(obj.keys())}")
    tok=obj.get("next_page_token") or obj.get("nextPageToken") or ""
    return rows,str(tok)

def int_field(row,key):
    v=row.get(key)
    if isinstance(v,dict) and "value" in v:
        v=v["value"]
    if v is None:
        return None
    return int(v)

def contract_preflight(status,end_field):
    params={
      "validator_index_gte":0,
      "status_eq":status,
      "epoch_lte":MAX_EPOCH,
      f"{end_field}_gte":MIN_EPOCH,
      "page_size":3,
      "order_by":"validator_index,epoch",
    }
    http,raw,obj=get_json(qurl(params))
    rows,tok=extract_rows(obj)
    if http!=200 or not rows:
        raise RuntimeError(f"sparse preflight empty for {status}")
    required={"validator_index","status","epoch","epoch_start_date_time",end_field}
    fields=set(rows[0].keys()) if isinstance(rows[0],dict) else set()
    if not required.issubset(fields):
        raise RuntimeError(f"sparse preflight schema incomplete for {status}: {sorted(fields)}")
    return {
      "status":status,
      "row_count":len(rows),
      "first_page_sha256":hashlib.sha256(raw).hexdigest(),
      "next_page_token_present":bool(tok),
      "field_names":sorted(fields),
    }

def fetch_dataset(name,status,end_field):
    params={
      "validator_index_gte":0,
      "status_eq":status,
      "epoch_lte":MAX_EPOCH,
      f"{end_field}_gte":MIN_EPOCH,
      "page_size":10000,
      "order_by":"validator_index,epoch",
    }
    all_rows=[]
    token=""
    seen_tokens=set()
    page=0
    while True:
        p=dict(params)
        if token:
            p["page_token"]=token
        http,raw,obj=get_json(qurl(p))
        if http!=200:
            raise RuntimeError(f"{name}: http {http}")
        rows,next_token=extract_rows(obj)
        page+=1
        for r in rows:
            if str(r.get("status"))!=status:
                raise RuntimeError(f"{name}: status filter leakage")
            all_rows.append(r)
        print(json.dumps({"dataset":name,"page":page,"rows_total":len(all_rows),"next":bool(next_token)}),flush=True)
        if not next_token:
            break
        if next_token in seen_tokens:
            raise RuntimeError(f"{name}: repeated page token")
        seen_tokens.add(next_token)
        token=next_token
        if page>2000:
            raise RuntimeError(f"{name}: pagination runaway")
        time.sleep(0.15)

    if not all_rows:
        raise RuntimeError(f"{name}: zero rows after full acquisition")

    canonical=[]
    validators=set()
    enters=[]
    leaves=[]
    for r in all_rows:
        vi=int_field(r,"validator_index")
        ep=int_field(r,"epoch")
        ep_ts=int_field(r,"epoch_start_date_time")
        leave=int_field(r,end_field)
        if None in (vi,ep,ep_ts,leave):
            raise RuntimeError(f"{name}: null required lifecycle field")
        if vi in validators:
            raise RuntimeError(f"{name}: duplicate validator_index {vi}")
        validators.add(vi)
        if leave < ep:
            raise RuntimeError(f"{name}: lifecycle end before transition for {vi}")
        if ep>MAX_EPOCH or leave<MIN_EPOCH:
            raise RuntimeError(f"{name}: API filter leakage")
        canonical.append({
          "validator_index":vi,"status":status,"epoch":ep,"epoch_start_date_time":ep_ts,
          "activation_epoch":int_field(r,"activation_epoch"),"exit_epoch":int_field(r,"exit_epoch"),
        })
        enters.append(ep); leaves.append(leave)

    canonical.sort(key=lambda x:(x["validator_index"],x["epoch"]))
    raw=(json.dumps(canonical,sort_keys=True,separators=(",",":"))+"\n").encode()
    sha=hashlib.sha256(raw).hexdigest()
    enters.sort(); leaves.sort()
    return {
      "name":name,"status":status,"end_field":end_field,"row_count":len(canonical),
      "page_count":page,"rows_sha256":sha,"enters":enters,"leaves":leaves
    }

def count_at(ds,e):
    return bisect.bisect_right(ds["enters"],e)-bisect.bisect_right(ds["leaves"],e)

def load_legacy(root=Path("legacy_artifacts")):
    recs={}
    files=sorted(root.rglob("queue_rep_*.json"))
    if len(files)!=20:
        raise RuntimeError(f"legacy monthly shard count {len(files)} != 20")
    for p in files:
        x=json.loads(p.read_text())
        for r in x.get("daily_source_records",[]):
            d=str(r["date"])
            row={
              "date":d,
              "selected_epoch":int(r["selected_epoch"]),
              "selected_unix_time":int(r["selected_unix_time"]),
              "pending_queued_count":int(r["pending_queued_count"]),
              "active_exiting_count":int(r["active_exiting_count"]),
              "net_queue_count":int(r["net_queue_count"]),
            }
            if d in recs and recs[d]!=row:
                raise RuntimeError(f"legacy conflicting duplicate {d}")
            recs[d]=row
    if len(recs)!=601:
        raise RuntimeError(f"legacy unique daily rows {len(recs)} != 601")
    if set(MISSING)&set(recs):
        raise RuntimeError("frozen missing date unexpectedly present in legacy")
    return recs,files

receipt={
 "lab_id":LAB_ID,
 "stage":"V3_STAGEA_CBT_CONTRACT_BOUND_RECONSTRUCTION_V0_2_0",
 "classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE",
 "source_base":BASE,
 "legacy_run_id":LEGACY_RUN_ID,
 "frozen_range":{"start":"2025-01-01","end":"2026-08-31","expected_dates":608,"min_epoch":MIN_EPOCH,"max_epoch":MAX_EPOCH},
 "source_only":True,
 "signal_evaluated":False,
 "market_prices_opened":False,
 "returns_opened":False,
 "pnl_opened":False,
 "source_after_2026_08_31_opened":False,
}

try:
    receipt["sparse_preflight"]=[
      contract_preflight("pending_queued","activation_epoch"),
      contract_preflight("active_exiting","exit_epoch"),
    ]
    legacy,legacy_files=load_legacy()
    receipt["legacy_artifact_monthly_file_count"]=len(legacy_files)
    pending=fetch_dataset("pending_queued","pending_queued","activation_epoch")
    exiting=fetch_dataset("active_exiting","active_exiting","exit_epoch")
except Exception as e:
    receipt["failure"]=repr(e)
    (OUTDIR/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_2_0.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    raise SystemExit(2)

receipt["lifecycle_datasets"]={
 "pending_queued":{"row_count":pending["row_count"],"page_count":pending["page_count"],"rows_sha256":pending["rows_sha256"]},
 "active_exiting":{"row_count":exiting["row_count"],"page_count":exiting["page_count"],"rows_sha256":exiting["rows_sha256"]},
}

ledger=[]
for d in daterange(START_DATE,END_DATE):
    e,ts=target_epoch_time(d)
    pq=count_at(pending,e)
    ae=count_at(exiting,e)
    ledger.append({
      "date":d.isoformat(),"selected_epoch":e,"selected_unix_time":ts,
      "selected_time_utc":datetime.fromtimestamp(ts,tz=timezone.utc).isoformat(),
      "pending_queued_count":pq,"active_exiting_count":ae,"net_queue_count":pq-ae,
      "source":"XATU_CBT_DIM_VALIDATOR_STATUS_V0_2_0",
    })

by_date={r["date"]:r for r in ledger}
control_mismatches=[]
for d,(ep,ts,pq,ae,nq) in CONTROLS.items():
    r=by_date[d]
    expected=(ep,ts,pq,ae,nq)
    got=(r["selected_epoch"],r["selected_unix_time"],r["pending_queued_count"],r["active_exiting_count"],r["net_queue_count"])
    if got!=expected:
        control_mismatches.append({"date":d,"expected":expected,"got":got})

overlap_mismatches=[]
for d,old in sorted(legacy.items()):
    new=by_date.get(d)
    if new is None:
        overlap_mismatches.append({"date":d,"reason":"missing_new"}); continue
    keys=["selected_epoch","selected_unix_time","pending_queued_count","active_exiting_count","net_queue_count"]
    diffs={k:{"legacy":old[k],"new":new[k]} for k in keys if old[k]!=new[k]}
    if diffs:
        overlap_mismatches.append({"date":d,"diffs":diffs})

missing_rows=[by_date[d] for d in sorted(MISSING)]
missing_epoch_mismatch=[r for r in missing_rows if r["selected_epoch"]!=MISSING[r["date"]]]

canon=[{k:r[k] for k in ("date","selected_epoch","selected_unix_time","pending_queued_count","active_exiting_count","net_queue_count")} for r in ledger]
receipt["daily_series_sha256"]=hashlib.sha256((json.dumps(canon,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
receipt["observed_date_count"]=len(ledger)
receipt["control_exact_match_count"]=3-len(control_mismatches)
receipt["control_mismatches"]=control_mismatches
receipt["legacy_overlap_exact_match_count"]=601-len(overlap_mismatches)
receipt["legacy_overlap_mismatch_count"]=len(overlap_mismatches)
receipt["legacy_overlap_mismatches"]=overlap_mismatches[:50]
receipt["recovered_missing_date_count"]=len(missing_rows)
receipt["recovered_missing_dates"]=missing_rows
receipt["missing_epoch_mismatch_count"]=len(missing_epoch_mismatch)

if len(ledger)!=608 or len(by_date)!=608:
    receipt["classification"]="SOURCE_PROVENANCE_FAILURE"
    receipt["failure"]="final ledger cardinality"
elif control_mismatches or overlap_mismatches or missing_epoch_mismatch:
    receipt["classification"]="SOURCE_PROVENANCE_FAILURE"
else:
    receipt["classification"]="SOURCE_REPLICATION_PASS"

out_receipt=OUTDIR/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_2_0.json"
out_ledger=OUTDIR/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_LEDGER_V0_2_0.json"
out_receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
out_ledger.write_text(json.dumps({"lab_id":LAB_ID,"stage":"V3_STAGEA_SOURCE_LEDGER_V0_2_0","daily_series_sha256":receipt["daily_series_sha256"],"records":ledger},indent=2,sort_keys=True)+"\n")

print(json.dumps({
 "classification":receipt["classification"],
 "pending_rows":pending["row_count"],
 "active_exiting_rows":exiting["row_count"],
 "control_exact_match_count":receipt["control_exact_match_count"],
 "legacy_overlap_exact_match_count":receipt["legacy_overlap_exact_match_count"],
 "legacy_overlap_mismatch_count":receipt["legacy_overlap_mismatch_count"],
 "recovered_missing_date_count":receipt["recovered_missing_date_count"],
 "observed_date_count":receipt["observed_date_count"],
 "daily_series_sha256":receipt["daily_series_sha256"],
},sort_keys=True))
raise SystemExit(0 if receipt["classification"]=="SOURCE_REPLICATION_PASS" else 2)
