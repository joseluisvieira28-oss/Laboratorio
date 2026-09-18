#!/usr/bin/env python3
"""Adjudicate one bounded-census chunk for historical first-success authority.

SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED.
Consumes unchanged CSV from BIGQUERY_BOUNDED_CANDIDATE_CENSUS_V0_3.sql.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,pathlib
from collections import defaultdict
from datetime import datetime,timezone

PROGRAMS={
 "save_solend":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
 "marginfi_v2":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
 "kamino_lend":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
 "drift_v2":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH",
}
PREFIXES={
 "save_solend":{"LiquidateObligation":"0c","LiquidateObligationAndRedeemReserveCollateral":"11"},
 "marginfi_v2":{"lending_account_liquidate":"d6a997d5fba756db"},
 "kamino_lend":{"liquidate_obligation_and_redeem_reserve_collateral":"b1479abce2854a37"},
 "drift_v2":{
   "liquidate_perp":"4b2377f7bf128b02",
   "liquidate_spot":"6b00802923e5fb12",
   "liquidate_borrow_for_perp_pnl":"a911205acf94d11b",
   "liquidate_perp_pnl_for_deposit":"ed4bc6ebe9ba4b23",
 }
}
RETIRED={"b1479acce2854a37","0c2bb0539cfb750d","8e58a3a0df4b37e1"}
REQUIRED={
 "protocol","program_id","match_name","encoding","reference_prefix_hex","source_supported_from",
 "block_slot","block_timestamp","tx_signature","instruction_index","parent_index",
 "instruction_type","data","data_prefix_8_hex","status","err","status_err_consistency",
 "classification","instruction_location"
}

def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def ts(s):
    x=str(s).strip().replace(" UTC","+00:00")
    if " " in x and "T" not in x:x=x.replace(" ","T",1)
    if x.endswith("Z"):x=x[:-1]+"+00:00"
    d=datetime.fromisoformat(x)
    if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)
def nullish(v):return v is None or str(v).strip().lower() in {"","null","none"}
def asint(v):return None if nullish(v) else int(v)

def load(path,protocol,start,end):
    with path.open("r",encoding="utf-8-sig",newline="") as f: rows=[dict(x) for x in csv.DictReader(f)]
    if not rows:return []
    missing=REQUIRED-set(rows[0])
    if missing:raise RuntimeError(f"MISSING_COLUMNS:{sorted(missing)}")
    expected_program=PROGRAMS[protocol]; seen=set(); out=[]
    for n,r in enumerate(rows,1):
        if r["protocol"]!=protocol:raise RuntimeError(f"PROTOCOL_MISMATCH:{n}")
        if r["program_id"]!=expected_program:raise RuntimeError(f"PROGRAM_MISMATCH:{n}")
        name=r["match_name"];pref=r["reference_prefix_hex"].strip().lower()
        if name not in PREFIXES[protocol]:raise RuntimeError(f"UNEXPECTED_CLASS:{n}:{name}")
        if pref!=PREFIXES[protocol][name]:raise RuntimeError(f"PREFIX_MISMATCH:{n}:{name}:{pref}")
        if pref in RETIRED:raise RuntimeError(f"RETIRED_PREFIX_ACTIVE:{n}:{pref}")
        bts=ts(r["block_timestamp"])
        if not(start<=bts<end):raise RuntimeError(f"CHUNK_BOUNDS:{n}:{bts.isoformat()}")
        src=ts(r["source_supported_from"])
        status=r["status"].strip();err=str(r["err"]);cons=r["status_err_consistency"].strip()
        cls=r["classification"].strip()
        if cons=="STATUS_ERR_INCONSISTENT":
            expected="SOURCE_ANOMALY_FAIL_CLOSED"
        elif bts<src:
            expected="PRE_SOURCE_AUTHORITY_BOUNDARY_FAIL_CLOSED"
        elif status=="Fail" and err!="":
            expected="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"
        elif status=="Success" and err=="":
            expected="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_ONCHAIN_BOUNDARY_AND_RAW_CLASS_VALIDATION"
        else:
            expected="SOURCE_ANOMALY_FAIL_CLOSED"
        if cls!=expected:raise RuntimeError(f"CLASSIFICATION_MISMATCH:{n}:{cls}:{expected}")
        pi=asint(r["parent_index"]);ii=int(r["instruction_index"]);slot=int(r["block_slot"])
        loc="outer" if pi is None else "inner"
        if r["instruction_location"]!=loc:raise RuntimeError(f"LOCATION_MISMATCH:{n}")
        key=(slot,r["tx_signature"],ii,pi,name)
        if key in seen:raise RuntimeError(f"EXACT_DUPLICATE:{n}")
        seen.add(key)
        r["_ts"]=bts;r["_src"]=src;r["block_slot"]=slot;r["instruction_index"]=ii;r["parent_index"]=pi
        out.append(r)
    out.sort(key=lambda r:(r["_ts"],r["block_slot"],r["tx_signature"],-1 if r["parent_index"] is None else r["parent_index"],r["instruction_index"]))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True);ap.add_argument("--protocol",required=True,choices=sorted(PROGRAMS))
    ap.add_argument("--chunk-start",required=True);ap.add_argument("--chunk-end",required=True);ap.add_argument("--output",required=True)
    a=ap.parse_args();src=pathlib.Path(a.input).resolve();out=pathlib.Path(a.output).resolve()
    if not src.exists():raise RuntimeError("INPUT_NOT_FOUND")
    if out.exists():raise RuntimeError("OUTPUT_EXISTS")
    start=ts(a.chunk_start);end=ts(a.chunk_end)
    if not start<end:raise RuntimeError("INVALID_CHUNK_BOUNDS")
    if (end-start).total_seconds()>7*86400:raise RuntimeError("CHUNK_EXCEEDS_7_DAYS")
    out.mkdir(parents=True)
    rows=load(src,a.protocol,start,end)
    anomalies=[r for r in rows if r["classification"]=="SOURCE_ANOMALY_FAIL_CLOSED"]
    pre=[r for r in rows if r["classification"]=="PRE_SOURCE_AUTHORITY_BOUNDARY_FAIL_CLOSED"]
    failed=[r for r in rows if r["classification"]=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"]
    success=[r for r in rows if r["classification"]=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_ONCHAIN_BOUNDARY_AND_RAW_CLASS_VALIDATION"]
    earliest={}
    for r in success:
        n=r["match_name"]
        if n not in earliest:earliest[n]=r
    if anomalies:status="SOURCE_ANOMALY_FAIL_CLOSED"
    elif earliest:status="FIRST_SUCCESS_CANDIDATE_FOUND_RAW_REQUIRED"
    else:status="NO_SUCCESS_IN_CHUNK_CONTINUE_CHRONOLOGICALLY"
    first=[{
      "match_name":n,"reference_prefix_hex":r["reference_prefix_hex"],"block_timestamp":r["block_timestamp"],
      "block_slot":r["block_slot"],"tx_signature":r["tx_signature"],"instruction_index":r["instruction_index"],
      "parent_index":r["parent_index"],"instruction_location":r["instruction_location"],
      "classification":r["classification"]
    } for n,r in sorted(earliest.items())]
    receipt={
      "document_id":"DLS_FIRST_SUCCESS_CHUNK_RECEIPT_V0.1","status":status,"protocol":a.protocol,
      "chunk_start":a.chunk_start,"chunk_end_exclusive":a.chunk_end,
      "input_sha256":sha(src.read_bytes()),"rows":len(rows),"successful_rows":len(success),
      "failed_attempt_rows":len(failed),"pre_source_boundary_rows":len(pre),"source_anomaly_rows":len(anomalies),
      "earliest_success_candidates":first,"source_data_pass_granted":False,
      "governance":{"source_only":True,"outcome_blind":True,"prices":False,"returns":False,"pnl":False,
                    "direction":False,"live_trading":False,"orders":False,"wallets":False,"merge_main":False}
    }
    receipt["fingerprint"]=sha(canonical(receipt))
    (out/"DLS_FIRST_SUCCESS_CHUNK_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    if anomalies:raise SystemExit(2)

if __name__=="__main__":main()
