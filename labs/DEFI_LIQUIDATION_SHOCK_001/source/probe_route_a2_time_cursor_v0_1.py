#!/usr/bin/env python3
import datetime as dt,json,os,time,urllib.request,urllib.error
from pathlib import Path

START=1721417452  # 2024-07-19T19:30:52Z
END=1721433600    # 2024-07-20T00:00:00Z
TARGET="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
OUT=Path("route_a2_time_cursor_probe")
EXPECTED=1868

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-a2-cursor-probe/0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read())

def ts_slot(unix):
    o=get(f"{TSROOT}/{unix}/block")
    if isinstance(o,int):return o
    if isinstance(o,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(o.get(k),int):return o[k]
    raise RuntimeError("timestamp_resolver_schema")

class RPC:
    def __init__(self):
        key=os.environ.get("HELIUS_API_KEY")
        url=os.environ.get("DLS_RPC_URL")
        self.url=("https://mainnet.helius-rpc.com/?api-key="+key) if key else url
        if not self.url:raise RuntimeError("archival_rpc_credential_absent")
        self.calls=0
    def call(self,method,params):
        if method not in ("getBlock","getSignaturesForAddress"):
            raise RuntimeError("method_not_authorized")
        payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
        last=None
        for n in range(4):
            time.sleep(.20)
            try:
                req=urllib.request.Request(self.url,data=payload,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-a2-cursor-probe/0.1"},method="POST")
                with urllib.request.urlopen(req,timeout=45) as r: obj=json.loads(r.read())
                self.calls+=1
                if obj.get("error"):raise RuntimeError("rpc_error_response")
                return obj.get("result")
            except urllib.error.HTTPError as e:
                last=f"http_{e.code}"
                if e.code in (401,402,403):raise RuntimeError("credential_or_plan_rejected")
                if e.code==429:
                    ra=e.headers.get("Retry-After")
                    try: delay=float(ra) if ra else min(30,2**(n+1))
                    except Exception: delay=min(30,2**(n+1))
                    time.sleep(max(2.0,delay))
                    continue
            except Exception as e:
                last=type(e).__name__
            time.sleep(min(30,2**n))
        raise RuntimeError("rpc_transport_exhausted:"+str(last))

def block_sig(rpc,slot0,direction,predicate):
    # Transport-only sparse search: stay ~30-90 minutes outside the scientific boundary,
    # avoiding rate-limit-heavy slot-by-slot archival block scans.
    offsets=(6000,9000,12000,15000,18000,24000)
    tried=[]
    for off in offsets:
        slot=slot0 + direction*off
        r=rpc.call("getBlock",[slot,{"transactionDetails":"signatures","rewards":False,"maxSupportedTransactionVersion":0}])
        tried.append(slot)
        if isinstance(r,dict):
            bt=r.get("blockTime"); sigs=r.get("signatures") or []
            if isinstance(bt,int) and sigs and predicate(bt):
                return {"slot":slot,"blockTime":bt,"signature":sigs[0],"offset":off,"tried":tried}
    raise RuntimeError("cursor_block_not_found_sparse:"+str(tried))

