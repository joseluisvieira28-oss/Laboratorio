#!/usr/bin/env python3
import argparse, hashlib, json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_PROGRAM_SIGNATURE_DAILY_MANIFEST_V0.1.json")
RECEIPT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_PROGRAM_SIGNATURE_DAILY_MANIFEST_RECEIPT_V0.1.json")
PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
CURSOR_SIG="47XL1cg6q8WtXxgAhoQGhtRMRm7EnrTtHZUR4QarxxuvpXTxCQANAnrDku7mHukz7JYxSYAquSyWAnH4DKSDiAis"

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(o): return json.dumps(o,separators=(",",":"),sort_keys=True).encode()
def day_of(ts): return datetime.fromtimestamp(int(ts),timezone.utc).date()
def row_min(r): return {"signature":r["signature"],"slot":int(r["slot"]),"blockTime":int(r["blockTime"]),"err":r.get("err")}
def anchor(r):
    if r is None: return None
    return {"signature":r["signature"],"slot":int(r["slot"]),"blockTime":int(r["blockTime"])}

def pages(root):
    found=[]
    for p in Path(root).rglob("signatures_page_*.json"):
        m=re.search(r"signatures_page_(\d+)\.json$",p.name)
        if m: found.append((int(m.group(1)),p))
    found.sort(key=lambda x:x[0])
    if not found: raise RuntimeError(f"NO_SIGNATURE_PAGES {root}")
    nums=[n for n,_ in found]
    if len(nums)!=len(set(nums)): raise RuntimeError(f"DUPLICATE_PAGE_NUMBER {root}")
    return found

def finalize_day(date,rows,newer,older,source_labels):
    ordered=sorted((row_min(r) for r in rows),key=lambda r:(r["blockTime"],r["slot"],r["signature"]))
    sigs=[r["signature"] for r in ordered]
    if len(sigs)!=len(set(sigs)): raise RuntimeError(f"DUPLICATE_SIGNATURE_WITHIN_DAY {date}")
    start=int(datetime(date.year,date.month,date.day,tzinfo=timezone.utc).timestamp())
    end=start+86400
    return {
      "date":date.isoformat(),
      "window_start":start,"window_end":end,
      "row_count":len(ordered),
      "signature_success_count":sum(r.get("err") is None for r in ordered),
      "signature_failed_count":sum(r.get("err") is not None for r in ordered),
      "queue_sha256":sha(canon(ordered)),
      "newer_adjacent_program_signature":anchor(newer),
      "older_adjacent_program_signature":anchor(older),
      "rpc_reconstruction_anchor_pair_ready":newer is not None and older is not None,
      "source_slices":sorted(source_labels)
    }

ap=argparse.ArgumentParser()
ap.add_argument("--newer-root",required=True)
ap.add_argument("--older-root",required=True)
a=ap.parse_args()

inputs=[
 ("newer",Path(a.newer_root),35689367726,10681229919,"bd0fd03a095e93fbdb95bfd6266686ee076b11ab863822f06430b1c77c6d3e74"),
 ("older",Path(a.older_root),35704794316,10686881756,"15097adc6e833edfc99ab11f24c6c4057752b2df7c5de831567bdc6cc01ecf14")
]

manifest_days=[]
prev_bt=None
prev_row=None
current_date=None
current_rows=[]
current_sources=set()
current_newer=None
total_rows=0
total_pages=0
coverage_max=None
coverage_min=None
slice_stats=[]
newer_last=None
older_first=None

for label,root,run_id,artifact_id,digest in inputs:
    ps=pages(root)
    slice_first=None
    slice_last=None
    slice_rows=0
    for pageno,p in ps:
        obj=json.loads(p.read_text(encoding="utf-8"))
        rs=obj.get("result")
        if not isinstance(rs,list): raise RuntimeError(f"PAGE_RESULT_NOT_LIST {label} {p}")
        total_pages+=1
        for raw in rs:
            if not isinstance(raw,dict): raise RuntimeError("ROW_NOT_OBJECT")
            sig=raw.get("signature"); slot=raw.get("slot"); bt=raw.get("blockTime")
            if not isinstance(sig,str) or not sig: raise RuntimeError("INVALID_SIGNATURE")
            if isinstance(slot,bool) or not isinstance(slot,int): raise RuntimeError(f"INVALID_SLOT {sig}")
            if isinstance(bt,bool) or not isinstance(bt,int): raise RuntimeError(f"NULL_OR_INVALID_BLOCKTIME {sig}")
            r={"signature":sig,"slot":slot,"blockTime":bt,"err":raw.get("err")}
            if prev_bt is not None and bt>prev_bt:
                raise RuntimeError(f"GLOBAL_NON_MONOTONIC_TIME {bt}>{prev_bt} sig={sig}")
            if slice_first is None: slice_first=r
            slice_last=r
            if label=="older" and older_first is None: older_first=r
            slice_rows+=1; total_rows+=1
            coverage_max=bt if coverage_max is None else max(coverage_max,bt)
            coverage_min=bt if coverage_min is None else min(coverage_min,bt)

            d=day_of(bt)
            if current_date is None:
                current_date=d; current_newer=prev_row
            elif d!=current_date:
                # Current row is the immediate older program signature for the day just completed.
                manifest_days.append(finalize_day(current_date,current_rows,current_newer,r,current_sources))
                # Materialize any UTC days with zero program signatures between the two active days.
                gap_day=current_date-timedelta(days=1)
                while gap_day>d:
                    manifest_days.append(finalize_day(gap_day,[],prev_row,r,{label}))
                    gap_day-=timedelta(days=1)
                current_date=d
                current_rows=[]
                current_sources=set()
                current_newer=prev_row

            current_rows.append(r)
            current_sources.add(label)
            prev_bt=bt
            prev_row=r
    if label=="newer": newer_last=slice_last
    slice_stats.append({
      "label":label,"run_id":run_id,"artifact_id":artifact_id,"artifact_sha256":digest,
      "page_files":len(ps),"rows":slice_rows,
      "first":anchor(slice_first),"last":anchor(slice_last)
    })

if current_date is not None:
    manifest_days.append(finalize_day(current_date,current_rows,current_newer,None,current_sources))

if not manifest_days: raise RuntimeError("NO_DAILY_ENTRIES")
if newer_last is None or older_first is None: raise RuntimeError("MISSING_SLICE_JOIN_ROWS")
if newer_last["signature"]!=CURSOR_SIG:
    raise RuntimeError(f"NEWER_SLICE_LAST_NOT_FROZEN_CURSOR {newer_last['signature']}")
if older_first["blockTime"]>newer_last["blockTime"]:
    raise RuntimeError("OLDER_SLICE_STARTS_NEWER_THAN_CURSOR")
if older_first["signature"]==newer_last["signature"]:
    raise RuntimeError("CONTINUATION_INCLUDES_EXCLUSIVE_CURSOR")

manifest_days.sort(key=lambda x:x["date"])
dates=[d["date"] for d in manifest_days]
if len(dates)!=len(set(dates)): raise RuntimeError("DUPLICATE_DAY_ENTRY")

manifest={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "program_id":PROGRAM,
 "source_order":"newest_to_oldest; newer artifact then continuation artifact",
 "coverage":{"min_block_time":coverage_min,"max_block_time":coverage_max,
             "min_iso":datetime.fromtimestamp(coverage_min,timezone.utc).isoformat().replace("+00:00","Z"),
             "max_iso":datetime.fromtimestamp(coverage_max,timezone.utc).isoformat().replace("+00:00","Z")},
 "slice_join":{"frozen_cursor_signature":CURSOR_SIG,"newer_last":anchor(newer_last),"older_first":anchor(older_first)},
 "source_slices":slice_stats,
 "days":manifest_days
}
manifest_blob=canon(manifest_days)
manifest["days_sha256"]=sha(manifest_blob)
OUT.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"KAMINO_PROGRAM_SIGNATURE_DAILY_MANIFEST_PASS",
 "program_id":PROGRAM,
 "source_rows":total_rows,"source_page_files":total_pages,
 "daily_entries":len(manifest_days),
 "zero_program_tx_days":sum(d["row_count"]==0 for d in manifest_days),
 "anchor_pair_ready_days":sum(d["rpc_reconstruction_anchor_pair_ready"] for d in manifest_days),
 "coverage":manifest["coverage"],"days_sha256":manifest["days_sha256"],
 "first_date":manifest_days[0]["date"],"last_date":manifest_days[-1]["date"],
 "slice_join":manifest["slice_join"],
 "firewalls":{"prices":False,"amounts":False,"returns":False,"pnl":False,"direction":False,
              "market_outcomes":False,"liquidation_classification":False,"live_trading":False,
              "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
              "account_creation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
