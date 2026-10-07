#!/usr/bin/env python3
from __future__ import annotations
import io,json,math,urllib.request,zipfile
from pathlib import Path
import numpy as np
import pandas as pd

MONTHLY_FUT="https://data.binance.vision/data/futures/um/monthly"
MONTHLY_SPOT="https://data.binance.vision/data/spot/monthly"
MONTHS=pd.period_range("2021-01","2024-12",freq="M").astype(str).tolist()
QS=[0.85,0.90,0.95]
HOLDS=[24,48,72,120,168]
MODES=["FIXED","STOP_NONPOSITIVE"]
SEED=20261007; BOOT=10000; BLOCK=5
CUTOFF=pd.Timestamp("2025-01-01",tz="UTC")

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-FundingSqueeze/0.1"})
    with urllib.request.urlopen(req,timeout=90) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(names)!=1: raise RuntimeError(f"zip_csv_members={len(names)}")
        return z.read(names[0])

def kline(data):
    d=pd.read_csv(io.BytesIO(data),header=None)
    d=d.iloc[:,:12].copy()
    d.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
    return d[["open_time","open"]]

def funding(data):
    d=pd.read_csv(io.BytesIO(data))
    if not {"calc_time","last_funding_rate"}.issubset(d.columns): raise RuntimeError("funding_schema")
    return d[["calc_time","last_funding_rate"]]

def ptime(s):
    n=pd.to_numeric(s,errors="coerce")
    med=float(n.dropna().abs().median())
    unit="ms" if med>1e11 else "s"
    return pd.to_datetime(n,unit=unit,utc=True,errors="coerce")

def pf(x):
    x=np.asarray(x,float); pos=x[x>0].sum(); neg=-x[x<0].sum()
    return float(pos/neg) if neg>0 else (float("inf") if pos>0 else 0.0)

def boot_ci(x):
    x=np.asarray(x,float); n=len(x)
    if n==0:return [None,None]
    rng=np.random.default_rng(SEED); sims=np.empty(BOOT); nb=math.ceil(n/BLOCK)
    for i in range(BOOT):
        vals=[]
        for s in rng.integers(0,n,size=nb):
            vals.extend(x[(s+np.arange(BLOCK))%n].tolist())
        sims[i]=np.mean(vals[:n])
    return [float(np.quantile(sims,.025)),float(np.quantile(sims,.975))]

def load_all():
    fs=[]; ps=[]; ss=[]; coverage=[]
    for m in MONTHS:
        routes={
          "funding":f"{MONTHLY_FUT}/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{m}.zip",
          "perp":f"{MONTHLY_FUT}/klines/BTCUSDT/1h/BTCUSDT-1h-{m}.zip",
          "spot":f"{MONTHLY_SPOT}/klines/BTCUSDT/1h/BTCUSDT-1h-{m}.zip"}
        row={"month":m}
        for kind,u in routes.items():
            try:
                raw=fetch(u); row[kind]=True
                if kind=="funding": fs.append(funding(raw))
                elif kind=="perp": ps.append(kline(raw))
                else: ss.append(kline(raw))
            except Exception as e:
                row[kind]=False; row[kind+"_error"]=f"{type(e).__name__}:{e}"
        coverage.append(row)
        print("MONTH",m,row)
    common=[r["month"] for r in coverage if r.get("funding") and r.get("perp") and r.get("spot")]
    if len(common)<46: raise RuntimeError(f"coverage_fail:{len(common)}")
    f=pd.concat(fs,ignore_index=True); p=pd.concat(ps,ignore_index=True); s=pd.concat(ss,ignore_index=True)
    f["ts"]=ptime(f["calc_time"]); f["rate"]=pd.to_numeric(f["last_funding_rate"],errors="coerce")
    f=f[f.ts.notna()&f.rate.notna()].sort_values("ts").drop_duplicates("ts",keep="last")
    f=f[(f.ts>=pd.Timestamp("2021-01-01",tz="UTC"))&(f.ts<CUTOFF)]
    for d in (p,s):
        d["ts"]=ptime(d["open_time"]); d["open"]=pd.to_numeric(d["open"],errors="coerce")
    p=p[p.ts.notna()&(p.open>0)].sort_values("ts").drop_duplicates("ts",keep="last")
    s=s[s.ts.notna()&(s.open>0)].sort_values("ts").drop_duplicates("ts",keep="last")
    return f,p.set_index("ts")["open"],s.set_index("ts")["open"],coverage

def make_trades(f,pp,sp,q,hold,mode):
    z=f.copy()
    z["thr"]=z["rate"].shift(1).rolling(540,min_periods=270).quantile(q)
    sig=z[(z.rate>0)&(z.rate>=z.thr)].copy()
    fr=z.set_index("ts")["rate"]
    f_times=list(fr.index)
    trades=[]; active_until=None
    for r in sig.itertuples(index=False):
        t=r.ts; entry=t+pd.Timedelta(hours=1); max_exit=entry+pd.Timedelta(hours=hold)
        if max_exit>=CUTOFF: continue
        if active_until is not None and entry<active_until: continue
        if entry not in pp.index or entry not in sp.index or max_exit not in pp.index or max_exit not in sp.index: continue
        future=[ft for ft in f_times if ft>t and ft<=max_exit]
        if not future: continue
        exit_t=max_exit
        if mode=="STOP_NONPOSITIVE":
            hit=None
            for ft in future:
                if float(fr.loc[ft])<=0:
                    cand=ft+pd.Timedelta(hours=1)
                    if cand<=max_exit:
                        hit=cand
                    break
            if hit is not None: exit_t=hit
        included=[ft for ft in future if ft<=exit_t]
        if not included: continue
        if exit_t not in pp.index or exit_t not in sp.index: continue
        s0=float(sp.loc[entry]); s1=float(sp.loc[exit_t]); p0=float(pp.loc[entry]); p1=float(pp.loc[exit_t])
        fund=sum(float(fr.loc[ft])*float(pp.loc[ft]) for ft in included)
        funding_comp=fund/s0
        basis_comp=((s1-s0)+(p0-p1))/s0
        gross=funding_comp+basis_comp
        trades.append({"signal":t,"entry":entry,"exit":exit_t,"signal_rate":float(r.rate),
                       "funding_component":funding_comp,"basis_component":basis_comp,
                       "gross":gross,"net30":gross-.003,"net10":gross-.001,
                       "settlements":len(included)})
        active_until=exit_t
    return pd.DataFrame(trades)

def summarize(d):
    if d.empty:return {"N":0}
    d=d.copy(); d["year"]=pd.to_datetime(d["signal"],utc=True).dt.year
    yrs={str(int(y)):float(v) for y,v in d.groupby("year")["net30"].mean().items()}
    ci=boot_ci(d.net30.to_numpy())
    return {"N":len(d),"mean_gross":float(d.gross.mean()),"mean_net30":float(d.net30.mean()),
            "mean_net10":float(d.net10.mean()),"median_net30":float(d.net30.median()),
            "win_net30":float((d.net30>0).mean()),"pf_net30":pf(d.net30),
            "bootstrap95_net30":ci,"year_means_net30":yrs,
            "positive_years":sum(v>0 for v in yrs.values()),
            "mean_funding_component":float(d.funding_component.mean()),
            "mean_basis_component":float(d.basis_component.mean()),
            "mean_settlements":float(d.settlements.mean())}

def main():
    f,pp,sp,coverage=load_all()
    results=[]; trade_map={}
    for q in QS:
      for hold in HOLDS:
        for mode in MODES:
          d=make_trades(f,pp,sp,q,hold,mode)
          st=summarize(d)
          gates={"N_ge_60":st.get("N",0)>=60,
                 "mean_net30_gt_0":st.get("mean_net30",-999)>0,
                 "pf_net30_ge_1_10":st.get("pf_net30",0)>=1.10,
                 "bootstrap_lower_gt_0":(st.get("bootstrap95_net30") or [None])[0] is not None and st["bootstrap95_net30"][0]>0,
                 "positive_years_ge_3":st.get("positive_years",0)>=3}
          key=f"q{q:.2f}_h{hold}_{mode}"
          results.append({"key":key,"q":q,"hold_hours":hold,"mode":mode,"stats":st,"gates":gates,"passes":all(gates.values())})
          trade_map[key]=d
          print("CELL",json.dumps(results[-1],sort_keys=True,default=str))
    passes=[x for x in results if x["passes"]]
    if passes:
        passes.sort(key=lambda x:(x["stats"]["bootstrap95_net30"][0],x["stats"]["mean_net30"],-x["hold_hours"],x["q"]),reverse=True)
        chosen=passes[0]
        verdict="DEVELOPMENT_CANDIDATE_SELECTED"
        trade_map[chosen["key"]].to_csv("funding_squeeze_v01_selected_dev_trades.csv",index=False)
    else:
        chosen=None; verdict="NO_VIABLE_CONFIRMATORY_SPEC"
    report={"family":"FUNDING-SQUEEZE-001","stage":"V0.1_DEVELOPMENT_2021_2024",
            "verdict":verdict,"grid":results,"selected":chosen,
            "governance":{"year_2025_opened":False,"year_2026_opened":False,
                          "live_trading":False,"private_endpoints":False,"main_modified":False}}
    Path("funding_squeeze_v01_development_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("VERDICT="+verdict)
    print("SELECTED="+json.dumps(chosen,sort_keys=True) if chosen else "SELECTED=null")
    return 0

if __name__=="__main__": raise SystemExit(main())
