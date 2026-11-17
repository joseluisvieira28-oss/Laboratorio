#!/usr/bin/env python3
"""DIGUI-011 strictly time-directed 1h/4h structure research, NO ORDERS.

Source: Binance Vision BTC ETH SOL perpetual monthly 1h; historical settled Binance
funding from CARRY-001. POC is typical-price/quote-volume *proxy*, NOT true trades
volume profile. OHLCV != executable bid/ask. No trade-related host actions exist.
"""
from pathlib import Path
from collections import defaultdict,Counter
from bisect import bisect_right
import csv,hashlib,json,datetime as dt,random,math,time
import numpy as np
import pandas as pd

ROOT=Path("digui011-evidence")
FUNDING=Path("carry001-evidence/extended_funding_events.csv")
PRICE=ROOT/"ohlcv_1h.csv"
FUNDING_SHA="a7fdd25b7155ca1a81db7aba0d9e6d7d4ee43c070d4cc15de98114a80c935ce0"
COINS=("BTC","ETH","SOL")
FRAMES=(1,4)
STRATS=("breakout","false_break","poc_proxy","sma_cross")
SLIPS=(.0002,.0005)
FEE=.0005
MAX_HOLD=8
DATE_START=dt.datetime(2023,6,1,tzinfo=dt.timezone.utc)
TRAIN_END=dt.datetime(2025,1,1,tzinfo=dt.timezone.utc)
VAL_END=dt.datetime(2025,7,1,tzinfo=dt.timezone.utc)
TEST_END=dt.datetime(2026,11,1,tzinfo=dt.timezone.utc)
CUTS=[int(x.timestamp()*1000) for x in (DATE_START,TRAIN_END,VAL_END,TEST_END)]
def phase(ts):
    if CUTS[0]<=ts<CUTS[1]:return "train"
    if CUTS[1]<=ts<CUTS[2]:return "validation"
    if CUTS[2]<=ts<CUTS[3]:return "test"
    return "out_of_range"

def read_funding():
    if hashlib.sha256(FUNDING.read_bytes()).hexdigest()!=FUNDING_SHA:
        raise ValueError("HISTORICAL FUNDING SOURCE DRIFT")
    events=defaultdict(list)
    with FUNDING.open() as f:
        for r in csv.DictReader(f):
            if r["venue"]=="Binance" and r["coin"] in COINS:
                events[r["coin"]].append((int(r["timestamp_ms"]),float(r["rate"])))
    out={}
    for coin,v in events.items():
        v.sort(); t=np.array([x[0] for x in v],dtype=np.int64)
        rates=np.array([x[1] for x in v])
        pref=np.r_[0.,np.cumsum(rates)]
        out[coin]=(t,pref)
    return out

def source():
    m=json.loads((ROOT/"source_manifest.json").read_text())
    if m["blocked"]:raise ValueError("SOURCE BLOCKED: missing monthly file")
    if hashlib.sha256(PRICE.read_bytes()).hexdigest()!=m["csv_sha256"]:
        raise ValueError("OHLCV SOURCE DRIFT")
    df=pd.read_csv(PRICE)
    if df.duplicated(["coin","time_ms"]).any():raise ValueError("duplicate OHLCV")
    if not set(COINS).issubset(df.coin.unique()):raise ValueError("missing asset")
    return df,m

def bars_for_coin(raw, frame):
    raw=raw.sort_values("time_ms").reset_index(drop=True).copy()
    unit=3_600_000
    if frame==1:
        b=raw[["time_ms","open","high","low","close","volume","quote_volume"]].copy()
    else:
        key=raw.time_ms//(unit*4)
        grp=raw.groupby(key,sort=True)
        b=grp.agg(time_ms=("time_ms","first"),open=("open","first"),
            high=("high","max"),low=("low","min"),close=("close","last"),
            volume=("volume","sum"),quote_volume=("quote_volume","sum"),
            count=("time_ms","size"),last=("time_ms","last")).reset_index(drop=True)
        b=b[(b["count"]==4)&(b["time_ms"]%(unit*4)==0)&
            ((b["last"]-b["time_ms"])==unit*3)].drop(columns=["count","last"])
        b=b.reset_index(drop=True)
    b["frame"]=frame
    return b

def features(b,look):
    b=b.copy()
    prev=b["close"].shift(1)
    true_range=pd.concat([b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"]=true_range.rolling(14,min_periods=14).mean().shift(1)
    b["prev_high"]=b.high.rolling(look,min_periods=look).max().shift(1)
    b["prev_low"]=b.low.rolling(look,min_periods=look).min().shift(1)
    b["vmed"]=b.volume.rolling(20,min_periods=20).median().shift(1)
    b["sma"]=b.close.rolling(20,min_periods=20).mean().shift(1)
    b["sma_prev"]=b.sma.shift(1)
    poc=np.full(len(b),np.nan)
    prices=((b.high+b.low+b.close)/3).to_numpy(float)
    weight=b.quote_volume.to_numpy(float)
    for i in range(look,len(b)):
        p=prices[i-look:i]; w=weight[i-look:i]
        lo=float(np.min(p));hi=float(np.max(p))
        if not(np.isfinite(lo) and np.isfinite(hi) and np.isfinite(w).all()) or hi<=lo:continue
        hist,edges=np.histogram(p,bins=20,range=(lo,hi),weights=w)
        if hist.sum()>0:
            j=int(np.argmax(hist));poc[i]=(edges[j]+edges[j+1])/2
    b["poc_proxy"]=poc
    return b

def signals(b):
    n=len(b);s={name:np.zeros(n,dtype=np.int8) for name in STRATS}
    high=b.high.to_numpy(float);low=b.low.to_numpy(float)
    c=b.close.to_numpy(float);v=b.volume.to_numpy(float)
    rh=b.prev_high.to_numpy(float);rl=b.prev_low.to_numpy(float)
    atr=b.atr.to_numpy(float);vm=b.vmed.to_numpy(float)
    poc=b.poc_proxy.to_numpy(float)
    sma=b.sma.to_numpy(float);prevsma=b.sma_prev.to_numpy(float)
    times=b.time_ms.to_numpy(np.int64)
    frame=int(b.frame.iloc[0]);scale=frame*3_600_000
    for i in range(2,n-1):
        if times[i]-times[i-1]!=scale:continue
        if not(np.isfinite(atr[i]) and atr[i]>0 and np.isfinite(rh[i]) and np.isfinite(rl[i])
               and rh[i]>rl[i] and np.isfinite(vm[i])):continue
        above=c[i]>rh[i]+.15*atr[i] and c[i-1]<=rh[i] and v[i]>=1.1*vm[i]
        below=c[i]<rl[i]-.15*atr[i] and c[i-1]>=rl[i] and v[i]>=1.1*vm[i]
        if above!=below:s["breakout"][i]=1 if above else -1
        sh=high[i]>=rh[i]+.10*atr[i] and c[i]<rh[i]-.05*atr[i] and c[i]>rl[i]
        sl=low[i]<=rl[i]-.10*atr[i] and c[i]>rl[i]+.05*atr[i] and c[i]<rh[i]
        if sh!=sl:s["false_break"][i]=-1 if sh else 1
        if np.isfinite(poc[i]):
            ph=c[i-1]>poc[i]+.30*atr[i] and low[i]<=poc[i] and c[i]>poc[i]+.10*atr[i]
            pl=c[i-1]<poc[i]-.30*atr[i] and high[i]>=poc[i] and c[i]<poc[i]-.10*atr[i]
            if ph!=pl:s["poc_proxy"][i]=1 if ph else -1
        if np.isfinite(sma[i]) and np.isfinite(prevsma[i]):
            up=c[i]>sma[i] and c[i-1]<=prevsma[i]
            down=c[i]<sma[i] and c[i-1]>=prevsma[i]
            if up!=down:s["sma_cross"][i]=1 if up else -1
    return s

def funding_for(funding,coin,t0,t1,direction):
    t,pref=funding[coin]
    # Only settlements strictly after market entry and <= exit.
    j=bisect_right(t,int(t0));k=bisect_right(t,int(t1))
    return float(-direction*(pref[k]-pref[j])),int(k-j)

def simulate(b,sig,coin,frame,slip,funding,random_direction=False,seed=11):
    x=b.reset_index(drop=True);n=len(x)
    t=x.time_ms.to_numpy(np.int64);o=x.open.to_numpy(float)
    hi=x.high.to_numpy(float);lo=x.low.to_numpy(float);cl=x.close.to_numpy(float)
    atr=x.atr.to_numpy(float)
    step=frame*3_600_000
    rng=random.Random(seed)
    events=[];i=0;blocked=Counter()
    while i<n-1:
        side=int(sig[i])
        if side==0 or not(np.isfinite(atr[i]) and atr[i]>0):
            i+=1;continue
        if random_direction:side=rng.choice((-1,1))
        entered=i+1
        if t[entered]-t[i]!=step:
            blocked["no_consecutive_next_open"]+=1;i+=1;continue
        entry=float(o[entered])*(1+side*slip)
        stop=entry-side*float(atr[i])
        target=entry+side*1.5*float(atr[i])
        exit_at=None;raw_exit=None;reason="";invalid=False
        for j in range(entered,min(n,entered+MAX_HOLD)):
            if j>entered and t[j]-t[j-1]!=step:
                blocked["gap_censored"]+=1;invalid=True;break
            # Stop checked FIRST when price interval hits both stop+target.
            if side==1 and lo[j]<=stop:
                raw_exit=min(stop,float(o[j]));reason="stop";exit_at=j
            elif side==-1 and hi[j]>=stop:
                raw_exit=max(stop,float(o[j]));reason="stop";exit_at=j
            elif side==1 and hi[j]>=target:
                raw_exit=target;reason="target";exit_at=j
            elif side==-1 and lo[j]<=target:
                raw_exit=target;reason="target";exit_at=j
            elif j==min(n,entered+MAX_HOLD)-1:
                raw_exit=float(cl[j]);reason="timeout";exit_at=j
            if exit_at is not None:break
        if invalid or exit_at is None:
            i=entered if invalid else i+1
            continue
        exitpx=float(raw_exit)*(1-side*slip)
        if exitpx<=0:
            blocked["invalid_exit"]+=1;i+=1;continue
        # Approximate funding per initial unit notional, not mark-adjusted at each settlement
        fund,ns=funding_for(funding,coin,t[entered],t[exit_at]+frame*3_600_000-1,side)
        gross=side*(exitpx/entry-1)
        fees=FEE*(1+exitpx/entry)
        net=gross-fees+fund
        entrytime=int(t[entered]);exittime=int(t[exit_at])
        p=phase(entrytime)
        if p!=phase(exittime):
            blocked["crosses_chronological_boundary"]+=1
        elif p!="out_of_range":
            events.append({"coin":coin,"frame_h":frame,"entry_ms":entrytime,"exit_ms":exittime,
              "phase":p,"side":side,"reason":reason,"slippage_bps":int(round(slip*10000)),
              "entry_price":entry,"exit_price":exitpx,
              "gross_return":gross,"fee_return":fees,"funding_return":fund,"funding_events":ns,
              "net_return":net,"holding_bars":exit_at-entered+1,"signal_ms":int(t[i])})
        i=exit_at+1
    return events,dict(blocked)

def metrics(rows):
    n=len(rows)
    if n==0:return {"n":0}
    y=np.array([x["net_return"] for x in rows])
    times=np.array([x["entry_ms"] for x in rows],dtype=np.int64)
    labels=pd.to_datetime(times,unit="ms",utc=True).strftime("%Y-%m")
    months=sorted(set(labels))
    month_vals={m:float(sum(y[labels==m])) for m in months}
    equity=np.r_[0.,np.cumsum(y)]
    dd=np.min(equity-np.maximum.accumulate(equity))
    return {"n":n,"active_months":len(months),"wins_pct":round(100*float((y>0).mean()),3),
      "mean_net_bps":round(float(np.mean(y))*10000,4),
      "median_net_bps":round(float(np.median(y))*10000,4),
      "sum_net_bps_per_1_fixed_notional":round(float(y.sum())*10000,3),
      "sum_usd_at_1000_fixed_notional":round(float(y.sum()*1000),3),
      "worst_trade_bps":round(float(min(y))*10000,3),
      "best_trade_bps":round(float(max(y))*10000,3),
      "max_closed_trade_dd_bps":round(float(dd)*10000,3),
      "positive_active_month_pct":round(100*sum(v>0 for v in month_vals.values())/len(months),2),
      "last_3_months_net_bps":round(sum(month_vals.get(m,0) for m in sorted(months)[-3:])*10000,3),
      "funding_sum_bps":round(float(sum(x["funding_return"] for x in rows))*10000,3),
      "stop_pct":round(100*sum(x["reason"]=="stop" for x in rows)/n,2),
      "top5_trade_contrib_bps":round(sum(sorted(y,reverse=True)[:min(n,5)])*10000,3)}
def run():
    t0=time.monotonic()
    raw,manifest=source()
    funding=read_funding()
    result={"study":"DIGUI-011","protocol_frozen_before_data":True,
      "source":{"ohlcv_sha256":manifest["csv_sha256"],"files":len(manifest["raw"]),
         "funding_sha256":FUNDING_SHA,"bars":manifest["num_bars"],
         "source_gaps":{coin:sum(x["internal_or_previous_gaps"] for x in manifest["raw"] if x["coin"]==coin) for coin in COINS}},
      "timing":"signal at close, next bar open, stop-first, no bridge missing hours",
      "poc_note":"typical-price weighted volume-bin proxy, NOT genuine traded volume-at-price POC",
      "splits":{"train":"2023-06..2024-12","validation":"2025-01..2025-06","test":"2025-07..2026-10"},
      "fixed_cost":{"taker_fee_side":FEE,"slippage_each_side":SLIPS,
        "funding":"official settled Binance rate, fixed-entry-notional approximation"},
      "test_report":{},"all_models":{},"blocked":{},
      "live_trading_gate":"NO-GO: candle prices not executable fills; no independent prospective economic proof",
      "orders":0}
    alltrades=[];counts=Counter()
    for coin in COINS:
        data=raw.loc[raw.coin==coin].copy()
        for frame in FRAMES:
            bars=features(bars_for_coin(data,frame),72 if frame==1 else 42)
            signal=signals(bars)
            print("SIGNALS",coin,frame,{k:int(np.count_nonzero(v)) for k,v in signal.items()},flush=True)
            for strat in STRATS:
                for slip in SLIPS:
                    entries,blocked=simulate(bars,signal[strat],coin,frame,slip,funding)
                    alltrades.extend([{**e,"strategy":strat} for e in entries])
                    result["blocked"][f"{coin}_{frame}h_{strat}_{int(slip*1e4)}bps"]=blocked
                    key=f"{coin}_{frame}h_{strat}_{int(slip*1e4)}bps"
                    result["all_models"][key]={p:metrics([r for r in entries if r["phase"]==p])
                        for p in ("train","validation","test")}
                    if slip==SLIPS[0]:
                        # Seeded direction-randomization negative control at same signal bars
                        rand,rb=simulate(bars,signal[strat],coin,frame,slip,funding,
                                         random_direction=True,seed=20261117)
                        result["all_models"][key]["random_direction_control_test"]=metrics(
                            [r for r in rand if r["phase"]=="test"])
                    m=result["all_models"][key]["test"]
                    counts[strat]+=m["n"]
                    print("BACKTEST",key,json.dumps({"test":m,"validation":result["all_models"][key]["validation"]},ensure_ascii=False),flush=True)
    # Explicit never-tradable gate, even in event of historical positives
    for key,v in result["all_models"].items():
        if key.endswith("_2bps"):
            test=v["test"];val=v["validation"]
            candidate=test.get("n",0)>=100 and test.get("active_months",0)>=9 and (
                test.get("mean_net_bps",0)>0 and val.get("mean_net_bps",0)>0)
            stresskey=key.replace("_2bps","_5bps")
            stress=result["all_models"].get(stresskey,{}).get("test",{})
            candidate=candidate and stress.get("mean_net_bps",0)>0
            result["test_report"][key]={"descriptive_candidate":bool(candidate),
                 "test":test,"validation":val,"slippage_stress_test":stress,
                 "NO_LIVE_GO":True,
                 "narrative":"Multiple-testing family; does not constitute independent positive replication"}
    result["sample_caution"]="All six asset-frame combinations and four families are prespecified comparisons; 1-hour candles cannot validate actual order fills, margin liquidations or intrabar price path."
    rawjson=json.dumps(result,indent=2,ensure_ascii=False,default=str).encode()
    (ROOT/"backtest.json").write_bytes(rawjson)
    (ROOT/"backtest.sha256").write_text(hashlib.sha256(rawjson).hexdigest()+"  backtest.json\n")
    with (ROOT/"trades.csv").open("w",newline="") as fh:
        if alltrades:
            w=csv.DictWriter(fh,fieldnames=list(alltrades[0].keys()))
            w.writeheader();w.writerows(alltrades)
    print("DIGUI011_FINAL",json.dumps({"source":result["source"],"results":result["test_report"],
      "trades":len(alltrades),"elapsed_s":round(time.monotonic()-t0,2),"economic_go":False},ensure_ascii=False)[:24000],flush=True)
if __name__=="__main__":run()
