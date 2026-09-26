#!/usr/bin/env python3
import datetime as dt, gc, hashlib, heapq, json, sys
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
def rank_hex(protocol,sig): return hashlib.sha256((protocol+":"+sig).encode()).hexdigest()

# Pass 1: metadata only. Never retain rows across files.
all_parts=[]; accepted=[]; excluded=[]
for p in sorted(ROOT.rglob("*.json")):
    try:
        with p.open("r",encoding="utf-8") as fh: r=json.load(fh)
    except Exception:
        continue
    if r.get("protocol") not in CFG or not r.get("effective_start") or not r.get("effective_end"):
        del r; gc.collect(); continue
    meta={"path":str(p),"protocol":r.get("protocol"),
          "start":r.get("effective_start"),"end":r.get("effective_end"),
          "classification":r.get("classification"),"stream_complete":r.get("stream_complete"),
          "anomaly_count":int(r.get("anomaly_count") or 0)}
    all_parts.append(meta)
    if meta["classification"]=="SOURCE_PARTITION_PASS" and meta["stream_complete"] is True and meta["anomaly_count"]==0:
        accepted.append(meta)
    else:
        excluded.append({**meta,"reason":"NON_AUTHORITATIVE_PARTIAL_TRANSPORT_EVIDENCE_EXCLUDED"})
    del r; gc.collect()

summary={"schema_version":"0.3","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
         "classification":"MARGINFI_SAVE0C_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE",
         "partition_count_seen":len(all_parts),"accepted_partition_count":len(accepted),
         "excluded_partial_partition_count":len(excluded),"excluded_partial_partitions":excluded,
         "evidence_selection_rule":"SOURCE_PARTITION_PASS_STREAM_COMPLETE_ANOMALY_ZERO_ONLY",
         "aggregation_mode":"STREAMING_FILE_BY_FILE_BOUNDED_MEMORY",
         "protocols":{},
         "firewall":{"prices":False,"balances":False,"token_amounts":False,"returns":False,"pnl":False,"direction":False,
         "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
         "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
         "post_outcome_tuning":False,"merge_main":False}}

queues={}; globally_blocked=False
for protocol,cfg in CFG.items():
    lower=parse(cfg["lower"]); upper=parse(cfg["upper"])
    ps=[x for x in accepted if x["protocol"]==protocol]
    ps.sort(key=lambda x:(parse(x["start"]),parse(x["end"]),x["path"]))

    # Exact range selection and chronology first, before reading any rows.
    cursor=lower; gaps=[]; overlaps=[]; duplicate_ranges=[]; seen_ranges={}; selected=[]
    for m in ps:
        s=parse(m["start"]); e=parse(m["end"]); key=(m["start"],m["end"])
        if key in seen_ranges:
            duplicate_ranges.append({"start":m["start"],"end":m["end"],"existing":seen_ranges[key],"duplicate":m["path"]})
            continue
        seen_ranges[key]=m["path"]
        if e<=lower or s>=upper: continue
        if s>cursor:
            gaps.append({"expected_start":cursor.isoformat().replace("+00:00","Z"),"observed_start":m["start"]})
            if e>cursor: cursor=e
        elif s<cursor:
            overlaps.append({"cursor":cursor.isoformat().replace("+00:00","Z"),"observed_start":m["start"],
                             "observed_end":m["end"],"file":m["path"]})
            if e>cursor: cursor=e
        else:
            cursor=e
        selected.append(m)
    if cursor<upper:
        gaps.append({"expected_start":cursor.isoformat().replace("+00:00","Z"),"observed_end":cfg["upper"]})

    success_count=0; failed_count=0; anomalies=[]
    success_signatures=set()
    top_heap=[] # max-heap emulation: (-rank_int, signature)
    top_sigs=set()
    meta_by_sig={}
    first_row=None; last_row=None
    first_sig=None; last_sig=None
    duplicate_instruction_key_count=0

    # Coverage must be exact before rows can be authoritative.
    coverage_ok=not gaps and not overlaps and not duplicate_ranges
    if coverage_ok:
        for m in selected:
            p=Path(m["path"])
            with p.open("r",encoding="utf-8") as fh: part=json.load(fh)
            local_seen=set()
            rows=part.get("rows") or []
            for r in rows:
                sig=r.get("signature"); addr=r.get("instructionAddress")
                key=(protocol,sig,addr_key(addr))
                kh=hashlib.sha256(json.dumps(key,separators=(",",":"),sort_keys=True).encode()).digest()
                if kh in local_seen:
                    duplicate_instruction_key_count+=1
                    continue
                local_seen.add(kh)
                try:t=parse(r.get("timestamp"))
                except Exception:
                    anomalies.append({"reason":"bad_timestamp","signature":sig}); continue
                if not (lower<=t<upper):
                    anomalies.append({"reason":"outside_window","signature":sig,"timestamp":r.get("timestamp")})
                st=r.get("classification")
                if st=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":
                    success_count+=1
                    if not sig:
                        anomalies.append({"reason":"successful_row_missing_signature"}); continue
                    sh=hashlib.sha256(sig.encode()).digest()
                    success_sig_hashes.add(sh)
                    if first_row is None or (t,r.get("slot",-1),sig,addr_key(addr)) < (parse(first_row["timestamp"]),first_row.get("slot",-1),first_row.get("signature",""),addr_key(first_row.get("instructionAddress"))):
                        first_row=r; first_sig=sig
                    if last_row is None or (t,r.get("slot",-1),sig,addr_key(addr)) > (parse(last_row["timestamp"]),last_row.get("slot",-1),last_row.get("signature",""),addr_key(last_row.get("instructionAddress"))):
                        last_row=r; last_sig=sig

                    rv=int(rank_hex(protocol,sig),16)
                    if sig in top_sigs:
                        pass
                    elif len(top_heap)<30:
                        heapq.heappush(top_heap,(-rv,sig)); top_sigs.add(sig)
                    elif rv < -top_heap[0][0]:
                        _,old=heapq.heapreplace(top_heap,(-rv,sig)); top_sigs.discard(old); top_sigs.add(sig)

                    if sig in top_sigs or sig==first_sig or sig==last_sig:
                        ent=meta_by_sig.setdefault(sig,{"protocol":protocol,"signature":sig,"slot":r.get("slot"),
                            "timestamp":r.get("timestamp"),"expected_path_classes":set(),"instruction_addresses":[],
                            "prefix":cfg["prefix"]})
                        if ent["slot"]!=r.get("slot") or ent["timestamp"]!=r.get("timestamp"):
                            anomalies.append({"reason":"signature_slot_time_inconsistent","signature":sig})
                        ent["expected_path_classes"].add(path_class(addr))
                        ent["instruction_addresses"].append(addr)
                elif st=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED":
                    failed_count+=1
                else:
                    anomalies.append({"reason":"unexpected_row_class","signature":sig,"classification":st})
            del rows,part,local_seen
            gc.collect()

    # First/last signatures might have been replaced before their full same-signature metadata was retained.
    # Re-scan only if needed to assemble exact RAW queue metadata for mandatory first/last/top30.
    target_sigs=set(top_sigs)
    if first_sig: target_sigs.add(first_sig)
    if last_sig: target_sigs.add(last_sig)
    meta_by_sig={s:{"protocol":protocol,"signature":s,"slot":None,"timestamp":None,
                    "expected_path_classes":set(),"instruction_addresses":[],"prefix":cfg["prefix"]} for s in target_sigs}
    if coverage_ok and target_sigs:
        for m in selected:
            with Path(m["path"]).open("r",encoding="utf-8") as fh: part=json.load(fh)
            for r in part.get("rows") or []:
                sig=r.get("signature")
                if sig not in target_sigs or r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":
                    continue
                ent=meta_by_sig[sig]
                if ent["slot"] is None:
                    ent["slot"]=r.get("slot"); ent["timestamp"]=r.get("timestamp")
                elif ent["slot"]!=r.get("slot") or ent["timestamp"]!=r.get("timestamp"):
                    anomalies.append({"reason":"signature_slot_time_inconsistent","signature":sig})
                ent["expected_path_classes"].add(path_class(r.get("instructionAddress")))
                ent["instruction_addresses"].append(r.get("instructionAddress"))
            del part; gc.collect()

    for ent in meta_by_sig.values():
        ent["expected_path_classes"]=sorted(ent["expected_path_classes"])

    ordered_top=sorted(top_sigs,key=lambda s:(rank_hex(protocol,s),s))
    selected_sigs=[]
    if first_sig: selected_sigs.append(first_sig)
    if last_sig and last_sig not in selected_sigs: selected_sigs.append(last_sig)
    selected_sigs += [s for s in ordered_top if s not in selected_sigs]
    entries=[meta_by_sig[s] for s in selected_sigs if s in meta_by_sig]
    queues[protocol]={"mandatory_first":first_sig,"mandatory_last":last_sig,
                      "selected_count":len(entries),"distinct_successful_signatures":len(success_signatures),
                      "entries":entries}

    summary["protocols"][protocol]={
      "expected_start":cfg["lower"],"expected_end":cfg["upper"],
      "coverage_through":cursor.isoformat().replace("+00:00","Z"),
      "accepted_partition_count":len(ps),"selected_partition_count":len(selected),
      "gap_count":len(gaps),"gaps":gaps,"overlap_count":len(overlaps),"overlaps":overlaps,
      "duplicate_range_count":len(duplicate_ranges),"duplicate_ranges":duplicate_ranges,
      "successful_instruction_count":success_count,
      "distinct_successful_signatures":len(success_sig_hashes),
      "failed_attempt_count":failed_count,"anomaly_count":len(anomalies),
      "duplicate_instruction_key_count":duplicate_instruction_key_count,
      "first_success":first_row,"last_success":last_row
    }
    if (not coverage_ok or anomalies or duplicate_instruction_key_count or first_row is None):
        globally_blocked=True
    del success_signatures,meta_by_sig,top_heap,top_sigs
    gc.collect()

if globally_blocked:
    summary["classification"]="MARGINFI_SAVE0C_SQD_EVENT_CENSUS_BLOCKED_FAIL_CLOSED"

CENSUS.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
QUEUE.write_text(json.dumps({"schema_version":"0.3","protocols":queues},indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":summary["classification"],
                  "seen":len(all_parts),"accepted":len(accepted),"excluded":len(excluded),
                  "protocols":{k:{"success":v["successful_instruction_count"],"failed":v["failed_attempt_count"],
                                  "distinct_success_signatures":v["distinct_successful_signatures"],
                                  "first":v["first_success"],"gaps":v["gap_count"],
                                  "overlaps":v["overlap_count"],"anomalies":v["anomaly_count"]}
                               for k,v in summary["protocols"].items()}},indent=2))
if summary["classification"]!="MARGINFI_SAVE0C_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE":
    raise SystemExit(2)
