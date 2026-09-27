#!/usr/bin/env python3
import hashlib,json,urllib.request
from pathlib import Path

URLS=[
 ("detail","https://cbt.mainnet.ethpandaops.io/api/v1/models/mainnet.dim_validator_status"),
 ("list","https://cbt.mainnet.ethpandaops.io/api/v1/models"),
]
receipt={"lab_id":"ETH-STAKING-FLOW-001","stage":"V3_STAGEA_CBT_MODEL_COVERAGE_V0_2_0A",
         "validator_rows_opened":False,"market_data_opened":False,"signal_evaluated":False,
         "returns_opened":False,"pnl_opened":False,"source_after_2026_08_31_opened":False,
         "attempts":[]}
selected=None
for name,url in URLS:
    a={"name":name,"url":url}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-cbt-model-coverage/0.2.0a","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read(); a["http_status"]=r.status; a["content_type"]=r.headers.get("content-type")
        a["raw_bytes"]=len(raw); a["raw_sha256"]=hashlib.sha256(raw).hexdigest()
        obj=json.loads(raw)
        a["root_type"]=type(obj).__name__
        if isinstance(obj,dict): a["top_level_keys"]=sorted(obj.keys())
        if name=="detail" and isinstance(obj,dict):
            selected=obj
        elif name=="list" and isinstance(obj,dict):
            models=obj.get("models",[])
            for m in models if isinstance(models,list) else []:
                if str(m.get("id",""))=="mainnet.dim_validator_status" or str(m.get("table",""))=="dim_validator_status":
                    selected=m; break
        a["selected_found"]=selected is not None
    except Exception as e:
        a["error"]=f"{type(e).__name__}:{str(e)[:500]}"
    receipt["attempts"].append(a)
    if selected is not None: break

if selected is None:
    receipt["classification"]="CBT_MODEL_COVERAGE_METADATA_INCONCLUSIVE"
else:
    receipt["model_metadata_sha256"]=hashlib.sha256(json.dumps(selected,sort_keys=True).encode()).hexdigest()

    # Schema/path inventory only: proves what metadata the registry actually publishes
    # without opening any validator rows or economic values.
    paths=[]
    def inventory(x,path=""):
        if isinstance(x,dict):
            if path: paths.append({"path":path,"type":"object","keys":sorted(x.keys())})
            for k,v in x.items(): inventory(v,path+"."+k if path else k)
        elif isinstance(x,list):
            paths.append({"path":path,"type":"array","length":len(x)})
            for i,v in enumerate(x[:3]): inventory(v,f"{path}[{i}]")
        else:
            paths.append({"path":path,"type":type(x).__name__})
    inventory(selected)
    receipt["model_metadata_path_inventory"]=paths[:300]

    # Emit values only for explicitly authorized model-level identity/status/coverage fields.
    allowed_tokens=("id","type","database","table","status","dependency","depend","bound","coverage",
                    "position","processed","min","max","start","end","epoch","slot","range","interval",
                    "schedule","backfill","forwardfill","updated","last","first")
    scalars=[]
    def collect(x,path=""):
        if isinstance(x,dict):
            for k,v in x.items(): collect(v,path+"."+k if path else k)
        elif isinstance(x,list):
            if any(t in path.lower() for t in ("depend","schedule","tag")):
                scalars.append({"path":path,"value":x})
            else:
                for i,v in enumerate(x[:20]): collect(v,f"{path}[{i}]")
        elif isinstance(x,(str,int,float,bool)) or x is None:
            if any(t in path.lower() for t in allowed_tokens):
                scalars.append({"path":path,"value":x})
    collect(selected)
    receipt["authorized_model_metadata_scalars"]=scalars[:300]

    lo,hi=335588,472163
    receipt["frozen_epoch_range"]=[lo,hi]
    numeric=[]
    for row in scalars:
        v=row.get("value")
        p=row.get("path","").lower()
        if isinstance(v,(int,float)) and any(t in p for t in ("bound","coverage","position","processed","min","max","start","end","epoch","slot","range")):
            numeric.append(row)
    receipt["numeric_coverage_candidates"]=numeric[:100]

    # Never infer coverage merely from unrelated numeric metadata.
    explicit=[r for r in numeric if any(t in r["path"].lower() for t in ("coverage","bound","processed","position","epoch","slot"))]
    vals=[r["value"] for r in explicit if isinstance(r["value"],(int,float))]
    receipt["classification"]="CBT_MODEL_METADATA_AVAILABLE_COVERAGE_NOT_AUTOMATICALLY_PROVEN"
    if vals and min(vals)<=lo and max(vals)>=hi:
        receipt["classification"]="CBT_MODEL_METADATA_CANDIDATE_COVERAGE_SPANS_FROZEN_EPOCHS"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/ETH_STAKING_FLOW_001_CBT_MODEL_COVERAGE_V0_2_0.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,sort_keys=True))
