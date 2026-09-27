#!/usr/bin/env python3
from __future__ import annotations
import json, urllib.request, time, hashlib, statistics, math, sys
from collections import defaultdict
from datetime import datetime, timezone

LAB="ETH-BLOCKSPACE-STATE-TRANSITION-001"
EPS=["https://public.1rpc.io/eth","https://rpc.flashbots.net"]
REQ=["number","hash","timestamp","gasLimit","gasUsed","baseFeePerGas","blobGasUsed","excessBlobGas"]
STEP_BLOCKS=600
LOOKBACK_BLOCKS=40*7200
MIN_SAMPLES_PER_DAY=8
PRIOR_DAYS=30

def post(ep,payload,retries=5):
    last=None
    for i in range(retries):
        try:
            body=json.dumps(payload).encode()
            req=urllib.request.Request(ep,data=body,headers={"Content-Type":"application/json","User-Agent":"EBST-warmup-v0.1b"})
            with urllib.request.urlopen(req,timeout=45) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last=e
            if i+1<retries: time.sleep(min(1.0*(2**i),8))
    raise RuntimeError(f"{type(last).__name__}:{last}")

def rpc(ep,method,params):
    o=post(ep,{"jsonrpc":"2.0","id":1,"method":method,"params":params})
    if not isinstance(o,dict) or o.get("error") is not None:
        raise RuntimeError(str(o))
    return o.get("result")

def qi(x):
    if not isinstance(x,str) or not x.startswith("0x"): raise ValueError("quantity")
    return int(x,16)

def parse_block(o,h):
    if not isinstance(o,dict): raise RuntimeError("null block")
    miss=[k for k in REQ if o.get(k) is None]
    if miss: raise RuntimeError("missing:"+",".join(miss))
    n=qi(o["number"]); gl=qi(o["gasLimit"]); gu=qi(o["gasUsed"])
    bg=qi(o["blobGasUsed"]); ex=qi(o["excessBlobGas"]); bf=qi(o["baseFeePerGas"])
    if n!=h or gl<=0 or gu<0 or gu>gl or bg<0 or ex<0 or bf<=0:
        raise RuntimeError("header sanity")
    return {"number":n,"hash":o["hash"].lower(),"timestamp":qi(o["timestamp"]),
            "gas_utilization":gu/gl,"blob_gas_used":bg,"excess_blob_gas":ex}

def fetch(ep,h):
    return parse_block(rpc(ep,"eth_getBlockByNumber",[hex(h),False]),h)

def batch_fetch(ep,heights):
    reqs=[{"jsonrpc":"2.0","id":i,"method":"eth_getBlockByNumber","params":[hex(h),False]}
          for i,h in enumerate(heights)]
    raw=post(ep,reqs)
    if not isinstance(raw,list): raise RuntimeError("batch non-list")
    byid={int(x["id"]):x for x in raw if isinstance(x,dict) and "id" in x}
    out=[]
    for i,h in enumerate(heights):
        x=byid.get(i)
        if x is None or x.get("error") is not None:
            raise RuntimeError(f"batch item failure {h}")
        out.append(parse_block(x.get("result"),h))
    return out

def percentile(vals,p):
    x=sorted(vals)
    pos=(len(x)-1)*p
    lo=math.floor(pos); hi=math.ceil(pos)
    if lo==hi:return x[lo]
    f=pos-lo
    return x[lo]*(1-f)+x[hi]*f

def main():
    out={"lab_id":LAB,"schema":"EBST_SOURCE_WARMUP_V0.1","classification":"SOURCE_WARMUP_FAILURE",
         "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
         "parent_protected_holdout_opened":False}
    try:
        for ep in EPS:
            if rpc(ep,"eth_chainId",[])!="0x1": raise RuntimeError("wrong chain")
        tip=rpc(EPS[0],"eth_getBlockByNumber",["finalized",False])
        tipn=qi(tip["number"])
        start=max(0,tipn-LOOKBACK_BLOCKS)
        heights=list(range(start,tipn+1,STEP_BLOCKS))
        if heights[-1]!=tipn: heights.append(tipn)
        rows=[]
        audit_pass=0
        chunk=40
        for base in range(0,len(heights),chunk):
            hs=heights[base:base+chunk]
            even_h=[h for j,h in enumerate(hs,start=base) if j%2==0]
            odd_h=[h for j,h in enumerate(hs,start=base) if j%2==1]
            even_rows=batch_fetch(EPS[0],even_h) if even_h else []
            odd_rows=batch_fetch(EPS[1],odd_h) if odd_h else []
            merged={r["number"]:r for r in even_rows+odd_rows}
            for j,h in enumerate(hs,start=base):
                a=merged[h]
                if j%40==0:
                    b=fetch(EPS[0],h)
                    if a["hash"]!=b["hash"] or a["timestamp"]!=b["timestamp"]:
                        raise RuntimeError(f"provider disagreement {h}")
                    audit_pass+=1
                rows.append(a)
            time.sleep(0.25)
        by=defaultdict(list)
        current_utc=datetime.now(timezone.utc).date().isoformat()
        for r in rows:
            d=datetime.fromtimestamp(r["timestamp"],timezone.utc).date().isoformat()
            if d!=current_utc: by[d].append(r)
        daily=[]
        for d in sorted(by):
            xs=by[d]
            if len(xs)<MIN_SAMPLES_PER_DAY: continue
            daily.append({"date":d,"samples":len(xs),
                          "exec_median":statistics.median(x["gas_utilization"] for x in xs),
                          "blob_median":statistics.median(x["blob_gas_used"] for x in xs),
                          "excess_blob_median":statistics.median(x["excess_blob_gas"] for x in xs)})
        if len(daily)<PRIOR_DAYS+2:
            raise RuntimeError(f"insufficient complete days:{len(daily)}")
        states=[]
        for i in range(PRIOR_DAYS,len(daily)):
            prior=daily[i-PRIOR_DAYS:i]
            ep75=percentile([x["exec_median"] for x in prior],0.75)
            bp75=percentile([x["blob_median"] for x in prior],0.75)
            ehigh=daily[i]["exec_median"]>=ep75
            bhigh=daily[i]["blob_median"]>=bp75
            states.append({**daily[i],"prior30_exec_p75":ep75,"prior30_blob_p75":bp75,
                           "exec_high":ehigh,"blob_high":bhigh,"joint_high":ehigh and bhigh})
        for j,s in enumerate(states):
            s["transition"]=False
            if j>=3:
                s["transition"]=bool(s["joint_high"] and states[j-1]["joint_high"] and
                                     ((not states[j-2]["joint_high"]) or (not states[j-3]["joint_high"])))
        out.update({"classification":"SOURCE_WARMUP_PASS","latest_finalized_block":tipn,
                    "sampled_headers":len(rows),"cross_provider_audits_pass":audit_pass,
                    "complete_daily_rows":len(daily),"state_rows":states,
                    "latest_complete_state":states[-1],"source_only_transition_dates":[x["date"] for x in states if x["transition"]]})
    except Exception as e:
        out["failure"]=f"{type(e).__name__}:{e}"
    canonical=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    out["receipt_sha256"]=hashlib.sha256(canonical).hexdigest()
    open("EBST_SOURCE_WARMUP_V0_1.json","w",encoding="utf-8").write(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":out["classification"],"sampled_headers":out.get("sampled_headers",0),
                      "complete_daily_rows":out.get("complete_daily_rows",0),
                      "cross_provider_audits_pass":out.get("cross_provider_audits_pass",0),
                      "source_only_transition_count":len(out.get("source_only_transition_dates",[])),
                      "market_prices_opened":False,"failure":out.get("failure")},sort_keys=True))
    return 0 if out["classification"]=="SOURCE_WARMUP_PASS" else 2

if __name__=="__main__": sys.exit(main())
