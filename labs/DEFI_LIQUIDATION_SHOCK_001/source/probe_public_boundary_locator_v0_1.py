#!/usr/bin/env python3
import json,os,time,urllib.request,urllib.error
from pathlib import Path
START=1721417452; END=1721433600; EXPECTED=1868
TARGET="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PUBLIC="https://api.mainnet-beta.solana.com"
OUT=Path("route_a2_public_boundary_probe")

def http_json(url,body=None,tries=6):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    for n in range(tries):
        try:
            req=urllib.request.Request(url,data=data,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-public-boundary/0.1"},method="GET" if data is None else "POST")
            with urllib.request.urlopen(req,timeout=45) as r:return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(min(15,2**(n+1))); continue
            raise
        except Exception:
            if n+1==tries: raise
            time.sleep(min(15,2**n))
    raise RuntimeError("transport_exhausted")

def ts_slot(u):
    o=http_json(f"{TSROOT}/{u}/block")
    if isinstance(o,int): return o
    if isinstance(o,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(o.get(k),int): return o[k]
    raise RuntimeError("bad_ts_slot")

def pub_block(slot):
    o=http_json(PUBLIC,{"jsonrpc":"2.0","id":1,"method":"getBlock","params":[slot,{"transactionDetails":"signatures","rewards":False,"maxSupportedTransactionVersion":0}]})
    if o.get("error"): return None
    return o.get("result")

def boundary(slot0,direction,pred):
    for off in (6000,9000,12000,18000,24000,36000):
        slot=slot0+direction*off
        r=pub_block(slot)
        if isinstance(r,dict) and isinstance(r.get("blockTime"),int) and r.get("signatures") and pred(r["blockTime"]):
            return {"slot":slot,"blockTime":r["blockTime"],"signature":r["signatures"][0],"offset":off}
    raise RuntimeError("public_boundary_not_found")

def helius_call(method,params):
    key=os.environ.get("HELIUS_API_KEY"); alt=os.environ.get("DLS_RPC_URL")
    url=("https://mainnet.helius-rpc.com/?api-key="+key) if key else alt
    if not url: raise RuntimeError("credential_absent")
    payload={"jsonrpc":"2.0","id":1,"method":method,"params":params}
    for n in range(8):
        try:
            o=http_json(url,payload,tries=1)
            if o.get("error"): raise RuntimeError("rpc_error")
            return o.get("result")
        except urllib.error.HTTPError as e:
            if e.code in (401,402,403): raise RuntimeError("credential_rejected")
            if e.code==429: time.sleep(min(30,2**(n+1))); continue
            raise
        except Exception:
            time.sleep(min(30,2**n))
    raise RuntimeError("helius_transport_exhausted")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    ss,es=ts_slot(START),ts_slot(END)
    lo=boundary(ss,-1,lambda t:t<START)
    hi=boundary(es,+1,lambda t:t>=END)
    before=hi["signature"]; until=lo["signature"]; seen=set(); inside=set(); pages=[]; dup=0; terminated=False
    for p in range(20):
        got=helius_call("getSignaturesForAddress",[TARGET,{"before":before,"until":until,"limit":1000,"commitment":"finalized"}])
        if not isinstance(got,list): raise RuntimeError("page_schema")
        if not got: terminated=True; pages.append({"page":p+1,"count":0}); break
        if any(type(x.get("blockTime")) is not int for x in got): raise RuntimeError("missing_blockTime")
        for x in got:
            sig=x["signature"]
            if sig in seen: dup+=1
            seen.add(sig)
            if START<=x["blockTime"]<END: inside.add(sig)
        pages.append({"page":p+1,"count":len(got),"first_time":got[0]["blockTime"],"last_time":got[-1]["blockTime"]})
        nxt=got[-1]["signature"]
        if nxt==before: raise RuntimeError("nonadvancing")
        before=nxt
        if got[-1]["blockTime"]<START: terminated=True; break
    cl="PUBLIC_BOUNDARY_LOCATOR_PASS" if terminated and len(inside)==EXPECTED and dup==0 else "PUBLIC_BOUNDARY_LOCATOR_BLOCKED"
    r={"lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":cl,"start_slot":ss,"end_slot":es,
       "lower_cursor":lo,"upper_cursor":hi,"expected":EXPECTED,"observed":len(inside),"duplicate_count":dup,
       "termination_reached":terminated,"pages":pages,"public_rpc_role":"BOUNDARY_CURSOR_ONLY",
       "protected_2025_acquisition":False,"market_outcomes_opened":False,"science_changed":False,"trading_authority":"NONE"}
    (OUT/"DLS_ROUTE_A2_PUBLIC_BOUNDARY_LOCATOR_RECEIPT_V0.1.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:r[k] for k in ("classification","expected","observed","duplicate_count","termination_reached","lower_cursor","upper_cursor")},indent=2,sort_keys=True))
    if cl!="PUBLIC_BOUNDARY_LOCATOR_PASS": raise SystemExit(2)
if __name__=="__main__": main()
