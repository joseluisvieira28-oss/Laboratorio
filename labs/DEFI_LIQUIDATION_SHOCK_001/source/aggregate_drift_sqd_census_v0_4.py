#!/usr/bin/env python3
import datetime as dt, hashlib, heapq, json, sys
from pathlib import Path

ROOT=Path(sys.argv[1])
BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
CENSUS=BASE/"DRIFT_SQD_EVENT_CENSUS_RECEIPT_V0.1.json"
QUEUE=BASE/"DRIFT_RAW_SAMPLE_QUEUE_V0.1.json"
LOWER=dt.datetime.fromisoformat("2022-11-04T15:17:54+00:00")
UPPER=dt.datetime.fromisoformat("2025-01-01T00:00:00+00:00")
CLASSES={
 "liquidate_perp":"4b2377f7bf128b02",
 "liquidate_spot":"6b00802923e5fb12",
 "liquidate_borrow_for_perp_pnl":"a911205acf94d11b",
 "liquidate_perp_pnl_for_deposit":"ed4bc6ebe9ba4b23",
}
SUCCESS="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"
FAILED="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"

def parse(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def sha_file(p):
    h=hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda:fh.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def addr_key(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def path_class(v): return "inner" if isinstance(v,list) and len(v)>1 else "outer"
def row_order(r): return (parse(r["timestamp"]),r.get("slot",-1),r.get("signature",""),addr_key(r.get("instructionAddress")))
def rank_int(cls,sig): return int(hashlib.sha256(("drift:"+cls+":"+sig).encode()).hexdigest(),16)

all_manifests=[];accepted=[];excluded=[]
for mp in sorted(ROOT.rglob("MANIFEST.json")):
    try:
        with mp.open("r",encoding="utf-8") as fh:m=json.load(fh)
    except Exception:continue
    if m.get("protocol")!="drift":continue
    all_manifests.append((mp,m))
    if m.get("classification")=="PARTITION_COMPLETE":accepted.append((mp,m))
    else:excluded.append({"manifest":str(mp),"classification":m.get("classification"),
                          "reason":"NON_AUTHORITATIVE_PARTIAL_TRANSPORT_EVIDENCE_EXCLUDED"})

bad_hash=[];chunk_errors=[];duplicate_slices=[];source_anomalies=[];slices={}
for mp,m in accepted:
    base=mp.parent
    for ch in m.get("chunks",[]):
        k=(ch.get("start"),ch.get("end"));fp=base/ch["file"]
        if not fp.exists():
            bad_hash.append({"slice":k,"reason":"missing_file","manifest":str(mp)});continue
        actual=sha_file(fp)
        if actual!=ch.get("sha256"):
            bad_hash.append({"slice":k,"reason":"sha_mismatch","file":str(fp)});continue
        with fp.open("r",encoding="utf-8") as fh:rec=json.load(fh)
        if rec.get("classification")!="SOURCE_CHUNK_PASS" or rec.get("stream_complete") is not True:
            chunk_errors.append({"slice":k,"classification":rec.get("classification"),"file":str(fp)});continue
        if int(rec.get("anomaly_count") or 0)!=0:
            source_anomalies.append({"slice":k,"reason":"chunk_anomaly","count":rec.get("anomaly_count"),"file":str(fp)});continue
        if k in slices:
            duplicate_slices.append({"start":k[0],"end":k[1],"existing":str(slices[k]),"duplicate":str(fp)});continue
        slices[k]=fp

ordered=sorted(((parse(a),parse(b),a,b,fp) for (a,b),fp in slices.items()),key=lambda x:(x[0],x[1]))
cursor=LOWER;gaps=[];overlaps=[];selected=[]
for s,e,a,b,fp in ordered:
    if e<=LOWER or s>=UPPER:continue
    if s>cursor:
        gaps.append({"expected_start":cursor.isoformat().replace("+00:00","Z"),"observed_start":a})
    if s<cursor:
        overlaps.append({"cursor":cursor.isoformat().replace("+00:00","Z"),"observed_start":a,"observed_end":b,"file":str(fp)})
    if e>cursor:cursor=e
    selected.append((s,e,fp))
if cursor<UPPER:gaps.append({"expected_start":cursor.isoformat().replace("+00:00","Z"),"observed_end":UPPER.isoformat().replace("+00:00","Z")})

stats={c:{"success":0,"failed":0,"sigs":set(),"first":None,"last":None,"heap":[],"heap_sigs":set(),"anomalies":[]} for c in CLASSES}
chunk_count_mismatch=[]

if not (bad_hash or chunk_errors or duplicate_slices or source_anomalies or gaps or overlaps):
    for s,e,fp in selected:
        with fp.open("r",encoding="utf-8") as fh:rec=json.load(fh)
        local_success=local_failed=0
        for r in rec.get("rows") or []:
            cls=r.get("class")
            if cls not in CLASSES:
                source_anomalies.append({"reason":"unknown_class","file":str(fp),"class":cls});continue
            try:t=parse(r.get("timestamp"))
            except Exception:
                stats[cls]["anomalies"].append({"reason":"bad_timestamp","signature":r.get("signature"),"file":str(fp)});continue
            if not (s<=t<e) or not (LOWER<=t<UPPER):
                stats[cls]["anomalies"].append({"reason":"row_outside_slice","timestamp":r.get("timestamp"),"file":str(fp)});continue
            st=r.get("classification")
            if st==SUCCESS:
                local_success+=1;stats[cls]["success"]+=1
                sig=r.get("signature")
                if not isinstance(sig,str) or not sig:
                    stats[cls]["anomalies"].append({"reason":"missing_signature","file":str(fp)});continue
                first=stats[cls]["first"];last=stats[cls]["last"]
                if first is None or row_order(r)<row_order(first):stats[cls]["first"]=r
                if last is None or row_order(r)>row_order(last):stats[cls]["last"]=r
                if sig not in stats[cls]["sigs"]:
                    stats[cls]["sigs"].add(sig)
                    rv=rank_int(cls,sig);heap=stats[cls]["heap"]
                    if len(heap)<30:
                        heapq.heappush(heap,(-rv,sig))
                    elif rv < -heap[0][0]:
                        heapq.heapreplace(heap,(-rv,sig))
            elif st==FAILED:
                local_failed+=1;stats[cls]["failed"]+=1
            else:
                stats[cls]["anomalies"].append({"reason":"unexpected_state","state":st,"signature":r.get("signature"),"file":str(fp)})
        if local_success!=int(rec.get("successful_instruction_count") or 0) or local_failed!=int(rec.get("failed_attempt_count") or 0):
            chunk_count_mismatch.append({"file":str(fp),"computed_success":local_success,"receipt_success":rec.get("successful_instruction_count"),
                                         "computed_failed":local_failed,"receipt_failed":rec.get("failed_attempt_count")})

# Build deterministic target signatures.
targets={}
for cls,st in stats.items():
    mandatory=[]
    if st["first"] and st["first"].get("signature"):mandatory.append(st["first"]["signature"])
    if st["last"] and st["last"].get("signature") and st["last"]["signature"] not in mandatory:mandatory.append(st["last"]["signature"])
    ranked=sorted([(-neg,sig) for neg,sig in st["heap"]],key=lambda x:(x[0],x[1]))
    targets[cls]=mandatory+[sig for _,sig in ranked if sig not in mandatory]

meta={cls:{sig:{"signature":sig,"slot":None,"timestamp":None,"expected_path_classes":set(),
                     "instruction_addresses":[],"class":cls,"prefix":CLASSES[cls]} for sig in targets[cls]} for cls in CLASSES}

# Second pass only collects RAW sample metadata.
if not (bad_hash or chunk_errors or duplicate_slices or source_anomalies or gaps or overlaps or chunk_count_mismatch):
    target_sets={c:set(v) for c,v in targets.items()}
    for s,e,fp in selected:
        with fp.open("r",encoding="utf-8") as fh:rec=json.load(fh)
        for r in rec.get("rows") or []:
            cls=r.get("class");sig=r.get("signature")
            if cls not in target_sets or sig not in target_sets[cls] or r.get("classification")!=SUCCESS:continue
            ent=meta[cls][sig]
            if ent["slot"] is None:
                ent["slot"]=r.get("slot");ent["timestamp"]=r.get("timestamp")
            elif ent["slot"]!=r.get("slot") or ent["timestamp"]!=r.get("timestamp"):
                stats[cls]["anomalies"].append({"reason":"signature_slot_time_inconsistent","signature":sig})
            ent["expected_path_classes"].add(path_class(r.get("instructionAddress")))
            ent["instruction_addresses"].append(r.get("instructionAddress"))

queues={}
summary={"schema_version":"0.4","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
         "classification":"DRIFT_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE",
         "aggregation_mode":"COMPOSITIONAL_TWO_PASS_SUCCESS_SIGNATURE_ONLY",
         "evidence_selection_rule":"PARTITION_COMPLETE_ONLY",
         "manifest_count_seen":len(all_manifests),"accepted_manifest_count":len(accepted),
         "excluded_partial_manifest_count":len(excluded),"excluded_partial_manifests":excluded,
         "classes":{},
         "firewall":{"prices":False,"balances":False,"token_amounts":False,"returns":False,"pnl":False,"direction":False,
         "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
         "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
         "post_outcome_tuning":False,"merge_main":False}}
for cls,st in stats.items():
    for ent in meta[cls].values():ent["expected_path_classes"]=sorted(ent["expected_path_classes"])
    entries=[meta[cls][sig] for sig in targets[cls] if sig in meta[cls]]
    queues[cls]={"mandatory_first":st["first"].get("signature") if st["first"] else None,
                 "mandatory_last":st["last"].get("signature") if st["last"] else None,
                 "selected_count":len(entries),"distinct_successful_signatures":len(st["sigs"]),"entries":entries}
    summary["classes"][cls]={"discriminator":CLASSES[cls],"successful_instruction_count":st["success"],
                             "distinct_successful_signatures":len(st["sigs"]),"failed_attempt_count":st["failed"],
                             "anomaly_count":len(st["anomalies"]),"first_success":st["first"],"last_success":st["last"]}
    source_anomalies.extend({"class":cls,**x} for x in st["anomalies"])

summary.update({"coverage_start":LOWER.isoformat().replace("+00:00","Z"),"coverage_end":UPPER.isoformat().replace("+00:00","Z"),
 "coverage_through":cursor.isoformat().replace("+00:00","Z"),"accepted_slice_count":len(slices),
 "gap_count":len(gaps),"gaps":gaps,"overlap_count":len(overlaps),"overlaps":overlaps,
 "bad_chunk_hash":bad_hash,"chunk_errors":chunk_errors,
 "duplicate_slice_count":len(duplicate_slices),"duplicate_slices":duplicate_slices,
 "duplicate_instruction_key_count":0,
 "duplicate_instruction_key_authority":"FROZEN_COLLECTOR_WITHIN_SLICE_DEDUP_PLUS_EXACT_DISJOINT_UTC_SLICES",
 "chunk_count_mismatch_count":len(chunk_count_mismatch),"chunk_count_mismatches":chunk_count_mismatch,
 "anomaly_count":len(source_anomalies)})

if (not accepted or bad_hash or chunk_errors or duplicate_slices or source_anomalies or gaps or overlaps or chunk_count_mismatch
    or any(summary["classes"][c]["successful_instruction_count"]<=0 for c in CLASSES)):
    summary["classification"]="DRIFT_SQD_EVENT_CENSUS_BLOCKED_FAIL_CLOSED"

CENSUS.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
QUEUE.write_text(json.dumps({"schema_version":"0.4","classes":queues},indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":summary["classification"],"accepted_manifests":len(accepted),
 "excluded_partials":len(excluded),"coverage_through":summary["coverage_through"],"gaps":len(gaps),"overlaps":len(overlaps),
 "chunk_count_mismatches":len(chunk_count_mismatch),"anomalies":summary["anomaly_count"],
 "classes":{c:{"success":v["successful_instruction_count"],"failed":v["failed_attempt_count"],
               "distinct_success_signatures":v["distinct_successful_signatures"],"first":v["first_success"]} for c,v in summary["classes"].items()}},indent=2))
if summary["classification"]!="DRIFT_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE":raise SystemExit(2)
