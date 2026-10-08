#!/usr/bin/env python3
"""Source-only transport gate for PREMIUM-BASIS-PERP-TRANSFER-001."""
from __future__ import annotations
import hashlib, json, math, time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE="https://api.mexc.com"
SYMBOL="MUSTOCK_USDT"
OUT=Path("evidence/premium-basis-perp-transfer-source-v01")
DURATION=630
POLL=30
STEP=300
ROLL_SEC=86400
ROLL_MAX=288
ROLL_MIN=240
MAX_AGE_MS=5000
FUTURE_TOL_MS=1000

def utcnow(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()

def save(name,b,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(b)
    return {"path":name,"sha256":sha(b),"bytes":len(b),**meta}

def fetch_kline(kind,start,end):
    route="index_price" if kind=="index" else "fair_price"
    url=f"{BASE}/api/v1/contract/kline/{route}/{SYMBOL}"
    r=requests.get(url,params={"interval":"Min5","start":start,"end":end},timeout=20)
    raw=r.content
    if r.status_code!=200: raise RuntimeError(f"{kind}_HTTP_{r.status_code}")
    j=r.json()
    if j.get("success") is not True: raise RuntimeError(f"{kind}_NON_SUCCESS:{j.get('code')}")
    out={}
    d=j.get("data") or {}
    for s,p in zip(d.get("time") or [],d.get("close") or []):
        try: s=int(s); p=float(p)
        except Exception: continue
        mapped=s+STEP
        if mapped<=end and p>0 and math.isfinite(p): out[mapped]=p
    return out,raw,r.url

def build_z(index,fair):
    premium={}
    for t in sorted(set(index)&set(fair)):
        ip=index[t]; fp=fair[t]
        if ip>0 and math.isfinite(ip) and math.isfinite(fp):
            premium[t]=(fp-ip)/ip*10000.0
    q=deque(); s=ss=0.0; z={}
    for t in sorted(premium):
        x=premium[t]; q.append((t,x)); s+=x; ss+=x*x
        cutoff=t-ROLL_SEC+STEP
        while q and q[0][0]<cutoff:
            _,old=q.popleft(); s-=old; ss-=old*old
        while len(q)>ROLL_MAX:
            _,old=q.popleft(); s-=old; ss-=old*old
        n=len(q)
        if n<ROLL_MIN: continue
        mean=s/n
        var=(ss-n*mean*mean)/(n-1)
        if var>0 and math.isfinite(var): z[t]=(x-mean)/math.sqrt(var)
    return premium,z

def depth():
    url=f"{BASE}/api/v1/contract/depth/{SYMBOL}"
    r=requests.get(url,params={"limit":20},timeout=20)
    raw=r.content; recv_ms=int(time.time()*1000)
    if r.status_code!=200: raise RuntimeError(f"DEPTH_HTTP_{r.status_code}")
    j=r.json()
    if j.get("success") is not True: raise RuntimeError(f"DEPTH_NON_SUCCESS:{j.get('code')}")
    d=j.get("data") or {}
    bids=d.get("bids") or []; asks=d.get("asks") or []
    if not bids or not asks: raise RuntimeError("EMPTY_BOOK")
    bp=max(float(x[0]) for x in bids if float(x[0])>0)
    ap=min(float(x[0]) for x in asks if float(x[0])>0)
    if not (math.isfinite(bp) and math.isfinite(ap) and 0<bp<ap): raise RuntimeError("CROSSED_OR_BAD_BOOK")
    ts=int(d.get("timestamp"))
    age=recv_ms-ts
    if age>MAX_AGE_MS: raise RuntimeError(f"STALE_BOOK:{age}")
    if age<-FUTURE_TOL_MS: raise RuntimeError(f"FUTURE_BOOK:{age}")
    return {"best_bid":bp,"best_ask":ap,"spread_bps":10000*(ap-bp)/((ap+bp)/2),
            "source_ts_ms":ts,"received_at_ms":recv_ms,"age_ms":age},raw,r.url

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=[]; errors=[]; healthy=[]; started=time.time(); deadline=time.monotonic()+DURATION
    # frozen-signal warmup source check: source-only, no forward outcome
    now=int(time.time()); start=now-31*3600
    signal_state={}
    try:
        idx,ib,iu=fetch_kline("index",start,now)
        fair,fb,fu=fetch_kline("fair",start,now)
        manifest.append(save("index_warmup.json",ib,{"source_url":iu,"received_at_utc":utcnow()}))
        manifest.append(save("fair_warmup.json",fb,{"source_url":fu,"received_at_utc":utcnow()}))
        premium,z=build_z(idx,fair)
        latest=max(z) if z else None
        signal_state={
          "index_rows":len(idx),"fair_rows":len(fair),"z_rows":len(z),"latest_z_ts":latest,
          "latest_z":(z.get(latest) if latest else None),
          "latest_premium_bps":(premium.get(latest) if latest else None),
          "warmup_pass": bool(len(idx)>=ROLL_MIN and len(fair)>=ROLL_MIN and z)
        }
    except Exception as e:
        errors.append({"phase":"WARMUP","type":type(e).__name__,"error":str(e),"at":utcnow()})
        signal_state={"warmup_pass":False}

    seq=0
    while True:
        seq+=1
        try:
            d,raw,url=depth()
            ref=save(f"depth_{seq:03d}.json",raw,{"source_url":url,"received_at_utc":utcnow()})
            d["raw_sha256"]=ref["sha256"]; healthy.append(d)
        except Exception as e:
            errors.append({"phase":"DEPTH","seq":seq,"type":type(e).__name__,"error":str(e),"at":utcnow()})
        if time.monotonic()>=deadline: break
        time.sleep(min(POLL,max(0,deadline-time.monotonic())))

    span=(healthy[-1]["received_at_ms"]-healthy[0]["received_at_ms"])/1000 if len(healthy)>=2 else 0
    verdict=("PERP_TRANSFER_SOURCE_PASS"
             if signal_state.get("warmup_pass") and len(healthy)>=20 and span>=600
             else "PERP_TRANSFER_SOURCE_BLOCKED")
    receipt={
      "experiment_id":"PREMIUM-BASIS-PERP-TRANSFER-001",
      "phase":"SOURCE_ONLY_TRANSPORT_GATE",
      "freeze_commit":"c0b402ac658974a944d42c62bd888a07db35bfd2",
      "freeze_boundary_utc":"2026-10-08T05:47:49Z",
      "verdict":verdict,
      "duration_seconds":time.time()-started,
      "healthy_depth_snapshots":len(healthy),
      "healthy_span_seconds":span,
      "median_spread_bps":(sorted(x["spread_bps"] for x in healthy)[len(healthy)//2] if healthy else None),
      "max_spread_bps":(max((x["spread_bps"] for x in healthy),default=None)),
      "signal_source":signal_state,
      "errors":errors,
      "outcomes_opened":0,
      "authenticated_calls":0,"orders":0,"account_reads":0,"exchange_mutation":0,
      "evidence":manifest
    }
    (OUT/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
