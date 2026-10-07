#!/usr/bin/env python3
from __future__ import annotations
import hashlib, io, json, math, re, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

FUT="https://data.binance.vision/data/futures/um/monthly"
SPOT="https://data.binance.vision/data/spot/monthly"
FUND_MONTHS=pd.period_range("2024-01","2025-12",freq="M").astype(str).tolist()
PX_MONTHS=pd.period_range("2025-01","2025-12",freq="M").astype(str).tolist()

START=pd.Timestamp("2025-01-01T00:00:00Z")
END=pd.Timestamp("2026-01-01T00:00:00Z")
Q=.90; TRAIL=540; MINH=270; HOLD_H=168
COST20=.0020; COST25=.0025
BOOT=10000; BLOCK=5; SEED=20261007

def http_bytes(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-FundingSqueeze/0.3"})
    with urllib.request.urlopen(req,timeout=90) as r:
        return r.read()

def verified_zip(url):
    side=http_bytes(url+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"\b([0-9a-fA-F]{64})\b",side)
    if not m: raise RuntimeError("checksum_parse_fail:"+url)
    expected=m.group(1).lower()
    raw=http_bytes(url)
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected: raise RuntimeError("checksum_mismatch:"+url)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(names)!=1: raise RuntimeError("zip_csv_member_count:"+url+":"+str(len(names)))
        data=z.read(names[0])
    return data,{"url":url,"sha256":actual,"zip_bytes":len(raw),"csv_bytes":len(data)}

def parse_ts(series):
    n=pd.to_numeric(series,errors="coerce")
    good=n.dropna().abs()
    if good.empty: return pd.to_datetime(series,utc=True,errors="coerce"),"text"
    med=float(good.median())
    unit="us" if med>=1e14 else ("ms" if med>=1e11 else "s")
    return pd.to_datetime(n,unit=unit,utc=True,errors="coerce"),unit

def parse_funding(data):
    d=pd.read_csv(io.BytesIO(data))
    if not {"calc_time","last_funding_rate"}.issubset(d.columns):
        raise RuntimeError("funding_schema:"+",".join(map(str,d.columns)))
    out=d[["calc_time","last_funding_rate"]].copy()
    out["ts_raw"],unit=parse_ts(out["calc_time"])
    out["rate"]=pd.to_numeric(out["last_funding_rate"],errors="coerce")
    out=out[out.ts_raw.notna()&out.rate.notna()].copy()
    out["ts"]=out["ts_raw"].dt.round("h")
    delta=(out.ts_raw-out.ts).abs().dt.total_seconds()
    if len(out) and float(delta.max())>5.0:
        raise RuntimeError("funding_alignment_gt_5s:"+str(float(delta.max())))
    return out[["ts_raw","ts","rate"]],unit

def parse_kline(data):
    d=pd.read_csv(io.BytesIO(data),header=None)
    if d.shape[1]<2: raise RuntimeError("kline_schema")
    out=d.iloc[:,:2].copy(); out.columns=["open_time","open"]
    out["ts"],unit=parse_ts(out["open_time"])
    out["open"]=pd.to_numeric(out["open"],errors="coerce")
    out=out[out.ts.notna()&(out.open>0)].copy()
    return out[["ts","open"]],unit

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

def main():
    manifest=[]; fs=[]; ps=[]; ss=[]
    try:
        for m in FUND_MONTHS:
            url=f"{FUT}/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{m}.zip"
            raw,rec=verified_zip(url); d,unit=parse_funding(raw)
            rec.update({"kind":"funding","month":m,"rows":len(d),"timestamp_unit":unit})
            manifest.append(rec); fs.append(d)
            print("SOURCE",json.dumps(rec,sort_keys=True))
        for m in PX_MONTHS:
            url=f"{FUT}/klines/BTCUSDT/1h/BTCUSDT-1h-{m}.zip"
            raw,rec=verified_zip(url); d,unit=parse_kline(raw)
            rec.update({"kind":"perp","month":m,"rows":len(d),"timestamp_unit":unit})
            manifest.append(rec); ps.append(d)
            print("SOURCE",json.dumps(rec,sort_keys=True))
        for m in PX_MONTHS:
            url=f"{SPOT}/klines/BTCUSDT/1h/BTCUSDT-1h-{m}.zip"
            raw,rec=verified_zip(url); d,unit=parse_kline(raw)
            rec.update({"kind":"spot","month":m,"rows":len(d),"timestamp_unit":unit})
            manifest.append(rec); ss.append(d)
            print("SOURCE",json.dumps(rec,sort_keys=True))
    except Exception as e:
        out={"family":"FUNDING-SQUEEZE-001","stage":"V0.3_BINANCE_2025_CONFIRMATORY",
             "verdict":"SOURCE_BLOCKED","source_error":type(e).__name__+":"+str(e),
             "governance":{"outcomes_2026_opened":False,"main_modified":False,"live_trading":False}}
        Path("funding_squeeze_v03_source_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
        Path("funding_squeeze_v03_report.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print("VERDICT=SOURCE_BLOCKED"); print(json.dumps(out,sort_keys=True)); return

    Path("funding_squeeze_v03_source_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    if len([x for x in manifest if x["kind"]=="funding"])!=24 or len([x for x in manifest if x["kind"]=="perp"])!=12 or len([x for x in manifest if x["kind"]=="spot"])!=12:
        raise RuntimeError("manifest_count_fail")

    f=pd.concat(fs,ignore_index=True).sort_values("ts").drop_duplicates("ts",keep="last")
    perp=pd.concat(ps,ignore_index=True).sort_values("ts").drop_duplicates("ts",keep="last")
    spot=pd.concat(ss,ignore_index=True).sort_values("ts").drop_duplicates("ts",keep="last")
    f=f[(f.ts>=pd.Timestamp("2024-01-01",tz="UTC"))&(f.ts<END)].copy()
    perp=perp[(perp.ts>=START)&(perp.ts<END)].copy()
    spot=spot[(spot.ts>=START)&(spot.ts<END)].copy()

    expected=int((END-START)/pd.Timedelta(hours=1))
    source_summary={"funding_rows":len(f),"perp_rows":len(perp),"spot_rows":len(spot),"expected_2025_hours":expected,
                    "perp_hour_coverage":len(perp)/expected,"spot_hour_coverage":len(spot)/expected,
                    "funding_months":24,"perp_months":12,"spot_months":12}
    if source_summary["perp_hour_coverage"]<.999 or source_summary["spot_hour_coverage"]<.999:
        out={"family":"FUNDING-SQUEEZE-001","stage":"V0.3_BINANCE_2025_CONFIRMATORY","verdict":"SOURCE_BLOCKED",
             "source":source_summary,"governance":{"outcomes_2026_opened":False,"main_modified":False,"live_trading":False}}
        Path("funding_squeeze_v03_report.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print("VERDICT=SOURCE_BLOCKED"); print(json.dumps(out,sort_keys=True)); return

    pp=perp.set_index("ts")["open"]; sp=spot.set_index("ts")["open"]
    fr=f.set_index("ts")["rate"]; funding_times=list(fr.index)
    f["thr"]=f["rate"].shift(1).rolling(TRAIL,min_periods=MINH).quantile(Q)
    sig=f[(f.ts>=START)&(f.ts<END)&(f.rate>0)&(f.rate>=f.thr)].copy()

    trades=[]; active_until=None; eligible=0; missing=0
    for r in sig.itertuples(index=False):
        t=r.ts; entry=t+pd.Timedelta(hours=1); exit_t=entry+pd.Timedelta(hours=HOLD_H)
        if exit_t>=END: continue
        if active_until is not None and entry<active_until: continue
        eligible+=1
        receipts=[ft for ft in funding_times if ft>t and ft<=exit_t]
        if entry not in sp.index or exit_t not in sp.index or entry not in pp.index or exit_t not in pp.index or any(ft not in pp.index for ft in receipts):
            missing+=1; active_until=exit_t; continue
        s0=float(sp.loc[entry]); s1=float(sp.loc[exit_t]); p0=float(pp.loc[entry]); p1=float(pp.loc[exit_t])
        fund=sum(float(fr.loc[ft])*float(pp.loc[ft]) for ft in receipts)
        fc=fund/s0; bc=((s1-s0)+(p0-p1))/s0; gross=fc+bc
        trades.append({"signal":t.isoformat(),"entry":entry.isoformat(),"exit":exit_t.isoformat(),
                       "signal_funding":float(r.rate),"funding_component":fc,"basis_component":bc,
                       "gross":gross,"net20":gross-COST20,"net25":gross-COST25,"settlements":len(receipts)})
        active_until=exit_t

    trade_cov=(len(trades)/eligible) if eligible else 0.0
    source_summary.update({"eligible_nonoverlap":eligible,"analyzable":len(trades),"missing_trades":missing,"trade_coverage":trade_cov})
    if eligible and trade_cov<1.0:
        out={"family":"FUNDING-SQUEEZE-001","stage":"V0.3_BINANCE_2025_CONFIRMATORY","verdict":"SOURCE_BLOCKED",
             "source":source_summary,"governance":{"outcomes_2026_opened":False,"main_modified":False,"live_trading":False}}
        Path("funding_squeeze_v03_report.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print("VERDICT=SOURCE_BLOCKED"); return

    d=pd.DataFrame(trades)
    if len(d)<20:
        verdict="INSUFFICIENT_SAMPLE_2025"
        st={"N":len(d)}
        gates={}
    else:
        x=d.net20.to_numpy(); ci=boot_ci(x)
        mid=len(d)//2
        h1=float(d.iloc[:mid].net20.mean()); h2=float(d.iloc[mid:].net20.mean())
        st={"N":len(d),"mean_gross":float(d.gross.mean()),"mean_net20":float(d.net20.mean()),
            "mean_net25":float(d.net25.mean()),"median_net20":float(d.net20.median()),
            "win_net20":float((d.net20>0).mean()),"pf_net20":pf(x),
            "bootstrap95_net20":ci,"chronological_half_1_mean_net20":h1,
            "chronological_half_2_mean_net20":h2,
            "mean_funding_component":float(d.funding_component.mean()),
            "mean_basis_component":float(d.basis_component.mean()),
            "mean_settlements":float(d.settlements.mean())}
        gates={"N_ge_20":len(d)>=20,"mean_net20_gt_0":st["mean_net20"]>0,
               "pf_net20_ge_1_10":st["pf_net20"]>=1.10,
               "bootstrap_lower_gt_0":ci[0]>0,
               "half1_positive":h1>0,"half2_positive":h2>0,
               "mean_net25_gt_0":st["mean_net25"]>0}
        verdict="SURVIVES_2025_CONFIRMATORY_LOWCOST" if all(gates.values()) else "NO_EDGE_LOWCOST_V03"

    out={"family":"FUNDING-SQUEEZE-001","stage":"V0.3_BINANCE_2025_CONFIRMATORY",
         "verdict":verdict,"source":source_summary,"stats":st,"gates":gates,
         "governance":{"outcomes_2026_opened":False,"main_modified":False,"live_trading":False,
                       "private_endpoints":False,"orders":False}}
    Path("funding_squeeze_v03_report.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    if len(d): d.to_csv("funding_squeeze_v03_trades.csv",index=False)
    print("RESULT",json.dumps(out,sort_keys=True))
    print("VERDICT="+verdict)

if __name__=="__main__": main()
