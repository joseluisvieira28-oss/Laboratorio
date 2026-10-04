#!/usr/bin/env python3
"""
MEXC-WTI-EVENT-SHOCK-001 V1.3

Frozen EIA WPSR event study:
Discovery -> Holm-Bonferroni -> September retrospective OOS.

Public/no-auth MEXC market data only.
No accounts, credentials, wallets, orders, exchange mutation or live trading.
"""
from __future__ import annotations
import csv, hashlib, json, math, os, time
from datetime import datetime, timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_WTI_EVENT_SHOCK_RULE_V1.3.json"
RULE=json.loads(RULE_PATH.read_text(encoding="utf-8"))

BASE="https://api.mexc.com"
UA="CryptoLab-MEXC-WTI-EIA-EventShock/1.3"
STEP=60
OUT=Path("artifacts/mexc_global_assets/mexc_wti_event_shock_v13")
RAW=OUT/"raw"

def ts(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

def iso(t):
    return datetime.fromtimestamp(t,tz=timezone.utc).isoformat().replace("+00:00","Z")

DISC=[ts(x) for x in RULE["discovery_events_utc"]]
OOS=[ts(x) for x in RULE["oos_events_utc"]]
ALL=DISC+OOS
HARD=ts(RULE["protected_after_utc"])

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save_raw(seq,raw,meta):
    RAW.mkdir(parents=True,exist_ok=True)
    p=RAW/f"mexc_event_{seq:03d}.json"
    p.write_bytes(raw)
    (RAW/f"mexc_event_{seq:03d}.meta.json").write_text(
        json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def get(params,retries=5):
    url=BASE+f"/api/v1/contract/kline/{RULE['mexc_symbol']}"
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
            raw=r.content
            if r.status_code!=200:
                raise RuntimeError(f"HTTP_{r.status_code}:{r.url}:{raw[:300]!r}")
            j=r.json()
            if not isinstance(j,dict) or j.get("success") is not True:
                raise RuntimeError(f"MEXC_NON_SUCCESS:{j}")
            return raw,j,r.url
        except Exception as e:
            last=e
            time.sleep(0.8*(i+1))
    raise last

def fetch_event(t0,seq):
    # Need raw starts T0 through T0+65m inclusive.
    start=t0
    end=t0+65*STEP
    # Last close becomes observable at end+60.
    if end+STEP>=HARD:
        raise RuntimeError(f"PROTECTED_BOUNDARY_REQUEST:{iso(t0)}")
    raw,j,url=get({"interval":"Min1","start":start,"end":end})
    meta={
      "event_t0_utc":iso(t0),
      "url":url,
      "requested_raw_start":start,
      "requested_raw_end":end,
      "captured_at_utc":datetime.now(timezone.utc).isoformat(),
      "sha256":sha_bytes(raw),
      "bytes":len(raw)
    }
    save_raw(seq,raw,meta)
    d=j.get("data") or {}
    times=d.get("time") or []
    opens=d.get("open") or []
    closes=d.get("close") or []
    if not (len(times)==len(opens)==len(closes)):
        raise RuntimeError(f"KLINE_LENGTH_MISMATCH:{iso(t0)}")
    raw_open={}
    close_obs={}
    for s,o,c in zip(times,opens,closes):
        try:
            s=int(s); op=float(o); cp=float(c)
        except Exception:
            continue
        if s<start or s>end:
            raise RuntimeError(f"TIMESTAMP_OUTSIDE_REQUEST:{iso(t0)}:{s}")
        obs=s+STEP
        if obs>=HARD:
            raise RuntimeError(f"PROTECTED_OBSERVABLE_TIMESTAMP:{iso(t0)}:{obs}")
        if op>0 and cp>0:
            raw_open[s]=op
            close_obs[obs]=cp

    required_raw={t0,t0+6*STEP}
    required_obs={t0+5*STEP}
    for h in RULE["horizons_min"]:
        required_obs.add(t0+(6+int(h))*STEP)

    missing_raw=sorted(x for x in required_raw if x not in raw_open)
    missing_obs=sorted(x for x in required_obs if x not in close_obs)
    usable=not missing_raw and not missing_obs
    return {
      "t0":t0,
      "raw_open":raw_open,
      "close_obs":close_obs,
      "usable":usable,
      "missing_raw":missing_raw,
      "missing_obs":missing_obs,
      "rows":len(raw_open),
      "raw_sha256":meta["sha256"]
    }

def mean(xs): return sum(xs)/len(xs) if xs else None

def median(xs):
    if not xs:return None
    y=sorted(xs); n=len(y)
    return y[n//2] if n%2 else (y[n//2-1]+y[n//2])/2

def thirds(xs):
    n=len(xs)
    if n==0:return [None,None,None]
    cuts=[0,n//3,(2*n)//3,n]
    return [mean(xs[cuts[i]:cuts[i+1]]) for i in range(3)]

def halves(xs):
    n=len(xs)
    if n==0:return [None,None]
    m=n//2
    return [mean(xs[:m]),mean(xs[m:])] if m else [None,mean(xs)]

def logsumexp(xs):
    m=max(xs)
    return m+math.log(sum(math.exp(x-m) for x in xs))

def binom_tail_half(w,n):
    if n<=0:return None
    ln2=math.log(2.0)
    logs=[
      math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)-n*ln2
      for k in range(w,n+1)
    ]
    return min(1.0,math.exp(logsumexp(logs)))

def event_shock(e):
    t0=e["t0"]
    open0=e["raw_open"][t0]
    close5=e["close_obs"][t0+5*STEP]
    return 10000.0*(close5/open0-1.0)

def score(events,threshold,mode,horizon):
    vals=[]; shocks=[]; obs=[]
    for e in events:
        if not e["usable"]:
            continue
        t0=e["t0"]
        shock=event_shock(e)
        if shock==0:
            continue
        if abs(shock)<threshold:
            continue
        direction=1 if shock>0 else -1
        side=direction if mode=="CONTINUATION" else -direction
        entry_t=t0+6*STEP
        entry=e["raw_open"][entry_t]
        exit_obs=t0+(6+horizon)*STEP
        exit_px=e["close_obs"][exit_obs]
        gross=side*10000.0*(exit_px/entry-1.0)
        vals.append(gross); shocks.append(shock)
        obs.append({
          "event_t0_utc":iso(t0),
          "shock_bps":shock,
          "side":"LONG" if side>0 else "SHORT",
          "entry_t_utc":iso(entry_t),
          "exit_observable_utc":iso(exit_obs),
          "gross_bps":gross
        })
    n=len(vals); wins=sum(x>0 for x in vals); mg=mean(vals)
    return {
      "n":n,"wins":wins,"losses":n-wins,
      "win_rate":wins/n if n else None,
      "mean_gross_bps":mg,
      "median_gross_bps":median(vals),
      "p_value_vs_50":binom_tail_half(wins,n) if n else None,
      "third_means_gross_bps":thirds(vals),
      "half_means_gross_bps":halves(vals),
      "mean_abs_shock_bps":mean([abs(x) for x in shocks]),
      "median_abs_shock_bps":median([abs(x) for x in shocks]),
      "economic_hurdles_cleared":{
        str(c):(mg>float(c) if mg is not None else False)
        for c in RULE["economic_hurdles_roundtrip_bps"]
      },
      "cost_scenarios_mean_net_bps":{
        str(c):(mg-float(c) if mg is not None else None)
        for c in RULE["cost_scenarios_roundtrip_bps"]
      },
      "observations":obs
    }

def discovery_eligible(r):
    g=RULE["discovery_gate"]
    return (
      r["n"]>=g["min_n"]
      and r["mean_gross_bps"] is not None and r["mean_gross_bps"]>0
      and r["win_rate"] is not None and r["win_rate"]>0.5
      and r["p_value_vs_50"] is not None
      and all(x is not None and x>0 for x in r["third_means_gross_bps"])
    )

def oos_pass(r):
    g=RULE["oos_gate"]
    return (
      r["n"]>=g["min_n"]
      and r["mean_gross_bps"] is not None and r["mean_gross_bps"]>0
      and r["win_rate"] is not None and r["win_rate"]>0.5
      and r["p_value_vs_50"] is not None
      and r["p_value_vs_50"]<g["exact_one_sided_binomial_p_lt"]
      and all(x is not None and x>=0 for x in r["half_means_gross_bps"])
    )

def holm(cells):
    eligible=[x for x in cells if x["eligible"]]
    eligible.sort(key=lambda x:x["discovery"]["p_value_vs_50"])
    m=len(eligible); selected=[]
    for rank,x in enumerate(eligible,1):
        cutoff=RULE["discovery_gate"]["family_wise_alpha"]/(m-rank+1)
        x["holm_cutoff"]=cutoff
        if x["discovery"]["p_value_vs_50"]<=cutoff:
            selected.append(x)
        else:
            break
    return selected,m

def compact(r):
    x=dict(r); x.pop("observations",None); return x

def main():
    forbidden={"MEXC_API_KEY","MEXC_SECRET_KEY","API_KEY","SECRET_KEY","PRIVATE_KEY"}
    if any(k.upper() in forbidden for k in os.environ):
        raise SystemExit("FAIL_CLOSED:CREDENTIAL_LIKE_ENV_DETECTED")
    if RULE.get("source_gate")!="MEXC_WTI_EIA_SOURCE_PASS":
        raise SystemExit("FAIL_CLOSED:SOURCE_GATE_NOT_PASS")
    if RULE.get("outcomes_opened_at_freeze")!=0:
        raise SystemExit("FAIL_CLOSED:FREEZE_INVALID")
    if RULE.get("parameter_rescue_authorized") is not False:
        raise SystemExit("FAIL_CLOSED:RESCUE_FLAG_INVALID")
    if RULE.get("live_trading_authorized") is not False:
        raise SystemExit("FAIL_CLOSED:LIVE_FLAG_INVALID")

    OUT.mkdir(parents=True,exist_ok=True)
    print("RULE_SHA256=",sha_file(RULE_PATH))
    print("EVENTS_TOTAL=",len(ALL))
    print("DISCOVERY_EVENTS=",len(DISC))
    print("OOS_EVENTS=",len(OOS))
    print("HARD_BOUNDARY=",RULE["protected_after_utc"])

    fetched=[]
    for i,t0 in enumerate(ALL,1):
        fetched.append(fetch_event(t0,i))
        time.sleep(0.04)

    disc_events=[e for e in fetched if e["t0"] in set(DISC)]
    oos_events=[e for e in fetched if e["t0"] in set(OOS)]

    bad=[{
      "event_t0_utc":iso(e["t0"]),
      "rows":e["rows"],
      "missing_raw":[iso(x) for x in e["missing_raw"]],
      "missing_obs":[iso(x) for x in e["missing_obs"]]
    } for e in fetched if not e["usable"]]

    coverage={
      "total_events":len(fetched),
      "usable_events":sum(e["usable"] for e in fetched),
      "discovery_usable":sum(e["usable"] for e in disc_events),
      "oos_usable":sum(e["usable"] for e in oos_events),
      "bad_events":bad,
      "first_event":iso(min(ALL)),
      "last_event":iso(max(ALL))
    }
    print(json.dumps({"SOURCE_COVERAGE_ONLY":True,"SCORING_NOT_YET_STARTED":True,**coverage},indent=2,sort_keys=True))

    if coverage["discovery_usable"]!=len(DISC) or coverage["oos_usable"]!=len(OOS):
        raise RuntimeError("EVENT_WINDOW_COVERAGE_INCOMPLETE")

    cells=[]
    for th in RULE["shock_thresholds_bps"]:
        for mode in RULE["modes"]:
            for h in RULE["horizons_min"]:
                r=score(disc_events,float(th),mode,int(h))
                cells.append({
                  "threshold_bps":th,"mode":mode,"horizon_min":h,
                  "eligible":discovery_eligible(r),
                  "discovery":compact(r)
                })

    selected,pre_holm=holm(cells)
    oos=[]; survivors=[]
    for x in selected:
        r=score(oos_events,float(x["threshold_bps"]),x["mode"],int(x["horizon_min"]))
        passed=oos_pass(r)
        row={
          "threshold_bps":x["threshold_bps"],
          "mode":x["mode"],
          "horizon_min":x["horizon_min"],
          "status":"OOS_PASS" if passed else "OOS_FAIL",
          "oos":compact(r),
          "observations":r["observations"]
        }
        oos.append(row)
        if passed: survivors.append(row)

    report={
      "family_id":RULE["family_id"],
      "version":RULE["version"],
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(RULE_PATH),
      "source_gate":RULE["source_gate"],
      "coverage":coverage,
      "discovery_cells":cells,
      "pre_holm_eligible_count":pre_holm,
      "holm_selected_count":len(selected),
      "holm_selected":[{
        "threshold_bps":x["threshold_bps"],
        "mode":x["mode"],
        "horizon_min":x["horizon_min"],
        "n":x["discovery"]["n"],
        "wins":x["discovery"]["wins"],
        "win_rate":x["discovery"]["win_rate"],
        "mean_gross_bps":x["discovery"]["mean_gross_bps"],
        "p":x["discovery"]["p_value_vs_50"],
        "holm_cutoff":x.get("holm_cutoff")
      } for x in selected],
      "oos_results":oos,
      "oos_survivors":survivors,
      "verdict":"WTI_EIA_EVENT_SHOCK_OOS_SIGNAL_CANDIDATES_SURVIVE"
                if survivors else
                "NO_WTI_EIA_EVENT_SHOCK_OOS_SURVIVOR_AT_FROZEN_V13_GATE",
      "october_data_opened":False,
      "inventory_surprise_used":False,
      "consensus_used":False,
      "parameter_rescue_authorized":False,
      "private_endpoints_used":False,
      "account_reads":False,
      "wallets_used":False,
      "orders":False,
      "exchange_mutation":False,
      "live_trading_authorized":False
    }
    (OUT/"MEXC_WTI_EVENT_SHOCK_CLOSEOUT_V13.json").write_text(
      json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    rows=[]
    selected_keys={(x["threshold_bps"],x["mode"],x["horizon_min"]) for x in selected}
    for x in cells:
        r=x["discovery"]; key=(x["threshold_bps"],x["mode"],x["horizon_min"])
        rows.append({
          "stage":"DISCOVERY","threshold_bps":x["threshold_bps"],"mode":x["mode"],
          "horizon_min":x["horizon_min"],"n":r["n"],"wins":r["wins"],
          "win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
          "p_value_vs_50":r["p_value_vs_50"],"eligible":x["eligible"],
          "selected":key in selected_keys
        })
    for x in oos:
        r=x["oos"]
        rows.append({
          "stage":"OOS","threshold_bps":x["threshold_bps"],"mode":x["mode"],
          "horizon_min":x["horizon_min"],"n":r["n"],"wins":r["wins"],
          "win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
          "p_value_vs_50":r["p_value_vs_50"],
          "eligible":x["status"]=="OOS_PASS","selected":True
        })
    if rows:
        with (OUT/"MEXC_WTI_EVENT_SHOCK_MATRIX_V13.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    print(json.dumps({
      "verdict":report["verdict"],
      "pre_holm_eligible_count":pre_holm,
      "holm_selected_count":len(selected),
      "holm_selected":report["holm_selected"],
      "oos_survivor_count":len(survivors),
      "oos_survivors":[{
        "threshold_bps":x["threshold_bps"],"mode":x["mode"],
        "horizon_min":x["horizon_min"],"n":x["oos"]["n"],
        "wins":x["oos"]["wins"],"win_rate":x["oos"]["win_rate"],
        "mean_gross_bps":x["oos"]["mean_gross_bps"],
        "p":x["oos"]["p_value_vs_50"],
        "economic_hurdles_cleared":x["oos"]["economic_hurdles_cleared"],
        "cost_scenarios_mean_net_bps":x["oos"]["cost_scenarios_mean_net_bps"]
      } for x in survivors],
      "october_data_opened":False,
      "live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
