#!/usr/bin/env python3
import datetime as dt, hashlib, json, sys
from pathlib import Path

ROOT=Path(sys.argv[1])
BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
CENSUS=BASE/"MARGINFI_SAVE0C_SQD_EVENT_CENSUS_RECEIPT_V0.1.json"
QUEUE=BASE/"MARGINFI_SAVE0C_RAW_SAMPLE_QUEUE_V0.1.json"
CFG={
 "marginfi":{"lower":"2023-02-07T15:47:04Z","upper":"2025-01-01T00:00:00Z","prefix":"d6a997d5fba756db"},
 "save0c":{"lower":"2021-12-08T00:00:00Z","upper":"2025-01-01T00:00:00Z","prefix":"0c"}
}
def parse(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def addr_key(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def path_class(v): return "inner" if isinstance(v,list) and len(v)>1 else "outer"

all_parts=[]; accepted=[]; excluded=[]
for p in sorted(ROOT.rglob("*.json")):
    try:r=json.loads(p.read_text())
    except Exception:continue
    if r.get("protocol") not in CFG or not r.get("effective_start") or not r.get("effective_end"):
        continue
    all_parts.append((p,r))
    if (r.get("classification")=="SOURCE_PARTITION_PASS"
        and r.get("stream_complete") is True
        and int(r.get("anomaly_count") or 0)==0):
        accepted.append((p,r))
    else:
        excluded.append({"file":str(p),"protocol":r.get("protocol"),
                         "start":r.get("effective_start"),"end":r.get("effective_end"),
                         "classification":r.get("classification"),
                         "reason":"NON_AUTHORITATIVE_PARTIAL_TRANSPORT_EVIDENCE_EXCLUDED"})

summary={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
         "classification":"MARGINFI_SAVE0C_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE",
         "partition_count_seen":len(all_parts),"accepted_partition_count":len(accepted),
         "excluded_partial_partition_count":len(excluded),"excluded_partial_partitions":excluded,
         "evidence_selection_rule":"SOURCE_PARTITION_PASS_STREAM_COMPLETE_ANOMALY_ZERO_ONLY",
         "protocols":{},
         "firewall":{"prices":False,"balances":False,"token_amounts":False,"returns":False,"pnl":False,"direction":False,
         "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
         "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
         "post_outcome_tuning":False,"merge_main":False}}

queues={}; blocked=False
for protocol,cfg in CFG.items():
    ps=[(p,r) for p,r in accepted if r.get("protocol")==protocol]
    ps.sort(key=lambda pr:(parse(pr[1]["effective_start"]),parse(pr[1]["effective_end"]),str(pr[0])))
    lower=parse(cfg["lower"]); upper=parse(cfg["upper"]); cursor=lower
    gaps=[]; overlaps=[]; rows=[]; seen_ranges={}; duplicate_ranges=[]
    for p,r in ps:
        s=parse(r["effective_start"]); e=parse(r["effective_end"]); key=(r["effective_start"],r["effective_end"])
        if key in seen_ranges:
            duplicate_ranges.append({"start":key[0],"end":key[1],"existing":seen_ranges[key],"duplicate":str(p)})
            continue
        seen_ranges[key]=str(p)
        if e<=lower or s>=upper: continue
        if s>cursor:
            gaps.append({"expected_start":cursor.isoformat().replace("+00:00","Z"),"observed_start":r["effective_start"]})
            if e>cursor: cursor=e
        elif s<cursor:
            overlaps.append({"cursor":cursor.isoformat().replace("+00:00","Z"),
                             "observed_start":r["effective_start"],"observed_end":r["effective_end"],"file":str(p)})
            if e>cursor: cursor=e
        else:
            cursor=e
        rows.extend(r.get("rows") or [])
    if cursor<upper:
        gaps.append({"expected_start":cursor.isoformat().replace("+00:00","Z"),"observed_end":cfg["upper"]})

    ded={}; dup_keys=[]; anomalies=[]; successful=[]; failed=[]
    for r in rows:
        sig=r.get("signature"); addr=r.get("instructionAddress")
        key=(protocol,sig,addr_key(addr))
        if key in ded:
            dup_keys.append(key)
            if ded[key]!=r: anomalies.append({"reason":"dedup_key_collision","key":key})
        ded[key]=r
    for r in ded.values():
        try:t=parse(r.get("timestamp"))
        except Exception:
            anomalies.append({"reason":"bad_timestamp","signature":r.get("signature")}); continue
        if not (lower<=t<upper):
            anomalies.append({"reason":"outside_window","signature":r.get("signature"),"timestamp":r.get("timestamp")})
        st=r.get("classification")
        if st=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":
            successful.append(r)
        elif st=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED":
            failed.append(r)
        else:
            anomalies.append({"reason":"unexpected_row_class","signature":r.get("signature"),"classification":st})

    successful.sort(key=lambda r:(parse(r["timestamp"]),r.get("slot",-1),r.get("signature",""),addr_key(r.get("instructionAddress"))))
    first=successful[0] if successful else None; last=successful[-1] if successful else None
    bysig={}
    for r in successful:
        sig=r.get("signature")
        if not sig: continue
        ent=bysig.setdefault(sig,{"protocol":protocol,"signature":sig,"slot":r.get("slot"),"timestamp":r.get("timestamp"),
                                  "expected_path_classes":set(),"instruction_addresses":[],"prefix":cfg["prefix"]})
        if ent["slot"]!=r.get("slot") or ent["timestamp"]!=r.get("timestamp"):
            anomalies.append({"reason":"signature_slot_time_inconsistent","signature":sig})
        ent["expected_path_classes"].add(path_class(r.get("instructionAddress")))
        ent["instruction_addresses"].append(r.get("instructionAddress"))
    for ent in bysig.values(): ent["expected_path_classes"]=sorted(ent["expected_path_classes"])
    sigs=sorted(bysig); mandatory=[]
    if first and first.get("signature"): mandatory.append(first["signature"])
    if last and last.get("signature") and last["signature"] not in mandatory: mandatory.append(last["signature"])
    rank=sorted((hashlib.sha256((protocol+":"+s).encode()).hexdigest(),s) for s in sigs if s not in mandatory)
    selected=mandatory+[s for _,s in rank[:30]]
    queues[protocol]={"mandatory_first":first.get("signature") if first else None,
                      "mandatory_last":last.get("signature") if last else None,
                      "selected_count":len(selected),"distinct_successful_signatures":len(sigs),
                      "entries":[bysig[s] for s in selected if s in bysig]}
    summary["protocols"][protocol]={
      "expected_start":cfg["lower"],"expected_end":cfg["upper"],
      "coverage_through":cursor.isoformat().replace("+00:00","Z"),
      "accepted_partition_count":len(ps),
      "gap_count":len(gaps),"gaps":gaps,
      "overlap_count":len(overlaps),"overlaps":overlaps,
      "duplicate_range_count":len(duplicate_ranges),"duplicate_ranges":duplicate_ranges,
      "successful_instruction_count":len(successful),
      "distinct_successful_signatures":len(sigs),
      "failed_attempt_count":len(failed),
      "anomaly_count":len(anomalies),
      "duplicate_instruction_key_count":len(dup_keys),
      "first_success":first,"last_success":last
    }
    if gaps or overlaps or duplicate_ranges or anomalies or dup_keys or not first:
        blocked=True

if blocked:
    summary["classification"]="MARGINFI_SAVE0C_SQD_EVENT_CENSUS_BLOCKED_FAIL_CLOSED"

CENSUS.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
QUEUE.write_text(json.dumps({"schema_version":"0.2","protocols":queues},indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":summary["classification"],
                  "seen":len(all_parts),"accepted":len(accepted),"excluded":len(excluded),
                  "protocols":{k:{"success":v["successful_instruction_count"],"failed":v["failed_attempt_count"],
                                  "first":v["first_success"],"gaps":v["gap_count"],
                                  "overlaps":v["overlap_count"],"anomalies":v["anomaly_count"]}
                               for k,v in summary["protocols"].items()}},indent=2))
if summary["classification"]!="MARGINFI_SAVE0C_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE":
    raise SystemExit(2)
