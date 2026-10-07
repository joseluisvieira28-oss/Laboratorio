#!/usr/bin/env python3
from __future__ import annotations
import json,math,time
from pathlib import Path
import requests, numpy as np, pandas as pd

BASE="https://api.mexc.com"
START=pd.Timestamp("2024-01-01",tz="UTC")
END=pd.Timestamp("2026-01-01",tz="UTC")
FUND_START=pd.Timestamp("2023-01-01",tz="UTC")
Q=.90; TRAIL=540; MINH=270; HOLD=168
COST15=.0015; COST20=.0020
BOOT=10000; BLOCK=5; SEED=20261007
S=requests.Session(); S.headers.update({"User-Agent":"CryptoLab-FundingSqueeze/0.2","Accept":"application/json"})

def get_json(url,params=None):
    last=None
    for i in range(5):
        r=S.get(url,params=params,timeout=45); last=r
        if r.status_code==200: return r.json()
        if r.status_code in (429,418,403):
            time.sleep(1.5*(i+1)); continue
        r.raise_for_status()
    raise RuntimeError("http_fail:%s:%s:%s"%(url,last.status_code,last.text[:200]))

def fetch_funding():
    rows=[]; page=1
    while page<=20:
        j=get_json(BASE+"/api/v1/contract/funding_rate/history",{"symbol":"BTC_USDT","page_num":page,"page_size":1000})
        d=j.get("data",{}) if isinstance(j,dict) else {}
        rr=d.get("resultList",[]) if isinstance(d,dict) else []
        if not rr: break
        for x in rr:
            try:
                rows.append((pd.to_datetime(int(x["settleTime"]),unit="ms",utc=True),float(x["fundingRate"]),int(x.get("collectCycle",0) or 0)))
            except Exception: pass
        total=d.get("totalPage")
        if isinstance(total,int) and page>=total: break
        page+=1; time.sleep(.15)
    z=pd.DataFrame(rows,columns=["ts_raw","rate","cycle"]).drop_duplicates("ts_raw").sort_values("ts_raw")
    z=z[(z.ts_raw>=FUND_START)&(z.ts_raw<END)].copy()
    z["ts"]=z["ts_raw"].dt.round("h")
    delta=(z.ts_raw-z.ts).abs().dt.total_seconds()
    if z.empty or float(delta.max())>300: raise RuntimeError("funding_timestamp_or_coverage_fail")
    return z

def chunks(start,end,days=30):
    cur=start
    while cur<end:
        nxt=min(cur+pd.Timedelta(days=days),end)
        yield cur,nxt; cur=nxt

def fetch_spot():
    out=[]
    for a,b in chunks(START,END,30):
        j=get_json(BASE+"/api/v3/klines",{"symbol":"BTCUSDT","interval":"1h","startTime":int(a.timestamp()*1000),"endTime":int((b-pd.Timedelta(milliseconds=1)).timestamp()*1000),"limit":1000})
        if not isinstance(j,list): raise RuntimeError("spot_schema:"+str(j)[:200])
        for x in j:
            if isinstance(x,list) and len(x)>=2: out.append((pd.to_datetime(int(x[0]),unit="ms",utc=True),float(x[1])))
        time.sleep(.08)
    d=pd.DataFrame(out,columns=["ts","open"]).drop_duplicates("ts").sort_values("ts")
    return d[(d.ts>=START)&(d.ts<END)]

def fetch_perp():
    out=[]
    for a,b in chunks(START,END,30):
        j=get_json(BASE+"/api/v1/contract/kline/BTC_USDT",{"interval":"Min60","start":int(a.timestamp()),"end":int((b-pd.Timedelta(seconds=1)).timestamp())})
        d=j.get("data",{}) if isinstance(j,dict) else {}
        tt=d.get("time",[]) if isinstance(d,dict) else []; oo=d.get("open",[]) if isinstance(d,dict) else []
        if len(tt)!=len(oo): raise RuntimeError("perp_schema")
        for t,o in zip(tt,oo): out.append((pd.to_datetime(int(t),unit="s",utc=True),float(o)))
        time.sleep(.08)
    d=pd.DataFrame(out,columns=["ts","open"]).drop_duplicates("ts").sort_values("ts")
    return d[(d.ts>=START)&(d.ts<END)]

def pf(x):
    x=np.asarray(x,float); p=x[x>0].sum(); n=-x[x<0].sum()
    return float(p/n) if n>0 else (float("inf") if p>0 else 0.0)

def boot_ci(x):
    x=np.asarray(x,float); n=len(x); rng=np.random.default_rng(SEED); sims=np.empty(BOOT); nb=math.ceil(n/BLOCK)
    for i in range(BOOT):
        vals=[]
        for s in rng.integers(0,n,size=nb): vals.extend(x[(s+np.arange(BLOCK))%n].tolist())
        sims[i]=np.mean(vals[:n])
    return [float(np.quantile(sims,.025)),float(np.quantile(sims,.975))]

def main():
    try:
        f=fetch_funding(); spot=fetch_spot(); perp=fetch_perp()
    except Exception as e:
        out={"verdict":"SOURCE_BLOCKED","source_error":type(e).__name__+":"+str(e),"governance":{"outcomes_2026_opened":False}}
        Path("funding_squeeze_v02_mexc_report.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print("VERDICT=SOURCE_BLOCKED"); print(json.dumps(out,sort_keys=True)); return
    expected=int((END-START)/pd.Timedelta(hours=1))
    source={"funding_rows":len(f),"spot_rows":len(spot),"perp_rows":len(perp),"expected_hours":expected,"spot_coverage":len(spot)/expected,"perp_coverage":len(perp)/expected}
    print("SOURCE",json.dumps(source,sort_keys=True))
    if len(f)<MINH+100 or source["spot_coverage"]<.98 or source["perp_coverage"]<.98:
        out={"verdict":"SOURCE_BLOCKED","source":source,"governance":{"outcomes_2026_opened":False}}
        Path("funding_squeeze_v02_mexc_report.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print("VERDICT=SOURCE_BLOCKED"); return

    sp=spot.set_index("ts")["open"]; pp=perp.set_index("ts")["open"]
    f=f.sort_values("ts").drop_duplicates("ts",keep="last")
    f["thr"]=f["rate"].shift(1).rolling(TRAIL,min_periods=MINH).quantile(Q)
    sig=f[(f.ts>=START)&(f.ts<END)&(f.rate>0)&(f.rate>=f.thr)].copy()
    fr=f.set_index("ts")["rate"]; allft=list(fr.index)
    trades=[]; active_until=None; eligible_nonoverlap=0; missing=0
    for r in sig.itertuples(index=False):
        t=r.ts; entry=t+pd.Timedelta(hours=1); exit_t=entry+pd.Timedelta(hours=HOLD)
        if exit_t>=END: continue
        if active_until is not None and entry<active_until: continue
        eligible_nonoverlap+=1
        future=[ft for ft in allft if ft>t and ft<=exit_t]
        if entry not in sp.index or exit_t not in sp.index or entry not in pp.index or exit_t not in pp.index or any(ft not in pp.index for ft in future):
            missing+=1; active_until=exit_t; continue
        s0=float(sp.loc[entry]); s1=float(sp.loc[exit_t]); p0=float(pp.loc[entry]); p1=float(pp.loc[exit_t])
        fund=sum(float(fr.loc[ft])*float(pp.loc[ft]) for ft in future)
        fc=fund/s0; bc=((s1-s0)+(p0-p1))/s0; gross=fc+bc
        trades.append({"signal":t.isoformat(),"entry":entry.isoformat(),"exit":exit_t.isoformat(),"signal_rate":float(r.rate),"funding_component":fc,"basis_component":bc,"gross":gross,"net15":gross-COST15,"net20":gross-COST20,"settlements":len(future)})
        active_until=exit_t
    analyzable=len(trades); trade_cov=analyzable/eligible_nonoverlap if eligible_nonoverlap else 0
    source.update({"eligible_nonoverlap":eligible_nonoverlap,"analyzable":analyzable,"trade_coverage":trade_cov,"missing_trades":missing})
    if eligible_nonoverlap==0 or trade_cov<.95:
        out={"verdict":"SOURCE_BLOCKED","source":source,"governance":{"outcomes_2026_opened":False}}
        Path("funding_squeeze_v02_mexc_report.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print("VERDICT=SOURCE_BLOCKED"); return

    d=pd.DataFrame(trades); d["year"]=pd.to_datetime(d.signal,utc=True).dt.year
    ci=boot_ci(d.net15.to_numpy()); yrs={str(int(y)):float(v) for y,v in d.groupby("year").net15.mean().items()}
    st={"N":len(d),"mean_gross":float(d.gross.mean()),"mean_net15":float(d.net15.mean()),"mean_net20":float(d.net20.mean()),"median_net15":float(d.net15.median()),"win_net15":float((d.net15>0).mean()),"pf_net15":pf(d.net15),"bootstrap95_net15":ci,"year_means_net15":yrs,"mean_funding_component":float(d.funding_component.mean()),"mean_basis_component":float(d.basis_component.mean()),"mean_settlements":float(d.settlements.mean())}
    gates={"N_ge_50":len(d)>=50,"mean_net15_gt_0":st["mean_net15"]>0,"pf_net15_ge_1_10":st["pf_net15"]>=1.10,"bootstrap_lower_gt_0":ci[0]>0,"year_2024_positive":yrs.get("2024",-999)>0,"year_2025_positive":yrs.get("2025",-999)>0,"mean_net20_gt_0":st["mean_net20"]>0}
    verdict="SURVIVES_LOW_COST_REPLICATION" if all(gates.values()) else "LOW_COST_REPLICATION_FAIL"
    out={"family":"FUNDING-SQUEEZE-001","stage":"V0.2_MEXC_LOWCOST_CONFIRMATORY","verdict":verdict,"source":source,"stats":st,"gates":gates,"governance":{"outcomes_2026_opened":False,"live_trading":False,"private_endpoints":False,"main_modified":False}}
    Path("funding_squeeze_v02_mexc_report.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); d.to_csv("funding_squeeze_v02_mexc_trades.csv",index=False)
    print("RESULT",json.dumps(out,sort_keys=True)); print("VERDICT="+verdict)

if __name__=="__main__": main()
