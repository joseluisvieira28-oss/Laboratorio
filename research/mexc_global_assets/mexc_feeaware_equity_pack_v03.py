#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,math,statistics,time,zipfile,hashlib
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_FEEAWARE_EQUITY_PACK_RULE_V0.3.json"
BIND_PATH=HERE/"MEXC_FEEAWARE_EQUITY_PACK_BINDING_V0.3.json"
RULE=json.loads(RULE_PATH.read_text()); BIND=json.loads(BIND_PATH.read_text())
OUT=Path("artifacts/mexc_global_assets/feeaware_equity_pack_v03")
UA="CryptoLab-MEXC-FeeAware-Equity-Pack/0.3"

def shaf(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def shab(b): return hashlib.sha256(b).hexdigest()
def mean(x): return sum(x)/len(x) if x else None
def med(x): return statistics.median(x) if x else None
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)
def ts(d,h,m): return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())

def sessions():
    a=date.fromisoformat(RULE["sample_start_date"]); b=date.fromisoformat(RULE["sample_end_date_inclusive"])
    ex={date.fromisoformat(x) for x in RULE["excluded_dates"]}; out=[]; d=a
    while d<=b:
        if d.weekday()<5 and d not in ex: out.append(d)
        d+=timedelta(days=1)
    return out

def req(u,p=None,t=60,retries=4):
    last=None
    for i in range(retries):
        try:
            r=requests.get(u,params=p,headers={"User-Agent":UA},timeout=t)
            if r.status_code!=200: raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
            return r
        except Exception as e:
            last=e; time.sleep(.7*(i+1))
    raise last

def fetch_mexc(d,sym):
    r=req(f"https://api.mexc.com/api/v1/contract/kline/{sym}",
          {"interval":"Min1","start":str(ts(d,14,29)),"end":str(ts(d,18,59))})
    j=r.json()
    if j.get("success") is not True: raise RuntimeError(f"MEXC:{sym}:{d}:{j}")
    out={}; z=j.get("data") or {}
    for t,p in zip(z.get("time") or [],z.get("close") or []):
        try: out[int(t)+60]=float(p)
        except Exception: pass
    return out,shab(r.content)

def fetch_bitget(d,sym):
    out={}; hs=[]
    for a,b in [(ts(d,14,29),ts(d,16,44)),(ts(d,16,45),ts(d,18,59))]:
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",
              {"symbol":sym,"productType":"USDT-FUTURES","granularity":"1m",
               "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
        hs.append(shab(r.content)); j=r.json()
        if j.get("code")!="00000": raise RuntimeError(f"BITGET:{sym}:{d}:{j}")
        for row in j.get("data") or []:
            try: out[int(row[0])//1000+60]=float(row[4])
            except Exception: pass
    return out,hs

def fetch_binance(d,sym):
    day=d.isoformat()
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{sym}/1m/{sym}-1m-{day}.zip",t=90)
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)!=1: raise RuntimeError(f"BINANCE_ID:{sym}:{day}:{names}")
    out={}; lo=ts(d,14,29); hi=ts(d,18,59)
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try: t=int(row[0])//1000; p=float(row[4])
        except Exception: continue
        if lo<=t<=hi: out[t+60]=p
    return out,shab(r.content)

def binom(w,n):
    return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None

def thirds(vals):
    if not vals: return [None,None,None]
    n=len(vals); cuts=[0,n//3,(2*n)//3,n]
    return [mean(vals[cuts[i]:cuts[i+1]]) for i in range(3)]

def evaluate(ticker,cfg,sess):
    vals=[]; events=[]; hashes={}; common_total=0
    for d in sess:
        m,mh=fetch_mexc(d,cfg["target"])
        b,bh=fetch_binance(d,cfg["external"])
        g,gh=fetch_bitget(d,cfg["external"])
        ds=d.isoformat(); hashes[ds]={"mexc":mh,"binance":bh,"bitget":gh}
        common=set(m)&set(b)&set(g); common_total+=len(common); nxt=ts(d,14,31)
        for t in sorted(common):
            if t<ts(d,14,31) or t>ts(d,18,44) or t<nxt: continue
            p=t-60; x=t+60
            if p not in m or p not in b or p not in g or x not in m: continue
            ext=(10000*(b[t]/b[p]-1)+10000*(g[t]/g[p]-1))/2
            mr=10000*(m[t]/m[p]-1); gap=ext-mr
            if abs(ext)<20 or sgn(gap)!=sgn(ext) or abs(gap)<10: continue
            gross=sgn(ext)*10000*(m[x]/m[t]-1)
            vals.append(gross)
            events.append({"date":ds,"t_utc":datetime.fromtimestamp(t,tz=timezone.utc).isoformat(),
                           "external_return_bps":ext,"lag_gap_bps":gap,"gross_signed_bps":gross})
            nxt=t+60
        time.sleep(.03)
    n=len(vals); wins=sum(x>0 for x in vals); days=len(set(e["date"] for e in events))
    pval=binom(wins,n); tr=thirds(vals); sg=RULE["scientific_gate"]; eg=RULE["execution_scale_gate"]
    eligible=bool(
        n>=sg["min_n"] and days>=sg["min_distinct_signal_sessions"] and
        mean(vals) is not None and mean(vals)>0 and
        med(vals) is not None and med(vals)>0 and
        wins/n>0.5 and all(x is not None and x>0 for x in tr)
    )
    scale=bool(
        mean(vals) is not None and med(vals) is not None and
        mean(vals)>eg["mean_gross_signed_bps_gt"] and
        med(vals)>eg["median_gross_signed_bps_gt"]
    )
    return {
        "ticker":ticker,"target":cfg["target"],"external":cfg["external"],
        "sessions":len(sess),"exact_common_minutes":common_total,
        "n":n,"distinct_signal_sessions":days,"wins":wins,
        "win_rate":wins/n if n else None,
        "mean_gross_bps":mean(vals),"median_gross_bps":med(vals),
        "chronological_third_means_bps":tr,
        "p_value_one_sided_binomial_vs_50":pval,
        "scientific_eligible_pre_holm":eligible,
        "execution_scale_raw_pass":scale,
        "cost_scenarios_mean_net_bps":{str(c):(mean(vals)-c if vals else None) for c in RULE["cost_scenarios_roundtrip_bps"]},
        "events":events,"source_hashes":hashes
    }

def apply_holm(results):
    items=sorted(results.items(),key=lambda kv:(kv[1]["p_value_one_sided_binomial_vs_50"] if kv[1]["p_value_one_sided_binomial_vs_50"] is not None else 1.0))
    m=len(items); active=True
    for rank,(ticker,r) in enumerate(items,1):
        cutoff=RULE["scientific_gate"]["family_wise_alpha"]/(m-rank+1)
        p=r["p_value_one_sided_binomial_vs_50"]
        reject=bool(active and p is not None and p<=cutoff)
        r["holm_rank"]=rank; r["holm_cutoff"]=cutoff; r["holm_reject"]=reject
        if not reject: active=False
    for ticker,r in results.items():
        r["scientific_pass"]=bool(r["scientific_eligible_pre_holm"] and r["holm_reject"])
        r["execution_scale_pass"]=bool(r["scientific_pass"] and r["execution_scale_raw_pass"])
        if r["execution_scale_pass"]:
            r["classification"]=RULE["promotion_if_science_and_scale"]
        elif r["scientific_pass"]:
            r["classification"]=RULE["science_only_classification"]
        elif r["n"]<RULE["scientific_gate"]["min_n"] or r["distinct_signal_sessions"]<RULE["scientific_gate"]["min_distinct_signal_sessions"]:
            r["classification"]=RULE["underpowered_classification"]
        else:
            r["classification"]=RULE["fail_classification"]

def main():
    if RULE["outcomes_opened_at_freeze"]!=0 or BIND["historical_outcomes_opened_at_binding"]!=0:
        raise SystemExit("FAIL_CLOSED_NOT_PRE_OUTCOME")
    if not RULE["evaluate_all_assets_regardless_of_earlier_result"]:
        raise SystemExit("FAIL_CLOSED_STOPPING_RULE_CHANGED")
    c=RULE["frozen_cell"]
    if [c["shock_threshold_bps"],c["lag_gap_threshold_bps"],c["horizon_min"]] != [20,10,1]:
        raise SystemExit("FAIL_CLOSED_CELL_CHANGED")
    sess=sessions()
    if len(sess)!=17: raise SystemExit(f"EXPECTED_17_SESSIONS_GOT_{len(sess)}")
    results={}
    for ticker in ["NFLX","BABA","GOOGL","ORCL"]:
        results[ticker]=evaluate(ticker,RULE["assets"][ticker],sess)
    apply_holm(results)
    science=sum(r["scientific_pass"] for r in results.values())
    scale=sum(r["execution_scale_pass"] for r in results.values())
    report={
        "study_id":RULE["study_id"],"generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "rule_sha256":shaf(RULE_PATH),"binding_sha256":shaf(BIND_PATH),
        "results":results,"scientific_survivor_count":science,
        "execution_scale_survivor_count":scale,
        "verdict":"FEEAWARE_EXECUTION_SCALE_CANDIDATE_FOUND" if scale else
                  ("FEEAWARE_SCIENTIFIC_SURVIVOR_ONLY" if science else "NO_FEEAWARE_SURVIVOR_AT_FROZEN_V03_GATE"),
        "live_trading_authorized":False
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_FEEAWARE_EQUITY_PACK_CLOSEOUT_V03.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    slim={k:{x:v[x] for x in ["n","distinct_signal_sessions","wins","win_rate","mean_gross_bps","median_gross_bps",
        "chronological_third_means_bps","p_value_one_sided_binomial_vs_50","scientific_eligible_pre_holm",
        "holm_rank","holm_cutoff","holm_reject","scientific_pass","execution_scale_pass","classification"]} for k,v in results.items()}
    print(json.dumps({"verdict":report["verdict"],"scientific_survivor_count":science,
                      "execution_scale_survivor_count":scale,"results":slim},indent=2,sort_keys=True))

if __name__=="__main__": main()
