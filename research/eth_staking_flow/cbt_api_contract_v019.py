#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, urllib.parse, urllib.request, urllib.error
from pathlib import Path

ENDPOINTS=[
 ("LAB_PROXY_MAINNET","https://lab.ethpandaops.io/api/v1/mainnet/dim_validator_status"),
 ("LAB_PROXY_ROOT","https://lab.ethpandaops.io/api/v1/dim_validator_status"),
 ("DIRECT_CBT_API","https://cbt-api-mainnet.primary.production.platform.ethpandaops.io/api/v1/dim_validator_status"),
]
VALIDATORS=[0,1,2]
REQUIRED={"validator_index","status","epoch","epoch_start_date_time","activation_epoch","exit_epoch"}

def fetch(url,timeout=35):
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-cbt-contract-v019/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read()
            return r.status,dict(r.headers),raw,None
    except urllib.error.HTTPError as e:
        raw=e.read()
        return e.code,dict(e.headers),raw,repr(e)
    except Exception as e:
        return None,{},b"",repr(e)

def identify(obj):
    out={"json_type":type(obj).__name__,"top_level_keys":[],"row_field":None,"row_count":0,"row_field_names":[],"next_page_token_present":False}
    rows=[]
    if isinstance(obj,dict):
        out["top_level_keys"]=sorted(obj.keys())
        out["next_page_token_present"]=bool(obj.get("next_page_token") or obj.get("nextPageToken"))
        for k,v in obj.items():
            if isinstance(v,list):
                if not rows or len(v)>len(rows):
                    rows=v; out["row_field"]=k
        if not rows and isinstance(obj.get("item"),dict):
            rows=[obj["item"]]; out["row_field"]="item"
    elif isinstance(obj,list):
        rows=obj; out["row_field"]="<top_level_list>"
    out["row_count"]=len(rows)
    if rows and isinstance(rows[0],dict):
        fields=set()
        for r in rows[:20]:
            if isinstance(r,dict): fields.update(r.keys())
        out["row_field_names"]=sorted(fields)
        out["required_fields_present"]=sorted(REQUIRED & fields)
        out["required_fields_complete"]=REQUIRED.issubset(fields)
    else:
        out["required_fields_present"]=[]
        out["required_fields_complete"]=False
    return out,rows

receipt={
 "lab_id":"ETH-STAKING-FLOW-001",
 "stage":"V3_STAGEA_CBT_API_CONTRACT_REMEDIATION_V0_1_9",
 "source_only":True,
 "market_data_opened":False,
 "signal_evaluated":False,
 "returns_opened":False,
 "pnl_opened":False,
 "source_after_2026_08_31_opened":False,
 "probes":[],
}
usable=[]
for name,base in ENDPOINTS:
    ep={"name":name,"base":base,"requests":[]}
    for vi in VALIDATORS:
        q=urllib.parse.urlencode({"validator_index_eq":vi,"page_size":20})
        url=base+"?"+q
        status,headers,raw,error=fetch(url)
        rec={
          "validator_index":vi,
          "url":url,
          "http_status":status,
          "content_type":headers.get("Content-Type") or headers.get("content-type"),
          "body_sha256":hashlib.sha256(raw).hexdigest(),
          "body_bytes":len(raw),
          "transport_error":error,
        }
        try:
            obj=json.loads(raw) if raw else None
            meta,rows=identify(obj)
            rec.update(meta)
            # private debugging only; no market outcomes
            rec["first_row"]=rows[0] if rows and isinstance(rows[0],dict) else None
            if status==200 and rec.get("row_count",0)>0 and rec.get("required_fields_complete"):
                usable.append({"endpoint":name,"validator_index":vi,"row_field":rec.get("row_field")})
        except Exception as e:
            rec["json_parse_error"]=repr(e)
            rec["body_prefix"]=raw[:500].decode("utf-8","replace")
        ep["requests"].append(rec)
    receipt["probes"].append(ep)

receipt["usable_contracts"]=usable
receipt["classification"]="CBT_API_CONTRACT_PASS" if usable else "SOURCE_ACQUISITION_TECHNICAL_FAILURE"

out=Path("artifacts/ETH_STAKING_FLOW_001_CBT_API_CONTRACT_V0_1_9.json")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":receipt["classification"],
 "usable_contracts":usable,
 "summary":[{
   "name":p["name"],
   "requests":[{
      k:r.get(k) for k in ("validator_index","http_status","json_type","top_level_keys","row_field","row_count","row_field_names","required_fields_complete","transport_error","json_parse_error")
      if k in r
   } for r in p["requests"]]
 } for p in receipt["probes"]]
},sort_keys=True))
raise SystemExit(0 if usable else 2)
