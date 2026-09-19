#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, re, sys
from pathlib import Path
import numpy as np
import pandas as pd

P=Path(sys.argv[1] if len(sys.argv)>1 else "btc_option_data_toshare.parquet")
RATE=0.0003
CAP=0.125
SEED=230919
BOOT=10000
BLOCK=5

def parse_inst(s):
    return s.astype(str).str.extract(r"^[^-]+-(\d{1,2}[A-Z]{3}\d{2})-([0-9]+(?:\.[0-9]+)?)-([CP])$",expand=True)

def fee(px):
    return min(RATE,CAP*float(px))

def pf(x):
    pos=sum(v for v in x if v>0); neg=-sum(v for v in x if v<0)
    if neg==0: return float("inf") if pos>0 else 0.0
    return pos/neg

def streak(x):
    m=c=0
    for v in x:
        if v<0: c+=1; m=max(m,c)
        else: c=0
    return m

def circ_boot_mean(x):
    x=np.asarray(x,float); n=len(x)
    if n==0:return [None,None]
    rng=np.random.default_rng(SEED)
    out=np.empty(BOOT)
    nb=math.ceil(n/BLOCK)
    for i in range(BOOT):
        vals=[]
        starts=rng.integers(0,n,size=nb)
        for s in starts:
            vals.extend(x[(s+np.arange(BLOCK))%n].tolist())
        out[i]=np.mean(vals[:n])
    return [float(np.quantile(out,.025)),float(np.quantile(out,.975))]

def main():
    raw=P.read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    expected="6ed2162288d177d3c3a5443456c3fb78ed2c175249f0a0ff1665a5dd9c89800b"
    if sha!=expected:
        raise SystemExit(f"source hash mismatch {sha}")

    df=pd.read_parquet(P,columns=["snapshot_time","instrument_name","bid_price","ask_price","underlying_price","expiry_date"])
    df["ts"]=pd.to_datetime(df["snapshot_time"],utc=True,errors="coerce")
    df["expiry"]=pd.to_datetime(df["expiry_date"],utc=True,errors="coerce")
    p=parse_inst(df["instrument_name"])
    df["strike"]=pd.to_numeric(p[1],errors="coerce")
    df["right"]=p[2]
    for c in ["bid_price","ask_price","underlying_price"]:
        df[c]=pd.to_numeric(df[c],errors="coerce")

    df=df[df["ts"].notna() & df["expiry"].notna() & df["strike"].notna() & df["right"].isin(["C","P"])]
    df=df[(df["bid_price"]>0)&(df["ask_price"]>0)&(df["ask_price"]>=df["bid_price"])&(df["underlying_price"]>0)]
    df["dte"]=(df["expiry"]-df["ts"]).dt.total_seconds()/86400.0
    df=df[(df["dte"]>=25)&(df["dte"]<=35)&(df["ts"].dt.hour==8)].copy()
    df["date"]=df["ts"].dt.date
    df["hour0"]=df["ts"].dt.floor("h")
    # Keep the row closest to 08:00 for each instrument/day.
    df["secs"]=(df["ts"]-df["hour0"]).dt.total_seconds().abs()
    df=df.sort_values(["date","instrument_name","secs"]).drop_duplicates(["date","instrument_name"],keep="first")

    bydate={d:g.copy() for d,g in df.groupby("date")}
    dates=sorted(bydate)
    trades=[]
    for d in dates:
        g=bydate[d]
        # entry spot fixed from same-hour source only
        spot=float(g["underlying_price"].median())
        if not np.isfinite(spot) or spot<=0: continue
        # eligible expiry chosen using median DTE at each expiry
        exps=g.groupby("expiry",as_index=False)["dte"].median()
        exps["dist"]=(exps["dte"]-30.0).abs()
        exps=exps.sort_values(["dist","dte","expiry"])
        if exps.empty: continue
        expiry=exps.iloc[0]["expiry"]
        ge=g[g["expiry"]==expiry]
        # strikes with both C and P
        rights=ge.groupby("strike")["right"].nunique()
        strikes=rights[rights>=2].index.to_numpy(dtype=float)
        if len(strikes)==0: continue
        strike=float(sorted(strikes,key=lambda k:(abs(math.log(k/spot)),k))[0])
        pair=ge[ge["strike"]==strike]
        c=pair[pair["right"]=="C"]; p=pair[pair["right"]=="P"]
        if c.empty or p.empty: continue
        c=c.iloc[0]; p=p.iloc[0]

        d1=(pd.Timestamp(d)+pd.Timedelta(days=1)).date()
        gx=bydate.get(d1)
        if gx is None: continue
        cx=gx[gx["instrument_name"]==c["instrument_name"]]
        px=gx[gx["instrument_name"]==p["instrument_name"]]
        if cx.empty or px.empty: continue
        cx=cx.iloc[0]; px=px.iloc[0]

        entry=float(c["bid_price"]+p["bid_price"])
        exitv=float(cx["ask_price"]+px["ask_price"])
        if entry<=0: continue
        fees=fee(c["bid_price"])+fee(p["bid_price"])+fee(cx["ask_price"])+fee(px["ask_price"])
        gross=entry-exitv
        net=gross-fees
        trades.append({
          "date":str(d),"exit_date":str(d1),
          "expiry":str(pd.Timestamp(expiry).date()),"strike":strike,
          "entry_credit_btc":entry,"exit_debit_btc":exitv,
          "fees_btc":fees,"gross_btc":gross,"net_btc":net,
          "net_premium_return":net/entry
        })

    n=len(trades)
    rets=[t["net_premium_return"] for t in trades]
    cash=[t["net_btc"] for t in trades]
    if n:
        tmp=pd.DataFrame(trades)
        tmp["month"]=pd.to_datetime(tmp["date"]).dt.to_period("M").astype(str)
        monthly=tmp.groupby("month")["net_premium_return"].mean().to_dict()
        ci=circ_boot_mean(rets)
        stats={
          "N":n,
          "mean_net_premium_return":float(np.mean(rets)),
          "median_net_premium_return":float(np.median(rets)),
          "positive_fraction":float(np.mean(np.asarray(rets)>0)),
          "profit_factor_net_cash":float(pf(cash)),
          "bootstrap_95_ci_mean":ci,
          "monthly_means":{k:float(v) for k,v in monthly.items()},
          "positive_month_count":int(sum(v>0 for v in monthly.values())),
          "max_losing_streak":int(streak(cash))
        }
    else:
        stats={"N":0}

    gates={
      "N_gte_40":n>=40,
      "mean_gt_0":n>0 and stats["mean_net_premium_return"]>0,
      "median_gt_0":n>0 and stats["median_net_premium_return"]>0,
      "profit_factor_gt_1":n>0 and stats["profit_factor_net_cash"]>1,
      "bootstrap_lower_gt_0":n>0 and stats["bootstrap_95_ci_mean"][0]>0,
      "positive_months_gte_3":n>0 and stats["positive_month_count"]>=3
    }
    if n<40:
        verdict="EXPLORATORY_INSUFFICIENT_SAMPLE"
    elif all(gates.values()):
        verdict="EXPLORATORY_SIGNAL_PRESENT_NONPROMOTIONAL"
    elif (stats["mean_net_premium_return"]<=0 and stats["median_net_premium_return"]<=0 and stats["profit_factor_net_cash"]<=1):
        verdict="EXPLORATORY_NO_SIGNAL"
    else:
        verdict="EXPLORATORY_MIXED_NONPROMOTIONAL"

    out={
      "lab_id":"BTC-OPTIONS-VRP-CRYPTA-EXP-001",
      "mve_id":"CRYPTA-ATM30-24H-QUOTE-CARRY-001",
      "verdict":verdict,
      "source_sha256":sha,
      "stats":stats,
      "gates":gates,
      "trade_count":n,
      "capacity_proven":False,
      "bid_ask_sizes_available":False,
      "promotion_authorized":False,
      "old_90_day_gate_rewritten":False,
      "protected_2025_2026_opened":False
    }
    Path("crypta_quote_carry_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    pd.DataFrame(trades).to_csv("crypta_quote_carry_trades_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
