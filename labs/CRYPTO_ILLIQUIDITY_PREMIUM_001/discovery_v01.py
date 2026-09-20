#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures, io, json, math, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

SYMS=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]
MONTHS=pd.period_range("2020-12","2025-12",freq="M").astype(str).tolist()
BASE="https://data.binance.vision/data/futures/um/monthly/klines"
SEED=230924; BOOT=10000; BLOCK=4

def fetch_one(args):
    s,m=args
    u=f"{BASE}/{s}/1d/{s}-1d-{m}.zip"
    try:
        req=urllib.request.Request(u,headers={"User-Agent":"CryptoLab-CIP/0.1"})
        with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            data=z.read(z.namelist()[0])
        d=pd.read_csv(io.BytesIO(data),header=None)
        if d.shape[1]<8: raise RuntimeError("kline schema")
        d=d.iloc[:,:12].copy()
        d.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
        d=d[["open_time","open","close","quote_volume"]]
        d["symbol"]=s; d["source_month"]=m
        return s,m,d,len(raw),None
    except Exception as e:
        return s,m,None,0,f"{type(e).__name__}:{str(e)[:220]}"

def ptime(s):
    n=pd.to_numeric(s,errors="coerce")
    med=float(n.dropna().abs().median()) if n.notna().any() else 0
    unit="ms" if med>1e11 else "s"
    return pd.to_datetime(n,unit=unit,utc=True,errors="coerce").astype("datetime64[ns, UTC]")

def pf(x):
    x=np.asarray(x,float); p=x[x>0].sum(); n=-x[x<0].sum()
    return float(p/n) if n>0 else (float("inf") if p>0 else 0.0)

def streak(x):
    m=c=0
    for v in x:
        if v<0:c+=1;m=max(m,c)
        else:c=0
    return m

def boot(x,seed):
    x=np.asarray(x,float); n=len(x); rng=np.random.default_rng(seed); out=np.empty(BOOT); nb=math.ceil(n/BLOCK)
    for i in range(BOOT):
        vals=[]
        for s in rng.integers(0,n,size=nb): vals.extend(x[(s+np.arange(BLOCK))%n].tolist())
        out[i]=np.mean(vals[:n])
    return [float(np.quantile(out,.025)),float(np.quantile(out,.975))]

def stat(d,col,seed):
    x=d[col].to_numpy(float); yrs={str(int(y)):float(v) for y,v in d.groupby("year")[col].mean().items()}
    return {"N":int(len(d)),"mean":float(np.mean(x)),"median":float(np.median(x)),
            "hit_rate":float(np.mean(x>0)),"profit_factor":pf(x),
            "bootstrap_95_ci_mean":boot(x,seed),"year_means":yrs,
            "positive_year_count":int(sum(v>0 for v in yrs.values())),
            "max_losing_streak":int(streak(x))}

def main():
    rec=[]; frames=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for s,m,d,n,e in ex.map(fetch_one,[(s,m) for s in SYMS for m in MONTHS]):
            rec.append({"symbol":s,"month":m,"ok":d is not None,"bytes":n,"error":e})
            if d is not None: frames.append(d)

    cov={}
    for s in SYMS:
        ok=[r["month"] for r in rec if r["symbol"]==s and r["ok"]]
        cov[s]={"months_total":len(ok),"by_year":{str(y):sum(m.startswith(str(y)+"-") for m in ok) for y in range(2021,2026)}}
    disc_ok=all(sum(v["by_year"][str(y)] for y in range(2021,2024))>=35 and min(v["by_year"][str(y)] for y in range(2021,2024))>=11 for v in cov.values())
    hold_ok=all(sum(v["by_year"][str(y)] for y in range(2024,2026))>=23 and min(v["by_year"][str(y)] for y in range(2024,2026))>=11 for v in cov.values())
    src_cls="CIP_SOURCE_FULL" if disc_ok and hold_ok else ("CIP_SOURCE_DISCOVERY_ONLY" if disc_ok else "CIP_SOURCE_BLOCKED")
    src={"classification":src_cls,"coverage":cov,"records":rec,"outcomes_opened":False}
    Path("cip_source_receipt_v01.json").write_text(json.dumps(src,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"source":src_cls,"coverage":cov},sort_keys=True))
    if not disc_ok: return 2

    d=pd.concat(frames,ignore_index=True)
    d["time"]=ptime(d["open_time"])
    for c in ["open","close","quote_volume"]: d[c]=pd.to_numeric(d[c],errors="coerce")
    d=d[d["time"].notna()&(d["open"]>0)&(d["quote_volume"]>0)].sort_values(["symbol","time"]).drop_duplicates(["symbol","time"],keep="last")
    # Daily open-to-next-open return known at the next daily boundary.
    d["next_open"]=d.groupby("symbol")["open"].shift(-1)
    d["ret1"]=np.log(d["next_open"]/d["open"])
    d["amihud"]=d["ret1"].abs()/d["quote_volume"]
    # Feature at Monday uses information through completed Sunday: rolling 20 on rows ending Sunday.
    d["illiq20"]=d.groupby("symbol")["amihud"].transform(lambda x:x.rolling(20,min_periods=20).mean())

    piv_open=d.pivot(index="time",columns="symbol",values="open").sort_index()
    piv_ill=d.pivot(index="time",columns="symbol",values="illiq20").sort_index()

    trades=[]
    mondays=[t for t in piv_open.index if t.weekday()==0 and t.hour==0]
    for t in mondays:
        sunday=t-pd.Timedelta(days=1)
        exit_t=t+pd.Timedelta(days=7)
        if sunday not in piv_ill.index or exit_t not in piv_open.index: continue
        if any(pd.isna(piv_ill.at[sunday,s]) or pd.isna(piv_open.at[t,s]) or pd.isna(piv_open.at[exit_t,s]) for s in SYMS): continue
        ranks=sorted(SYMS,key=lambda s:(float(piv_ill.at[sunday,s]),s))
        short=ranks[:2]; long=ranks[-2:]
        rr={s:float(np.log(piv_open.at[exit_t,s]/piv_open.at[t,s])) for s in SYMS}
        gross=float(np.mean([rr[s] for s in long])-np.mean([rr[s] for s in short]))
        trades.append({"signal_monday":t.isoformat(),"exit_monday":exit_t.isoformat(),
                       "long_1":long[0],"long_2":long[1],"short_1":short[0],"short_2":short[1],
                       "gross":gross,"net20":gross-.002,"net40":gross-.004})

    tr=pd.DataFrame(trades)
    if tr.empty:
        out={"verdict":"INSUFFICIENT_SAMPLE","N":0,"holdout_opened":False,"year_2026_opened":False}
        Path("cip_final_receipt_v01.json").write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out)); return 0
    tr["ts"]=pd.to_datetime(tr["signal_monday"],utc=True,format="mixed"); tr["year"]=tr["ts"].dt.year
    disc=tr[(tr["ts"]>=pd.Timestamp("2021-01-04",tz="UTC"))&(tr["ts"]<=pd.Timestamp("2023-12-25",tz="UTC"))].copy()
    if len(disc)<130:
        out={"verdict":"INSUFFICIENT_SAMPLE","N":len(disc),"holdout_opened":False,"year_2026_opened":False}
        Path("cip_final_receipt_v01.json").write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out)); return 0
    s20=stat(disc,"net20",SEED); s40=stat(disc,"net40",SEED+1)
    dg={"N_gte_130":len(disc)>=130,"mean_net20_gt_0":s20["mean"]>0,
        "pf_net20_gte_1_15":s20["profit_factor"]>=1.15,
        "bootstrap_lower_gt_0":s20["bootstrap_95_ci_mean"][0]>0,
        "positive_years_gte_2":s20["positive_year_count"]>=2,
        "mean_net40_gt_0":s40["mean"]>0,"pf_net40_gt_1":s40["profit_factor"]>1}
    dp=all(dg.values())
    discovery={"verdict":"DISCOVERY_PASS" if dp else "DISCOVERY_FAIL_NO_PROMOTION","stats_net20":s20,"stats_net40":s40,"gates":dg}
    Path("cip_discovery_receipt_v01.json").write_text(json.dumps(discovery,indent=2,sort_keys=True)+"\n")
    disc.to_csv("cip_discovery_trades_v01.csv",index=False)
    print(json.dumps({"discovery":discovery},sort_keys=True))
    if not dp:
        out={"lab_id":"CRYPTO-ILLIQUIDITY-PREMIUM-001","verdict":"DISCOVERY_FAIL_NO_PROMOTION",
             "discovery":discovery,"holdout_opened":False,"year_2026_opened":False}
        Path("cip_final_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); return 0

    if not hold_ok:
        out={"lab_id":"CRYPTO-ILLIQUIDITY-PREMIUM-001","verdict":"BLOCKED_HOLDOUT_SOURCE",
             "discovery":discovery,"holdout_opened":False,"year_2026_opened":False}
        Path("cip_final_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); return 0

    hold=tr[(tr["ts"]>=pd.Timestamp("2024-01-01",tz="UTC"))&(tr["ts"]<=pd.Timestamp("2025-12-22",tz="UTC"))].copy()
    h20=stat(hold,"net20",SEED+2); h40=stat(hold,"net40",SEED+3)
    hg={"N_gte_90":len(hold)>=90,"mean_net20_gt_0":h20["mean"]>0,
        "pf_net20_gte_1_10":h20["profit_factor"]>=1.10,
        "bootstrap_lower_gt_0":h20["bootstrap_95_ci_mean"][0]>0,
        "positive_years_eq_2":h20["positive_year_count"]==2,
        "mean_net40_gt_0":h40["mean"]>0}
    hp=all(hg.values())
    verdict="SURVIVES_2024_2025_HOLDOUT" if hp else "DISCOVERY_PASS_HOLDOUT_FAIL"
    out={"lab_id":"CRYPTO-ILLIQUIDITY-PREMIUM-001","mve_id":"CIP-MAJOR5-WEEKLY-AMIHUD-001",
         "verdict":verdict,"source":src_cls,"discovery":discovery,
         "holdout":{"stats_net20":h20,"stats_net40":h40,"gates":hg},
         "holdout_opened":True,"year_2026_opened":False}
    Path("cip_final_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    hold.to_csv("cip_holdout_trades_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
