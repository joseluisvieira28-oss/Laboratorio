#!/usr/bin/env python3
import datetime as dt, hashlib, json, sys
from pathlib import Path

root=Path(sys.argv[1])
OUTDIR=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
CENSUS=OUTDIR/"KAMINO_SAVE11_SQD_EVENT_CENSUS_RECEIPT_V0.4.2.json"
QUEUE=OUTDIR/"KAMINO_SAVE11_RAW_SAMPLE_QUEUE_V0.4.2.json"

expected={
 "kamino":{
   "start_date":"2023-11-17","end_date":"2025-01-01",
   "start_iso":"2023-11-17T14:48:24Z",
   "first_sig":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
   "first_slot":230572965
 },
 "save11":{
   "start_date":"2024-07-19","end_date":"2025-01-01",
   "start_iso":"2024-07-19T19:30:52Z",
   "first_sig":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
   "first_slot":278496102
 }
}

def sha_file(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def iso_dt(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def path_class(addr): return "inner" if isinstance(addr,list) and len(addr)>1 else "outer"

manifest_paths=sorted(root.rglob("MANIFEST.json"))
summary={
 "schema_version":"0.4.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE",
 "partition_manifest_count":len(manifest_paths),"protocols":{},
 "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,
   "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,
   "live_trading":False,"orders":False,"wallets":False,
   "exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}
}
queue={}
if not manifest_paths:
 summary["classification"]="SQD_EVENT_CENSUS_BLOCKED"

for protocol,cfg in expected.items():
 manifests=[]
 for mp in manifest_paths:
  try: m=json.loads(mp.read_text())
  except Exception: continue
  if m.get("protocol")==protocol:
   manifests.append((mp,m))
 if not manifests:
  summary["classification"]="SQD_EVENT_CENSUS_BLOCKED"

 days={}
 rows=[]
 duplicate_days=[]
 bad_chunk_hash=[]
 bad_partition=[]
 for mp,m in manifests:
  if m.get("classification")!="PARTITION_COMPLETE":
   bad_partition.append({"manifest":str(mp),"classification":m.get("classification")})
  base=mp.parent
  for ch in m.get("chunks",[]):
   day=ch.get("day")
   if day in days:
    duplicate_days.append(day)
    continue
   fp=base/ch["file"]
   if not fp.exists():
    bad_chunk_hash.append({"day":day,"reason":"missing_file"})
    continue
   actual=sha_file(fp)
   if actual!=ch.get("sha256"):
    bad_chunk_hash.append({"day":day,"reason":"sha_mismatch","actual":actual,"expected":ch.get("sha256")})
    continue
   rec=json.loads(fp.read_text())
   days[day]={"chunk":ch,"receipt":rec}
   rows.extend(rec.get("rows",[]))

 d0=dt.date.fromisoformat(cfg["start_date"]); d1=dt.date.fromisoformat(cfg["end_date"])
 expdays=[]; d=d0
 while d<d1:
  expdays.append(d.isoformat()); d+=dt.timedelta(days=1)
 missing=[d for d in expdays if d not in days]
 extras=sorted(set(days)-set(expdays))

 anomalies=[]
 successful=[]
 failed=[]
 instruction_keys=set()
 duplicate_instruction_keys=[]
 for r in rows:
  cls=r.get("classification")
  sig=r.get("signature"); addr=r.get("instructionAddress")
  key=(protocol,sig,json.dumps(addr,separators=(",",":"),sort_keys=True))
  if key in instruction_keys: duplicate_instruction_keys.append(key)
  instruction_keys.add(key)
  ts=r.get("timestamp")
  try: t=iso_dt(ts)
  except Exception:
   anomalies.append({"signature":sig,"reason":"bad_timestamp","timestamp":ts}); continue
  if not (iso_dt(cfg["start_iso"]) <= t < iso_dt("2025-01-01T00:00:00Z")):
   anomalies.append({"signature":sig,"reason":"outside_authoritative_interval","timestamp":ts})
  if cls=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION": successful.append(r)
  elif cls=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED": failed.append(r)
  elif cls=="SOURCE_ANOMALY_FAIL_CLOSED" or r.get("anomaly"): anomalies.append(r)
  else: anomalies.append({"signature":sig,"reason":"unknown_classification","classification":cls})

 if duplicate_days or duplicate_instruction_keys or bad_chunk_hash or bad_partition or missing or extras or anomalies:
  summary["classification"]="SQD_EVENT_CENSUS_BLOCKED"

 successful.sort(key=lambda r:(r.get("slot",-1),r.get("signature",""),json.dumps(r.get("instructionAddress"))))
 first_rows=[r for r in successful if r.get("signature")==cfg["first_sig"] and r.get("slot")==cfg["first_slot"]]
 first_found=bool(first_rows)
 if not first_found:
  summary["classification"]="SQD_EVENT_CENSUS_BLOCKED"

 bysig={}
 for r in successful:
  sig=r.get("signature")
  if not sig: continue
  ent=bysig.setdefault(sig,{
    "signature":sig,"slot":r.get("slot"),"timestamp":r.get("timestamp"),
    "expected_path_classes":set(),"instruction_addresses":[]
  })
  if ent["slot"]!=r.get("slot") or ent["timestamp"]!=r.get("timestamp"):
   anomalies.append({"signature":sig,"reason":"signature_slot_time_inconsistent"})
   summary["classification"]="SQD_EVENT_CENSUS_BLOCKED"
  ent["expected_path_classes"].add(path_class(r.get("instructionAddress")))
  ent["instruction_addresses"].append(r.get("instructionAddress"))
 for ent in bysig.values():
  ent["expected_path_classes"]=sorted(ent["expected_path_classes"])

 sigs=sorted(bysig)
 chron_sigs=[]
 seen=set()
 for r in successful:
  sig=r["signature"]
  if sig not in seen: seen.add(sig); chron_sigs.append(sig)
 last=chron_sigs[-1] if chron_sigs else None
 mandatory=[cfg["first_sig"]]+([last] if last and last!=cfg["first_sig"] else [])
 hash_rank=sorted((hashlib.sha256((protocol+":"+s).encode()).hexdigest(),s) for s in sigs if s not in mandatory)
 if len(sigs)<32:
  selected=sigs
 else:
  selected=mandatory+[s for _,s in hash_rank[:30]]
 sample_entries=[bysig[s] for s in selected if s in bysig]
 queue[protocol]={
  "mandatory_first":cfg["first_sig"],"mandatory_last":last,
  "selected_count":len(sample_entries),"distinct_successful_signatures":len(sigs),
  "entries":sample_entries
 }

 summary["protocols"][protocol]={
  "expected_days":len(expdays),"completed_days":len(days),"missing_days":missing,"extra_days":extras,
  "duplicate_days":sorted(set(duplicate_days)),"bad_chunk_hash":bad_chunk_hash,"bad_partitions":bad_partition,
  "successful_instruction_count":len(successful),
  "distinct_successful_signatures":len(sigs),
  "failed_attempt_count":len(failed),"anomaly_count":len(anomalies),
  "duplicate_instruction_key_count":len(duplicate_instruction_keys),
  "known_first_success_recovered":first_found,
  "chronological_last_success_signature":last
 }

CENSUS.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
QUEUE.write_text(json.dumps(queue,indent=2,sort_keys=True)+"\n")
print(json.dumps(summary,indent=2,sort_keys=True))
if summary["classification"]!="SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE":
 raise SystemExit(2)
