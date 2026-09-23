#!/usr/bin/env python3
import argparse, json
from pathlib import Path

PASS_CENSUS="SAVE11_EVENT_CENSUS_FIRST_CHUNK_PASS"
PASS_LOCATOR="SAVE11_OFFICIAL_API_LOCATOR_CHUNK_PASS"
BOUNDARY="WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L"

def jsonl(path):
    p=Path(path)
    if not p.exists(): return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

ap=argparse.ArgumentParser()
ap.add_argument("--census-receipt",required=True)
ap.add_argument("--events",required=True)
ap.add_argument("--attempts",required=True)
ap.add_argument("--locator-receipt",required=True)
ap.add_argument("--locator",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()

cr=json.loads(Path(a.census_receipt).read_text(encoding="utf-8"))
lr=json.loads(Path(a.locator_receipt).read_text(encoding="utf-8"))
events=jsonl(a.events)
attempts=jsonl(a.attempts)
locator_obj=json.loads(Path(a.locator).read_text(encoding="utf-8"))
locator_rows=locator_obj.get("rows")
if not isinstance(locator_rows,list):
    raise SystemExit("LOCATOR_ROWS_NOT_LIST")

raw={}
for row in events+attempts:
    sig=row.get("signature")
    if not isinstance(sig,str): raise SystemExit("RAW_REFERENCE_INVALID_SIGNATURE")
    rec={"signature":sig,"slot":int(row["slot"]),"timestamp":int(row["blockTime"]),"classification":row["classification"]}
    if sig in raw and raw[sig]!=rec:
        raise SystemExit("RAW_REFERENCE_CONFLICTING_DUPLICATE")
    raw[sig]=rec

loc={}
for row in locator_rows:
    sig=row.get("signature")
    if not isinstance(sig,str): raise SystemExit("LOCATOR_INVALID_SIGNATURE")
    rec={"signature":sig,"slot":int(row["slot"]),"timestamp":int(row["timestamp"]),"success":bool(row["success"])}
    if sig in loc and loc[sig]!=rec:
        raise SystemExit("LOCATOR_CONFLICTING_DUPLICATE")
    loc[sig]=rec

missing=[]
mismatch=[]
found=0
for sig,r in sorted(raw.items()):
    l=loc.get(sig)
    if l is None:
        missing.append(sig)
        continue
    found+=1
    diffs={}
    if l["slot"]!=r["slot"]: diffs["slot"]={"raw":r["slot"],"locator":l["slot"]}
    if l["timestamp"]!=r["timestamp"]: diffs["timestamp"]={"raw":r["timestamp"],"locator":l["timestamp"]}
    if diffs: mismatch.append({"signature":sig,"diffs":diffs})

n=len(raw)
recall=(found/n) if n else 1.0
preconditions={
 "census_pass":cr.get("classification")==PASS_CENSUS,
 "locator_pass":lr.get("classification")==PASS_LOCATOR,
 "boundary_in_raw":BOUNDARY in raw,
 "boundary_in_locator":BOUNDARY in loc
}
ok=all(preconditions.values()) and not missing and not mismatch and found==n
receipt={
 "schema_version":"0.1",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"SAVE11_OFFICIAL_API_LOCATOR_RECALL_CALIBRATION_PASS" if ok else "SAVE11_OFFICIAL_API_LOCATOR_RECALL_CALIBRATION_FAIL",
 "window":{"start":"2024-07-19T19:30:52Z","end":"2024-07-20T00:00:00Z","semantics":"half_open"},
 "raw_reference_signatures":n,
 "raw_realized_events":len(events),
 "raw_failed_attempts":len(attempts),
 "locator_signatures":len(loc),
 "raw_found_in_locator":found,
 "raw_missing_from_locator":len(missing),
 "slot_or_timestamp_mismatches":len(mismatch),
 "locator_recall":recall,
 "preconditions":preconditions,
 "missing_signatures":missing,
 "mismatches":mismatch,
 "authority":"SECONDARY_LOCATOR_CALIBRATION_ONLY",
 "global_completeness_authorized":False,
 "firewalls":{"prices":False,"amounts":False,"balances":False,"returns":False,"pnl":False,"direction":False,
              "market_outcomes":False,"threshold_tuning":False,"live_trading":False,"orders":False,"wallets":False,
              "exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}
}
Path(a.out).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
if not ok: raise SystemExit(2)
