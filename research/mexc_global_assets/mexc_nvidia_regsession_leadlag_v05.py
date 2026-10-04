#!/usr/bin/env python3
"""MEXC-NVIDIA-REGSESSION-LEADLAG-001 V0.5 frozen discovery."""
from __future__ import annotations
import csv, io, json, math, statistics, time, zipfile, hashlib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_NVIDIA_REGSESSION_LEADLAG_RULE_V0.5.json"
BIND_PATH=HERE/"MEXC_NVIDIA_REGSESSION_SOURCE_BINDING_V0.5.json"
RULE=json.loads(RULE_PATH.read_text())
BIND=json.loads(BIND_PATH.read_text())
OUT=Path("artifacts/mexc_global_assets/nvidia_regsession_leadlag_v05")
UA="CryptoLab-MEXC-NVIDIA-RegSession/0.5"

def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def mean(xs): return sum(xs)/len(xs) if xs else None
def median(xs): return statistics.median(xs) if xs else None
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)

def sessions():
    a=date.fromisoformat(RULE["discovery_start_date"])
    b=date.fromisoformat(RULE["discovery_end_date_inclusive"])
    excluded={date.fromisoformat(x) for x in RULE["excluded_dates"]}
    d=a; out=[]
    while d<=b:
        if d.weekday()<5 and d not in excluded: out.append(d)
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
    s=utcsec(d,14,29); e=utcsec(d,18,59)
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
    chunks=[
      (utcsec(d,14,29),utcsec(d,16,44)),
      (utcsec(d,16,45),utcsec(d,18,59))
    ]
    out={}; hashes=[]
    for a,b in chunks:
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
          "symbol":"NVDAUSDT","productType":"USDT-FUTURES","granularity":"1m",
          "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"
        })
        hashes.append(sha_bytes(r.content))
        j=r.json()
        if j.get("code")!="00000":
            raise RuntimeError(f"BITGET_NON_SUCCESS:{d}:{j}")
        for row in j.get("data") or []:
            try: out[int(row[0])//1000+60]=float(row[4])
            except Exception: pass
        time.sleep(0.04)
    return out,hashes

def fetch_binance(d):
    day=d.isoformat()
    url=f"https://data.binance.vision/data/futures/um/daily/klines/NVDAUSDT/1m/NVDAUSDT-1m-{day}.zip"
    r=req(url,timeout=90)
    z=zipfile.ZipFile(io.BytesIO(r.content))
    names=z.namelist()
    if len(names)!=1: raise RuntimeError(f"BINANCE_ZIP_IDENTITY:{day}:{names}")
    lo=utcsec(d,14,29); hi=utcsec(d,18,59)
    out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try:
            raw=int(row[0])//1000; px=float(row[4])
        except Exception:
            continue
        if lo<=raw<=hi: out[raw+60]=px
    return out,sha_bytes(r.content)

def binom_tail_half(w,n):
    if n<=0:return None
    return sum(math.comb(n,k) for k in range(w,n+1))/(2**n)

def thirds(vals):
    n=len(vals)
    if n==0:return [None,None,None]
    cuts=[0,n//3,(2*n)//3,n]
    return [mean(vals[cuts[i]:cuts[i+1]]) for i in range(3)]

def summarize(vals,exts,gaps):
    n=len(vals); wins=sum(x>0 for x in vals)
    return {
      "n":n,"wins":wins,"losses_or_zero":n-wins,
      "win_rate":wins/n if n else None,
      "mean_gross_signed_bps":mean(vals),
      "median_gross_signed_bps":median(vals),
      "chronological_third_means_bps":thirds(vals),
      "p_value_one_sided_binomial_vs_50":binom_tail_half(wins,n) if n else None,
      "mean_abs_external_shock_bps":mean([abs(x) for x in exts]) if exts else None,
      "mean_abs_lag_gap_bps":mean([abs(x) for x in gaps]) if gaps else None,
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
      all(x is not None and x>0 for x in r["chronological_third_means_bps"])
    )

def holm_all(cells,alpha=0.05):
    ordered=sorted(cells,key=lambda x:(x["result"]["p_value_one_sided_binomial_vs_50"] if x["result"]["p_value_one_sided_binomial_vs_50"] is not None else 1.0))
    m=len(ordered); still=True
    for rank,x in enumerate(ordered,1):
        cutoff=alpha/(m-rank+1)
        x["holm_rank"]=rank; x["holm_cutoff"]=cutoff
        p=x["result"]["p_value_one_sided_binomial_vs_50"]
        passed=bool(still and p is not None and p<=cutoff)
        x["holm_reject"]=passed
        if not passed: still=False
    return [x for x in cells if x.get("holm_reject") and x["eligible"]]

def score(all_days,shock,gap,hmin):
    vals=[]; exts=[]; gaps=[]; times=[]
    cooldown=hmin*60
    for ds,D in all_days.items():
        d=date.fromisoformat(ds)
        start=utcsec(d,14,31); stop=utcsec(d,18,44)
        next_allowed=start
        common=sorted(set(D["mexc"]) & set(D["binance"]) & set(D["bitget"]))
        for t in common:
            if t<start or t>stop or t<next_allowed: continue
            prev=t-60; exit_t=t+hmin*60
            if prev not in D["mexc"] or prev not in D["binance"] or prev not in D["bitget"]: continue
            if exit_t not in D["mexc"]: continue
            rb=10000*(D["binance"][t]/D["binance"][prev]-1)
            rg=10000*(D["bitget"][t]/D["bitget"][prev]-1)
            ext=(rb+rg)/2
            mr=10000*(D["mexc"][t]/D["mexc"][prev]-1)
            lag=ext-mr
            if abs(ext)<shock: continue
            if sgn(lag)!=sgn(ext): continue
            if abs(lag)<gap: continue
            side=sgn(ext)
            gross=side*10000*(D["mexc"][exit_t]/D["mexc"][t]-1)
            vals.append(gross); exts.append(ext); gaps.append(lag); times.append(f"{ds}T{datetime.fromtimestamp(t,tz=timezone.utc).strftime('%H:%M:%S')}Z")
            next_allowed=t+cooldown
    return summarize(vals,exts,gaps),times

def main():
    if RULE.get("outcomes_opened_at_freeze")!=0:
        raise SystemExit("FAIL_CLOSED: rule not pre-outcome")
    if BIND.get("historical_outcomes_opened_at_binding")!=0:
        raise SystemExit("FAIL_CLOSED: binding not pre-outcome")
    if BIND.get("source_gate",{}).get("verdict")!="NVIDIA_REGSESSION_SOURCE_PASS":
        raise SystemExit("FAIL_CLOSED: source gate not PASS")

    sess=sessions()
    if len(sess)!=17:
        raise SystemExit(f"FAIL_CLOSED: expected 17 sessions, got {len(sess)}")

    all_days={}; hashes={}
    for d in sess:
        m,mh=fetch_mexc(d); b,bh=fetch_binance(d); g,gh=fetch_bitget(d)
        ds=d.isoformat()
        all_days[ds]={"mexc":m,"binance":b,"bitget":g}
        hashes[ds]={"mexc":mh,"binance":bh,"bitget":gh}
        time.sleep(0.04)

    exact_common=sum(len(set(D["mexc"]) & set(D["binance"]) & set(D["bitget"])) for D in all_days.values())
    if exact_common<4000:
        raise RuntimeError(f"INSUFFICIENT_EXACT_COMMON_MINUTES:{exact_common}")

    cells=[]
    for shock in RULE["signal"]["shock_thresholds_bps"]:
        for gap in RULE["signal"]["lag_gap_thresholds_bps"]:
            for h in RULE["signal"]["horizons_min"]:
                r,times=score(all_days,float(shock),float(gap),int(h))
                cells.append({"shock_bps":shock,"gap_bps":gap,"horizon_min":h,
                              "eligible":eligible(r),"result":r,"signal_times":times})
    selected=holm_all(cells,RULE["discovery_gate"]["family_wise_alpha"])

    selected_summary=[
      {"shock_bps":x["shock_bps"],"gap_bps":x["gap_bps"],"horizon_min":x["horizon_min"],
       "n":x["result"]["n"],"wins":x["result"]["wins"],"win_rate":x["result"]["win_rate"],
       "mean_gross_bps":x["result"]["mean_gross_signed_bps"],
       "median_gross_bps":x["result"]["median_gross_signed_bps"],
       "p":x["result"]["p_value_one_sided_binomial_vs_50"],
       "holm_cutoff":x["holm_cutoff"],
       "mean_net_12bps":x["result"]["cost_scenarios_mean_net_bps"]["12"]}
      for x in selected
    ]

    report={
      "family_id":RULE["family_id"],"version":RULE["version"],
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(RULE_PATH),"binding_sha256":sha_file(BIND_PATH),
      "session_count":len(sess),"exact_common_minutes_all_downloaded_windows":exact_common,
      "source_hashes":hashes,"cells":cells,
      "pre_holm_eligible_count":sum(x["eligible"] for x in cells),
      "holm_selected_count":len(selected),"holm_selected":selected_summary,
      "verdict":"NVIDIA_REGSESSION_DISCOVERY_CANDIDATES_FOUND" if selected else "NO_NVIDIA_REGSESSION_DISCOVERY_CANDIDATE_AT_FROZEN_V05_GATE",
      "retrospective_oos_opened":False,"post_outcome_tuning_authorized":False,"live_trading_authorized":False
    }

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_NVIDIA_REGSESSION_LEADLAG_CLOSEOUT_V05.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    with (OUT/"MEXC_NVIDIA_REGSESSION_LEADLAG_MATRIX_V05.csv").open("w",newline="") as f:
        fields=["shock_bps","gap_bps","horizon_min","n","wins","win_rate","mean_gross_bps","median_gross_bps",
                "third1_mean_bps","third2_mean_bps","third3_mean_bps","p_value","eligible",
                "holm_rank","holm_cutoff","holm_reject","mean_net_12bps"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for x in cells:
            r=x["result"]; tr=r["chronological_third_means_bps"]
            w.writerow({
              "shock_bps":x["shock_bps"],"gap_bps":x["gap_bps"],"horizon_min":x["horizon_min"],
              "n":r["n"],"wins":r["wins"],"win_rate":r["win_rate"],
              "mean_gross_bps":r["mean_gross_signed_bps"],"median_gross_bps":r["median_gross_signed_bps"],
              "third1_mean_bps":tr[0],"third2_mean_bps":tr[1],"third3_mean_bps":tr[2],
              "p_value":r["p_value_one_sided_binomial_vs_50"],"eligible":x["eligible"],
              "holm_rank":x.get("holm_rank"),"holm_cutoff":x.get("holm_cutoff"),"holm_reject":x.get("holm_reject"),
              "mean_net_12bps":r["cost_scenarios_mean_net_bps"]["12"]
            })

    top=sorted(cells,key=lambda x:(x["result"]["p_value_one_sided_binomial_vs_50"] if x["result"]["p_value_one_sided_binomial_vs_50"] is not None else 1.0))[:8]
    print(json.dumps({
      "verdict":report["verdict"],"sessions":len(sess),"exact_common_minutes":exact_common,
      "pre_holm_eligible_count":report["pre_holm_eligible_count"],
      "holm_selected_count":len(selected),"selected":selected_summary,
      "top_by_p":[{"shock":x["shock_bps"],"gap":x["gap_bps"],"h":x["horizon_min"],
                   "n":x["result"]["n"],"wins":x["result"]["wins"],
                   "mean":x["result"]["mean_gross_signed_bps"],
                   "median":x["result"]["median_gross_signed_bps"],
                   "p":x["result"]["p_value_one_sided_binomial_vs_50"],
                   "eligible":x["eligible"],"holm_cutoff":x.get("holm_cutoff")} for x in top],
      "retrospective_oos_opened":False,"live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
