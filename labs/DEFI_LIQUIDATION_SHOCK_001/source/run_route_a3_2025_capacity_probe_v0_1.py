#!/usr/bin/env python3
from __future__ import annotations
import json,os,time,urllib.request,urllib.error
from pathlib import Path

PROBES=[
 ("marginfi","MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",1735689600,1738368000),
 ("save","So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",1735689600,1738368000),
 ("kamino","KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",1746057600,1748736000)
]
MAX_PAGES=25
OUT=Path("route_a3_capacity")

class RPC:
    def __init__(self):
        key=os.environ.get("HELIUS_API_KEY")
        url=os.environ.get("DLS_RPC_URL")
        if key:self.url="https://mainnet.helius-rpc.com/?api-key="+key
        elif url:self.url=url
        else:raise RuntimeError("credential_absent")
        self.calls=0
    def call(self,address,start,end):
        token=None;pages=0;count=0;complete=False
        while pages<MAX_PAGES:
            opts={
              "transactionDetails":"signatures",
              "sortOrder":"asc",
              "limit":1000,
              "filters":{"blockTime":{"gte":start,"lt":end},"status":"succeeded"}
            }
            if token:opts["paginationToken"]=token
            payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransactionsForAddress","params":[address,opts]},separators=(",",":")).encode()
            last=None
            for attempt in range(3):
                time.sleep(.26)
                try:
                    req=urllib.request.Request(self.url,data=payload,headers={"Content-Type":"application/json"},method="POST")
                    with urllib.request.urlopen(req,timeout=45) as r:
                        obj=json.loads(r.read())
                    if obj.get("error"):
                        code=(obj.get("error") or {}).get("code")
                        raise RuntimeError(f"rpc_error_code:{code}")
                    result=obj.get("result")
                    if not isinstance(result,dict) or not isinstance(result.get("data"),list):
                        raise RuntimeError("result_schema")
                    self.calls+=1;pages+=1;count+=len(result["data"])
                    nxt=result.get("paginationToken")
                    if nxt is None:
                        complete=True
                        return {"pages":pages,"transactions":count,"complete":True,"ceiling_hit":False}
                    if not isinstance(nxt,str) or not nxt or nxt==token:
                        raise RuntimeError("pagination_nonadvancing")
                    token=nxt
                    break
                except urllib.error.HTTPError as e:
                    if e.code in (401,402,403):raise RuntimeError(f"capability_or_credential_rejected:{e.code}") from None
                    last=f"http_{e.code}"
                    if attempt<2:time.sleep(2**attempt)
                except urllib.error.URLError:
                    last="transport"
                    if attempt<2:time.sleep(2**attempt)
            else:raise RuntimeError("transport_exhausted:"+str(last))
        return {"pages":pages,"transactions":count,"complete":complete,"ceiling_hit":True}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rpc=RPC();rows=[];errors=[]
    for name,address,start,end in PROBES:
        try:
            x=rpc.call(address,start,end)
            rows.append({"probe":name,"start_unix":start,"end_unix_exclusive":end,**x})
        except Exception as e:
            errors.append({"probe":name,"reason":str(e)[:240]})
            rows.append({"probe":name,"start_unix":start,"end_unix_exclusive":end,"complete":False,"ceiling_hit":False})
    passed=len(rows)==3 and all(r.get("complete") and not r.get("ceiling_hit") for r in rows) and not errors
    receipt={
      "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":"ROUTE_A3_CAPACITY_PASS" if passed else "ROUTE_A3_CAPACITY_BLOCKED",
      "max_pages_per_probe":MAX_PAGES,"results":rows,"errors":errors,"gtfa_rpc_call_count":rpc.calls,
      "transaction_details":"signatures","market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
      "protected_2025_full_acquisition":False,"data_2026":False,"purchases":False,
      "trading_authority":"NONE"
    }
    (OUT/"DLS_ROUTE_A3_2025_CAPACITY_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"results":rows,"errors":errors,"gtfa_rpc_call_count":rpc.calls},indent=2,sort_keys=True))
    if not passed:raise SystemExit(2)
if __name__=="__main__":main()
