#!/usr/bin/env python3
"""MEXC NVIDIA cash-open discovery V0.2, frozen pre-outcome."""
from __future__ import annotations
import csv, io, json, math, statistics, time, zipfile, hashlib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_NVIDIA_CASHOPEN_RULE_V0.2.json"
BIND_PATH=HERE/"MEXC_NVIDIA_CASHOPEN_SOURCE_BINDING_V0.2.json"
RULE=json.loads(RULE_PATH.read_text())
BIND=json.loads(BIND_PATH.read_text())
OUT=Path("artifacts/mexc_global_assets/nvidia_cashopen_v02")
UA="CryptoLab-MEXC-NVIDIA-CashOpen/0.2"

def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def mean(xs): return sum(xs)/len(xs) if xs else None
def median(xs): return statistics.median(xs) if xs else None
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)

def sessions():
    a=date.fromisoformat(RULE["discovery_start_date"])
    b=date.fromisoformat(RULE["discovery_end_date_inclusive"])
    d=a
    out=[]
    while d<=b:
        if d.weekday()<5: out.append(d)
        d+=timedelta(days=1)
    return out

def utcsec(d,hh,mm):
    return int(datetime(d.year,d.month,d.day,hh,mm,tzinfo=timezone.utc).timestamp())

def req(url,params=None,timeout=60,retries=4):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code!=200:
                raise RuntimeError(f"HTTP_{r.status_code}:{r.url}:{r.content[:250]!r}")
            return r
        except Exception as e:
            last=e
            time.sleep(0.7*(i+1))
    raise last

def fetch_mexc(d):
    s=utcsec(d,13,20); e=utcsec(d,14,1)
    r=req("https://api.mexc.com/api/v1/contract/kline/NVIDIA_USDT",
          {"interval":"Min1","start":str(s),"end":str(e)})
    j=r.json()
    if j.get("success") is not True:
        raise RuntimeError(f"MEXC_NON_SUCCESS:{d}:{j}")
    dat=j.get("data") or {}
    out={}
    for raw,p in zip(dat.get("time") or [],dat.get("close") or []):
        try: out[int(raw)+60]=float(p)
        except Exception: pass
    return out,sha_bytes(r.content)

def fetch_bitget(d):
    s=utcsec(d,13,20)*1000; e=utcsec(d,14,1)*1000
    r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
      "symbol":"NVDAUSDT","productType":"USDT-FUTURES","granularity":"1m",
      "startTime":str(s),"endTime":str(e),"limit":"200"
    })
    j=r.json()
    if j.get("code")!="00000":
        raise RuntimeError(f"BITGET_NON_SUCCESS:{d}:{j}")
    out={}
    for row in j.get("data") or []:
        try: out[int(row[0])//1000+60]=float(row[4])
        except Exception: pass
    return out,sha_bytes(r.content)

def fetch_binance(d):
    day=d.isoformat()
    url=f"https://data.binance.vision/data/futures/um/daily/klines/NVDAUSDT/1m/NVDAUSDT-1m-{day}.zip"
    r=req(url,timeout=90)
    z=zipfile.ZipFile(io.BytesIO(r.content))
    names=z.namelist()
    if len(names)!=1: raise RuntimeError(f"BINANCE_ZIP_IDENTITY:{day}:{names}")
    out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try:
            raw=int(row[0])//1000
            px=float(row[4])
        except Exception:
            continue
        if utcsec(d,13,20)<=raw<=utcsec(d,14,1):
            out[raw+60]=px
    return out,sha_bytes(r.content)

def binom_tail_half(w,n):
    if n<=0:return None
    return sum(math.comb(n,k) for k in range(w,n+1))/(2**n)

def halves(vals):
    n=len(vals); k=n//2
    return [mean(vals[:k]),mean(vals[k:])] if n>=2 else [None,None]

def summarize(vals,predictors):
    n=len(vals); wins=sum(x>0 for x in vals)
    return {
      "n":n,
      "wins":wins,
      "losses_or_zero":n-wins,
      "win_rate":wins/n if n else None,
      "mean_gross_signed_bps":mean(vals),
      "median_gross_signed_bps":median(vals),
      "chronological_half_means_bps":halves(vals),
      "p_value_one_sided_binomial_vs_50":binom_tail_half(wins,n) if n else None,
      "mean_abs_predictor_bps":mean([abs(x) for x in predictors]) if predictors else None,
      "cost_scenarios_mean_net_bps":{
        str(c):(mean(vals)-float(c) if vals else None)
        for c in RULE["cost_scenarios_roundtrip_bps"]
      }
    }

def eligible(r):
    g=RULE["discovery_gate"]
    return (
      r["n"]>=g["min_n"] and
      r["mean_gross_signed_bps"] is not None and r["mean_gross_signed_bps"]>0 and
      r["median_gross_signed_bps"] is not None and r["median_gross_signed_bps"]>0 and
      r["win_rate"] is not None and r["win_rate"]>0.5 and
      all(x is not None and x>0 for x in r["chronological_half_means_bps"])
    )

def holm_all(cells,alpha=0.05):
    ordered=sorted(cells,key=lambda x:x["result"]["p_value_one_sided_binomial_vs_50"])
    m=len(ordered); still=True
    for rank,x in enumerate(ordered,1):
        cutoff=alpha/(m-rank+1)
        x["holm_rank"]=rank
        x["holm_cutoff"]=cutoff
        p=x["result"]["p_value_one_sided_binomial_vs_50"]
        passed=bool(still and p is not None and p<=cutoff)
        x["holm_reject"]=passed
        if not passed: still=False
    return [x for x in cells if x.get("holm_reject") and x["eligible"]]

def main():
    if RULE.get("outcomes_opened_at_freeze")!=0:
        raise SystemExit("FAIL_CLOSED: rule not pre-outcome")
    if BIND.get("historical_outcomes_opened_at_binding")!=0:
        raise SystemExit("FAIL_CLOSED: binding not pre-outcome")
    if BIND.get("allowed_historical_legs")!=["MEXC","BINANCE","BITGET"]:
        raise SystemExit("FAIL_CLOSED: source binding changed")

    sess=sessions()
    if len(sess)!=18:
        raise SystemExit(f"FAIL_CLOSED: expected 18 sessions, got {len(sess)}")

    daydata={}
    source_hashes={}
    for d in sess:
        m,mh=fetch_mexc(d)
        b,bh=fetch_binance(d)
        g,gh=fetch_bitget(d)
        daydata[d.isoformat()]={"mexc":m,"binance":b,"bitget":g}
        source_hashes[d.isoformat()]={"mexc":mh,"binance":bh,"bitget":gh}
        time.sleep(0.05)

    horizons=[2,5,15,30]
    famA={h:{"vals":[],"pred":[],"days":[]} for h in horizons}
    famB={h:{"vals":[],"pred":[],"days":[]} for h in horizons}
    obs=[]

    for ds in [d.isoformat() for d in sess]:
        d=date.fromisoformat(ds)
        t24=utcsec(d,13,24)
        t29=utcsec(d,13,29)
        D=daydata[ds]
        required=[t24,t29]+[t29+h*60 for h in horizons]
        if any(t not in D["mexc"] for t in [t29]+[t29+h*60 for h in horizons]):
            obs.append({"date":ds,"status":"MEXC_MISSING"})
            continue
        if any(t not in D["binance"] or t not in D["bitget"] for t in [t24,t29]):
            obs.append({"date":ds,"status":"EXTERNAL_MISSING"})
            continue

        ext24=(D["binance"][t24]+D["bitget"][t24])/2
        ext29=(D["binance"][t29]+D["bitget"][t29])/2
        mexc29=D["mexc"][t29]
        basis=10000*(mexc29/ext29-1)
        mom=10000*(ext29/ext24-1)
        sideA=-sgn(basis)
        sideB=sgn(mom)

        row={"date":ds,"status":"OK","mexc_1329":mexc29,"ext_1324":ext24,"ext_1329":ext29,
             "basis_bps":basis,"external_momentum_5m_bps":mom}
        for h in horizons:
            px=D["mexc"][t29+h*60]
            rawret=10000*(px/mexc29-1)
            row[f"mexc_raw_ret_{h}m_bps"]=rawret
            if sideA!=0:
                v=sideA*rawret
                famA[h]["vals"].append(v); famA[h]["pred"].append(basis); famA[h]["days"].append(ds)
                row[f"basis_fade_signed_{h}m_bps"]=v
            if sideB!=0:
                v=sideB*rawret
                famB[h]["vals"].append(v); famB[h]["pred"].append(mom); famB[h]["days"].append(ds)
                row[f"extmom_follow_signed_{h}m_bps"]=v
        obs.append(row)

    families={}
    for key,fam,fid in [
      ("cashopen_basis_fade",famA,"MEXC-NVIDIA-CASHOPEN-BASIS-FADE-001"),
      ("cashopen_external_momentum",famB,"MEXC-NVIDIA-CASHOPEN-EXTMOM-FOLLOW-001")
    ]:
        cells=[]
        for h in horizons:
            r=summarize(fam[h]["vals"],fam[h]["pred"])
            cells.append({"horizon_min":h,"eligible":eligible(r),"result":r,"days":fam[h]["days"]})
        selected=holm_all(cells,alpha=0.05)
        families[key]={
          "family_id":fid,
          "cells":cells,
          "pre_holm_eligible_count":sum(x["eligible"] for x in cells),
          "holm_selected_count":len(selected),
          "holm_selected":[{"horizon_min":x["horizon_min"],**x["result"],"holm_cutoff":x["holm_cutoff"]} for x in selected]
        }

    total_selected=sum(v["holm_selected_count"] for v in families.values())
    report={
      "family_pack":RULE["family_pack"],
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(RULE_PATH),
      "binding_sha256":sha_file(BIND_PATH),
      "session_count_frozen":len(sess),
      "session_count_with_complete_signal_data":sum(1 for x in obs if x.get("status")=="OK"),
      "source_hashes":source_hashes,
      "families":families,
      "total_holm_selected":total_selected,
      "verdict":"NVIDIA_CASHOPEN_DISCOVERY_CANDIDATE_FOUND" if total_selected else "NO_NVIDIA_CASHOPEN_DISCOVERY_CANDIDATE_AT_FROZEN_V02_GATE",
      "retrospective_oos_opened":False,
      "post_outcome_tuning_authorized":False,
      "live_trading_authorized":False
    }

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_NVIDIA_CASHOPEN_CLOSEOUT_V02.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    keys=sorted(set(k for r in obs for k in r.keys()))
    with (OUT/"MEXC_NVIDIA_CASHOPEN_SESSION_OBSERVATIONS_V02.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(obs)
    with (OUT/"MEXC_NVIDIA_CASHOPEN_MATRIX_V02.csv").open("w",newline="") as f:
        fields=["family","horizon_min","n","wins","win_rate","mean_gross_signed_bps","median_gross_signed_bps",
                "half1_mean_bps","half2_mean_bps","p_value","eligible","holm_rank","holm_cutoff","holm_reject",
                "mean_net_12bps"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for fname,fam in families.items():
            for x in fam["cells"]:
                r=x["result"]; hs=r["chronological_half_means_bps"]
                w.writerow({
                  "family":fname,"horizon_min":x["horizon_min"],"n":r["n"],"wins":r["wins"],
                  "win_rate":r["win_rate"],"mean_gross_signed_bps":r["mean_gross_signed_bps"],
                  "median_gross_signed_bps":r["median_gross_signed_bps"],
                  "half1_mean_bps":hs[0],"half2_mean_bps":hs[1],
                  "p_value":r["p_value_one_sided_binomial_vs_50"],"eligible":x["eligible"],
                  "holm_rank":x.get("holm_rank"),"holm_cutoff":x.get("holm_cutoff"),"holm_reject":x.get("holm_reject"),
                  "mean_net_12bps":r["cost_scenarios_mean_net_bps"]["12"]
                })

    print(json.dumps({
      "verdict":report["verdict"],
      "complete_sessions":report["session_count_with_complete_signal_data"],
      "basis_fade_pre_holm":families["cashopen_basis_fade"]["pre_holm_eligible_count"],
      "basis_fade_holm_selected":families["cashopen_basis_fade"]["holm_selected"],
      "extmom_pre_holm":families["cashopen_external_momentum"]["pre_holm_eligible_count"],
      "extmom_holm_selected":families["cashopen_external_momentum"]["holm_selected"],
      "retrospective_oos_opened":False,
      "live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
