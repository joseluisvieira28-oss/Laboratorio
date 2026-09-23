#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path

root=Path(sys.argv[1])
parts=sorted(root.rglob("MANIFEST.json"))
if not parts: raise SystemExit("no partition manifests")
manifests=[json.loads(p.read_text()) for p in parts]
expected={
 "kamino":("2023-11-17","2025-01-01","2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv"),
 "save11":("2024-07-19","2025-01-01","WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L")
}
summary={"schema_version":"0.4","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":"SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE",
         "protocols":{},"partition_manifest_count":len(manifests),
         "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
                     "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
                     "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}}
all_success={}
for protocol,(start,end,first_sig) in expected.items():
    ms=[m for m in manifests if m.get("protocol")==protocol]
    if not ms or any(m.get("classification")!="PARTITION_COMPLETE" for m in ms):
        summary["classification"]="SQD_EVENT_CENSUS_BLOCKED"
    days={}
    successes=[]
    failed=anoms=0
    for m in ms:
        base=next(p.parent for p in parts if json.loads(p.read_text()).get("protocol")==protocol and json.loads(p.read_text()).get("requested_start")==m.get("requested_start") and json.loads(p.read_text()).get("requested_end")==m.get("requested_end"))
        for c in m.get("chunks",[]):
            if c["day"] in days: summary["classification"]="SOURCE_ANOMALY_FAIL_CLOSED"
            days[c["day"]]=c
            rec=json.loads((base/c["file"]).read_text())
            for r in rec.get("rows",[]):
                if r.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":
                    successes.append(r)
            failed+=rec.get("failed_attempt_count",0); anoms+=rec.get("anomaly_count",0)
    import datetime as dt
    d0=dt.date.fromisoformat(start); d1=dt.date.fromisoformat(end)
    expected_days=[]; d=d0
    while d<d1: expected_days.append(d.isoformat()); d+=dt.timedelta(days=1)
    missing=[d for d in expected_days if d not in days]
    if missing or anoms: summary["classification"]="SQD_EVENT_CENSUS_BLOCKED"
    sigs=sorted(set(r["signature"] for r in successes if r.get("signature")))
    first_found=first_sig in sigs
    if not first_found: summary["classification"]="SQD_EVENT_CENSUS_BLOCKED"
    all_success[protocol]=sigs
    summary["protocols"][protocol]={
      "expected_days":len(expected_days),"completed_days":len(days),"missing_days":missing,
      "successful_instruction_count":len(successes),"distinct_successful_signatures":len(sigs),
      "failed_attempt_count":failed,"anomaly_count":anoms,"known_first_success_recovered":first_found
    }

# deterministic RAW sample selection
sample={}
for protocol,sigs in all_success.items():
    first=expected[protocol][2]
    mandatory=[first]
    if sigs: mandatory.append(sigs[-1]) # replaced below by chronological last from rows would be better; signature lexical is not chronology
    # remove second mandatory here; aggregator derives chronological last by scanning rows below
    rows=[]
    for p in root.rglob("*.json"):
        if p.name=="MANIFEST.json": continue
        try: rec=json.loads(p.read_text())
        except: continue
        if rec.get("protocol")!=protocol: continue
        for r in rec.get("rows",[]):
            if r.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION": rows.append(r)
    rows.sort(key=lambda r:(r.get("slot",-1),r.get("signature","")))
    last=rows[-1]["signature"] if rows else None
    mandatory=[first]+([last] if last and last!=first else [])
    hashes=sorted((hashlib.sha256((protocol+":"+s).encode()).hexdigest(),s) for s in sigs if s not in mandatory)
    selected=mandatory+[s for _,s in hashes[:30]]
    if len(sigs)<32: selected=sigs
    sample[protocol]={"mandatory_first":first,"mandatory_last":last,"selected_signatures":selected,"selected_count":len(selected)}
summary["raw_sample"]=sample
Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_SQD_EVENT_CENSUS_RECEIPT_V0.4.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_RAW_SAMPLE_QUEUE_V0.4.json").write_text(json.dumps(sample,indent=2,sort_keys=True)+"\n")
print(json.dumps(summary,indent=2,sort_keys=True))
if summary["classification"]!="SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE": raise SystemExit(2)
