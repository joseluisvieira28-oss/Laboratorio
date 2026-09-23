#!/usr/bin/env python3
import argparse, hashlib, json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE11_PROGRAM_SIGNATURE_DAILY_MANIFEST_V0.1.json")
RECEIPT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE11_PROGRAM_SIGNATURE_DAILY_MANIFEST_RECEIPT_V0.1.json")

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(o): return json.dumps(o,separators=(",",":"),sort_keys=True).encode()
def day_of(ts): return datetime.fromtimestamp(int(ts),timezone.utc).date()
def row_min(r): return {"signature":r["signature"],"slot":int(r["slot"]),"blockTime":int(r["blockTime"]),"err":r.get("err")}
def anchor(r):
    if r is None: return None
    return {"signature":r["signature"],"slot":int(r["slot"]),"blockTime":int(r["blockTime"])}

def finalize_day(date,rows,newer,older):
    ordered=sorted((row_min(r) for r in rows),key=lambda r:(r["blockTime"],r["slot"],r["signature"]))
    sigs=[r["signature"] for r in ordered]
    if len(sigs)!=len(set(sigs)): raise RuntimeError(f"DUPLICATE_SIGNATURE_WITHIN_DAY {date}")
    start=int(datetime(date.year,date.month,date.day,tzinfo=timezone.utc).timestamp())
    return {
      "date":date.isoformat(),"window_start":start,"window_end":start+86400,
      "row_count":len(ordered),
      "signature_success_count":sum(r.get("err") is None for r in ordered),
      "signature_failed_count":sum(r.get("err") is not None for r in ordered),
      "queue_sha256":sha(canon(ordered)),
      "newer_adjacent_program_signature":anchor(newer),
      "older_adjacent_program_signature":anchor(older),
      "rpc_reconstruction_anchor_pair_ready":newer is not None and older is not None
    }

ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); a=ap.parse_args()
pages=[]
for p in Path(a.root).rglob("signatures_page_*.json"):
    m=re.search(r"signatures_page_(\d+)\.json$",p.name)
    if m: pages.append((int(m.group(1)),p))
pages.sort(key=lambda x:x[0])
if not pages: raise RuntimeError("NO_SIGNATURE_PAGES")
nums=[n for n,_ in pages]
if len(nums)!=len(set(nums)): raise RuntimeError("DUPLICATE_PAGE_NUMBER")

days=[]
prev_bt=None; prev_row=None
current_date=None; current_rows=[]; current_newer=None
total_rows=0; coverage_min=None; coverage_max=None
for pageno,p in pages:
    obj=json.loads(p.read_text(encoding="utf-8")); rows=obj.get("result")
    if not isinstance(rows,list): raise RuntimeError(f"PAGE_RESULT_NOT_LIST {p}")
    for raw in rows:
        if not isinstance(raw,dict): raise RuntimeError("ROW_NOT_OBJECT")
        sig=raw.get("signature"); slot=raw.get("slot"); bt=raw.get("blockTime")
        if not isinstance(sig,str) or not sig: raise RuntimeError("INVALID_SIGNATURE")
        if isinstance(slot,bool) or not isinstance(slot,int): raise RuntimeError(f"INVALID_SLOT {sig}")
        if isinstance(bt,bool) or not isinstance(bt,int): raise RuntimeError(f"NULL_OR_INVALID_BLOCKTIME {sig}")
        r={"signature":sig,"slot":slot,"blockTime":bt,"err":raw.get("err")}
        if prev_bt is not None and bt>prev_bt:
            raise RuntimeError(f"GLOBAL_NON_MONOTONIC_TIME {bt}>{prev_bt} sig={sig}")
        coverage_max=bt if coverage_max is None else max(coverage_max,bt)
        coverage_min=bt if coverage_min is None else min(coverage_min,bt)
        total_rows+=1
        d=day_of(bt)
        if current_date is None:
            current_date=d; current_newer=prev_row
        elif d!=current_date:
            days.append(finalize_day(current_date,current_rows,current_newer,r))
            gap=current_date-timedelta(days=1)
            while gap>d:
                days.append(finalize_day(gap,[],prev_row,r))
                gap-=timedelta(days=1)
            current_date=d; current_rows=[]; current_newer=prev_row
        current_rows.append(r)
        prev_bt=bt; prev_row=r

if current_date is not None:
    days.append(finalize_day(current_date,current_rows,current_newer,None))
days.sort(key=lambda x:x["date"])
if not days: raise RuntimeError("NO_DAILY_ENTRIES")
if len({d["date"] for d in days})!=len(days): raise RuntimeError("DUPLICATE_DAY_ENTRY")

manifest={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","program_id":PROGRAM,
 "coverage":{"min_block_time":coverage_min,"max_block_time":coverage_max,
             "min_iso":datetime.fromtimestamp(coverage_min,timezone.utc).isoformat().replace("+00:00","Z"),
             "max_iso":datetime.fromtimestamp(coverage_max,timezone.utc).isoformat().replace("+00:00","Z")},
 "source":{"run_id":35715830047,"artifact_id":10690805384,
           "artifact_sha256":"e72c22a7164ba8787c03201a3d7b2eb1a42a6ffc4384d3dcb8e80695aa9e8c7c"},
 "days":days,"days_sha256":sha(canon(days))
}
OUT.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"SAVE11_PROGRAM_SIGNATURE_DAILY_MANIFEST_PASS",
 "program_id":PROGRAM,"source_rows":total_rows,"source_page_files":len(pages),
 "daily_entries":len(days),"zero_program_tx_days":sum(d["row_count"]==0 for d in days),
 "anchor_pair_ready_days":sum(d["rpc_reconstruction_anchor_pair_ready"] for d in days),
 "first_date":days[0]["date"],"last_date":days[-1]["date"],
 "coverage":manifest["coverage"],"days_sha256":manifest["days_sha256"],
 "firewalls":{"prices":False,"amounts":False,"returns":False,"pnl":False,"direction":False,
              "market_outcomes":False,"liquidation_classification":False,"live_trading":False,
              "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
              "account_creation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
