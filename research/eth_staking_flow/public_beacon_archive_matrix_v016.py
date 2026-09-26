#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINTS=[
 ("BEACONCHAIN","https://sync-mainnet.beaconcha.in"),
 ("PIETJEPUK","https://checkpointz.pietjepuk.net"),
 ("BEACONSTATE_INFO","https://beaconstate.info"),
 ("CHAINSAFE_LODESTAR","https://lodestar-mainnet.chainsafe.io"),
 ("ALCHEMY_DOCS_DEMO","https://eth-mainnetbeacon.g.alchemy.com/v2/docs-demo"),
]

CONTROLS=[
 {"date":"2025-02-24","epoch":347738,"slot":11127616,"pending_queued":0,"active_exiting":5},
 {"date":"2025-03-02","epoch":349088,"slot":11170816,"pending_queued":0,"active_exiting":0},
 {"date":"2025-10-17","epoch":400613,"slot":12819616,"pending_queued":48,"active_exiting":55209},
]
MISSING=[
 {"date":"2025-02-25","epoch":347963,"slot":11134816},
 {"date":"2025-02-26","epoch":348188,"slot":11142016},
 {"date":"2025-02-27","epoch":348413,"slot":11149216},
 {"date":"2025-02-28","epoch":348638,"slot":11156416},
 {"date":"2025-03-01","epoch":348863,"slot":11163616},
 {"date":"2025-10-18","epoch":400838,"slot":12826816},
 {"date":"2025-10-19","epoch":401063,"slot":12834016},
]

def fetch(base,slot,status,timeout=75):
    url=f"{base.rstrip('/')}/eth/v1/beacon/states/{slot}/validators?"+urllib.parse.urlencode({"status":status})
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-beacon-v016/1.0","Accept":"application/json"})
    t0=time.time()
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read()
            elapsed=time.time()-t0
            obj=json.loads(raw)
            data=obj.get("data") if isinstance(obj,dict) else None
            if not isinstance(data,list):
                raise RuntimeError(f"HTTP 200 but data array absent; keys={sorted(obj.keys()) if isinstance(obj,dict) else type(obj)}")
            indices=[]
            for item in data:
                idx=int(item["index"])
                if str(item.get("status"))!=status:
                    raise RuntimeError("status-filter leakage")
                indices.append(idx)
            if len(indices)!=len(set(indices)):
                raise RuntimeError("duplicate validator index")
            return {
              "ok":True,"url":url,"http_status":r.status,"count":len(indices),
              "body_bytes":len(raw),"body_sha256":hashlib.sha256(raw).hexdigest(),
              "elapsed_seconds":round(elapsed,3)
            }
    except urllib.error.HTTPError as e:
        body=e.read()
        return {"ok":False,"url":url,"http_status":e.code,"body_bytes":len(body),
                "body_sha256":hashlib.sha256(body).hexdigest(),"error":body[:400].decode("utf-8","replace")}
    except Exception as e:
        return {"ok":False,"url":url,"error":repr(e),"elapsed_seconds":round(time.time()-t0,3)}

receipt={
 "lab_id":"ETH-STAKING-FLOW-001",
 "stage":"V3_STAGEA_PUBLIC_BEACON_ARCHIVE_MATRIX_V0_1_6",
 "classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE",
 "endpoints":[],
 "control_pass_endpoints":[],
 "signal_evaluated":False,
 "market_prices_opened":False,
 "returns_opened":False,
 "pnl_opened":False,
 "source_after_2026_08_31_opened":False,
 "mutation":False
}

for name,base in ENDPOINTS:
    ep={"name":name,"base":base,"controls":[],"missing":[],"classification":"CONTROL_FAIL"}
    control_ok=True
    for c in CONTROLS:
        row={"date":c["date"],"epoch":c["epoch"],"slot":c["slot"],"calls":{}}
        for st in ("pending_queued","active_exiting"):
            res=fetch(base,c["slot"],st)
            row["calls"][st]=res
            if not res.get("ok") or res.get("count")!=c[st]:
                control_ok=False
        if all(row["calls"][s].get("ok") for s in ("pending_queued","active_exiting")):
            row["net_queue_count"]=row["calls"]["pending_queued"]["count"]-row["calls"]["active_exiting"]["count"]
        ep["controls"].append(row)
        if not control_ok:
            # Continue controls for full evidence, but never open missing dates for failed endpoint.
            pass
    if control_ok:
        ep["classification"]="CONTROL_PASS"
        receipt["control_pass_endpoints"].append(name)
        missing_ok=True
        for m in MISSING:
            row={"date":m["date"],"epoch":m["epoch"],"slot":m["slot"],"calls":{}}
            for st in ("pending_queued","active_exiting"):
                res=fetch(base,m["slot"],st)
                row["calls"][st]=res
                if not res.get("ok"):
                    missing_ok=False
            if all(row["calls"][s].get("ok") for s in ("pending_queued","active_exiting")):
                row["pending_queued_count"]=row["calls"]["pending_queued"]["count"]
                row["active_exiting_count"]=row["calls"]["active_exiting"]["count"]
                row["net_queue_count"]=row["pending_queued_count"]-row["active_exiting_count"]
            ep["missing"].append(row)
        ep["classification"]="MISSING_DATES_PASS" if missing_ok else "MISSING_DATES_TECHNICAL_FAILURE"
    receipt["endpoints"].append(ep)

# Quorum: every missing date must have >=2 CONTROL_PASS usable endpoint values, all agreeing.
recover=[]
provenance_failure=False
technical_failure=False
for m in MISSING:
    vals=[]
    for ep in receipt["endpoints"]:
        if ep["classification"]!="MISSING_DATES_PASS":
            continue
        row=next((x for x in ep["missing"] if x["date"]==m["date"]),None)
        if row and "pending_queued_count" in row:
            vals.append({
              "endpoint":ep["name"],
              "pending_queued_count":row["pending_queued_count"],
              "active_exiting_count":row["active_exiting_count"],
              "net_queue_count":row["net_queue_count"]
            })
    unique={(x["pending_queued_count"],x["active_exiting_count"]) for x in vals}
    if len(vals)<2:
        technical_failure=True
    if len(unique)>1:
        provenance_failure=True
    recover.append({"date":m["date"],"epoch":m["epoch"],"slot":m["slot"],"endpoint_values":vals,
                    "quorum_count":len(vals),"unique_value_count":len(unique)})

receipt["recovery_quorum"]=recover
if provenance_failure:
    receipt["classification"]="SOURCE_PROVENANCE_FAILURE"
elif technical_failure:
    receipt["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
else:
    receipt["classification"]="BEACON_ARCHIVE_RECOVERY_PASS"
    receipt["recovered_missing_dates"]=[]
    for r in recover:
        v=r["endpoint_values"][0]
        receipt["recovered_missing_dates"].append({
          "date":r["date"],"selected_epoch":r["epoch"],
          "selected_unix_time":1606824023+r["epoch"]*384,
          "pending_queued_count":v["pending_queued_count"],
          "active_exiting_count":v["active_exiting_count"],
          "net_queue_count":v["net_queue_count"],
          "quorum_endpoints":[x["endpoint"] for x in r["endpoint_values"]]
        })

Path("artifacts").mkdir(exist_ok=True)
out=Path("artifacts/ETH_STAKING_FLOW_001_BEACON_ARCHIVE_RECOVERY_V0_1_6.json")
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":receipt["classification"],
 "control_pass_endpoints":receipt["control_pass_endpoints"],
 "quorum":[{"date":x["date"],"quorum_count":x["quorum_count"],"unique_value_count":x["unique_value_count"]} for x in recover],
 "signal":False,"market":False,"returns":False,"pnl":False
},indent=2,sort_keys=True))
raise SystemExit(0 if receipt["classification"]=="BEACON_ARCHIVE_RECOVERY_PASS" else 2)
