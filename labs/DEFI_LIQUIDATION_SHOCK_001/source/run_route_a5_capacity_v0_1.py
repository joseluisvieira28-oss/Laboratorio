#!/usr/bin/env python3
from __future__ import annotations
import json,os,time,urllib.request,urllib.error
from pathlib import Path

ACCOUNTS=[
("marginfi","BpmLoZcyKJP9Jncq5TE7TTzxPV6PSbKNZkuvU1MB6t8e"),
("marginfi","CCKtUs6Cgwo4aaQUmBPmyoApH2gUDErxNZCAntD6LYGh"),
("save0c","3WPYWiZtc2uJq1JiF3Z3KswicFAp5VrFgEHwP3CkuDUn"),
("save0c","7trBAMkVU8dcPQVdScz7VNywZwqnD1rwXkwkVPQJ95bT"),
("save0c","8xogd14bBxBdGKDfkDciPPp6pZ3Cw4Yj5USRbGJDbZpA"),
("save0c","UTABCRXirrbpCNDogCoqEECtM3V44jXGCsK23ZepV3Z"),
("kamino","GafNuUXj9rxGLn4y79dPu6MHSuPWeJR6UtTWuexpGh3U"),
("save11","8UviNr47S8eL6J3WfDxMRa3hvLta1VDJwNWqsDgtN3Cv"),
("save11","5cSfC32xBUYqGfkURLGfANuK64naHmMp27jUT7LQSujY"),
("save11","8jVVXXxzC9N5FeHUxKBgXLM8xARzLpnzXz8dqZHzpykY"),
("save11","APJAFijv9XrtnrAvktzsqgJboq4Uhs3mu7YN7DQ5bFMH"),
("save11","6ToFgS59GXhYMoHHL2GNPh5aNypxc1UAR1RYpfdHftBE"),
("save11","6s8hmMLgdhpffsL7H9neZBhFSxaQYTnQ1gkjaRN25GS7")]
START=1704067200; END=1735689600; MAX_PAGES=25
OUT=Path("route_a5_capacity")

class RPC:
    def __init__(self):
        key=os.environ.get("HELIUS_API_KEY"); url=os.environ.get("DLS_RPC_URL")
        if key:self.url="https://mainnet.helius-rpc.com/?api-key="+key
        elif url:self.url=url
        else:raise RuntimeError("credential_absent")
        self.calls=0
    def scan(self,address):
        token=None;pages=count=0
        while pages<MAX_PAGES:
            opts={"transactionDetails":"signatures","sortOrder":"asc","limit":1000,
                  "filters":{"blockTime":{"gte":START,"lt":END},"status":"succeeded"}}
            if token:opts["paginationToken"]=token
            payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransactionsForAddress","params":[address,opts]},separators=(",",":")).encode()
            last=None
            for attempt in range(4):
                time.sleep(.27)
                try:
                    req=urllib.request.Request(self.url,data=payload,headers={"Content-Type":"application/json"},method="POST")
                    with urllib.request.urlopen(req,timeout=45) as r: obj=json.loads(r.read())
                    if obj.get("error"): raise RuntimeError("rpc_error_code:"+str((obj.get("error") or {}).get("code")))
                    res=obj.get("result")
                    if not isinstance(res,dict) or not isinstance(res.get("data"),list): raise RuntimeError("result_schema")
                    self.calls+=1; pages+=1; count+=len(res["data"])
                    nxt=res.get("paginationToken")
                    if nxt is None:return {"pages":pages,"transactions":count,"complete":True,"ceiling_hit":False}
                    if not isinstance(nxt,str) or not nxt or nxt==token: raise RuntimeError("pagination_nonadvancing")
                    token=nxt;break
                except urllib.error.HTTPError as e:
                    if e.code in (401,402,403): raise RuntimeError(f"capability_or_credential_rejected:{e.code}") from None
                    last=f"http_{e.code}"
                    if attempt<3: time.sleep(min(8,2**attempt))
                except urllib.error.URLError:
                    last="transport"
                    if attempt<3: time.sleep(min(8,2**attempt))
            else: raise RuntimeError("transport_exhausted:"+str(last))
        return {"pages":pages,"transactions":count,"complete":False,"ceiling_hit":True}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rpc=RPC();rows=[];errors=[]
    for proto,address in ACCOUNTS:
        try:r=rpc.scan(address)
        except Exception as e:
            r={"complete":False,"ceiling_hit":False,"pages":0,"transactions":0}
            errors.append({"protocol":proto,"address":address,"reason":str(e)[:240]})
        row={"protocol":proto,"address":address,**r};rows.append(row);print(json.dumps(row,sort_keys=True),flush=True)
    passed=len(rows)==13 and all(x["complete"] and not x["ceiling_hit"] for x in rows) and not errors
    receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":"ROUTE_A5_CAPACITY_PASS" if passed else "ROUTE_A5_CAPACITY_BLOCKED",
      "window":{"start":"2024-01-01T00:00:00Z","end":"2025-01-01T00:00:00Z"},
      "max_pages_per_address":MAX_PAGES,"result_count":len(rows),"results":rows,"errors":errors,
      "gtfa_rpc_call_count":rpc.calls,"transaction_details":"signatures",
      "protected_2025_acquisition":False,"market_prices_opened":False,"returns_opened":False,
      "pnl_opened":False,"purchases":False,"trading_authority":"NONE"}
    (OUT/"DLS_ROUTE_A5_CAPACITY_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"calls":rpc.calls,
      "blocked":[{"protocol":x["protocol"],"address":x["address"],"transactions":x["transactions"]} for x in rows if not x["complete"]]},indent=2))
    if not passed:raise SystemExit(2)
if __name__=="__main__":main()
