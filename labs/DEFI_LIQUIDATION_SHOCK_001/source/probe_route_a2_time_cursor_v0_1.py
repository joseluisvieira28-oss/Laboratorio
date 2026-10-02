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

def block_sig(rpc,slot0,direction,predicate,max_steps=1500):
    slot=slot0
    for i in range(max_steps):
        r=rpc.call("getBlock",[slot,{"transactionDetails":"signatures","rewards":False,"maxSupportedTransactionVersion":0}])
        if isinstance(r,dict):
            bt=r.get("blockTime"); sigs=r.get("signatures") or []
            if isinstance(bt,int) and sigs and predicate(bt):
                return {"slot":slot,"blockTime":bt,"signature":sigs[0],"steps":i}
        slot+=direction
        if slot<0:break
    raise RuntimeError("cursor_block_not_found")

def main():
    OUT.mkdir(exist_ok=True)
    rpc=RPC()
    ss=ts_slot(START); es=ts_slot(END)
    lower=block_sig(rpc,ss,-1,lambda x:x<START)
    upper=block_sig(rpc,es,1,lambda x:x>=END)
    assert lower["blockTime"]<START and upper["blockTime"]>=END
    before=upper["signature"]; until=lower["signature"]
    seen=set(); rows=[]; pages=[]; dup=0
    for page in range(20):
        params=[TARGET,{"before":before,"until":until,"limit":1000,"commitment":"finalized"}]
        got=rpc.call("getSignaturesForAddress",params)
        if not isinstance(got,list):raise RuntimeError("signature_page_schema")
        if not got:
            pages.append({"page":page+1,"count":0,"before":before})
            break
        if any(type(x.get("blockTime")) is not int for x in got):
            raise RuntimeError("signature_blocktime_missing")
        if any(got[i]["slot"]<got[i+1]["slot"] for i in range(len(got)-1)):
            raise RuntimeError("non_descending_slot_page")
        for x in got:
            sig=x.get("signature")
            if sig in seen:dup+=1
            seen.add(sig)
            if START<=x["blockTime"]<END:rows.append(x)
        nxt=got[-1]["signature"]
        pages.append({"page":page+1,"count":len(got),"first_slot":got[0]["slot"],"last_slot":got[-1]["slot"],"before":before,"next_before":nxt})
        if nxt==before:raise RuntimeError("nonadvancing_cursor")
        before=nxt
        if got[-1]["blockTime"]<START:break
    unique_in={x["signature"] for x in rows}
    classification="TIME_CURSOR_TRANSPORT_PASS" if len(unique_in)==EXPECTED and dup==0 else "TIME_CURSOR_TRANSPORT_BLOCKED"
    receipt={
      "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":classification,
      "target":TARGET,
      "interval":{"start_unix":START,"end_unix":END},
      "resolved_slots":{"start":ss,"end":es},
      "lower_cursor":lower,"upper_cursor":upper,
      "expected_in_window_signatures":EXPECTED,
      "observed_in_window_signatures":len(unique_in),
      "duplicate_count":dup,
      "page_count":len(pages),"pages":pages,
      "rpc_request_count":rpc.calls,
      "paid_getTransactionsForAddress_used":False,
      "transaction_payloads_opened":False,
      "market_outcomes_opened":False,
      "protected_2025_acquisition":False,
      "science_changed":False,
      "trading_authority":"NONE"
    }
    (OUT/"DLS_ROUTE_A2_TIME_CURSOR_PROBE_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    if classification!="TIME_CURSOR_TRANSPORT_PASS":raise SystemExit(2)

if __name__=="__main__":main()
