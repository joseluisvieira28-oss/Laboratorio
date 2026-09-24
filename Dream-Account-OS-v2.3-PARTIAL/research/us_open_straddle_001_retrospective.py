#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, random, re, statistics, sys
from pathlib import Path
import pandas as pd

P=Path(sys.argv[1] if len(sys.argv)>1 else "btc_option_data_toshare.parquet")
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/usopen_straddle_001_retrospective_receipt.json")
TZ="America/New_York"

HOLIDAYS={
"2024-01-15","2024-02-19","2024-03-29","2024-05-27","2024-06-19","2024-07-04"
}

ALIASES={
 "timestamp":["snapshot_time","timestamp","time","datetime","date_time","creation_timestamp"],
 "instrument":["instrument_name","symbol","instrument"],
 "expiry":["expiry_date","expiration","expiry","expiration_timestamp","expiry_timestamp"],
 "bid":["bid_price","best_bid_price","bid"],
 "ask":["ask_price","best_ask_price","ask"],
 "underlying":["underlying_price","index_price","spot_price","underlying"]
}

def norm(x):
    return re.sub(r"[^a-z0-9]+","_",str(x).strip().lower()).strip("_")

def find_col(cols,names):
    by={norm(c):c for c in cols}
    for n in names:
        if norm(n) in by:
            return by[norm(n)]
    return None

def parse_ts(s):
    return pd.to_datetime(s,utc=True,errors="coerce")

def parse_expiry(df,col,inst):
    if col:
        x=pd.to_datetime(df[col],utc=True,errors="coerce")
        if x.notna().any():
            return x
    tok=inst.astype(str).str.extract(r"(\d{1,2}[A-Z]{3}\d{2})",expand=False)
    return pd.to_datetime(tok,format="%d%b%y",utc=True,errors="coerce")

def pf(xs):
    pos=sum(x for x in xs if x>0)
    neg=-sum(x for x in xs if x<0)
    if neg==0:
        return None if pos==0 else "INF"
    return pos/neg

def pct(xs,p):
    ys=sorted(xs)
    if not ys: return None
    k=(len(ys)-1)*p
    f=math.floor(k); c=math.ceil(k)
    return ys[f] if f==c else ys[f]*(c-k)+ys[c]*(k-f)

def bootstrap_mean(xs,reps=10000,seed=20261001):
    rng=random.Random(seed)
    n=len(xs); vals=[]
    for _ in range(reps):
        vals.append(sum(xs[rng.randrange(n)] for __ in range(n))/n)
    return [pct(vals,.025),pct(vals,.975)]

def fee(premium):
    return min(0.0003,0.125*premium)

def main():
    raw=P.read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    df=pd.read_parquet(P)
    cols=list(df.columns)
    c={k:find_col(cols,v) for k,v in ALIASES.items()}
    missing=[k for k in ("timestamp","instrument","bid","ask","underlying") if not c[k]]
    if missing:
        raise SystemExit("missing semantic columns: "+repr(missing))

    ts=parse_ts(df[c["timestamp"]])
    inst=df[c["instrument"]].astype(str)
    expiry=parse_expiry(df,c["expiry"],inst)
    parts=inst.str.extract(r"^[^-]+-(\d{1,2}[A-Z]{3}\d{2})-([0-9]+(?:\.[0-9]+)?)-([CP])$",expand=True)
    strike=pd.to_numeric(parts[1],errors="coerce")
    right=parts[2]
    bid=pd.to_numeric(df[c["bid"]],errors="coerce")
    ask=pd.to_numeric(df[c["ask"]],errors="coerce")
    und=pd.to_numeric(df[c["underlying"]],errors="coerce")

    local=ts.dt.tz_convert(TZ)
    base=pd.DataFrame({
      "ts":ts,"local":local,"date":local.dt.date,"time":local.dt.strftime("%H:%M"),
      "instrument":inst,"expiry":expiry,"strike":strike,"right":right,
      "bid":bid,"ask":ask,"underlying":und
    })
    valid=(base["ts"].notna() & base["expiry"].notna() & base["strike"].notna() &
           base["right"].isin(["C","P"]) & (base["bid"]>0) & (base["ask"]>0) &
           (base["ask"]>=base["bid"]) & (base["underlying"]>0))
    base=base[valid].copy()
    base["date_s"]=base["date"].astype(str)
    weekday=base["local"].dt.weekday<5
    base=base[weekday & ~base["date_s"].isin(HOLIDAYS)].copy()

    entry=base[base["time"]=="09:00"].copy()
    exitdf=base[base["time"]=="11:00"].copy()

    episodes=[]
    source_dates=sorted(set(entry["date_s"]))
    for ds,g in entry.groupby("date_s",sort=True):
        if ds not in set(exitdf["date_s"]):
            continue
        # A snapshot is exact by frozen local clock. If provider duplicated rows, keep first deterministic row per instrument.
        g=g.sort_values(["ts","instrument"]).drop_duplicates("instrument",keep="first").copy()
        e_ts=g["ts"].iloc[0]
        g["dte"]=(g["expiry"]-e_ts).dt.total_seconds()/86400.0
        g=g[(g["dte"]>=7.0)&(g["dte"]<=14.0)].copy()
        if g.empty: continue
        nearest_expiry=g["expiry"].min()
        g=g[g["expiry"]==nearest_expiry].copy()
        underlying=float(g["underlying"].median())
        if not math.isfinite(underlying) or underlying<=0: continue

        pairs=[]
        for strike_v,sg in g.groupby("strike",sort=True):
            rights=set(sg["right"])
            if not {"C","P"}.issubset(rights): continue
            call=sg[sg["right"]=="C"].iloc[0]
            put=sg[sg["right"]=="P"].iloc[0]
            dist=abs(math.log(float(strike_v)/underlying))
            pairs.append((dist,float(strike_v),call,put))
        if not pairs: continue
        pairs.sort(key=lambda x:(x[0],x[1]))
        _,strike_v,call,put=pairs[0]

        x=exitdf[exitdf["date_s"]==ds].sort_values(["ts","instrument"]).drop_duplicates("instrument",keep="first")
        xc=x[x["instrument"]==call["instrument"]]
        xp=x[x["instrument"]==put["instrument"]]
        if xc.empty or xp.empty: continue
        xc=xc.iloc[0]; xp=xp.iloc[0]

        entry_call_ask=float(call["ask"]); entry_put_ask=float(put["ask"])
        exit_call_bid=float(xc["bid"]); exit_put_bid=float(xp["bid"])
        if min(entry_call_ask,entry_put_ask,exit_call_bid,exit_put_bid)<=0: continue

        fees=(fee(entry_call_ask)+fee(entry_put_ask)+fee(exit_call_bid)+fee(exit_put_bid))
        gross=(exit_call_bid+exit_put_bid)-(entry_call_ask+entry_put_ask)
        base_net=gross-fees
        extra=max(float(call["ask"]-call["bid"]),float(xc["ask"]-xc["bid"])) + \
              max(float(put["ask"]-put["bid"]),float(xp["ask"]-xp["bid"]))
        stress_net=base_net-extra
        premium=entry_call_ask+entry_put_ask

        episodes.append({
          "date":ds,
          "month":ds[:7],
          "expiry":str(nearest_expiry.date()),
          "dte":float((nearest_expiry-e_ts).total_seconds()/86400.0),
          "strike":strike_v,
          "underlying":underlying,
          "entry_premium_btc":premium,
          "gross_btc":gross,
          "fees_btc":fees,
          "base_net_btc":base_net,
          "stress_net_btc":stress_net
        })

    base_x=[e["base_net_btc"] for e in episodes]
    stress_x=[e["stress_net_btc"] for e in episodes]
    months={}
    for m in sorted(set(e["month"] for e in episodes)):
        xs=[e["base_net_btc"] for e in episodes if e["month"]==m]
        months[m]={"n":len(xs),"mean_base_net_btc":sum(xs)/len(xs)}
    total_pos=sum(x for x in base_x if x>0)
    max_share=(max([x for x in base_x if x>0],default=0)/total_pos) if total_pos>0 else None
    ci=bootstrap_mean(base_x) if base_x else [None,None]
    mean_base=sum(base_x)/len(base_x) if base_x else None
    mean_stress=sum(stress_x)/len(stress_x) if stress_x else None
    pf_base=pf(base_x) if base_x else None
    pf_stress=pf(stress_x) if stress_x else None
    nonneg_months=sum(1 for v in months.values() if v["mean_base_net_btc"]>=0)

    def pf_num(v):
        return float("inf") if v=="INF" else (v if isinstance(v,(int,float)) else float("-inf"))

    enough=len(episodes)>=50
    passed=bool(
      enough and mean_base is not None and mean_base>0 and
      pf_num(pf_base)>=1.20 and ci[0] is not None and ci[0]>0 and
      nonneg_months>=4 and mean_stress is not None and mean_stress>0 and
      pf_num(pf_stress)>1 and max_share is not None and max_share<=0.25
    )
    classification=("RETROSPECTIVE_PRICE_ONLY_PROMISING_FORWARD_TEST_JUSTIFIED" if passed
                    else ("PRICE_ONLY_SAMPLE_INSUFFICIENT" if not enough
                          else "RETROSPECTIVE_PRICE_ONLY_NO_SUPPORT"))

    receipt={
      "lab_id":"USOPEN-STRADDLE-001",
      "scope":"RETROSPECTIVE_CONTAMINATED_2024H1_PRICE_ONLY",
      "classification":classification,
      "promotion_credit":"ZERO",
      "source":{
        "file":P.name,
        "file_bytes":len(raw),
        "sha256":sha,
        "rows":int(len(df)),
        "timestamp_min":ts.min().isoformat() if ts.notna().any() else None,
        "timestamp_max":ts.max().isoformat() if ts.notna().any() else None,
        "bid_size_present":False,
        "ask_size_present":False
      },
      "construction":{
        "entry":"09:00 America/New_York exact snapshot; buy ATM 7-14 DTE call+put at ask",
        "exit":"11:00 America/New_York exact snapshot; sell same call+put at bid",
        "fee":"min(0.0003 BTC, 12.5% option premium) per option trade",
        "stress":"base minus max(entry spread,exit spread) once per leg"
      },
      "sample":{
        "entry_snapshot_dates":len(source_dates),
        "executable_episodes":len(episodes),
        "months":months
      },
      "economics":{
        "mean_gross_btc":(sum(e["gross_btc"] for e in episodes)/len(episodes)) if episodes else None,
        "mean_fees_btc":(sum(e["fees_btc"] for e in episodes)/len(episodes)) if episodes else None,
        "mean_base_net_btc":mean_base,
        "base_profit_factor":pf_base,
        "bootstrap95_mean_base_net_btc":ci,
        "nonnegative_month_means":nonneg_months,
        "mean_stress_net_btc":mean_stress,
        "stress_profit_factor":pf_stress,
        "max_single_positive_episode_share":max_share,
        "win_rate_base":(sum(1 for x in base_x if x>0)/len(base_x)) if base_x else None,
        "median_base_net_btc":statistics.median(base_x) if base_x else None,
        "median_entry_premium_btc":statistics.median([e["entry_premium_btc"] for e in episodes]) if episodes else None
      },
      "per_month":months,
      "individual_episodes_retained_in_receipt":False,
      "capacity_claim":False,
      "protected_2025_opened":False,
      "protected_2026_preboundary_opened":False,
      "live_execution":False,
      "exchange_mutation":False,
      "merge_to_main":False
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
      "classification":classification,
      "executable_episodes":len(episodes),
      "economics":receipt["economics"],
      "per_month":months
    },indent=2,allow_nan=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
