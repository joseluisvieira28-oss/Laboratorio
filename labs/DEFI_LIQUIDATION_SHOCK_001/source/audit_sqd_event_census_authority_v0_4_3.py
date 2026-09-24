#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(sys.argv[1])
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_SQD_EVENT_CENSUS_AUTHORITY_AUDIT_V0.4.3.json")

CFG={
 "kamino":{
   "start":"2023-11-17T14:48:24Z",
   "start_date":"2023-11-17",
   "end":"2025-01-01T00:00:00Z",
   "end_date":"2025-01-01",
   "prefix":"b1479abce2854a37",
   "first_sig":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
   "first_slot":230572965,
   "first_ts":"2023-11-17T14:48:24Z",
 },
 "save11":{
   "start":"2024-07-19T19:30:52Z",
   "start_date":"2024-07-19",
   "end":"2025-01-01T00:00:00Z",
   "end_date":"2025-01-01",
   "prefix":"11",
   "first_sig":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
   "first_slot":278496102,
   "first_ts":"2024-07-19T19:30:52Z",
 }
}

def iso(s):
    return dt.datetime.fromisoformat(s.replace("Z","+00:00"))

def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def expected_days(a,b):
    d=dt.date.fromisoformat(a); e=dt.date.fromisoformat(b); out=[]
    while d<e:
        out.append(d.isoformat())
        d+=dt.timedelta(days=1)
    return out

errors=[]
warnings=[]
protocol_reports={}
manifests=sorted(ROOT.rglob("MANIFEST.json"))

for protocol,cfg in CFG.items():
    pman=[]
    for mp in manifests:
        try:
            m=json.loads(mp.read_text())
        except Exception as e:
            errors.append({"protocol":protocol,"manifest":str(mp),"reason":"manifest_json_error","detail":type(e).__name__})
            continue
        if m.get("protocol")==protocol:
            pman.append((mp,m))

    days={}
    duplicate_days=[]
    total_manifest_success=0
    total_manifest_failed=0
    total_manifest_anomaly=0
    rows=[]

    for mp,m in pman:
        if m.get("schema_version")!="0.4.3":
            errors.append({"protocol":protocol,"manifest":str(mp),"reason":"bad_manifest_schema","value":m.get("schema_version")})
        if m.get("classification")!="PARTITION_COMPLETE":
            errors.append({"protocol":protocol,"manifest":str(mp),"reason":"partition_not_complete","value":m.get("classification")})
        chunks=m.get("chunks")
        if not isinstance(chunks,list):
            errors.append({"protocol":protocol,"manifest":str(mp),"reason":"chunks_not_list"})
            continue
        if m.get("chunk_count")!=len(chunks):
            errors.append({"protocol":protocol,"manifest":str(mp),"reason":"chunk_count_mismatch","declared":m.get("chunk_count"),"actual":len(chunks)})

        chunk_success=chunk_failed=chunk_anomaly=0
        for ch in chunks:
            day=ch.get("day")
            if day in days:
                duplicate_days.append(day)
                continue
            fp=mp.parent/ch.get("file","")
            if not fp.exists():
                errors.append({"protocol":protocol,"day":day,"reason":"missing_chunk_file"})
                continue
            actual_sha=sha256_file(fp)
            if actual_sha!=ch.get("sha256"):
                errors.append({"protocol":protocol,"day":day,"reason":"chunk_sha_mismatch","expected":ch.get("sha256"),"actual":actual_sha})
                continue

            try:
                rec=json.loads(fp.read_text())
            except Exception as e:
                errors.append({"protocol":protocol,"day":day,"reason":"receipt_json_error","detail":type(e).__name__})
                continue

            days[day]=rec
            if rec.get("schema_version")!="0.4.3":
                errors.append({"protocol":protocol,"day":day,"reason":"bad_receipt_schema","value":rec.get("schema_version")})
            if rec.get("protocol")!=protocol:
                errors.append({"protocol":protocol,"day":day,"reason":"receipt_protocol_mismatch","value":rec.get("protocol")})
            if rec.get("classification")!="SOURCE_CHUNK_PASS":
                errors.append({"protocol":protocol,"day":day,"reason":"receipt_not_pass","value":rec.get("classification")})
            if rec.get("stream_complete") is not True:
                errors.append({"protocol":protocol,"day":day,"reason":"stream_not_complete","value":rec.get("stream_complete")})
            if rec.get("anomaly_count")!=0:
                errors.append({"protocol":protocol,"day":day,"reason":"receipt_anomaly_count_nonzero","value":rec.get("anomaly_count")})

            ds=day+"T00:00:00Z"
            de=(dt.date.fromisoformat(day)+dt.timedelta(days=1)).isoformat()+"T00:00:00Z"
            if rec.get("day_start")!=ds or rec.get("day_end")!=de:
                errors.append({"protocol":protocol,"day":day,"reason":"receipt_day_boundary_mismatch","day_start":rec.get("day_start"),"day_end":rec.get("day_end")})

            term=rec.get("termination_evidence") or []
            for ev in term:
                reason=ev.get("reason")
                status=ev.get("http_status")
                valid=(reason=="EMPTY_NDJSON_DOCUMENTED_STREAM_TERMINATION" and status==200) or (reason=="NO_CONTENT_DOCUMENTED_STREAM_TERMINATION" and status==204)
                if not valid:
                    errors.append({"protocol":protocol,"day":day,"reason":"invalid_termination_evidence","evidence":ev})

            rr=rec.get("rows") or []
            success_rows=[x for x in rr if x.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"]
            failed_rows=[x for x in rr if x.get("classification")=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"]
            other_rows=[x for x in rr if x.get("classification") not in (
                "SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION",
                "LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"
            )]
            if other_rows:
                errors.append({"protocol":protocol,"day":day,"reason":"unknown_row_classification","count":len(other_rows)})
            if rec.get("successful_instruction_count")!=len(success_rows):
                errors.append({"protocol":protocol,"day":day,"reason":"receipt_success_count_mismatch","declared":rec.get("successful_instruction_count"),"actual":len(success_rows)})
            if rec.get("failed_attempt_count")!=len(failed_rows):
                errors.append({"protocol":protocol,"day":day,"reason":"receipt_failed_count_mismatch","declared":rec.get("failed_attempt_count"),"actual":len(failed_rows)})
            if ch.get("successful_instruction_count")!=len(success_rows) or ch.get("failed_attempt_count")!=len(failed_rows) or ch.get("anomaly_count")!=0:
                errors.append({"protocol":protocol,"day":day,"reason":"manifest_chunk_counter_mismatch"})

            for r in rr:
                sig=r.get("signature")
                addr=r.get("instructionAddress")
                slot=r.get("slot")
                ts=r.get("timestamp")
                if not isinstance(sig,str) or not sig:
                    errors.append({"protocol":protocol,"day":day,"reason":"bad_signature"})
                if not isinstance(addr,list) or not addr:
                    errors.append({"protocol":protocol,"day":day,"signature":sig,"reason":"bad_instruction_address","value":addr})
                if not isinstance(slot,int):
                    errors.append({"protocol":protocol,"day":day,"signature":sig,"reason":"bad_slot","value":slot})
                if r.get("decoded_prefix_hex")!=cfg["prefix"]:
                    errors.append({"protocol":protocol,"day":day,"signature":sig,"reason":"decoded_prefix_mismatch","value":r.get("decoded_prefix_hex")})
                try:
                    t=iso(ts)
                except Exception:
                    errors.append({"protocol":protocol,"day":day,"signature":sig,"reason":"bad_timestamp","value":ts})
                    continue
                day0=iso(ds); day1=iso(de)
                if not (day0<=t<day1):
                    errors.append({"protocol":protocol,"day":day,"signature":sig,"reason":"row_outside_receipt_day","timestamp":ts})
                if not (iso(cfg["start"])<=t<iso(cfg["end"])):
                    errors.append({"protocol":protocol,"day":day,"signature":sig,"reason":"row_outside_authoritative_interval","timestamp":ts})

                cls=r.get("classification")
                if cls=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":
                    if r.get("transactionErr") is not None or r.get("instructionError") is not None or r.get("isCommitted") is not True:
                        errors.append({"protocol":protocol,"day":day,"signature":sig,"reason":"success_semantics_mismatch"})
                elif cls=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED":
                    fully_successful=(r.get("transactionErr") is None and r.get("instructionError") is None and r.get("isCommitted") is True)
                    if fully_successful:
                        errors.append({"protocol":protocol,"day":day,"signature":sig,"reason":"failed_row_is_fully_successful"})

            rows.extend(rr)
            chunk_success+=len(success_rows)
            chunk_failed+=len(failed_rows)
            chunk_anomaly+=rec.get("anomaly_count",0)

        if m.get("successful_instruction_count")!=chunk_success:
            errors.append({"protocol":protocol,"manifest":str(mp),"reason":"manifest_success_count_mismatch","declared":m.get("successful_instruction_count"),"actual":chunk_success})
        if m.get("failed_attempt_count")!=chunk_failed:
            errors.append({"protocol":protocol,"manifest":str(mp),"reason":"manifest_failed_count_mismatch","declared":m.get("failed_attempt_count"),"actual":chunk_failed})
        if m.get("anomaly_count")!=chunk_anomaly:
            errors.append({"protocol":protocol,"manifest":str(mp),"reason":"manifest_anomaly_count_mismatch","declared":m.get("anomaly_count"),"actual":chunk_anomaly})

        total_manifest_success+=chunk_success
        total_manifest_failed+=chunk_failed
        total_manifest_anomaly+=chunk_anomaly

    exp=expected_days(cfg["start_date"],cfg["end_date"])
    missing=[d for d in exp if d not in days]
    extras=sorted(set(days)-set(exp))
    if duplicate_days:
        errors.append({"protocol":protocol,"reason":"duplicate_days","days":sorted(set(duplicate_days))})
    if missing:
        errors.append({"protocol":protocol,"reason":"missing_days","days":missing})
    if extras:
        errors.append({"protocol":protocol,"reason":"extra_days","days":extras})

    keys=set(); dup_keys=[]
    for r in rows:
        key=(protocol,r.get("signature"),json.dumps(r.get("instructionAddress"),separators=(",",":")))
        if key in keys:
            dup_keys.append(key)
        keys.add(key)
    if dup_keys:
        errors.append({"protocol":protocol,"reason":"duplicate_instruction_keys","count":len(dup_keys)})

    first=[
      r for r in rows
      if r.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"
      and r.get("signature")==cfg["first_sig"]
      and r.get("slot")==cfg["first_slot"]
      and r.get("timestamp")==cfg["first_ts"]
    ]
    if len(first)!=1:
        errors.append({"protocol":protocol,"reason":"known_first_success_exact_match_count","count":len(first)})

    success_count=sum(1 for r in rows if r.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION")
    failed_count=sum(1 for r in rows if r.get("classification")=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED")
    protocol_reports[protocol]={
      "partition_manifest_count":len(pman),
      "expected_days":len(exp),
      "completed_days":len(days),
      "successful_instruction_count":success_count,
      "failed_attempt_count":failed_count,
      "anomaly_count":0,
      "known_first_success_exact":len(first)==1,
      "duplicate_instruction_key_count":len(dup_keys),
      "missing_day_count":len(missing),
      "extra_day_count":len(extras),
    }

classification="KAMINO_SAVE11_V043_AUTHORITY_AUDIT_PASS" if not errors else "KAMINO_SAVE11_V043_AUTHORITY_AUDIT_FAIL_CLOSED"
receipt={
  "schema_version":"0.4.3",
  "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "classification":classification,
  "manifest_count":len(manifests),
  "protocols":protocol_reports,
  "error_count":len(errors),
  "errors":errors,
  "warnings":warnings,
  "firewall":{
    "prices":False,"returns":False,"pnl":False,"direction":False,
    "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,
    "live_trading":False,"orders":False,"wallets":False,
    "exchange_mutation":False,"paid_source":False,"account_creation":False,
    "merge_main":False
  }
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
  "classification":classification,
  "manifest_count":len(manifests),
  "error_count":len(errors),
  "protocols":protocol_reports
},indent=2))
if errors:
    raise SystemExit(2)
