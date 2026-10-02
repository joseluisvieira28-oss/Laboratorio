#!/usr/bin/env python3
import json,os,time,urllib.request,urllib.error
from pathlib import Path

START=1735689600
END=1767225599
PROGRAMS={
 "marginfi":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
 "solend":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
 "kamino":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
}
CAP=100
key=os.environ.get("HELIUS_API_KEY")
if not key: raise SystemExit("credential_absent")
url="https://mainnet.helius-rpc.com/?api-key="+key

def call(address,token=None):
    opts={"transactionDetails":"signatures","sortOrder":"asc","limit":1000,
          "filters":{"blockTime":{"gte":START,"lte":END},"status":"succeeded"}}
    if token: opts["paginationToken"]=token
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransactionsForAddress","params":[address,opts]},
                       separators=(",",":")).encode()
    last=None
    for n in range(6):
        time.sleep(.28)
        try:
            req=urllib.request.Request(url,data=payload,headers={"Content-Type":"application/json"},method="POST")
            with urllib.request.urlopen(req,timeout=45) as r:o=json.loads(r.read())
            if o.get("error"): raise RuntimeError("rpc_error:"+str((o["error"] or {}).get("code")))
            x=o.get("result")
            if not isinstance(x,dict) or not isinstance(x.get("data"),list): raise RuntimeError("result_schema")
            return x
        except urllib.error.HTTPError as e:
            last="http_"+str(e.code)
            if e.code in (401,402,403): raise RuntimeError("capability_or_credential_rejected:"+str(e.code))
            if n<5: time.sleep(min(30,2**n))
        except (urllib.error.URLError,TimeoutError,OSError,RuntimeError) as e:
            last=type(e).__name__
            if n<5: time.sleep(min(30,2**n))
    raise RuntimeError("transport_exhausted:"+str(last))

out={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
     "classification":"ROUTE_A3_2025_VOLUME_PREFLIGHT_PASS","window":[START,END],
     "programs":{},"errors":[],
     "firewall":{"full_transactions_opened":False,"economic_outcomes_opened":False,"data_2026":False,
                 "science_changed":False,"merge_main":False}}
for name,address in PROGRAMS.items():
    token=None;tokens=set();pages=0;count=0;terminal=False
    try:
        while pages<CAP:
            x=call(address,token);pages+=1
            data=x["data"];count+=len(data)
            nxt=x.get("paginationToken")
            if nxt is None:
                terminal=True;break
            if not isinstance(nxt,str) or not nxt or nxt==token or nxt in tokens:
                raise RuntimeError("pagination_nonadvancing")
            tokens.add(nxt);token=nxt
        if not terminal:
            raise RuntimeError("page_ceiling_100")
    except Exception as e:
        out["errors"].append({"program":name,"reason":str(e)[:160]})
    out["programs"][name]={"pages":pages,"successful_2025_program_transactions":count,
                           "terminal_pagination_reached":terminal,
                           "estimated_full_detail_calls":(count+99)//100 if terminal else None}
if out["errors"]:out["classification"]="ROUTE_A3_2025_VOLUME_PREFLIGHT_BLOCKED"
Path("route_a3_volume").mkdir(exist_ok=True)
Path("route_a3_volume/DLS_ROUTE_A3_2025_VOLUME_PREFLIGHT_RECEIPT_V0.1.json").write_text(
 json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))
if out["errors"]:raise SystemExit(2)
