from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import json
import math
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import pandas as pd

ASSETS=("BTCUSDT","ETHUSDT")
BASE="https://data.binance.vision/data/spot/monthly/klines"
FREEZE_COMMIT="79577d02184113a4c67486b42f30b360bfdab76e"
TRANSLATION_ID="CIRV-VOLTARGET-BTCETH-SPOT-001"
BASE_COST=0.0020
STRESS_COST=0.0030


def _url(symbol:str, month:str)->str:
    return f"{BASE}/{symbol}/5m/{symbol}-5m-{month}.zip"


def _head(url:str)->dict:
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CIRV-Econ/0.1"},method="HEAD")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return {"url":url,"http_status":int(getattr(r,"status",200)),
                    "content_length":r.headers.get("Content-Length"),
                    "last_modified":r.headers.get("Last-Modified")}
    except Exception as exc:
        return {"url":url,"http_status":None,"error":f"{type(exc).__name__}:{exc}"}


def source_gate()->dict:
    months=pd.period_range("2021-01","2025-12",freq="M").astype(str).tolist()
    urls=[_url(s,m) for s in ASSETS for m in months]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        rows=list(ex.map(_head,urls))
    ok=[r for r in rows if r.get("http_status")==200]
    missing=[r for r in rows if r.get("http_status")!=200]
    return {
        "translation_id":TRANSLATION_ID,
        "mode":"SOURCE_ONLY",
        "frozen_commit":FREEZE_COMMIT,
        "checked_files":len(rows),
        "http_200":len(ok),
        "missing_or_blocked":len(missing),
        "coverage_ratio":len(ok)/len(rows) if rows else 0,
        "source_data_pass":len(missing)==0,
        "outcomes_opened":False,
        "prices_read":False,
        "returns_computed":False,
        "pnl_computed":False,
        "year_2026_accessed":False,
        "missing":missing,
        "sample_metadata":ok[:4]+ok[-4:],
    }


def _fetch_zip(url:str)->tuple[bytes,bytes]:
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CIRV-Econ/0.1"})
    with urllib.request.urlopen(req,timeout=90) as r:
        raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        data=z.read(z.namelist()[0])
    return raw,data


def _parse(data:bytes,symbol:str)->pd.DataFrame:
    df=pd.read_csv(io.BytesIO(data),header=None)
    if df.shape[1] < 7:
        raise RuntimeError("unexpected kline schema")
    df=df.iloc[:,:12].copy()
    df.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
    for c in ("open","close"):
        df[c]=pd.to_numeric(df[c],errors="coerce")
    n=pd.to_numeric(df["open_time"],errors="coerce")
    med=float(n.dropna().abs().median()) if n.notna().any() else 0
    unit="us" if med>1e14 else ("ms" if med>1e11 else "s")
    df["ts"]=pd.to_datetime(n,unit=unit,utc=True,errors="coerce")
    df["symbol"]=symbol
    return df[["symbol","ts","open","close"]].dropna()


def load_history(end_month:str)->tuple[pd.DataFrame,str,list[dict]]:
    months=pd.period_range("2021-01",end_month,freq="M").astype(str).tolist()
    tasks=[(s,_url(s,m)) for s in ASSETS for m in months]
    frames=[]
    evidence=[]
    def one(task):
        s,u=task
        raw,data=_fetch_zip(u)
        return _parse(data,s),{"url":u,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for frame,ev in ex.map(one,tasks):
            frames.append(frame); evidence.append(ev)
    raw=pd.concat(frames,ignore_index=True)
    raw=raw.sort_values(["symbol","ts"]).drop_duplicates(["symbol","ts"],keep="last")
    digest=hashlib.sha256(("\n".join(f'{x["url"]} {x["sha256"]}' for x in sorted(evidence,key=lambda z:z["url"]))).encode()).hexdigest()
    return raw,digest,evidence


def daily_rv(raw:pd.DataFrame)->pd.DataFrame:
    x=raw.copy()
    x["prev_ts"]=x.groupby("symbol")["ts"].shift(1)
    x["prev_close"]=x.groupby("symbol")["close"].shift(1)
    gap=(x["ts"]-x["prev_ts"]).dt.total_seconds()/60
    x["ret5"]=np.where(gap.eq(5),np.log(x["close"]/x["prev_close"]),np.nan)
    x["date"]=x["ts"].dt.floor("D")
    d=(x.groupby(["symbol","date"])
       .agg(rv=("ret5",lambda z:float(np.nansum(np.square(z.to_numpy(float))))),
            nret=("ret5",lambda z:int(np.isfinite(z.to_numpy(float)).sum())))
       .reset_index())
    return d[(d["nret"]>=270)&(d["rv"]>0)].copy()


def _features(daily:pd.DataFrame,symbol:str,target:pd.Timestamp):
    x=daily[daily.symbol==symbol].sort_values("date").copy().set_index("date")
    x["x1"]=np.log(x["rv"])
    x["x5"]=np.log(x["rv"].rolling(5,min_periods=5).mean())
    x["x22"]=np.log(x["rv"].rolling(22,min_periods=22).mean())
    train=x.dropna(subset=["x1","x5","x22"]).copy()
    train["next_date"]=train.index.to_series().shift(-1)
    train["y"]=np.log(train["rv"].shift(-1))
    train["target_dow"]=train["next_date"].dt.weekday
    train=train[(train["next_date"]-train.index.to_series()).dt.days.eq(1)].dropna(subset=["y","target_dow"])
    train=train[train["next_date"]<target].tail(730)
    prev=target-pd.Timedelta(days=1)
    if prev not in x.index:
        raise RuntimeError(f"{symbol} missing D-1 RV")
    row=x.loc[prev]
    hist=x.loc[x.index<target,"rv"].tail(22)
    if len(hist)<22:
        raise RuntimeError(f"{symbol} insufficient target-vol history")
    return train,row,float(np.sqrt(hist.mean()))


def _design(train:pd.DataFrame,dow:bool)->np.ndarray:
    base=np.column_stack([np.ones(len(train)),train["x1"],train["x5"],train["x22"]])
    if not dow: return base
    ds=np.column_stack([(train["target_dow"].astype(int).to_numpy()==k).astype(float) for k in range(1,7)])
    return np.column_stack([base,ds])


def _row(row:pd.Series,target_dow:int,dow:bool)->np.ndarray:
    base=np.array([1.,row["x1"],row["x5"],row["x22"]],float)
    if not dow:return base
    return np.r_[base,np.array([1. if target_dow==k else 0. for k in range(1,7)],float)]


def forecasts(daily:pd.DataFrame,symbol:str,target:pd.Timestamp)->tuple[float,float,float,int]:
    train,row,target_sigma=_features(daily,symbol,target)
    if len(train)<500: raise RuntimeError(f"{symbol} training rows {len(train)} < 500")
    y=train["y"].to_numpy(float)
    b0=np.linalg.lstsq(_design(train,False),y,rcond=None)[0]
    b1=np.linalg.lstsq(_design(train,True),y,rcond=None)[0]
    dow=int(target.weekday())
    p0=float(_row(row,dow,False)@b0)
    p1=float(_row(row,dow,True)@b1)
    return float(np.exp(p0)),float(np.exp(p1)),target_sigma,len(train)


def exec_return(raw:pd.DataFrame,symbol:str,target:pd.Timestamp)->float:
    x=raw[raw.symbol==symbol].set_index("ts")
    t0=target+pd.Timedelta(hours=9,minutes=5)
    t1=target+pd.Timedelta(hours=23,minutes=55)
    if t0 not in x.index or t1 not in x.index:
        raise RuntimeError(f"{symbol} missing execution bar")
    entry=float(x.loc[t0,"open"])
    exit_=float(x.loc[t1,"close"])
    if entry<=0 or exit_<=0: raise RuntimeError("invalid execution price")
    return exit_/entry-1.0


def pf(x:pd.Series)->float|None:
    pos=float(x[x>0].sum()); neg=float(-x[x<0].sum())
    if neg==0: return None if pos==0 else float("inf")
    return pos/neg


def maxdd(x:pd.Series)->float:
    eq=(1+x).cumprod()
    dd=eq/eq.cummax()-1
    return float(dd.min())


def metrics(x:pd.Series)->dict:
    x=x.dropna().astype(float)
    sd=float(x.std(ddof=1)) if len(x)>1 else float("nan")
    return {
        "N":int(len(x)),
        "mean_daily":float(x.mean()) if len(x) else None,
        "profit_factor":pf(x),
        "annualized_sharpe":float(x.mean()/sd*np.sqrt(365)) if len(x)>1 and sd>0 else None,
        "annualized_vol":float(sd*np.sqrt(365)) if len(x)>1 else None,
        "max_drawdown":maxdd(x) if len(x) else None,
        "total_compound_return":float((1+x).prod()-1) if len(x) else None,
    }


def run_block(year:int)->dict:
    raw,digest,evidence=load_history(f"{year}-12")
    daily=daily_rv(raw)
    days=pd.date_range(f"{year}-01-01",f"{year}-12-31",freq="D",tz="UTC")
    rows=[]
    for day in days:
        rec={"date":day.date().isoformat()}
        ok=True
        for symbol in ASSETS:
            try:
                h,d,tgt,n=forecasts(daily,symbol,day)
                r=exec_return(raw,symbol,day)
                wh=min(1.0,tgt/math.sqrt(h))
                wd=min(1.0,tgt/math.sqrt(d))
                rec[symbol]={
                    "har_rv":h,"dow_rv":d,"target_sigma":tgt,
                    "har_exposure":wh,"dow_exposure":wd,
                    "gross_return_0905_2355":r,"training_rows":n
                }
            except Exception as exc:
                rec[symbol]={"error":f"{type(exc).__name__}:{exc}"}
                ok=False
        rec["evaluable"]=ok
        if ok:
            base_gross=sum(0.5*rec[s]["har_exposure"]*rec[s]["gross_return_0905_2355"] for s in ASSETS)
            dow_gross=sum(0.5*rec[s]["dow_exposure"]*rec[s]["gross_return_0905_2355"] for s in ASSETS)
            base_notional=sum(0.5*rec[s]["har_exposure"] for s in ASSETS)
            dow_notional=sum(0.5*rec[s]["dow_exposure"] for s in ASSETS)
            rec.update({
                "har_base_net":base_gross-base_notional*BASE_COST,
                "dow_base_net":dow_gross-dow_notional*BASE_COST,
                "har_stress_net":base_gross-base_notional*STRESS_COST,
                "dow_stress_net":dow_gross-dow_notional*STRESS_COST,
                "har_gross_exposure":base_notional,
                "dow_gross_exposure":dow_notional,
            })
        rows.append(rec)
    ev=pd.DataFrame([{
        "date":r["date"],
        "har_base_net":r.get("har_base_net"),
        "dow_base_net":r.get("dow_base_net"),
        "har_stress_net":r.get("har_stress_net"),
        "dow_stress_net":r.get("dow_stress_net"),
        "har_gross_exposure":r.get("har_gross_exposure"),
        "dow_gross_exposure":r.get("dow_gross_exposure"),
    } for r in rows if r["evaluable"]])
    hb=metrics(ev["har_base_net"]) if len(ev) else {}
    db=metrics(ev["dow_base_net"]) if len(ev) else {}
    hs=metrics(ev["har_stress_net"]) if len(ev) else {}
    ds=metrics(ev["dow_stress_net"]) if len(ev) else {}
    gates={
        "min_evaluable_portfolio_days":len(ev)>=330,
        "challenger_base_mean_gt_0":db.get("mean_daily") is not None and db["mean_daily"]>0,
        "challenger_base_pf_gt_1":db.get("profit_factor") is not None and db["profit_factor"]>1,
        "challenger_stress_mean_gt_0":ds.get("mean_daily") is not None and ds["mean_daily"]>0,
        "challenger_stress_pf_gt_1":ds.get("profit_factor") is not None and ds["profit_factor"]>1,
        "challenger_sharpe_gt_baseline_har":db.get("annualized_sharpe") is not None and hb.get("annualized_sharpe") is not None and db["annualized_sharpe"]>hb["annualized_sharpe"],
        "challenger_annualized_vol_lte_baseline_har":db.get("annualized_vol") is not None and hb.get("annualized_vol") is not None and db["annualized_vol"]<=hb["annualized_vol"],
        "challenger_max_drawdown_not_worse_than_baseline_har":db.get("max_drawdown") is not None and hb.get("max_drawdown") is not None and db["max_drawdown"]>=hb["max_drawdown"],
    }
    passed=all(gates.values())
    return {
        "translation_id":TRANSLATION_ID,
        "mode":f"ECONOMIC_BLOCK_{year}",
        "frozen_commit":FREEZE_COMMIT,
        "year":year,
        "source_digest":digest,
        "source_files":len(evidence),
        "evaluable_portfolio_days":int(len(ev)),
        "baseline_HAR":{"BASE":hb,"STRESS":hs,"mean_gross_exposure":float(ev["har_gross_exposure"].mean()) if len(ev) else None},
        "challenger_HAR_DOW":{"BASE":db,"STRESS":ds,"mean_gross_exposure":float(ev["dow_gross_exposure"].mean()) if len(ev) else None},
        "incremental":{"mean_daily_base_dow_minus_har":float((ev["dow_base_net"]-ev["har_base_net"]).mean()) if len(ev) else None},
        "gates":gates,
        "pass":passed,
        "rows":rows,
        "year_2026_accessed":False,
        "orders_created":False,
        "exchange_mutation_performed":False,
        "live_capital_enabled":False,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--stage",required=True,choices=["SOURCE_ONLY","DISCOVERY_2023","REPLICATION_2024","OOS_2025"])
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    if args.stage=="SOURCE_ONLY":
        result=source_gate()
    else:
        year={"DISCOVERY_2023":2023,"REPLICATION_2024":2024,"OOS_2025":2025}[args.stage]
        result=run_block(year)
        result["stage"]=args.stage
    Path(args.out).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in {"rows","missing","sample_metadata"}},indent=2,sort_keys=True))


if __name__=="__main__":
    main()
