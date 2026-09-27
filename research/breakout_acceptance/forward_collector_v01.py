#!/usr/bin/env python3
from __future__ import annotations
import csv, io, json, math, statistics, time, urllib.parse, urllib.request, hashlib, sys
from datetime import datetime, timezone

LAB="BREAKOUT-ACCEPTANCE-001"
CANDIDATE="BAV-ARQ018-4H-H48-001"
BASE="https://data-api.binance.vision"
SYMS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
INTERVAL="4h"
BOUNDARY_MS=int(datetime(2026,9,28,tzinfo=timezone.utc).timestamp()*1000)
BAR_MS=4*60*60*1000
BASE_COST=20.0
STRESS_COST=30.0
LOOKBACK=60
ATR_N=14
HOLD_BARS=12

def get_klines(sym):
    q=urllib.parse.urlencode({"symbol":sym,"interval":INTERVAL,"limit":1000})
    req=urllib.request.Request(BASE+"/api/v3/klines?"+q,headers={"User-Agent":"BREAKOUT-ACCEPTANCE-forward-v0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        o=json.loads(r.read().decode())
    if not isinstance(o,list): raise RuntimeError(f"{sym}: non-list response")
    now=int(time.time()*1000)
    rows=[]
    for x in o:
        ot=int(x[0]); ct=int(x[6])
        if ct>=now: continue
        rows.append({"ot":ot,"ct":ct,"open":float(x[1]),"high":float(x[2]),"low":float(x[3]),"close":float(x[4]),"vol":float(x[5])})
    if len(rows)<100: raise RuntimeError(f"{sym}: insufficient closed bars")
    for a,b in zip(rows,rows[1:]):
        if b["ot"]-a["ot"]!=BAR_MS: raise RuntimeError(f"{sym}: noncontiguous bars")
    return rows

def percentile(vals,p):
    x=sorted(vals)
    pos=(len(x)-1)*p
    lo=math.floor(pos); hi=math.ceil(pos)
    if lo==hi:return x[lo]
    f=pos-lo
    return x[lo]*(1-f)+x[hi]*f

def true_range(cur,prev_close):
    return max(cur["high"]-cur["low"],abs(cur["high"]-prev_close),abs(cur["low"]-prev_close))

def wilder_atr_strict_prior(rows,idx,n=ATR_N):
    # ATR at breakout idx using completed bars strictly before idx.
    if idx<n+1: return None
    trs=[]
    for j in range(1,idx):
        trs.append(true_range(rows[j],rows[j-1]["close"]))
    if len(trs)<n:return None
    atr=sum(trs[:n])/n
    for tr in trs[n:]:
        atr=((n-1)*atr+tr)/n
    return atr

def pf(vals):
    pos=sum(x for x in vals if x>0); neg=-sum(x for x in vals if x<0)
    return pos/neg if neg>0 else None

def scan(sym,rows):
    obs=[]; active_until=-1
    for i in range(max(LOOKBACK,ATR_N+1),len(rows)-2):
        if i<=active_until: continue
        prior=rows[i-LOOKBACK:i]
        rh=max(x["high"] for x in prior)
        atr=wilder_atr_strict_prior(rows,i)
        if atr is None: continue
        vol75=percentile([x["vol"] for x in prior],0.75)
        b=rows[i]
        if not (b["close"]>rh+0.25*atr and b["vol"]>=vol75): continue
        if i+2>=len(rows): continue
        a1,a2=rows[i+1],rows[i+2]
        if not (a1["close"]>rh and a2["close"]>rh): continue
        entry_idx=i+3
        if entry_idx>=len(rows): continue
        entry=rows[entry_idx]
        if entry["ot"]<BOUNDARY_MS: continue
        exit_idx=entry_idx+HOLD_BARS
        rec={"symbol":sym,"breakout_open_ms":b["ot"],"accept1_open_ms":a1["ot"],"accept2_open_ms":a2["ot"],
             "entry_open_ms":entry["ot"],"entry_price":entry["open"],"frozen_range_high":rh,
             "prior_atr14":atr,"prior_volume_p75":vol75,"breakout_volume":b["vol"],
             "status":"OPEN","exit_open_ms":entry["ot"]+HOLD_BARS*BAR_MS}
        active_until=exit_idx
        if exit_idx<len(rows):
            ex=rows[exit_idx]
            # Strict source rule: exit bar itself must be completed because only completed bars are usable.
            gross=(ex["open"]/entry["open"]-1.0)*10000.0
            rec.update({"status":"RESOLVED","exit_price":ex["open"],"gross_bps":gross,
                        "base_net_bps":gross-BASE_COST,"stress_net_bps":gross-STRESS_COST})
        obs.append(rec)
    return obs

def main():
    out={"lab_id":LAB,"candidate_id":CANDIDATE,"schema":"BREAKOUT_ACCEPTANCE_FORWARD_V0.1",
         "boundary_utc":"2026-09-28T00:00:00Z","classification":"FORWARD_COLLECTOR_ERROR",
         "source_host":BASE,"symbols":{},"observations":[],"safety":{"live_trading":False,"orders":False,
         "exchange_mutation":False,"wallets":False,"preboundary_outcome_count":0}}
    try:
        allobs=[]
        for s in SYMS:
            rows=get_klines(s)
            xs=scan(s,rows)
            out["symbols"][s]={"closed_bars":len(rows),"first_open_ms":rows[0]["ot"],"last_open_ms":rows[-1]["ot"],"eligible_observations":len(xs)}
            allobs.extend(xs)
        allobs.sort(key=lambda x:(x["entry_open_ms"],x["symbol"]))
        if any(x["entry_open_ms"]<BOUNDARY_MS for x in allobs):
            out["safety"]["preboundary_outcome_count"]=sum(x["entry_open_ms"]<BOUNDARY_MS for x in allobs)
            raise RuntimeError("BOUNDARY_BREACH")
        resolved=[x for x in allobs if x["status"]=="RESOLVED"]
        base=[x["base_net_bps"] for x in resolved]
        stress=[x["stress_net_bps"] for x in resolved]
        out["observations"]=allobs
        out["metrics"]={"resolved_n":len(resolved),"open_n":len(allobs)-len(resolved),
                        "represented_symbols":len({x["symbol"] for x in resolved}),
                        "base_mean_bps":statistics.mean(base) if base else None,
                        "base_pf":pf(base) if base else None,
                        "stress_mean_bps":statistics.mean(stress) if stress else None,
                        "calendar_weeks_since_boundary":max(0.0,(time.time()*1000-BOUNDARY_MS)/(7*24*3600*1000))}
        if int(time.time()*1000)<BOUNDARY_MS:
            out["classification"]="PRE_BOUNDARY_ARMED"
        elif len(resolved)<20:
            out["classification"]="INSUFFICIENT_MATURITY"
        else:
            out["classification"]="DESCRIPTIVE_CHECKPOINT_READY"
        # Formal adjudication is intentionally not performed before both frozen maturity conditions are met.
        if len(resolved)>=40 and out["metrics"]["calendar_weeks_since_boundary"]>=8 and out["metrics"]["represented_symbols"]>=3:
            out["classification"]="FORMAL_REVIEW_READY"
    except Exception as e:
        out["failure"]=f"{type(e).__name__}:{e}"
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    out["receipt_sha256"]=hashlib.sha256(raw).hexdigest()
    with open("BREAKOUT_ACCEPTANCE_FORWARD_V0_1.json","w",encoding="utf-8") as f:
        json.dump(out,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps({"classification":out["classification"],"resolved_n":out.get("metrics",{}).get("resolved_n"),
                      "open_n":out.get("metrics",{}).get("open_n"),"preboundary_outcome_count":out["safety"]["preboundary_outcome_count"],
                      "failure":out.get("failure")},sort_keys=True))
    return 0 if out["classification"]!="FORWARD_COLLECTOR_ERROR" else 2

if __name__=="__main__": sys.exit(main())
