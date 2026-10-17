"""One fixed historical OKX public JSON schema-only read, no prices or URLs exposed."""
from __future__ import annotations
import json,hashlib,urllib.request,urllib.parse,urllib.error
from pathlib import Path
from research.convex_okx_l2_stop_v02.okx_source_gate import epoch_ms,ENDPOINT

def shape(obj,level=0):
    if level>5:return {"type":"DEPTH_LIMIT"}
    if isinstance(obj,dict):
        return {"type":"object","keys":sorted(obj.keys())[:30],
                "members":{k:shape(v,level+1) for k,v in list(obj.items())[:30]}}
    if isinstance(obj,list):
        return {"type":"array","count":len(obj),
                "first_shape":shape(obj[0],level+1) if obj else None}
    if isinstance(obj,str):
        url=urllib.parse.urlsplit(obj)
        if url.scheme=="https" and url.hostname:
            return {"type":"https_url","hostname":url.hostname}
        return {"type":"string","length":len(obj)}
    if isinstance(obj,(int,float)) and not isinstance(obj,bool):
        return {"type":"number"}
    if isinstance(obj,bool):return {"type":"boolean"}
    return {"type":"null"}

def main():
    date="2024-06-03";ts=epoch_ms(date)
    q=urllib.parse.urlencode({
        "module":"4","instType":"SWAP","instFamilyList":"SOL-USDT",
        "dateAggrType":"daily","begin":ts,"end":ts
    })
    req=urllib.request.Request(ENDPOINT+"?"+q,headers={"Accept":"application/json"})
    code=0;raw=b"";error=""
    try:
        with urllib.request.urlopen(req,timeout=8) as response:
            code=response.status;raw=response.read(1_000_001)
            if len(raw)>1_000_000:raise ValueError("CAP_EXCEEDED")
    except urllib.error.HTTPError as exc:
        code=exc.code;error="HTTP_"+str(exc.code)
    except Exception as exc:
        error=type(exc).__name__
    result={"status":"SCHEMA_ONLY_NOT_BOOK_PROOF",
            "symbol":"SOL-USDT","date":date,"module":"4",
            "http":code,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest() if raw else None,
            "error":error,"shape":None,"orders_or_trading":False}
    if code==200 and raw:
        try:result["shape"]=shape(json.loads(raw.decode("utf-8")))
        except Exception as exc:result["error"]=type(exc).__name__
    out=Path("research/convex_okx_l2_stop_v02/receipts_schema")
    out.mkdir(parents=True,exist_ok=True)
    (out/"OKX_SCHEMA_ONLY_ONE_READ.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("SCHEMA_ONLY_RESULT",json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
