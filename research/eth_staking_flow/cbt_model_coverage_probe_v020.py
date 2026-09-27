#!/usr/bin/env python3
import hashlib,json,urllib.request
from pathlib import Path

URLS=[
 ("detail","https://cbt.mainnet.ethpandaops.io/api/v1/models/mainnet.dim_validator_status"),
 ("list","https://cbt.mainnet.ethpandaops.io/api/v1/models"),
]
receipt={"lab_id":"ETH-STAKING-FLOW-001","stage":"V3_STAGEA_CBT_MODEL_COVERAGE_V0_2_0",
         "validator_rows_opened":False,"market_data_opened":False,"signal_evaluated":False,
         "returns_opened":False,"pnl_opened":False,"source_after_2026_08_31_opened":False,
         "attempts":[]}
selected=None
for name,url in URLS:
    a={"name":name,"url":url}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-cbt-model-coverage/1.0","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read(); a["http_status"]=r.status; a["content_type"]=r.headers.get("content-type")
        a["raw_bytes"]=len(raw); a["raw_sha256"]=hashlib.sha256(raw).hexdigest()
        obj=json.loads(raw)
        a["root_type"]=type(obj).__name__
        if isinstance(obj,dict):
            a["top_level_keys"]=sorted(obj.keys())
        if name=="detail" and isinstance(obj,dict):
            selected=obj
        elif name=="list" and isinstance(obj,dict):
            models=obj.get("models",[])
            for m in models if isinstance(models,list) else []:
                mid=str(m.get("id",""))
                if mid=="mainnet.dim_validator_status" or str(m.get("table",""))=="dim_validator_status":
                    selected=m; break
        a["selected_found"]=selected is not None
    except Exception as e:
        a["error"]=f"{type(e).__name__}:{str(e)[:500]}"
    receipt["attempts"].append(a)
    if selected is not None: break

if selected is None:
    receipt["classification"]="CBT_MODEL_COVERAGE_METADATA_INCONCLUSIVE"
else:
    # Persist only model metadata, never row data.
    keep={}
    for k,v in selected.items():
        if k.lower() in {"id","type","database","table","status","config","dependencies","dependents","bounds","coverage","min","max","position","processed","metadata"}:
            keep[k]=v
    receipt["model_metadata"]=keep
    blob=json.dumps(selected,sort_keys=True)
    receipt["model_metadata_sha256"]=hashlib.sha256(blob.encode()).hexdigest()

    nums=[]
    def walk(x,path=""):
        if isinstance(x,dict):
            for k,v in x.items(): walk(v,path+"."+k if path else k)
        elif isinstance(x,(int,float)) and any(t in path.lower() for t in ["min","max","bound","position","slot","epoch","start","end"]):
            nums.append({"path":path,"value":x})
    walk(selected)
    receipt["numeric_bound_candidates"]=nums[:100]
    # Metadata alone only passes if an explicit model bound/position range spans both frozen epochs.
    lo=335588; hi=472163
    vals=[x["value"] for x in nums if isinstance(x["value"],(int,float))]
    receipt["frozen_epoch_range"]=[lo,hi]
    receipt["classification"]="CBT_MODEL_METADATA_AVAILABLE_COVERAGE_NOT_AUTOMATICALLY_PROVEN"
    if vals and min(vals)<=lo and max(vals)>=hi:
        receipt["classification"]="CBT_MODEL_METADATA_CANDIDATE_COVERAGE_SPANS_FROZEN_EPOCHS"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/ETH_STAKING_FLOW_001_CBT_MODEL_COVERAGE_V0_2_0.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,sort_keys=True))
