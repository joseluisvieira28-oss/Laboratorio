#!/usr/bin/env python3
import datetime as dt, hashlib, json, sys
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
def parse(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def sha_file(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def addr_key(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def path_class(v): return "inner" if isinstance(v,list) and len(v)>1 else "outer"

all_manifests=[]; accepted=[]; excluded=[]
for mp in sorted(ROOT.rglob("MANIFEST.json")):
    try:m=json.loads(mp.read_text())
    except Exception:continue
    if m.get("protocol")!="drift": continue
    all_manifests.append((mp,m))
    if m.get("classification")=="PARTITION_COMPLETE":
        accepted.append((mp,m))
    else:
        excluded.append({"manifest":str(mp),"classification":m.get("classification"),
                         "reason":"NON_AUTHORITATIVE_PARTIAL_TRANSPORT_EVIDENCE_EXCLUDED"})

summary={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
         "classification":"DRIFT_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE",
         "manifest_count_seen":len(all_manifests),"accepted_manifest_count":len(accepted),
         "excluded_partial_manifest_count":len(excluded),"excluded_partial_manifests":excluded,
         "classes":{},
         "evidence_selection_rule":"PARTITION_COMPLETE_ONLY",
         "firewall":{"prices":False,"balances":False,"token_amounts":False,"returns":False,"pnl":False,"direction":False,
         "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
         "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
         "post_outcome_tuning":False,"merge_main":False}}

slices={}; rows=[]
bad_hash=[]; duplicate_slices=[]; chunk_errors=[]; anomalies=[]
for mp,m in accepted:
    base=mp.parent
    for ch in m.get("chunks",[]):
        k=(ch.get("start"),ch.get("end"))
        fp=base/ch["file"]
        if not fp.exists():
            bad_hash.append({"slice":k,"reason":"missing_file","manifest":str(mp)}); continue
        actual=sha_file(fp)
        if actual!=ch.get("sha256"):
            bad_hash.append({"slice":k,"reason":"sha_mismatch","actual":actual,"expected":ch.get("sha256"),"manifest":str(mp)}); continue
        rec=json.loads(fp.read_text())
        if rec.get("classification")!="SOURCE_CHUNK_PASS" or rec.get("stream_complete") is not True:
            chunk_errors.append({"slice":k,"classification":rec.get("classification"),"stream_complete":rec.get("stream_complete"),"file":str(fp)})
            continue
        if int(rec.get("anomaly_count") or 0)!=0:
            anomalies.append({"slice":k,"anomaly_count":rec.get("anomaly_count"),"file":str(fp)})
            continue
        if k in slices:
            duplicate_slices.append({"start":k[0],"end":k[1],"existing":str(slices[k][0]),"duplicate":str(fp)})
            continue
        slices[k]=(fp,rec)
        rows.extend(rec.get("rows") or [])

ordered=sorted(((parse(a),parse(b),a,b) for a,b in slices),key=lambda x:(x[0],x[1]))
cursor=LOWER; gaps=[]; overlaps=[]; used_ranges=[]
for s,e,a,b in ordered:
    if e<=LOWER or s>=UPPER: continue
    if s>cursor:
        gaps.append({"expected_start":cursor.isoformat().replace("+00:00","Z"),"observed_start":a})
        cursor=e if e>cursor else cursor
    elif s<cursor:
        overlaps.append({"cursor":cursor.isoformat().replace("+00:00","Z"),"observed_start":a,"observed_end":b})
        if e>cursor: cursor=e
    else:
        cursor=e
    used_ranges.append({"start":a,"end":b})
if cursor<UPPER:
    gaps.append({"expected_start":cursor.isoformat().replace("+00:00","Z"),"observed_end":UPPER.isoformat().replace("+00:00","Z")})

ded={}; duplicate_instruction_keys=[]
for r in rows:
    cls=r.get("class"); sig=r.get("signature"); addr=r.get("instructionAddress")
    key=(cls,sig,addr_key(addr))
    if key in ded:
        duplicate_instruction_keys.append(key)
        if ded[key]!=r: anomalies.append({"reason":"dedup_key_collision","key":key})
    ded[key]=r
rows=list(ded.values())

queues={}
for cls,prefix in CLASSES.items():
    rs=[r for r in rows if r.get("class")==cls]
    successful=[]; failed=[]; local_anom=[]
    for r in rs:
        try:t=parse(r.get("timestamp"))
        except Exception:
            local_anom.append({"reason":"bad_timestamp","signature":r.get("signature")}); continue
        if not (LOWER<=t<UPPER):
            local_anom.append({"reason":"outside_window","signature":r.get("signature"),"timestamp":r.get("timestamp")})
        state=r.get("classification")
        if state=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION": successful.append(r)
        elif state=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED": failed.append(r)
        else: local_anom.append({"reason":"unexpected_row_class","signature":r.get("signature"),"classification":state})
    successful.sort(key=lambda r:(parse(r["timestamp"]),r.get("slot",-1),r.get("signature",""),addr_key(r.get("instructionAddress"))))
    first=successful[0] if successful else None; last=successful[-1] if successful else None
    bysig={}
    for r in successful:
        sig=r.get("signature")
        if not sig: continue
        ent=bysig.setdefault(sig,{"signature":sig,"slot":r.get("slot"),"timestamp":r.get("timestamp"),
                                  "expected_path_classes":set(),"instruction_addresses":[],"class":cls,"prefix":prefix})
        if ent["slot"]!=r.get("slot") or ent["timestamp"]!=r.get("timestamp"):
            local_anom.append({"reason":"signature_slot_time_inconsistent","signature":sig})
        ent["expected_path_classes"].add(path_class(r.get("instructionAddress")))
        ent["instruction_addresses"].append(r.get("instructionAddress"))
    for ent in bysig.values(): ent["expected_path_classes"]=sorted(ent["expected_path_classes"])
    sigs=sorted(bysig); mandatory=[]
    if first and first.get("signature"): mandatory.append(first["signature"])
    if last and last.get("signature") and last["signature"] not in mandatory: mandatory.append(last["signature"])
    rank=sorted((hashlib.sha256(("drift:"+cls+":"+s).encode()).hexdigest(),s) for s in sigs if s not in mandatory)
    selected=mandatory+[s for _,s in rank[:30]]
    entries=[bysig[s] for s in selected if s in bysig]
    queues[cls]={"mandatory_first":first.get("signature") if first else None,
                 "mandatory_last":last.get("signature") if last else None,
                 "selected_count":len(entries),"distinct_successful_signatures":len(sigs),"entries":entries}
    summary["classes"][cls]={
      "discriminator":prefix,
      "successful_instruction_count":len(successful),
      "distinct_successful_signatures":len(sigs),
      "failed_attempt_count":len(failed),
      "anomaly_count":len(local_anom),
      "first_success":first,"last_success":last
    }
    anomalies.extend({"class":cls,**x} for x in local_anom)

summary.update({
 "coverage_start":LOWER.isoformat().replace("+00:00","Z"),
 "coverage_end":UPPER.isoformat().replace("+00:00","Z"),
 "coverage_through":cursor.isoformat().replace("+00:00","Z"),
 "accepted_slice_count":len(slices),
 "gap_count":len(gaps),"gaps":gaps,
 "overlap_count":len(overlaps),"overlaps":overlaps,
 "bad_chunk_hash":bad_hash,"chunk_errors":chunk_errors,
 "duplicate_slice_count":len(duplicate_slices),"duplicate_slices":duplicate_slices,
 "duplicate_instruction_key_count":len(duplicate_instruction_keys),
 "anomaly_count":len(anomalies)
})
if (not accepted or gaps or overlaps or bad_hash or chunk_errors or duplicate_slices
    or duplicate_instruction_keys or anomalies
    or any((summary["classes"].get(c) or {}).get("successful_instruction_count",0)<=0 for c in CLASSES)):
    summary["classification"]="DRIFT_SQD_EVENT_CENSUS_BLOCKED_FAIL_CLOSED"

CENSUS.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
QUEUE.write_text(json.dumps({"schema_version":"0.2","classes":queues},indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":summary["classification"],
                  "seen_manifests":len(all_manifests),"accepted_manifests":len(accepted),
                  "excluded_partials":len(excluded),"coverage_through":summary["coverage_through"],
                  "gaps":len(gaps),"overlaps":len(overlaps),"anomalies":summary["anomaly_count"],
                  "classes":{k:{"success":v["successful_instruction_count"],"failed":v["failed_attempt_count"],
                                "first":v["first_success"]} for k,v in summary["classes"].items()}},indent=2))
if summary["classification"]!="DRIFT_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE": raise SystemExit(2)
