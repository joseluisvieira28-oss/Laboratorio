#!/usr/bin/env python3
from __future__ import annotations
import json,math
from pathlib import Path
import numpy as np
import pandas as pd

SEED=230919; BOOT=10000; BLOCK=5

def parse_time(s):
    n=pd.to_numeric(s,errors="coerce")
    if n.notna().any() and n.notna().mean()>0.8:
        med=float(n.dropna().abs().median()); unit="ms" if med>1e11 else "s"
        return pd.to_datetime(n,unit=unit,utc=True,errors="coerce")
    return pd.to_datetime(s,utc=True,errors="coerce")

def pf(x):
    x=np.asarray(x,float); p=x[x>0].sum(); n=-x[x<0].sum()
    return float(p/n) if n>0 else (float("inf") if p>0 else 0.0)

def streak(x):
    m=c=0
    for v in x:
        if v<0:c+=1;m=max(m,c)
        else:c=0
    return m

def boot_ci(x):
    x=np.asarray(x,float); n=len(x); rng=np.random.default_rng(SEED); out=np.empty(BOOT)
    nb=math.ceil(n/BLOCK)
    for i in range(BOOT):
        vals=[]
        for s in rng.integers(0,n,size=nb):
            vals.extend(x[(s+np.arange(BLOCK))%n].tolist())
        out[i]=np.mean(vals[:n])
    return [float(np.quantile(out,.025)),float(np.quantile(out,.975))]

def main():
    cov=json.loads(Path("pcu_coverage_receipt_v01.json").read_text())
    if cov["classification"]=="PCU_COVERAGE_BLOCKED":
        raise SystemExit("blocked coverage")
    m=pd.read_csv("pcu_cache/metrics.csv")
    f=pd.read_csv("pcu_cache/funding.csv")
    k=pd.read_csv("pcu_cache/klines.csv")

    m["ts"]=parse_time(m["create_time"])
    m["oi"]=pd.to_numeric(m["sum_open_interest"],errors="coerce")
    m=m[m["ts"].notna()&(m["oi"]>0)].sort_values("ts").drop_duplicates("ts",keep="last")

    f["ts"]=parse_time(f["calc_time"])
    f["funding"]=pd.to_numeric(f["last_funding_rate"],errors="coerce")
    f=f[f["ts"].notna()&f["funding"].notna()].sort_values("ts").drop_duplicates("ts",keep="last")
    f=f[(f["ts"]>=pd.Timestamp("2021-01-01",tz="UTC"))&(f["ts"]<pd.Timestamp("2025-01-01",tz="UTC"))]

    k["ts"]=parse_time(k["open_time"])
    k["open"]=pd.to_numeric(k["open"],errors="coerce")
    k=k[k["ts"].notna()&(k["open"]>0)].sort_values("ts").drop_duplicates("ts",keep="last")
    px=k.set_index("ts")["open"]

    ev=f[["ts","funding"]].copy().sort_values("ts")
    ev=pd.merge_asof(ev,m[["ts","oi"]],on="ts",direction="backward",tolerance=pd.Timedelta("15min"))
    prev=ev[["ts"]].copy(); prev["target"]=prev["ts"]-pd.Timedelta(hours=24)
    prev=prev.sort_values("target")
    pm=m[["ts","oi"]].rename(columns={"ts":"m_ts","oi":"oi_prev"}).sort_values("m_ts")
    prev=pd.merge_asof(prev,pm,left_on="target",right_on="m_ts",direction="backward",tolerance=pd.Timedelta("15min"))
    ev["oi_prev"]=prev.set_index("ts").reindex(ev["ts"])["oi_prev"].to_numpy()
    ev["oi_growth_24h"]=ev["oi"]/ev["oi_prev"]-1

    # Past-only thresholds.
    ev["fund_q95"]=ev["funding"].shift(1).rolling(540,min_periods=270).quantile(.95)
    ev["fund_q05"]=ev["funding"].shift(1).rolling(540,min_periods=270).quantile(.05)
    ev["oi_q80"]=ev["oi_growth_24h"].shift(1).rolling(540,min_periods=270).quantile(.80)

    ev["side"]=0
    ev.loc[(ev["funding"]>=ev["fund_q95"])&(ev["oi_growth_24h"]>=ev["oi_q80"]),"side"]=-1
    ev.loc[(ev["funding"]<=ev["fund_q05"])&(ev["oi_growth_24h"]>=ev["oi_q80"]),"side"]=1
    ev=ev[ev["side"]!=0].copy()

    trades=[]; active_until=None
    for r in ev.itertuples(index=False):
        t=r.ts
        if active_until is not None and t<active_until: continue
        entry_t=t.floor("h"); exit_t=entry_t+pd.Timedelta(hours=24)
        if entry_t not in px.index or exit_t not in px.index: continue
        entry=float(px.loc[entry_t]); exitp=float(px.loc[exit_t])
        gross=int(r.side)*(exitp/entry-1)
        net10=gross-0.001
        net20=gross-0.002
        trades.append({"ts":t.isoformat(),"side":int(r.side),"funding":float(r.funding),"oi_growth_24h":float(r.oi_growth_24h),
                       "entry":entry,"exit":exitp,"gross_return":gross,"net10":net10,"net20":net20})
        active_until=exit_t

    d=pd.DataFrame(trades)
    n=len(d)
    if n:
        d["year"]=pd.to_datetime(d["ts"],utc=True).dt.year
        years={str(int(y)):float(v) for y,v in d.groupby("year")["net10"].mean().items()}
        ci=boot_ci(d["net10"].to_numpy())
        st={
          "N":n,"long_N":int((d["side"]==1).sum()),"short_N":int((d["side"]==-1).sum()),
          "mean_net10":float(d["net10"].mean()),"median_net10":float(d["net10"].median()),
          "hit_rate":float((d["net10"]>0).mean()),"profit_factor_net10":pf(d["net10"]),
          "bootstrap_95_ci_mean_net10":ci,"mean_net20":float(d["net20"].mean()),
          "profit_factor_net20":pf(d["net20"]),"year_means_net10":years,
          "positive_year_count":int(sum(v>0 for v in years.values())),
          "max_losing_streak":int(streak(d["net10"].to_numpy()))
        }
    else: st={"N":0}
    gates={
      "N_gte_60":n>=60,
      "mean_net10_gt_0":n>0 and st["mean_net10"]>0,
      "pf_net10_gte_1_10":n>0 and st["profit_factor_net10"]>=1.10,
      "bootstrap_lower_gt_0":n>0 and st["bootstrap_95_ci_mean_net10"][0]>0,
      "positive_years_gte_3":n>0 and st["positive_year_count"]>=3,
      "mean_net20_gt_0":n>0 and st["mean_net20"]>0,
      "pf_net20_gt_1":n>0 and st["profit_factor_net20"]>1
    }
    if n<60: verdict="INSUFFICIENT_EXECUTABLE_SAMPLE"
    elif all(gates.values()): verdict="DISCOVERY_PASS_CROWDING_UNWIND_SIGNAL"
    else: verdict="DISCOVERY_FAIL_NO_PROMOTION"
    out={"lab_id":"PERP-CROWDING-UNWIND-001","mve_id":"PCU-BTC-24H-TRAILING-CROWDING-001",
         "source_coverage_classification":cov["classification"],"verdict":verdict,"stats":st,"gates":gates,
         "funding_cashflows_included":False,"protected_2025_2026_opened":False}
    Path("pcu_discovery_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    d.to_csv("pcu_discovery_trades_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
