#!/usr/bin/env python3
"""Generate deterministic chronological first-success source-probe queue.

SOURCE ONLY / OUTCOME BLIND. No network, prices, returns or PnL.
The queue uses 7-day max chunks and never skips dates.
"""
from __future__ import annotations
import csv,hashlib,json,pathlib
from datetime import datetime,timedelta,timezone

END=datetime(2025,1,1,tzinfo=timezone.utc)
CHUNK=timedelta(days=7)

PROGRAMS=[
 {
  "protocol":"save_solend",
  "program_id":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
  "start":"2021-12-08T00:00:00Z",
  "classes":"LiquidateObligation:0c;LiquidateObligationAndRedeemReserveCollateral:11"
 },
 {
  "protocol":"drift_v2",
  "program_id":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH",
  "start":"2022-11-04T15:17:54Z",
  "classes":"liquidate_perp:4b2377f7bf128b02;liquidate_spot:6b00802923e5fb12;liquidate_borrow_for_perp_pnl:a911205acf94d11b;liquidate_perp_pnl_for_deposit:ed4bc6ebe9ba4b23"
 },
 {
  "protocol":"marginfi_v2",
  "program_id":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
  "start":"2023-02-07T15:47:04Z",
  "classes":"lending_account_liquidate:d6a997d5fba756db"
 },
 {
  "protocol":"kamino_lend",
  "program_id":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
  "start":"2023-11-17T13:25:35Z",
  "classes":"liquidate_obligation_and_redeem_reserve_collateral:b1479abce2854a37"
 }
]

def dt(s):
    return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)

def iso(x):
    return x.isoformat().replace("+00:00","Z")

def canonical(o):
    return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()

def build():
    rows=[]
    for p in PROGRAMS:
        cur=dt(p["start"]);seq=0
        while cur<END:
            nxt=min(cur+CHUNK,END)
            seq+=1
            rows.append({
              "protocol":p["protocol"],
              "program_id":p["program_id"],
              "chunk_sequence":seq,
              "chunk_start_utc":iso(cur),
              "chunk_end_utc_exclusive":iso(nxt),
              "max_chunk_days":7,
              "candidate_sql":"BIGQUERY_BOUNDED_CANDIDATE_CENSUS_V0_3.sql",
              "active_reference_classes":p["classes"],
              "execution_state":"NOT_EXECUTED",
              "estimated_bytes":"PENDING_DRY_RUN",
              "result_file":"",
              "notes":"Execute strictly in ascending sequence while unresolved historically applicable class remains."
            })
            cur=nxt
    return rows

def main():
    here=pathlib.Path(__file__).resolve().parent
    out=here.parent/"FIRST_SUCCESS_PROBE_QUEUE_V0.1.csv"
    meta=here.parent/"FIRST_SUCCESS_PROBE_QUEUE_V0.1.json"
    rows=build()
    fields=list(rows[0])
    with out.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
    summary={}
    for p in PROGRAMS:
        pr=[r for r in rows if r["protocol"]==p["protocol"]]
        summary[p["protocol"]]={
          "chunks":len(pr),
          "first_chunk_start":pr[0]["chunk_start_utc"],
          "final_chunk_end":pr[-1]["chunk_end_utc_exclusive"]
        }
    doc={
      "document_id":"DLS_FIRST_SUCCESS_PROBE_QUEUE_V0.1",
      "status":"GENERATED_NOT_EXECUTED",
      "chunk_max_days":7,
      "frozen_end_exclusive":"2025-01-01T00:00:00Z",
      "rows":len(rows),
      "by_protocol":summary,
      "queue_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
      "governance":{
        "source_only":True,"outcome_blind":True,"prices":False,"returns":False,
        "pnl":False,"direction":False,"live_trading":False,"merge_main":False
      }
    }
    doc["fingerprint"]=hashlib.sha256(canonical(doc)).hexdigest()
    meta.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(doc,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
