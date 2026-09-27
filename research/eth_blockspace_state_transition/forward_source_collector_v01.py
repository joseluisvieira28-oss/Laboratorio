#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, urllib.request, time, hashlib, statistics, math, sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

LAB="ETH-BLOCKSPACE-STATE-TRANSITION-001"
PRIMARY="https://rpc.flashbots.net"
AUDITORS=["https://public.1rpc.io/eth","https://eth.drpc.org"]
REQ=["number","hash","timestamp","gasLimit","gasUsed","baseFeePerGas","blobGasUsed","excessBlobGas"]
STATE_DIR=Path("forward_state/ebst")
LEDGER=STATE_DIR/"EBST_HEADER_SAMPLES_V0_1.jsonl"
RECEIPT=STATE_DIR/"EBST_FORWARD_SOURCE_STATE_V0_1.json"
MIN_SAMPLES_DAY=8
PRIOR_DAYS=30

def rpc(ep,method,params,retries=4):
    last=None
    for i in range(retries):
        try:
            body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
            req=urllib.request.Request(ep,data=body,headers={"Content-Type":"application/json","User-Agent":"EBST-forward-source-v0.1"})
            with urllib.request.urlopen(req,timeout=30) as r:
                o=json.loads(r.read().decode())
            if not isinstance(o,dict) or o.get("error") is not None:
                raise RuntimeError(str(o)[:250])
            return o.get("result")
        except Exception as e:
            last=e
            if i+1<retries: time.sleep(min(1.0*(2**i),6.0))
    raise RuntimeError(f"{type(last).__name__}:{last}")

def qi(x):
    if not isinstance(x,str) or not x.startswith("0x"): raise ValueError("quantity")
    return int(x,16)

def parse(o):
    if not isinstance(o,dict): raise RuntimeError("null block")
    miss=[k for k in REQ if o.get(k) is None]
    if miss: raise RuntimeError("missing:"+",".join(miss))
    n=qi(o["number"]); gl=qi(o["gasLimit"]); gu=qi(o["gasUsed"]); bf=qi(o["baseFeePerGas"])
    bg=qi(o["blobGasUsed"]); ex=qi(o["excessBlobGas"])
    if gl<=0 or gu<0 or gu>gl or bf<=0 or bg<0 or ex<0: raise RuntimeError("header sanity")
    return {"block_number":n,"block_hash":str(o["hash"]).lower(),"timestamp":qi(o["timestamp"]),
            "gas_utilization":gu/gl,"blob_gas_used":bg,"excess_blob_gas":ex}

def sample_once():
    p=parse(rpc(PRIMARY,"eth_getBlockByNumber",["finalized",False]))
    audit_errors=[]
    audit=None
    for ep in AUDITORS:
        try:
            a=parse(rpc(ep,"eth_getBlockByNumber",[hex(p["block_number"]),False]))
            if a["block_hash"]!=p["block_hash"] or a["timestamp"]!=p["timestamp"]:
                raise RuntimeError("provider identity disagreement")
            audit={"provider":ep,"block_hash":a["block_hash"],"timestamp":a["timestamp"]}
            break
        except Exception as e:
            audit_errors.append(f"{ep}:{type(e).__name__}:{str(e)[:160]}")
    if audit is None: raise RuntimeError("no independent audit provider: "+" | ".join(audit_errors))
    now=datetime.now(timezone.utc)
    slot_hour=(now.hour//2)*2
    slot=f"{now.date().isoformat()}T{slot_hour:02d}:00:00Z"
    return {**p,"slot_utc":slot,"observed_at_utc":now.isoformat().replace("+00:00","Z"),
            "primary_provider":PRIMARY,"audit_provider":audit["provider"]}

def load_ledger():
    if not LEDGER.exists(): return []
    out=[]
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.strip(): out.append(json.loads(line))
    return out

def percentile(vals,p):
    x=sorted(vals); pos=(len(x)-1)*p
    lo=math.floor(pos); hi=math.ceil(pos)
    if lo==hi:return x[lo]
    f=pos-lo
    return x[lo]*(1-f)+x[hi]*f

def build_state(rows):
    by=defaultdict(list)
    for r in rows:
        d=datetime.fromtimestamp(r["timestamp"],timezone.utc).date().isoformat()
        by[d].append(r)
    today=datetime.now(timezone.utc).date().isoformat()
    daily=[]
    for d in sorted(by):
        if d==today: continue
        xs=by[d]
        if len(xs)<MIN_SAMPLES_DAY: continue
        daily.append({"date":d,"samples":len(xs),
                      "exec_median":statistics.median(x["gas_utilization"] for x in xs),
                      "blob_median":statistics.median(x["blob_gas_used"] for x in xs),
                      "excess_blob_median":statistics.median(x["excess_blob_gas"] for x in xs)})
    states=[]
    for i in range(PRIOR_DAYS,len(daily)):
        prior=daily[i-PRIOR_DAYS:i]
        ep75=percentile([x["exec_median"] for x in prior],0.75)
        bp75=percentile([x["blob_median"] for x in prior],0.75)
        e=daily[i]["exec_median"]>=ep75; b=daily[i]["blob_median"]>=bp75
        states.append({**daily[i],"prior30_exec_p75":ep75,"prior30_blob_p75":bp75,
                       "exec_high":e,"blob_high":b,"joint_high":e and b})
    for j,s in enumerate(states):
        s["transition"]=False
        if j>=3:
            s["transition"]=bool(s["joint_high"] and states[j-1]["joint_high"] and
                                 ((not states[j-2]["joint_high"]) or (not states[j-3]["joint_high"])))
    return daily,states

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--collect",action="store_true"); ap.add_argument("--preflight",action="store_true")
    a=ap.parse_args()
    rec={"lab_id":LAB,"classification":"FORWARD_SOURCE_ERROR","market_prices_opened":False,
         "returns_opened":False,"pnl_opened":False,"parent_holdout_opened":False}
    try:
        s=sample_once()
        if a.preflight and not a.collect:
            rec.update({"classification":"FORWARD_SOURCE_PREFLIGHT_PASS","sample":s,"ledger_mutated":False})
        else:
            STATE_DIR.mkdir(parents=True,exist_ok=True)
            rows=load_ledger()
            slots={x["slot_utc"] for x in rows}
            if s["slot_utc"] not in slots:
                rows.append(s); rows.sort(key=lambda x:(x["slot_utc"],x["block_number"]))
                LEDGER.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows),encoding="utf-8")
            daily,states=build_state(rows)
            rec.update({"classification":"FORWARD_SOURCE_COLLECTING","sample":s,"ledger_samples":len(rows),
                        "complete_daily_rows":len(daily),"state_rows":len(states),
                        "warmup_complete":len(daily)>=PRIOR_DAYS+2,
                        "latest_state":states[-1] if states else None,
                        "transition_dates":[x["date"] for x in states if x["transition"]],
                        "ledger_mutated":True})
            RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    except Exception as e:
        rec["failure"]=f"{type(e).__name__}:{e}"
    rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(json.dumps({"classification":rec["classification"],"ledger_samples":rec.get("ledger_samples"),
                      "complete_daily_rows":rec.get("complete_daily_rows"),"warmup_complete":rec.get("warmup_complete"),
                      "market_prices_opened":False,"failure":rec.get("failure")},sort_keys=True))
    return 0 if rec["classification"]!="FORWARD_SOURCE_ERROR" else 2

if __name__=="__main__": sys.exit(main())
