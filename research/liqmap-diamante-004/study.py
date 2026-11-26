#!/usr/bin/env python3
"""LIQMAP004: falsify continuation/reversal after ACTUAL Hyperliquid liquidations.
Public historical Parquet. Not orders. Not Neuron. No wallet rows exported.
"""
import collections,datetime as dt,hashlib,io,json,math,pathlib,random,statistics,urllib.request
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"study_results"
MONTHS=("2026-07","2026-08","2026-09","2026-10")
COINS=("BTC-PERP","ETH-PERP")
T0=pd.Timestamp("2026-07-01T00:00:00Z")
T1=pd.Timestamp("2026-11-01T00:00:00Z")
HOURS=336
HORIZON=4
FEE_BPS=(10,35,80,100)
SLIP_BPS=5
SOURCE={
 "events":"ironflow/hyperliquid-liquidations",
 "candles":"ironflow/hyperliquid-candles-1h"
}
def utcnow():return dt.datetime.now(dt.timezone.utc)
def download(kind,month,meta=None):
    repo=SOURCE[kind]
    part="data/events" if kind=="events" else "data"
    path=part+"/"+month+".parquet"
    url="https://huggingface.co/datasets/"+repo+"/resolve/main/"+path+"?download=true"
    begin=utcnow().isoformat()
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-LIQMAP004-ReadOnly/1.0"})
    with urllib.request.urlopen(req,timeout=120) as f:
        raw=f.read(85000000)
    end=utcnow().isoformat()
    if len(raw)>=85000000:raise RuntimeError("SOURCE_BLOCKED file too large "+path)
    digest=hashlib.sha256(raw).hexdigest()
    rec={"dataset":repo,"path":path,"url":url,"timestamp_start_utc":begin,
         "timestamp_end_utc":end,"bytes":len(raw),"sha256":digest}
    if meta:
        target=meta.get("oid")
        if target and target!=digest:raise RuntimeError("SOURCE_BLOCKED LFS hash mismatch "+path)
        if meta.get("bytes") and int(meta["bytes"])!=len(raw):
            raise RuntimeError("SOURCE_BLOCKED file size mismatch "+path)
    table=pq.read_table(io.BytesIO(raw))
    return table,rec

def load_schema_manifest():
    loc=HERE/"results"/"SOURCE_INVENTORY.json"
    if not loc.exists():raise RuntimeError("SOURCE_BLOCKED prerequisite inventory missing")
    inventory=json.loads(loc.read_text())
    if inventory.get("status")!="SCHEMA_PASS":raise RuntimeError("SOURCE_BLOCKED prerequisite failed")
    return inventory

def read_source():
    inventory=load_schema_manifest()
    receipts=[]
    frames={"events":[],"candles":[]}
    for kind in ("events","candles"):
        for month in MONTHS:
            meta=inventory["datasets"][kind]["files"][month]
            table,rec=download(kind,month,meta)
            needed=["timestamp","market"]
            needed+=["position_side","notional_usd","wallet","tx_hash"] if kind=="events" else ["open","high","low","close"]
            if not set(needed).issubset(table.schema.names):
                raise RuntimeError("SOURCE_BLOCKED unexpected schema "+kind+" "+month+" "+str(table.schema.names))
            # Only market-specific aggregate fields survive; raw wallet/tx_hash never in output.
            frames[kind].append(table.select(needed).to_pandas())
            receipts.append(rec)
            print("MONTH_SOURCE_PASS",kind,month,"rows",table.num_rows,"sha256",rec["sha256"],flush=True)
    return pd.concat(frames["events"],ignore_index=True),pd.concat(frames["candles"],ignore_index=True),receipts

def prepare(events,candles):
    events=events[events.market.isin(COINS)].copy()
    events["timestamp"]=pd.to_datetime(events["timestamp"],utc=True)
    events=events[(events.timestamp>=T0)&(events.timestamp<T1)]
    events["position_side"]=events["position_side"].str.lower()
    if not events["position_side"].isin(["long","short"]).all():
        raise RuntimeError("SOURCE_BLOCKED side ambiguous: "+repr(events["position_side"].value_counts().to_dict()))
    events["notional_usd"]=pd.to_numeric(events["notional_usd"],errors="coerce")
    if (not np.isfinite(events.notional_usd.to_numpy(dtype=float)).all()
        or (events.notional_usd<=0).any()):
        raise RuntimeError("SOURCE_BLOCKED invalid USD liquidation notional")
    duplicates=events.duplicated(subset=["market","timestamp","wallet","tx_hash","position_side","notional_usd"])
    if duplicates.any():
        # Events are one position. Identical duplicate rows are a data fault, not
        # permission to double-count forced liquidation.
        raise RuntimeError("SOURCE_BLOCKED duplicated original liquidated position rows "+str(int(duplicates.sum())))
    events["hour"]=events.timestamp.dt.floor("h")
    counts=events.groupby(["market","hour","position_side"],observed=True).agg(
         usd=("notional_usd","sum"),count=("notional_usd","size")).reset_index()
    candles=candles[candles.market.isin(COINS)].copy()
    candles["timestamp"]=pd.to_datetime(candles["timestamp"],utc=True)
    candles=candles[(candles.timestamp>=T0)&(candles.timestamp<T1)]
    for field in ("open","high","low","close"):
        candles[field]=pd.to_numeric(candles[field],errors="coerce")
    if candles.duplicated(subset=["market","timestamp"]).any():
        raise RuntimeError("PRICE_SOURCE_BLOCKED duplicate market/hour")
    if not np.isfinite(candles[["open","high","low","close"]].to_numpy(dtype=float)).all():
        raise RuntimeError("PRICE_SOURCE_BLOCKED nonfinite prices")
    if ((candles[["open","high","low","close"]]<=0).any().any() or
        (candles.low>candles[["open","close"]].min(axis=1)).any() or
        (candles.high<candles[["open","close"]].max(axis=1)).any()):
        raise RuntimeError("PRICE_SOURCE_BLOCKED invalid OHLC")
    fullhours=pd.date_range(T0,T1-pd.Timedelta(hours=1),freq="h")
    panel={}
    for coin in COINS:
        sub=candles[candles.market==coin].set_index("timestamp").reindex(fullhours)
        if len(sub)!=len(fullhours) or sub.close.isna().any():
            raise RuntimeError("PRICE_SOURCE_BLOCKED missing "+coin+" "+str(int(sub.close.isna().sum()))+" hours")
        raw=counts[counts.market==coin]
        table=raw.pivot(index="hour",columns="position_side",values=["usd","count"])
        table=table.reindex(fullhours).fillna(0)
        def get(field,side):
            return table[(field,side)].to_numpy(dtype=float) if (field,side) in table.columns else np.zeros(len(fullhours))
        panel[coin]={"time":fullhours,"open":sub.open.to_numpy(dtype=float),
           "close":sub.close.to_numpy(dtype=float),"long":get("usd","long"),"short":get("usd","short"),
           "nlong":get("count","long"),"nshort":get("count","short"),
           "raw_position_events":int((events.market==coin).sum())}
    return panel

def quantile95(arr):
    if len(arr)!=HOURS:raise ValueError("lookback must contain exactly 336 past hours")
    return float(sorted(float(v) for v in arr)[math.ceil(.95*len(arr))-1])

def mode_at(data,i):
    """A and B have inverse directions. ONLY prices/cascades <= closed hour i."""
    n=int(data["nlong"][i]+data["nshort"][i])
    total=float(data["long"][i]+data["short"][i])
    threshold=quantile95(data["long"][i-HOURS:i]+data["short"][i-HOURS:i])
    if total<=0 or total<threshold or n<3:return None,threshold
    dominance=max(data["long"][i],data["short"][i])/total
    if dominance<.65:return "NEUTRAL",threshold
    forced=-1 if data["long"][i]>=data["short"][i] else 1
    return forced,threshold

def ann_vol24(close,i):
    if i<25:return None
    x=np.log(close[i-24:i+1])
    return float(np.std(np.diff(x),ddof=1))

def placebo(data,i,direction):
    """No future: deterministic prior same weekday+hour and past known volatility regime."""
    times=data["time"];close=data["close"]
    vi=ann_vol24(close,i)
    if vi is None:return {"status":"CONTROL_BLOCKED"}
    lagvol=[ann_vol24(close,j) for j in range(i-HOURS,i) if j>=25]
    median=float(np.median(lagvol))
    high=vi>=median
    weekday=times[i].weekday();hour=times[i].hour
    choices=[]
    for j in range(i-HOURS,max(i-4,0)):
        if j<HOURS or times[j].weekday()!=weekday or times[j].hour!=hour:continue
        if ann_vol24(close,j) is None or (ann_vol24(close,j)>=median)!=high:continue
        tag,th=mode_at(data,j)
        if tag is None:
            choices.append(j)
    if not choices:return {"status":"CONTROL_BLOCKED"}
    j=choices[-1]
    gain=direction*(close[j+4]/data["open"][j+1]-1)
    return {"status":"MATCHED_PAST_CONTROL","past_hour_utc":str(times[j]),
            "same_forced_direction_gross_bps":gain*10000}

def event_return(close_exit,open_entry,sign,bps):
    return 10000*sign*(close_exit/open_entry-1)-2*(bps+SLIP_BPS)

def study_one(data,coin):
    entries=[];last=-1000;potential=0;neutral=0;overlap=0
    for i in range(HOURS,len(data["close"])-HORIZON):
        sign,threshold=mode_at(data,i)
        if sign is None:continue
        potential+=1
        if sign=="NEUTRAL":neutral+=1;continue
        if i<=last+HORIZON-1:
            overlap+=1;continue
        last=i
        entry=float(data["open"][i+1]);exit=float(data["close"][i+HORIZON])
        momo=1 if data["close"][i]>data["close"][i-4] else -1
        forced=int(sign)
        ret=exit/entry-1
        control=placebo(data,i,forced)
        base={
           "time":data["time"][i].isoformat(),"month":data["time"][i].strftime("%Y-%m"),
           "hour_index":i,"notional_usd":round(float(data["long"][i]+data["short"][i]),2),
           "long_usd":round(float(data["long"][i]),2),"short_usd":round(float(data["short"][i]),2),
           "n_liquidated_positions":int(data["nlong"][i]+data["nshort"][i]),
           "past_336h_95pct_usd":round(threshold,2),
           "forced_direction":"UP" if forced==1 else "DOWN",
           "past_4h_momentum":"UP" if momo==1 else "DOWN",
           "future_4h_price_return_pct":round(100*ret,6),
           "controls":control,"hypothetical_net_bps":{}
        }
        for fee in FEE_BPS:
            base["hypothetical_net_bps"][str(fee)]={
              "continuation":round(event_return(exit,entry,forced,fee),6),
              "reversal":round(event_return(exit,entry,-forced,fee),6),
              "momentum4":round(event_return(exit,entry,momo,fee),6)}
        entries.append(base)
    return {"market":coin,"input_position_events":data["raw_position_events"],
      "total_candidates_before_dominance":potential,"neutral_skipped":neutral,
      "overlapping_candidates_skipped":overlap,
      "independent_event_count":len(entries),"events":entries}

def bootstrap_week(events,series,seed=4004,percentile=0.0125):
    weekly=collections.defaultdict(list)
    for row in events:
        d=dt.datetime.fromisoformat(row["time"]).date().isocalendar()
        weekly[(d.year,d.week)].append(float(series(row)))
    groups=list(weekly.values())
    if len(groups)<4:return {"low":None,"high":None,"n_weeks":len(groups)}
    rng=random.Random(seed);results=[]
    for _ in range(2000):
        samples=[groups[rng.randrange(len(groups))] for j in range(len(groups))]
        vals=[x for g in samples for x in g]
        results.append(statistics.mean(vals))
    results.sort()
    return {"low":round(results[int(2000*percentile)],6),
            "high":round(results[int(2000*(1-percentile))-1],6),
            "n_weeks":len(groups)}

def maxdraw(events,name):
    peak=1.;nav=1.;dd=0.
    for row in events:
        r=row["hypothetical_net_bps"]["80"][name]/10000
        nav*=1+r
        if nav<=0:return -100.
        peak=max(peak,nav);dd=min(dd,nav/peak-1)
    return 100*dd

def summarize(result):
    events=result["events"]
    models={}
    for model in ("continuation","reversal"):
        r=[e["hypothetical_net_bps"]["80"][model] for e in events]
        mom=[e["hypothetical_net_bps"]["80"]["momentum4"] for e in events]
        diff=[a-b for a,b in zip(r,mom)]
        month={}
        for m in MONTHS:
            vals=[e["hypothetical_net_bps"]["80"][model] for e in events if e["month"]==m]
            month[m]={"n":len(vals),"mean_net_bps":round(statistics.mean(vals),5) if vals else None}
        models[model]={
           "n_events":len(events),
           "mean_80bps_plus5_slip_per_side_net_bps":round(statistics.mean(r),5) if r else None,
           "mean_momentum4_same_events_bps":round(statistics.mean(mom),5) if mom else None,
           "mean_net_adv_vs_mom4_bps":round(statistics.mean(diff),5) if diff else None,
           "wins_net":sum(x>0 for x in r),"win_rate_net":sum(x>0 for x in r)/len(r) if r else None,
           "worst_net_bps":round(min(r),4) if r else None,
           "max_sequential_close_drawdown_pct":round(maxdraw(events,model),5),
           "weekly_bootstrap_mean_net_CI975":bootstrap_week(events,lambda e:e["hypothetical_net_bps"]["80"][model]),
           "weekly_bootstrap_excess_v_mom_CI975":bootstrap_week(events,lambda e:e["hypothetical_net_bps"]["80"][model]-e["hypothetical_net_bps"]["80"]["momentum4"]),
           "months":month,
           "months_positive":sum(x["mean_net_bps"] is not None and x["mean_net_bps"]>0 for x in month.values())}
    return models

def gate(report):
    data=report["results"]
    count=sum(x["independent_event_count"] for x in data.values())
    sufficiently_sampled=count>=100 and all(x["independent_event_count"]>=40 for x in data.values())
    details={}
    for model in ("continuation","reversal"):
        verdicts=[]
        for market,result in data.items():
            x=result["summary"][model]
            low=x["weekly_bootstrap_mean_net_CI975"]["low"]
            low_mom=x["weekly_bootstrap_excess_v_mom_CI975"]["low"]
            passed= (x["n_events"]>=40 and x["mean_80bps_plus5_slip_per_side_net_bps"] is not None
               and x["mean_80bps_plus5_slip_per_side_net_bps"]>0
               and low is not None and low>0 and low_mom is not None and low_mom>0
               and x["months_positive"]>=3 and x["max_sequential_close_drawdown_pct"]>-30)
            verdicts.append(passed)
        details[model]={"per_coin_all_gates_pass":verdicts,"candidate_shadow_only":all(verdicts)}
    status=("INCONCLUSIVE_SMALL_INDEPENDENT_SAMPLE" if not sufficiently_sampled
        else "HISTORICAL_SHADOW_CANDIDATE_ONLY" if any(x["candidate_shadow_only"] for x in details.values())
        else "ECONOMIC_NO_GO_AFTER_COSTS")
    return {"total_independent":count,"minimum_per_market":40,"sample_gate_pass":sufficiently_sampled,
            "models":details,"scientific_verdict":status,"real_trading":"NO_GO"}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={"study":"LIQMAP-DIAMANTE-004","cutoff":"2026-11-01T00:00:00Z",
       "begin":"2026-07-01T00:00:00Z","retrospective_not_true_out_of_sample":True,
       "not_Neuron":True,"no_trades":True,"funding_not_modelled":True,
       "sources":{"provider":"Ironflow (ironflow.sh)","datasets":SOURCE},"status":"SOURCE_BLOCKED"}
    try:
        raw_events,raw_candles,receipts=read_source()
        result["sources"]["receipts"]=receipts
        data=prepare(raw_events,raw_candles)
        result["source_counts"]={coin:{"complete_hourly_candles":len(x["close"]),
                         "liquidated_positions":x["raw_position_events"]} for coin,x in data.items()}
        for coin,x in data.items():
            if len(x["close"])!=2952:raise RuntimeError("SOURCE_BLOCKED insufficient hours")
        result["results"]={}
        for coin,x in data.items():
            r=study_one(x,coin)
            r["summary"]=summarize(r)
            result["results"][coin]=r
            print("LIQMAP004_EVALUATED",coin,"independent_events",r["independent_event_count"],
                  "mean net bps continuation/reversal",
                  [r["summary"][k]["mean_80bps_plus5_slip_per_side_net_bps"] for k in ("continuation","reversal")],flush=True)
        result["gate"]=gate(result)
        result["status"]=result["gate"]["scientific_verdict"]
    except Exception as e:
        result["status"]="SOURCE_OR_TECH_BLOCKED"
        result["error"]=type(e).__name__+": "+str(e)
    (OUT/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# LIQMAP004 — real BTC ETH liquidation cascades, economic verdict","",
       "Read-only actual executed position liquidations and same-exchange BTC/ETH hourly prices.",
       "All historical and RETROSPECTIVE. No margin, funding, trading, exact execution fills.",
       "No Neuron predictions involved. Source credits Ironflow (ironflow.sh).",
       "", "Status: **"+result["status"]+"**",""]
    if "results" in result:
        lines+=["| Market | Indep cascades | Continuation net after 80bps/side | Reversal net | MOM4 comparator |",
                "|---|---:|---:|---:|---:|"]
        for market,r in result["results"].items():
            a=r["summary"]["continuation"];b=r["summary"]["reversal"]
            lines.append("| "+market+" | "+str(r["independent_event_count"])+" | "
                 +str(a["mean_80bps_plus5_slip_per_side_net_bps"])+" bps | "
                 +str(b["mean_80bps_plus5_slip_per_side_net_bps"])+" bps | "
                 +str(a["mean_momentum4_same_events_bps"])+" bps |")
        lines+=["","## Gate","",str(result.get("gate")),
                "All individual event costs, bootstrap confidence intervals and four monthly regimes are in RESULT.json.",
                "Exclusion rules: failed source, neutral direction or four-hour overlap documented for every coin.",
                "Never substitute raw fills for positions, or use a cascade trigger timestamped after exit."]
    else:lines+=["","Source blocked: "+str(result.get("error"))]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
    print("LIQMAP004_VERDICT",result["status"],flush=True)
    if result["status"]=="SOURCE_OR_TECH_BLOCKED":raise RuntimeError(result.get("error"))
if __name__=="__main__":main()
