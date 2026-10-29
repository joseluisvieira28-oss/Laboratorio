#!/usr/bin/env python3
"""MU vs MEXC index 10m disagreement: 2-day frozen historical diagnostic ONLY."""
import datetime as dt
import hashlib,json,math
from pathlib import Path
from zoneinfo import ZoneInfo
import event10m_mu_source_v01 as parent

OUT=Path("artifacts/event10m_mu_divergence_v02")
UTC=dt.timezone.utc
NY=ZoneInfo("America/New_York")
SHA_Y="aea2418b3308cec57eb1480fcf847ab9e4b82f2f9091b72a8eb14770dfcb6c5d"
SHA_M={"2026-10-26":"a950a8fef646d3773cd415e13a10c55d2e35cbef608bcfa1b02752aa149c884a",
       "2026-10-27":"a93f2e96071080ff7769aea2665353a28509623a099928181b4af2341b1c00a3"}
PAYOUT=(0.80,0.85)
SIDES=("MU_SIGN","ALWAYS_UP","ALWAYS_DOWN","MEXC_MOMENTUM")

def canonical(series):
    # Exactly the same representation as pre-outcome V0.2.1 source gate.
    return hashlib.sha256(json.dumps(sorted(series.items()),
                          separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

def data(stock):
    if stock:
        start=parent.seconds(parent.midnight(parent.DAYS[0]))
        end=parent.seconds(parent.midnight(parent.DAYS[-1]+dt.timedelta(days=1)))
        import urllib.parse
        url="https://query1.finance.yahoo.com/v8/finance/chart/MU?"+urllib.parse.urlencode(
             {"period1":start,"period2":end,"interval":"1m","includePrePost":"false"})
        raw=parent.download(url,3500000)
        result=json.loads(raw)["chart"]["result"][0]
        timestamps=result["timestamp"]
        closes=result["indicators"]["quote"][0]["close"]
        if len(timestamps)!=len(closes):raise ValueError("STOCK_SOURCE_MISALIGNED")
        series={int(t):float(v) for t,v in zip(timestamps,closes)
                if v is not None and math.isfinite(float(v)) and float(v)>0}
        digest=canonical(series)
        if digest!=SHA_Y:raise ValueError("YAHOO_CANONICAL_SHA_CHANGED "+digest)
        return series
    out={}
    for day in parent.DAYS:
        a=parent.seconds(parent.midnight(day));import urllib.parse
        url="https://contract.mexc.com/api/v1/contract/kline/index_price/MUSTOCK_USDT?"+urllib.parse.urlencode(
           {"interval":"Min1","start":a,"end":a+86400-60})
        raw=parent.download(url)
        d=json.loads(raw)["data"]
        ts=d["time"];prices=d["open"]
        if len(ts)!=len(prices) or not ts:raise ValueError("INDEX_SOURCE_SCHEMA")
        daily={}
        for t,p in zip(ts,prices):
            t=int(t);p=float(p)
            if t in daily or t in out or not math.isfinite(p) or p<=0 or not a<=t<a+86400:
                raise ValueError("INDEX_SOURCE_INVALID")
            daily[t]=p
        digest=canonical(daily)
        if digest!=SHA_M[day.isoformat()]:
            raise ValueError("MEXC_CANONICAL_SHA_CHANGED "+day.isoformat()+" "+digest)
        out.update(daily)
    return out
def direction(x,y):return 1 if x>y else -1 if x<y else 0
def times(day):
    base=dt.datetime.combine(day,dt.time(9,40),NY)
    return [int((base+dt.timedelta(minutes=i*10)).timestamp()) for i in range(5)]
def result(sign,delta):
    return "TIE" if delta==0 else "WIN" if sign*delta>0 else "LOSS"
def score(events):
    w=sum(x=="WIN" for x in events)
    loss=sum(x=="LOSS" for x in events)
    ties=len(events)-w-loss
    return {"n":len(events),"wins":w,"losses":loss,"ties":ties,
            "accuracy_non_tie":w/(w+loss) if w+loss else None,
            "hypothetical_unit_EV":{str(q):(q*w-loss)/len(events) if events else None for q in PAYOUT}}
def main():
    OUT.mkdir(exist_ok=True,parents=True)
    report={"lab":"EVENT10M_MU_DIVERGENCE_V02","stage":"TWO_DAY_DESCRIPTIVE_HISTORICAL",
      "dates":[str(x) for x in parent.DAYS],"scheduled_slots":10,
      "source_locked_by_sha":True,"trigger":"MU_2MIN_SIGN_OPPOSITE_MEXC_2MIN_SIGN",
      "outcome_type":"MEXC_STANDARD_FUTURES_INDEX_OPEN_10M_PROXY",
      "actual_event_payouts_known":False,"executed_event_entry_price_known":False,
      "collector_asof_known":False,"NVIDIA_tested":False,"SPCX_tested":False,
      "MLIUSDT_alias_used":False,"protected_sep_opened":False,"live_orders":0}
    try:
        mu=data(True);idx=data(False)
        by_day={}
        pools={side:[] for side in SIDES}
        detail=[]
        for day in parent.DAYS:
            counts={"scheduled":0,"missing":0,"flat_feature":0,"agree":0,"disagree":0}
            for t in times(day):
                counts["scheduled"]+=1
                required_mu=(t-300,t-180)
                required_ix=(t-300,t-180,t,t+600)
                if any(z not in mu for z in required_mu) or any(z not in idx for z in required_ix):
                    counts["missing"]+=1;continue
                s_mu=direction(mu[t-180],mu[t-300])
                s_ix=direction(idx[t-180],idx[t-300])
                if s_mu==0 or s_ix==0:
                    counts["flat_feature"]+=1;continue
                if s_mu==s_ix:
                    counts["agree"]+=1;continue
                counts["disagree"]+=1
                delta=idx[t+600]-idx[t]
                sides={"MU_SIGN":s_mu,"ALWAYS_UP":1,"ALWAYS_DOWN":-1,"MEXC_MOMENTUM":s_ix}
                per={label:result(sign,delta) for label,sign in sides.items()}
                for label,outcome in per.items():pools[label].append(outcome)
                detail.append({"decision_utc":dt.datetime.fromtimestamp(t,UTC).isoformat(),
                   "mu_sign":s_mu,"mexc_sign":s_ix,"results":per})
            by_day[str(day)]=counts
        report.update({"source_gate":"SHA_MATCH_SOURCE_PASS","by_day":by_day,
           "summary":{label:score(seq) for label,seq in pools.items()},
           "events":detail,"verdict":"DESCRIPTIVE_HISTORY_ONLY_NO_INDEPENDENT_EDGE"})
    except Exception as err:
        report["source_gate"]="SOURCE_BLOCKED"
        report["reason"]=type(err).__name__+":"+str(err)[:180]
        report["verdict"]="NO_OUTCOMES"
        raise
    finally:
        (OUT/"receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True),flush=True)
if __name__=="__main__":main()
