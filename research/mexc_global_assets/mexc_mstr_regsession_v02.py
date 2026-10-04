#!/usr/bin/env python3
"""MEXC MSTR regular-session V0.2: confirmatory multi-asset rule transfer + exploratory grid."""
from __future__ import annotations
import csv,io,json,math,statistics,time,zipfile,hashlib
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_MSTR_REGSESSION_RULE_V0.2.json"
BIND_PATH=HERE/"MEXC_MSTR_REGSESSION_SOURCE_BINDING_V0.2.json"
RULE=json.loads(RULE_PATH.read_text())
BIND=json.loads(BIND_PATH.read_text())
OUT=Path("artifacts/mexc_global_assets/mstr_regsession_v02")
UA="CryptoLab-MEXC-MSTR-RegSession/0.2"

def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def mean(xs): return sum(xs)/len(xs) if xs else None
def med(xs): return statistics.median(xs) if xs else None
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)
def utcsec(d,h,m): return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())

def sessions():
    a=date.fromisoformat(RULE["discovery_start_date"])
    b=date.fromisoformat(RULE["discovery_end_date_inclusive"])
    excluded={date.fromisoformat(x) for x in RULE["excluded_dates"]}
    out=[]; d=a
    while d<=b:
        if d.weekday()<5 and d not in excluded: out.append(d)
        d+=timedelta(days=1)
    return out

def req(url,params=None,timeout=60,retries=4):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code!=200:
                raise RuntimeError(f"HTTP_{r.status_code}:{r.url}:{r.content[:220]!r}")
            return r
        except Exception as e:
            last=e; time.sleep(.7*(i+1))
    raise last

def fetch_mexc(d):
    a=utcsec(d,14,29); b=utcsec(d,18,59)
    r=req("https://api.mexc.com/api/v1/contract/kline/MSTRSTOCK_USDT",
          {"interval":"Min1","start":str(a),"end":str(b)})
    j=r.json()
    if j.get("success") is not True: raise RuntimeError(f"MEXC_NON_SUCCESS:{d}:{j}")
    z=j.get("data") or {}; out={}
    for t,p in zip(z.get("time") or [],z.get("close") or []):
        try: out[int(t)+60]=float(p)
        except Exception: pass
    return out,sha_bytes(r.content)

def fetch_bitget(d):
    chunks=[(utcsec(d,14,29),utcsec(d,16,44)),(utcsec(d,16,45),utcsec(d,18,59))]
    out={}; hs=[]
    for a,b in chunks:
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
          "symbol":"MSTRUSDT","productType":"USDT-FUTURES","granularity":"1m",
          "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
        hs.append(sha_bytes(r.content)); j=r.json()
        if j.get("code")!="00000": raise RuntimeError(f"BITGET_NON_SUCCESS:{d}:{j}")
        for row in j.get("data") or []:
            try: out[int(row[0])//1000+60]=float(row[4])
            except Exception: pass
        time.sleep(.03)
    return out,hs

def fetch_binance(d):
    day=d.isoformat()
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/MSTRUSDT/1m/MSTRUSDT-1m-{day}.zip",timeout=90)
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)!=1: raise RuntimeError(f"BINANCE_ZIP_IDENTITY:{day}:{names}")
    lo=utcsec(d,14,29); hi=utcsec(d,18,59); out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try: t=int(row[0])//1000; p=float(row[4])
        except Exception: continue
        if lo<=t<=hi: out[t+60]=p
    return out,sha_bytes(r.content)

def binom_tail(w,n):
    if n<=0:return None
    return sum(math.comb(n,k) for k in range(w,n+1))/(2**n)

def thirds(vals):
    n=len(vals)
    if n==0:return [None,None,None]
    cuts=[0,n//3,(2*n)//3,n]
    return [mean(vals[cuts[i]:cuts[i+1]]) for i in range(3)]

def score(all_days,shock,gap,h):
    vals=[]; exts=[]; gaps=[]; times=[]; signal_days=[]
    cooldown=h*60
    for ds,D in all_days.items():
        d=date.fromisoformat(ds)
        start=utcsec(d,14,31); stop=utcsec(d,18,44)
        next_allowed=start
        common=sorted(set(D["mexc"])&set(D["binance"])&set(D["bitget"]))
        for t in common:
            if t<start or t>stop or t<next_allowed: continue
            prev=t-60; ex=t+h*60
            if prev not in D["mexc"] or prev not in D["binance"] or prev not in D["bitget"] or ex not in D["mexc"]: continue
            rb=10000*(D["binance"][t]/D["binance"][prev]-1)
            rg=10000*(D["bitget"][t]/D["bitget"][prev]-1)
            ext=(rb+rg)/2
            mr=10000*(D["mexc"][t]/D["mexc"][prev]-1)
            lg=ext-mr
            if abs(ext)<shock or sgn(lg)!=sgn(ext) or abs(lg)<gap: continue
            gross=sgn(ext)*10000*(D["mexc"][ex]/D["mexc"][t]-1)
            vals.append(gross); exts.append(ext); gaps.append(lg); signal_days.append(ds)
            times.append(f"{ds}T{datetime.fromtimestamp(t,tz=timezone.utc).strftime('%H:%M:%S')}Z")
            next_allowed=t+cooldown
    n=len(vals); wins=sum(x>0 for x in vals)
    return {
      "n":n,"wins":wins,"losses_or_zero":n-wins,
      "win_rate":wins/n if n else None,
      "mean_gross_signed_bps":mean(vals),
      "median_gross_signed_bps":med(vals),
      "chronological_third_means_bps":thirds(vals),
      "p_value_one_sided_binomial_vs_50":binom_tail(wins,n) if n else None,
      "distinct_signal_sessions":len(set(signal_days)),
      "mean_abs_external_shock_bps":mean([abs(x) for x in exts]) if exts else None,
      "mean_abs_lag_gap_bps":mean([abs(x) for x in gaps]) if gaps else None,
      "cost_scenarios_mean_net_bps":{
        str(c):(mean(vals)-float(c) if vals else None)
        for c in RULE["cost_scenarios_roundtrip_bps"]
      },
      "signal_times":times
    }

def confirmatory_pass(r):
    g=RULE["confirmatory_transfer"]["validation_gate"]
    return bool(
      r["n"]>=g["min_n"] and
      r["distinct_signal_sessions"]>=g["min_distinct_signal_sessions"] and
      r["mean_gross_signed_bps"] is not None and r["mean_gross_signed_bps"]>0 and
      r["median_gross_signed_bps"] is not None and r["median_gross_signed_bps"]>0 and
      r["win_rate"] is not None and r["win_rate"]>0.5 and
      all(x is not None and x>0 for x in r["chronological_third_means_bps"]) and
      r["p_value_one_sided_binomial_vs_50"] is not None and
      r["p_value_one_sided_binomial_vs_50"]<g["exact_one_sided_binomial_p_lt"]
    )

def exploratory_eligible(r):
    g=RULE["exploratory_grid"]["discovery_gate"]
    return bool(
      r["n"]>=g["min_n"] and
      r["mean_gross_signed_bps"] is not None and r["mean_gross_signed_bps"]>0 and
      r["median_gross_signed_bps"] is not None and r["median_gross_signed_bps"]>0 and
      r["win_rate"] is not None and r["win_rate"]>0.5 and
      all(x is not None and x>0 for x in r["chronological_third_means_bps"])
    )

def holm(cells,alpha):
    ordered=sorted(cells,key=lambda x:(x["result"]["p_value_one_sided_binomial_vs_50"]
                                       if x["result"]["p_value_one_sided_binomial_vs_50"] is not None else 1.0))
    m=len(ordered); still=True
    for rank,x in enumerate(ordered,1):
        cutoff=alpha/(m-rank+1)
        x["holm_rank"]=rank; x["holm_cutoff"]=cutoff
        p=x["result"]["p_value_one_sided_binomial_vs_50"]
        reject=bool(still and p is not None and p<=cutoff)
        x["holm_reject"]=reject
        if not reject: still=False
    return [x for x in cells if x.get("holm_reject") and x["eligible"]]

def main():
    if RULE.get("outcomes_opened_at_freeze")!=0 or BIND.get("historical_outcomes_opened_at_binding")!=0:
        raise SystemExit("FAIL_CLOSED_NOT_PRE_OUTCOME")
    if BIND.get("source_gate",{}).get("verdict")!="MSTR_REGSESSION_PUBLIC_CORE_SOURCE_PASS":
        raise SystemExit("FAIL_CLOSED_SOURCE_NOT_PASS")
    if RULE["familywise_alpha_budget"]!={"total":0.05,"confirmatory_transfer":0.025,"exploratory_grid":0.025}:
        raise SystemExit("FAIL_CLOSED_ALPHA_BUDGET_CHANGED")

    sess=sessions()
    if len(sess)!=17: raise SystemExit(f"FAIL_CLOSED_EXPECTED_17_SESSIONS_GOT_{len(sess)}")
    all_days={}; hashes={}
    for d in sess:
        m,mh=fetch_mexc(d); b,bh=fetch_binance(d); g,gh=fetch_bitget(d)
        ds=d.isoformat()
        all_days[ds]={"mexc":m,"binance":b,"bitget":g}
        hashes[ds]={"mexc":mh,"binance":bh,"bitget":gh}
        time.sleep(.03)

    exact_common=sum(len(set(D["mexc"])&set(D["binance"])&set(D["bitget"])) for D in all_days.values())
    if exact_common<4000: raise RuntimeError(f"INSUFFICIENT_EXACT_COMMON_MINUTES:{exact_common}")

    # Confirmatory transfer: exact NVDA winner, single predefined cell.
    c=RULE["confirmatory_transfer"]
    transfer=score(all_days,float(c["shock_threshold_bps"]),float(c["lag_gap_threshold_bps"]),int(c["horizon_min"]))
    transfer_pass=confirmatory_pass(transfer)

    # Exploratory grid, separate alpha budget.
    eg=RULE["exploratory_grid"]; cells=[]
    for shock in eg["shock_thresholds_bps"]:
        for gap in eg["lag_gap_thresholds_bps"]:
            for h in eg["horizons_min"]:
                r=score(all_days,float(shock),float(gap),int(h))
                cells.append({"shock_bps":shock,"gap_bps":gap,"horizon_min":h,
                              "eligible":exploratory_eligible(r),"result":r})
    selected=holm(cells,eg["discovery_gate"]["family_wise_alpha"])
    selected_summary=[{
      "shock_bps":x["shock_bps"],"gap_bps":x["gap_bps"],"horizon_min":x["horizon_min"],
      "n":x["result"]["n"],"wins":x["result"]["wins"],"win_rate":x["result"]["win_rate"],
      "mean_gross_bps":x["result"]["mean_gross_signed_bps"],
      "median_gross_bps":x["result"]["median_gross_signed_bps"],
      "p":x["result"]["p_value_one_sided_binomial_vs_50"],
      "holm_cutoff":x["holm_cutoff"],
      "mean_net_12bps":x["result"]["cost_scenarios_mean_net_bps"]["12"]
    } for x in selected]

    if transfer_pass:
        overall="MSTR_FOUR_ASSET_REPLICATION_SURVIVOR"
    elif selected:
        overall="MSTR_EXPLORATORY_DISCOVERY_CANDIDATES_FOUND"
    else:
        overall="NO_MSTR_REGSESSION_CANDIDATE_AT_FROZEN_V02_GATE"

    report={
      "family_pack":RULE["family_pack"],"generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(RULE_PATH),"binding_sha256":sha_file(BIND_PATH),
      "sessions":len(sess),"exact_common_minutes":exact_common,
      "confirmatory_transfer":{
        "family_id":c["family_id"],"result":transfer,"pass":transfer_pass,
        "alpha":RULE["familywise_alpha_budget"]["confirmatory_transfer"],
        "verdict":c["promotion_if_pass"] if transfer_pass else "CROSS_ASSET_TRANSFER_FAIL"
      },
      "exploratory_grid":{
        "family_id":eg["family_id"],"pre_holm_eligible_count":sum(x["eligible"] for x in cells),
        "holm_selected_count":len(selected),"holm_selected":selected_summary,"cells":cells,
        "alpha":RULE["familywise_alpha_budget"]["exploratory_grid"]
      },
      "verdict":overall,
      "retrospective_oos_opened":False,"post_outcome_tuning_authorized":False,
      "orders":False,"account_reads":False,"private_endpoints_used":False,
      "exchange_mutation":False,"live_trading_authorized":False,"source_hashes":hashes
    }

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_MSTR_REGSESSION_CLOSEOUT_V02.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    with (OUT/"MEXC_MSTR_REGSESSION_MATRIX_V02.csv").open("w",newline="") as f:
        fields=["shock_bps","gap_bps","horizon_min","n","wins","win_rate","mean_gross_bps","median_gross_bps",
                "third1","third2","third3","p_value","eligible","holm_rank","holm_cutoff","holm_reject","mean_net_12bps"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for x in cells:
            r=x["result"]; tr=r["chronological_third_means_bps"]
            w.writerow({
              "shock_bps":x["shock_bps"],"gap_bps":x["gap_bps"],"horizon_min":x["horizon_min"],
              "n":r["n"],"wins":r["wins"],"win_rate":r["win_rate"],
              "mean_gross_bps":r["mean_gross_signed_bps"],"median_gross_bps":r["median_gross_signed_bps"],
              "third1":tr[0],"third2":tr[1],"third3":tr[2],
              "p_value":r["p_value_one_sided_binomial_vs_50"],"eligible":x["eligible"],
              "holm_rank":x.get("holm_rank"),"holm_cutoff":x.get("holm_cutoff"),"holm_reject":x.get("holm_reject"),
              "mean_net_12bps":r["cost_scenarios_mean_net_bps"]["12"]
            })

    top=sorted(cells,key=lambda x:(x["result"]["p_value_one_sided_binomial_vs_50"]
                                   if x["result"]["p_value_one_sided_binomial_vs_50"] is not None else 1.0))[:8]
    print(json.dumps({
      "verdict":overall,"sessions":len(sess),"exact_common_minutes":exact_common,
      "transfer":{
        "pass":transfer_pass,"n":transfer["n"],"sessions":transfer["distinct_signal_sessions"],
        "wins":transfer["wins"],"win_rate":transfer["win_rate"],
        "mean":transfer["mean_gross_signed_bps"],"median":transfer["median_gross_signed_bps"],
        "thirds":transfer["chronological_third_means_bps"],
        "p":transfer["p_value_one_sided_binomial_vs_50"],
        "mean_net_12bps":transfer["cost_scenarios_mean_net_bps"]["12"]
      },
      "exploratory_pre_holm":report["exploratory_grid"]["pre_holm_eligible_count"],
      "exploratory_holm_selected":selected_summary,
      "top_by_p":[{
        "shock":x["shock_bps"],"gap":x["gap_bps"],"h":x["horizon_min"],
        "n":x["result"]["n"],"wins":x["result"]["wins"],
        "mean":x["result"]["mean_gross_signed_bps"],
        "median":x["result"]["median_gross_signed_bps"],
        "p":x["result"]["p_value_one_sided_binomial_vs_50"],
        "eligible":x["eligible"],"holm_cutoff":x.get("holm_cutoff")
      } for x in top],
      "retrospective_oos_opened":False,"live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
