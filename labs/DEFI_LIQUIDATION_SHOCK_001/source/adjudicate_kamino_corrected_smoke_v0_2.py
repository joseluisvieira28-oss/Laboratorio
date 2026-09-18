#!/usr/bin/env python3
"""Adjudicate corrected Kamino BigQuery smoke-test CSV V0.2.

SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED.

Input must be exported unchanged from:
  BIGQUERY_KAMINO_CORRECTED_SMOKE_TEST_V0_2.sql

Outputs:
- receipt JSON
- successful reference candidates CSV (also directly verifier-compatible)
- failed attempts CSV
- anomalies CSV when present

No market prices, returns, PnL or direction are read or computed.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,pathlib
from datetime import datetime,timezone

PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
PROTOCOL="kamino_lend"
MATCH="liquidate_obligation_and_redeem_reserve_collateral"
PREFIX="b1479abce2854a37"
RETIRED="b1479acce2854a37"
SOURCE_FROM="2023-11-17T13:25:35Z"
REQUIRED={
 "protocol","program_id","match_name","reference_prefix_hex","source_supported_from",
 "block_slot","block_timestamp","tx_signature","instruction_index","parent_index",
 "instruction_location","instruction_type","data","data_prefix_8_hex","status","err","classification"
}

def sha256_bytes(b):return hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def nullish(v):
    return v is None or str(v).strip().lower() in {"","null","none"}
def as_int(v):
    return None if nullish(v) else int(v)
def parse_ts(v):
    s=str(v).strip().replace(" UTC","+00:00")
    if " " in s and "T" not in s:s=s.replace(" ","T",1)
    if s.endswith("Z"):s=s[:-1]+"+00:00"
    dt=datetime.fromisoformat(s)
    if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
def write_csv(path,rows,fields=None):
    if fields is None:
        fields=sorted({k for r in rows for k in r}) if rows else sorted(REQUIRED)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n",extrasaction="ignore")
        w.writeheader();w.writerows(rows)

def load(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rows=[dict(x) for x in csv.DictReader(f)]
    if not rows:
        return []
    missing=REQUIRED-set(rows[0])
    if missing:raise RuntimeError(f"MISSING_COLUMNS:{sorted(missing)}")
    seen=set();out=[]
    source_from=parse_ts(SOURCE_FROM)
    for n,r in enumerate(rows,1):
        if r["protocol"]!=PROTOCOL:raise RuntimeError(f"PROTOCOL_MISMATCH:{n}:{r['protocol']}")
        if r["program_id"]!=PROGRAM:raise RuntimeError(f"PROGRAM_MISMATCH:{n}")
        if r["match_name"]!=MATCH:raise RuntimeError(f"MATCH_NAME_MISMATCH:{n}")
        pref=r["reference_prefix_hex"].strip().lower()
        data_pref=r["data_prefix_8_hex"].strip().lower()
        if pref!=PREFIX:raise RuntimeError(f"REFERENCE_PREFIX_MISMATCH:{n}:{pref}")
        if data_pref!=PREFIX:raise RuntimeError(f"DATA_PREFIX_MISMATCH:{n}:{data_pref}")
        if RETIRED in (pref,data_pref):raise RuntimeError(f"RETIRED_PREFIX_PRESENT:{n}")
        if not str(r["data"]).strip():raise RuntimeError(f"EMPTY_DATA:{n}")
        slot=int(r["block_slot"]);ii=int(r["instruction_index"]);pi=as_int(r["parent_index"])
        loc="outer" if pi is None else "inner"
        if r["instruction_location"]!=loc:raise RuntimeError(f"LOCATION_MISMATCH:{n}")
        ts=parse_ts(r["block_timestamp"])
        if ts<source_from:raise RuntimeError(f"PRE_SOURCE_BOUNDARY_ROW:{n}:{ts.isoformat()}")
        status=r["status"].strip();err=str(r["err"])
        cls=r["classification"].strip()
        if status=="Success" and err=="":
            expected="SUCCESSFUL_REFERENCE_CANDIDATE_REQUIRES_RAW_VALIDATION"
        elif status=="Fail" and err!="":
            expected="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"
        else:
            expected="SOURCE_ANOMALY_FAIL_CLOSED"
        if cls!=expected:raise RuntimeError(f"CLASSIFICATION_MISMATCH:{n}:{cls}:{expected}")
        key=(slot,r["tx_signature"],ii,pi,pref)
        if key in seen:raise RuntimeError(f"EXACT_DUPLICATE_ROW:{n}")
        seen.add(key)
        r["block_slot"]=slot;r["instruction_index"]=ii;r["parent_index"]=pi
        out.append(r)
    out.sort(key=lambda r:(parse_ts(r["block_timestamp"]),r["block_slot"],r["tx_signature"],
                           -1 if r["parent_index"] is None else r["parent_index"],r["instruction_index"]))
    return out

def adjudicate(rows):
    success=[r for r in rows if r["classification"]=="SUCCESSFUL_REFERENCE_CANDIDATE_REQUIRES_RAW_VALIDATION"]
    failed=[r for r in rows if r["classification"]=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"]
    anomalies=[r for r in rows if r["classification"]=="SOURCE_ANOMALY_FAIL_CLOSED"]
    if anomalies:
        status="KAMINO_CORRECTED_SMOKE_SOURCE_ANOMALY_FAIL_CLOSED"
    elif not rows:
        status="KAMINO_CORRECTED_SMOKE_ZERO_CANDIDATES"
    elif success:
        status="KAMINO_CORRECTED_SMOKE_CANDIDATES_FOUND_RAW_VALIDATION_REQUIRED"
    else:
        status="KAMINO_CORRECTED_SMOKE_FAILED_ATTEMPTS_ONLY_NO_REALIZED_EVENT_IN_SMOKE_DAY"
    return status,success,failed,anomalies

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--input",required=True);ap.add_argument("--output",required=True)
    a=ap.parse_args();src=pathlib.Path(a.input).resolve();out=pathlib.Path(a.output).resolve()
    if not src.exists():raise RuntimeError("INPUT_NOT_FOUND")
    if out.exists():raise RuntimeError("OUTPUT_EXISTS")
    out.mkdir(parents=True)
    rows=load(src)
    status,success,failed,anomalies=adjudicate(rows)

    fields=[
      "protocol","program_id","match_name","reference_prefix_hex","source_supported_from",
      "block_slot","block_timestamp","tx_signature","instruction_index","parent_index",
      "instruction_location","instruction_type","data","data_prefix_8_hex","status","err","classification"
    ]
    write_csv(out/"KAMINO_CORRECTED_SMOKE_ALL_ROWS_V0.2.csv",rows,fields)
    write_csv(out/"KAMINO_SUCCESSFUL_REFERENCE_CANDIDATES_RAW_VERIFY_INPUT_V0.2.csv",success,fields)
    write_csv(out/"KAMINO_FAILED_ATTEMPTS_V0.2.csv",failed,fields)
    write_csv(out/"KAMINO_SOURCE_ANOMALIES_V0.2.csv",anomalies,fields)

    receipt={
      "document_id":"DLS_KAMINO_CORRECTED_SMOKE_RECEIPT_V0.2",
      "status":status,
      "input_sha256":sha256_bytes(src.read_bytes()),
      "rows":len(rows),
      "unique_signatures":len({r["tx_signature"] for r in rows}),
      "successful_reference_rows":len(success),
      "successful_unique_transactions":len({r["tx_signature"] for r in success}),
      "failed_attempt_rows":len(failed),
      "failed_unique_transactions":len({r["tx_signature"] for r in failed}),
      "source_anomaly_rows":len(anomalies),
      "program_id":PROGRAM,
      "correct_prefix":PREFIX,
      "retired_wrong_prefix":RETIRED,
      "source_supported_from":SOURCE_FROM,
      "raw_validation_required":bool(success),
      "source_data_pass_granted":False,
      "governance":{"source_only":True,"outcome_blind":True,"prices_queried":False,
        "returns_computed":False,"pnl_computed":False,"direction_tested":False,
        "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
        "merge_main":False}
    }
    receipt["fingerprint"]=sha256_bytes(canonical(receipt))
    (out/"DLS_KAMINO_CORRECTED_SMOKE_RECEIPT_V0.2.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    if anomalies:raise SystemExit(2)

if __name__=="__main__":main()
