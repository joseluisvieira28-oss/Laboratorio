#!/usr/bin/env python3
import json,urllib.request,hashlib,os
from datetime import datetime,timezone

OUT="research/pos_unbonding_completion_001_v0_7_source_b/FORBOLE_COREUM_SOURCE_B_V07.json"
URL="https://gql.coreum.forbole.com/v1/graphql"
REF={
  5000000:{"hash":"D8A6B584C70FE38CD7D160A7F5151974E595AD9E241700F80D45AF15F53B0FF9","time":"2023-06-29T04:31:08.775170367Z"},
  10000000:{"hash":"227EE3C00731C6544D88478F9022100214767E0DF8779C66433BF5C0BB810F47","time":"2023-10-10T03:20:58.701998484Z"},
  15000000:{"hash":"DE285C3282D4EAC0EA6AF0FDAB0EF3F45273D5BB96289A76EA501CEDB52B1516","time":"2024-01-23T21:18:17.307101107Z"},
}
def post(query):
    raw=json.dumps({"query":query}).encode()
    req=urllib.request.Request(URL,data=raw,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-Unbonding-V07/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        body=r.read()
    return body,json.loads(body)

def main():
    rec={"freeze_commit":"d955b69661380462c4e5c2f699b41e46e7086893","generated_utc":datetime.now(timezone.utc).isoformat(),"event_counts_opened":False,"endpoint":URL,"operator":"Forbole","anchors":{}}
    # Capability/schema only
    try:
        raw,o=post('{__type(name:"block"){fields{name}}}')
        rec["schema_sha256"]=hashlib.sha256(raw).hexdigest()
        rec["block_fields"]=[x["name"] for x in (((o.get("data") or {}).get("__type") or {}).get("fields") or [])]
    except Exception as e:
        rec["schema_error"]=type(e).__name__+": "+str(e)
    for h,ref in REF.items():
        q='{block_by_pk(height:'+str(h)+'){height hash timestamp num_txs}}'
        try:
            raw,o=post(q)
            b=(o.get("data") or {}).get("block_by_pk")
            a={"response_sha256":hashlib.sha256(raw).hexdigest(),"block":b}
            if b:
                a["hash_match"]=str(b.get("hash","")).upper()==ref["hash"]
                a["time_match"]=str(b.get("timestamp",""))==ref["time"]
                a["reference"]=ref
                a["pass"]=bool(a["hash_match"] and a["time_match"])
            else:
                a["pass"]=False
            rec["anchors"][str(h)]=a
        except Exception as e:
            rec["anchors"][str(h)]={"pass":False,"error":type(e).__name__+": "+str(e)}
    rec["passing_anchors"]=sum(1 for x in rec["anchors"].values() if x.get("pass"))
    rec["source_b_fixed_height_pass"]=rec["passing_anchors"]>=2
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:
        json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(rec,indent=2))
if __name__=="__main__": main()
