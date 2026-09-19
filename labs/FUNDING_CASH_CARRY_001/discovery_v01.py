#!/usr/bin/env python3
from __future__ import annotations
import io,json,math,urllib.request,zipfile
from pathlib import Path
import numpy as np
import pandas as pd

MONTHLY_FUT="https://data.binance.vision/data/futures/um/monthly"
MONTHLY_SPOT="https://data.binance.vision/data/spot/monthly"
MONTHS=pd.period_range("2021-01","2024-12",freq="M").astype(str).tolist()
SEED=230921; BOOT=10000; BLOCK=5

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-FCC/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        n=z.namelist()[0]; data=z.read(n)
    return data,len(raw)

def kline(data):
    d=pd.read_csv(io.BytesIO(data),header=None)
    if d.shape[1]<7: raise RuntimeError("kline schema")
    d=d.iloc[:,:12].copy()
    d.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
    return d[["open_time","open"]]

def funding(data):
    d=pd.read_csv(io.BytesIO(data))
    if not {"calc_time","last_funding_rate"}.issubset(d.columns): raise RuntimeError("funding schema")
    return d[["calc_time","last_funding_rate"]]

def ptime(s):
    n=pd.to_numeric(s,errors="coerce")
    if n.notna().mean()>0.8:
        med=float(n.dropna().abs().median()); unit="ms" if med>1e11 else "s"
        x=pd.to_datetime(n,unit=unit,utc=True,errors="coerce")
    else:x=pd.to_datetime(s,utc=True,errors="coerce")
    return x.astype("datetime64[ns, UTC]")

def pf(x):
    x=np.asarray(x,float); p=x[x>0].sum(); n=-x[x<0].sum()
    return float(p/n) if n>0 else (float("inf") if p>0 else 0.0)

def streak(x):
    m=c=0
    for v in x:
        if v<0:c+=1;m=max(m,c)
        else:c=0
    return m

def boot(x):
    x=np.asarray(x,float); n=len(x); rng=np.random.default_rng(SEED); out=np.empty(BOOT); nb=math.ceil(n/BLOCK)
    for i in range(BOOT):
        vals=[]
        for s in rng.integers(0,n,size=nb): vals.extend(x[(s+np.arange(BLOCK))%n].tolist())
        out[i]=np.mean(vals[:n])
    return [float(np.quantile(out,.025)),float(np.quantile(out,.975))]

def main():
    rec=[]; fs=[]; ps=[]; ss=[]
    for m in MONTHS:
        row={"month":m}
        routes={
          "funding":f"{MONTHLY_FUT}/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{m}.zip",
          "perp":f"{MONTHLY_FUT}/klines/BTCUSDT/1h/BTCUSDT-1h-{m}.zip",
          "spot":f"{MONTHLY_SPOT}/klines/BTCUSDT/1h/BTCUSDT-1h-{m}.zip"
        }
        for kind,u in routes.items():
            try:
                data,n=fetch(u); row[kind+"_ok"]=True; row[kind+"_zip_bytes"]=n
                if kind=="funding":
                    d=funding(data); d["source_month"]=m; fs.append(d); row["funding_rows"]=len(d)
                elif kind=="perp":
                    d=kline(data); d["source_month"]=m; ps.append(d); row["perp_rows"]=len(d)
                else:
                    d=kline(data); d["source_month"]=m; ss.append(d); row["spot_rows"]=len(d)
            except Exception as e:
                row[kind+"_ok"]=False; row[kind+"_error"]=f"{type(e).__name__}:{str(e)[:220]}"
        rec.append(row)
    common=[r["month"] for r in rec if r.get("funding_ok") and r.get("perp_ok") and r.get("spot_ok")]
    yc={str(y):sum(m.startswith(str(y)+"-") for m in common) for y in range(2021,2025)}
    full=len(common)>=46 and min(yc.values())>=11
    limited=len(common)>=36 and min(yc.values())>=8
    cov="FCC_COVERAGE_FULL" if full else ("FCC_COVERAGE_LIMITED" if limited else "FCC_COVERAGE_BLOCKED")
    coverage={"classification":cov,"common_month_count":len(common),"common_months_by_year":yc,"records":rec,"outcomes_opened":False}
    Path("fcc_coverage_receipt_v01.json").write_text(json.dumps(coverage,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"coverage":cov,"common_month_count":len(common),"common_months_by_year":yc},sort_keys=True))
    if cov=="FCC_COVERAGE_BLOCKED": return 2

    f=pd.concat(fs,ignore_index=True); perp=pd.concat(ps,ignore_index=True); spot=pd.concat(ss,ignore_index=True)
    f["ts"]=ptime(f["calc_time"]); f["rate"]=pd.to_numeric(f["last_funding_rate"],errors="coerce")
    f=f[f["ts"].notna()&f["rate"].notna()].sort_values("ts").drop_duplicates("ts",keep="last")
    f=f[(f["ts"]>=pd.Timestamp("2021-01-01",tz="UTC"))&(f["ts"]<pd.Timestamp("2025-01-01",tz="UTC"))]
    for d in [perp,spot]:
        d["ts"]=ptime(d["open_time"]); d["open"]=pd.to_numeric(d["open"],errors="coerce")
    perp=perp[perp["ts"].notna()&(perp["open"]>0)].sort_values("ts").drop_duplicates("ts",keep="last")
    spot=spot[spot["ts"].notna()&(spot["open"]>0)].sort_values("ts").drop_duplicates("ts",keep="last")
    pp=perp.set_index("ts")["open"]; sp=spot.set_index("ts")["open"]; fr=f.set_index("ts")["rate"]

    f["q90"]=f["rate"].shift(1).rolling(540,min_periods=270).quantile(.90)
    sig=f[(f["rate"]>0)&(f["rate"]>=f["q90"])].copy()

    trades=[]; active_until=None
    for r in sig.itertuples(index=False):
        t=r.ts
        entry_t=t+pd.Timedelta(hours=1); exit_t=t+pd.Timedelta(hours=25)
        if active_until is not None and entry_t<active_until: continue
        if any(x not in pp.index for x in [entry_t,exit_t]) or any(x not in sp.index for x in [entry_t,exit_t]): continue
        funding_times=[t+pd.Timedelta(hours=h) for h in (8,16,24)]
        if any(ft not in fr.index or ft not in pp.index for ft in funding_times): continue
        s0=float(sp.loc[entry_t]); s1=float(sp.loc[exit_t]); p0=float(pp.loc[entry_t]); p1=float(pp.loc[exit_t])
        fund_usdt=sum(float(fr.loc[ft])*float(pp.loc[ft]) for ft in funding_times)
        spot_pnl=s1-s0; perp_pnl=p0-p1
        gross=(spot_pnl+perp_pnl+fund_usdt)/s0
        trades.append({"signal_ts":t.isoformat(),"entry_ts":entry_t.isoformat(),"exit_ts":exit_t.isoformat(),
                       "signal_funding":float(r.rate),"funding_component":fund_usdt/s0,
                       "basis_price_component":(spot_pnl+perp_pnl)/s0,
                       "gross":gross,"net30":gross-.003,"net40":gross-.004})
        active_until=exit_t
    d=pd.DataFrame(trades); n=len(d)
    if n:
        d["year"]=pd.to_datetime(d["signal_ts"],utc=True,format="mixed").dt.year
        years={str(int(y)):float(v) for y,v in d.groupby("year")["net30"].mean().items()}
        ci=boot(d["net30"].to_numpy())
        st={"N":n,"mean_net30":float(d.net30.mean()),"median_net30":float(d.net30.median()),
            "hit_rate":float((d.net30>0).mean()),"profit_factor_net30":pf(d.net30),
            "bootstrap_95_ci_mean_net30":ci,"mean_net40":float(d.net40.mean()),
            "profit_factor_net40":pf(d.net40),"year_means_net30":years,
            "positive_year_count":int(sum(v>0 for v in years.values())),
            "max_losing_streak":int(streak(d.net30.to_numpy())),
            "mean_funding_component":float(d.funding_component.mean()),
            "mean_basis_price_component":float(d.basis_price_component.mean())}
    else:st={"N":0}
    gates={"N_gte_80":n>=80,"mean_net30_gt_0":n>0 and st["mean_net30"]>0,
           "pf_net30_gte_1_10":n>0 and st["profit_factor_net30"]>=1.10,
           "bootstrap_lower_gt_0":n>0 and st["bootstrap_95_ci_mean_net30"][0]>0,
           "positive_years_gte_3":n>0 and st["positive_year_count"]>=3,
           "mean_net40_gt_0":n>0 and st["mean_net40"]>0,
           "pf_net40_gt_1":n>0 and st["profit_factor_net40"]>1}
    if n<80: verdict="INSUFFICIENT_SAMPLE"
    elif all(gates.values()): verdict="DISCOVERY_PASS_FUNDING_CARRY_SIGNAL"
    else: verdict="DISCOVERY_FAIL_NO_PROMOTION"
    out={"lab_id":"FUNDING-CASH-CARRY-001","mve_id":"FCC-BTC-24H-PERSISTENCE-001",
         "source_coverage":cov,"verdict":verdict,"stats":st,"gates":gates,
         "protected_2025_2026_opened":False}
    Path("fcc_discovery_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    d.to_csv("fcc_discovery_trades_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
