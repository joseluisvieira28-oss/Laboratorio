#!/usr/bin/env python3
import json,os,time,urllib.request,urllib.error
from pathlib import Path

START=1721417452
END=1721433600
TARGET="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
OUT=Path("route_a2_time_cursor_probe")
EXPECTED=1868

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-a2-cursor-probe/0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read())

def ts_slot(unix):
    o=get_json(f"{TSROOT}/{unix}/block")
    if isinstance(o,int): return o
    if isinstance(o,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(o.get(k),int): return o[k]
    raise RuntimeError("timestamp_resolver_schema")

class RPC:
    def __init__(self):
        key=os.environ.get("HELIUS_API_KEY")
        alt=os.environ.get("DLS_RPC_URL")
        self.url=("https://mainnet.helius-rpc.com/?api-key="+key) if key else alt
        if not self.url: raise RuntimeError("archival_rpc_credential_absent")
        self.calls=0

    def call(self,method,params):
        if method not in ("getBlock","getSignaturesForAddress"):
            raise RuntimeError("method_not_authorized")
        payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
        last=None
        for n in range(8):
            time.sleep(3.0 if method=="getBlock" else .30)
            try:
                req=urllib.request.Request(self.url,data=payload,headers={
                    "Content-Type":"application/json",
                    "User-Agent":"crypto-lab-dls-a2-cursor-probe/0.1"
                },method="POST")
                with urllib.request.urlopen(req,timeout=45) as r:
                    obj=json.loads(r.read())
                self.calls+=1
                if obj.get("error"):
                    raise RuntimeError("rpc_error_response")
                if "result" not in obj:
                    raise RuntimeError("rpc_result_missing")
                return obj["result"]
            except urllib.error.HTTPError as e:
                last=f"http_{e.code}"
                if e.code in (401,402,403):
                    raise RuntimeError("credential_or_plan_rejected")
                if e.code==429:
                    ra=e.headers.get("Retry-After")
                    try: delay=float(ra) if ra else min(30,2**(n+1))
                    except Exception: delay=min(30,2**(n+1))
                    time.sleep(max(3.0,delay))
                    continue
            except (urllib.error.URLError,TimeoutError,OSError,RuntimeError) as e:
                last=type(e).__name__
            time.sleep(min(30,2**n))
        raise RuntimeError("rpc_transport_exhausted:"+str(last))

def block_sig(rpc,slot0,direction,predicate):
    offsets=(6000,9000,12000,15000,18000,24000,36000)
    tried=[]
    for off in offsets:
        slot=slot0+direction*off
        r=rpc.call("getBlock",[slot,{
            "transactionDetails":"signatures",
            "rewards":False,
            "maxSupportedTransactionVersion":0
        }])
        tried.append(slot)
        if isinstance(r,dict):
            bt=r.get("blockTime"); sigs=r.get("signatures") or []
            if isinstance(bt,int) and sigs and predicate(bt):
                return {"slot":slot,"blockTime":bt,"signature":sigs[0],"offset":off,"tried":tried}
    raise RuntimeError("cursor_block_not_found_sparse:"+str(tried))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rpc=RPC()
    start_slot=ts_slot(START)
    end_slot=ts_slot(END)

    lower=block_sig(rpc,start_slot,-1,lambda x:x<START)
    upper=block_sig(rpc,end_slot,+1,lambda x:x>=END)
    assert lower["blockTime"]<START
    assert upper["blockTime"]>=END

    before=upper["signature"]
    until=lower["signature"]
    seen=set()
    in_window=set()
    pages=[]
    duplicate_count=0
    terminated=False

    for page in range(20):
        got=rpc.call("getSignaturesForAddress",[
            TARGET,
            {"before":before,"until":until,"limit":1000,"commitment":"finalized"}
        ])
        if not isinstance(got,list):
            raise RuntimeError("signature_page_schema")
        if not got:
            pages.append({"page":page+1,"count":0,"before":before})
            terminated=True
            break
        if any(type(x.get("blockTime")) is not int for x in got):
            raise RuntimeError("signature_blocktime_missing")
        if any(got[i]["slot"]<got[i+1]["slot"] for i in range(len(got)-1)):
            raise RuntimeError("non_descending_slot_page")
        for x in got:
            sig=x.get("signature")
            if not isinstance(sig,str) or not sig:
                raise RuntimeError("signature_missing")
            if sig in seen: duplicate_count+=1
            seen.add(sig)
            if START<=x["blockTime"]<END:
                in_window.add(sig)
        nxt=got[-1]["signature"]
        pages.append({
            "page":page+1,"count":len(got),"before":before,"next_before":nxt,
            "first_slot":got[0]["slot"],"last_slot":got[-1]["slot"],
            "first_time":got[0]["blockTime"],"last_time":got[-1]["blockTime"]
        })
        if nxt==before: raise RuntimeError("nonadvancing_cursor")
        before=nxt
        if got[-1]["blockTime"]<START:
            terminated=True
            break

    classification=(
        "TIME_CURSOR_TRANSPORT_PASS"
        if terminated and len(in_window)==EXPECTED and duplicate_count==0
        else "TIME_CURSOR_TRANSPORT_BLOCKED"
    )
    receipt={
      "schema_version":"0.1",
      "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":classification,
      "target_address":TARGET,
      "interval":{"start_unix":START,"end_unix":END},
      "resolved_slots":{"start":start_slot,"end":end_slot},
      "lower_cursor":lower,
      "upper_cursor":upper,
      "expected_in_window_signatures":EXPECTED,
      "observed_in_window_signatures":len(in_window),
      "duplicate_count":duplicate_count,
      "termination_reached":terminated,
      "pages":pages,
      "rpc_request_count":rpc.calls,
      "paid_getTransactionsForAddress_used":False,
      "transaction_payloads_opened":False,
      "protected_2025_acquisition":False,
      "market_outcomes_opened":False,
      "science_changed":False,
      "trading_authority":"NONE"
    }
    path=OUT/"DLS_ROUTE_A2_TIME_CURSOR_PROBE_RECEIPT_V0.1.json"
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":classification,
        "observed_in_window_signatures":len(in_window),
        "expected_in_window_signatures":EXPECTED,
        "duplicate_count":duplicate_count,
        "rpc_request_count":rpc.calls,
        "lower_cursor_time":lower["blockTime"],
        "upper_cursor_time":upper["blockTime"]
    },indent=2,sort_keys=True))
    if classification!="TIME_CURSOR_TRANSPORT_PASS":
        raise SystemExit(2)

if __name__=="__main__":
    main()
