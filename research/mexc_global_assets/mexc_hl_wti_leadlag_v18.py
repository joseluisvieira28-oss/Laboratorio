#!/usr/bin/env python3
"""
MEXC-HL-WTI-LEADLAG-001 V1.8

Frozen one-minute cross-venue WTI lead/lag:
Discovery -> Holm -> untouched October retrospective OOS.

Public/no-auth MEXC and Hyperliquid market data only.
"""
from __future__ import annotations
import csv, hashlib, json, math, os, time
from datetime import datetime, timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_HL_WTI_LEADLAG_RULE_V1.8.json"
RULE=json.loads(RULE_PATH.read_text(encoding="utf-8"))

MEXC="https://api.mexc.com"
HL="https://api.hyperliquid.xyz/info"
UA="CryptoLab-MEXC-HL-WTI-LeadLag/1.7"
STEP=60
OUT=Path("artifacts/mexc_global_assets/mexc_hl_wti_leadlag_v18")
RAW=OUT/"raw"

def ts(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

def iso(t):
    return datetime.fromtimestamp(t,tz=timezone.utc).isoformat().replace("+00:00","Z")

DISC_START=ts(RULE["windows"]["discovery_start"])
DISC_END=ts(RULE["windows"]["discovery_end"])
OOS_START=ts(RULE["windows"]["oos_start"])
OOS_END=ts(RULE["windows"]["oos_end"])
HARD=ts(RULE["windows"]["hard_fetch_end_exclusive"])
FETCH_OBS_START=DISC_START-STEP

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save_raw(prefix,seq,raw,meta):
    RAW.mkdir(parents=True,exist_ok=True)
    p=RAW/f"{prefix}_{seq:04d}.json"
    p.write_bytes(raw)
    (RAW/f"{prefix}_{seq:04d}.meta.json").write_text(
      json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def mexc_get(params,retries=5):
    url=MEXC+f"/api/v1/contract/kline/{RULE['mexc_symbol']}"
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
            raw=r.content
            if r.status_code!=200:
                raise RuntimeError(f"MEXC_HTTP_{r.status_code}:{r.url}:{raw[:250]!r}")
            j=r.json()
            if not isinstance(j,dict) or j.get("success") is not True:
                raise RuntimeError(f"MEXC_NON_SUCCESS:{j}")
            return raw,j,r.url
        except Exception as e:
            last=e; time.sleep(0.7*(i+1))
    raise last

def hl_post(payload,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.post(HL,json=payload,headers={"User-Agent":UA,"Content-Type":"application/json"},timeout=30)
            raw=r.content
            if r.status_code!=200:
                raise RuntimeError(f"HL_HTTP_{r.status_code}:{raw[:250]!r}")
            j=r.json()
            if not isinstance(j,list):
                raise RuntimeError(f"HL_NON_LIST:{type(j).__name__}")
            return raw,j
        except Exception as e:
            last=e; time.sleep(0.7*(i+1))
    raise last

def fetch_mexc():
    close_obs={}
    open_raw={}
    hashes=[]
    raw_first=FETCH_OBS_START-STEP
    raw_last=HARD-2*STEP
    cur=raw_first; seq=0; span=1200*STEP
    while cur<=raw_last:
        e=min(cur+span,raw_last)
        raw,j,url=mexc_get({"interval":"Min1","start":cur,"end":e})
        seq+=1
        meta={"source":"MEXC","url":url,"requested_start":cur,"requested_end":e,
              "captured_at_utc":datetime.now(timezone.utc).isoformat(),
              "sha256":sha_bytes(raw),"bytes":len(raw)}
        save_raw("mexc",seq,raw,meta); hashes.append(meta["sha256"])
        d=j.get("data") or {}
        times=d.get("time") or []; opens=d.get("open") or []; closes=d.get("close") or []
        if not (len(times)==len(opens)==len(closes)):
            raise RuntimeError("MEXC_LENGTH_MISMATCH")
        for s,o,c in zip(times,opens,closes):
            try:s=int(s); op=float(o); cp=float(c)
            except Exception:continue
            if s<cur or s>e:
                raise RuntimeError("MEXC_TIMESTAMP_OUTSIDE_REQUEST")
            obs=s+STEP
            if obs>=HARD:
                raise RuntimeError("MEXC_PROTECTED_OBSERVABLE_TIMESTAMP")
            if obs<FETCH_OBS_START:
                continue
            if op>0 and cp>0:
                open_raw[s]=op
                close_obs[obs]=cp
        cur=e+STEP
        time.sleep(0.035)
    return close_obs,open_raw,{"requests":seq,"raw_sha256":hashes}

def fetch_hl():
    close_obs={}
    hashes=[]
    raw_first_ms=(FETCH_OBS_START-STEP)*1000
    raw_last_ms=(HARD-2*STEP)*1000
    cur=raw_first_ms; seq=0; span=900*STEP*1000
    while cur<=raw_last_ms:
        e=min(cur+span,raw_last_ms)
        payload={"type":"candleSnapshot","req":{
          "coin":RULE["hyperliquid_coin"],
          "interval":"1m",
          "startTime":cur,
          "endTime":e
        }}
        raw,j=hl_post(payload)
        seq+=1
        meta={"source":"HYPERLIQUID","payload":payload,
              "captured_at_utc":datetime.now(timezone.utc).isoformat(),
              "sha256":sha_bytes(raw),"bytes":len(raw)}
        save_raw("hyperliquid",seq,raw,meta); hashes.append(meta["sha256"])
        for row in j:
            try: raw_ms=int(row["t"]); cp=float(row["c"])
            except Exception:continue
            if raw_ms<cur or raw_ms>e:
                raise RuntimeError("HL_TIMESTAMP_OUTSIDE_REQUEST")
            obs=raw_ms//1000+STEP
            if obs>=HARD:
                raise RuntimeError("HL_PROTECTED_OBSERVABLE_TIMESTAMP")
            if obs<FETCH_OBS_START:
                continue
            if cp>0: close_obs[obs]=cp
        cur=e+STEP*1000
        time.sleep(0.035)
    return close_obs,{"requests":seq,"raw_sha256":hashes}

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
    m=max(xs); return m+math.log(sum(math.exp(x-m) for x in xs))

def binom_tail_half(w,n):
    if n<=0:return None
    ln2=math.log(2.0)
    logs=[math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)-n*ln2 for k in range(w,n+1)]
    return min(1.0,math.exp(logsumexp(logs)))

def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)

def score(mclose,mopen,hclose,shock_th,gap_th,horizon,start,end):
    vals=[]; shocks=[]; gaps=[]; observations=[]
    times=sorted(set(mclose)&set(hclose))
    next_allowed=start
    for t in times:
        if t<start or t>=end or t<next_allowed:
            continue
        prev=t-STEP
        if prev not in mclose or prev not in hclose:
            continue
        # Signal is known at t. Next MEXC minute begins at raw start t.
        if t not in mopen:
            continue
        exit_obs=t+horizon*STEP
        if exit_obs>=end or exit_obs not in mclose:
            continue

        hr=10000.0*(hclose[t]/hclose[prev]-1.0)
        mr=10000.0*(mclose[t]/mclose[prev]-1.0)
        gap=hr-mr

        if abs(hr)<shock_th:
            continue
        if sgn(gap)!=sgn(hr):
            continue
        if abs(gap)<gap_th:
            continue

        side=sgn(hr)
        entry=mopen[t]
        exit_px=mclose[exit_obs]
        gross=side*10000.0*(exit_px/entry-1.0)
        vals.append(gross); shocks.append(hr); gaps.append(gap)
        observations.append({
          "signal_observable_utc":iso(t),
          "hl_ret_bps":hr,
          "mexc_ret_bps":mr,
          "lag_gap_bps":gap,
          "side":"LONG" if side>0 else "SHORT",
          "entry_raw_start_utc":iso(t),
          "exit_observable_utc":iso(exit_obs),
          "gross_bps":gross
        })
        next_allowed=exit_obs

    n=len(vals); wins=sum(x>0 for x in vals); mg=mean(vals)
    return {
      "n":n,"wins":wins,"losses":n-wins,
      "win_rate":wins/n if n else None,
      "mean_gross_bps":mg,
      "median_gross_bps":median(vals),
      "p_value_vs_50":binom_tail_half(wins,n) if n else None,
      "third_means_gross_bps":thirds(vals),
      "half_means_gross_bps":halves(vals),
      "mean_abs_hl_shock_bps":mean([abs(x) for x in shocks]),
      "median_abs_hl_shock_bps":median([abs(x) for x in shocks]),
      "mean_abs_lag_gap_bps":mean([abs(x) for x in gaps]),
      "median_abs_lag_gap_bps":median([abs(x) for x in gaps]),
      "economic_hurdles_cleared":{
        str(c):(mg>float(c) if mg is not None else False)
        for c in RULE["economic_hurdles_roundtrip_bps"]
      },
      "cost_scenarios_mean_net_bps":{
        str(c):(mg-float(c) if mg is not None else None)
        for c in RULE["cost_scenarios_roundtrip_bps"]
      },
      "observations":observations
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
    e=[x for x in cells if x["eligible"]]
    e.sort(key=lambda x:x["discovery"]["p_value_vs_50"])
    m=len(e); selected=[]
    for rank,x in enumerate(e,1):
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
    if RULE.get("source_binding")!="HYPERLIQUID_WTI_SOURCE_PASS__XYZ_CL":
        raise SystemExit("FAIL_CLOSED:SOURCE_BINDING_NOT_PASS")
    if RULE.get("outcomes_opened_at_freeze")!=0:
        raise SystemExit("FAIL_CLOSED:FREEZE_INVALID")
    if RULE.get("signal_mode")!="FOLLOW_HL_UNDERREACTION":
        raise SystemExit("FAIL_CLOSED:SIGNAL_MODE_INVALID")
    if OOS_END!=HARD:
        raise SystemExit("FAIL_CLOSED:HARD_BOUNDARY_MISMATCH")
    if RULE.get("live_trading_authorized") is not False:
        raise SystemExit("FAIL_CLOSED:LIVE_FLAG_INVALID")

    OUT.mkdir(parents=True,exist_ok=True)
    print("RULE_SHA256=",sha_file(RULE_PATH))
    print("HARD_FETCH_END_EXCLUSIVE=",RULE["windows"]["hard_fetch_end_exclusive"])

    mclose,mopen,ms=fetch_mexc()
    hclose,hs=fetch_hl()
    overlap=sorted(set(mclose)&set(hclose))
    if not overlap:
        raise RuntimeError("ZERO_EXACT_CLOCK_OVERLAP")

    minrows=max(1,min(len(mclose),len(hclose)))
    alignment=len(overlap)/minrows
    drows=sum(1 for t in overlap if DISC_START-STEP<=t<DISC_END)
    orows=sum(1 for t in overlap if OOS_START-STEP<=t<OOS_END)

    coverage={
      "mexc_close_rows":len(mclose),
      "mexc_open_rows":len(mopen),
      "hl_close_rows":len(hclose),
      "exact_overlap_rows":len(overlap),
      "alignment_ratio":alignment,
      "discovery_overlap_rows":drows,
      "oos_overlap_rows":orows,
      "first_overlap_utc":iso(overlap[0]),
      "last_overlap_utc":iso(overlap[-1]),
      "mexc_source":ms,
      "hyperliquid_source":hs
    }
    print(json.dumps({"SOURCE_COVERAGE_ONLY":True,"SCORING_NOT_YET_STARTED":True,**coverage},indent=2,sort_keys=True))
    if alignment<0.98:
        raise RuntimeError(f"CLOCK_ALIGNMENT_FAIL:{alignment}")
    if drows<2500:
        raise RuntimeError(f"DISCOVERY_COVERAGE_INSUFFICIENT:{drows}")
    if orows<1800:
        raise RuntimeError(f"OOS_COVERAGE_INSUFFICIENT:{orows}")

    cells=[]
    for shock in RULE["shock_thresholds_bps"]:
        for gap in RULE["lag_gap_thresholds_bps"]:
            for h in RULE["horizons_min"]:
                r=score(mclose,mopen,hclose,float(shock),float(gap),int(h),DISC_START,DISC_END)
                cells.append({
                  "shock_bps":shock,"lag_gap_bps":gap,"horizon_min":h,
                  "eligible":discovery_eligible(r),"discovery":compact(r)
                })

    selected,pre_holm=holm(cells)
    oos=[]; survivors=[]
    for x in selected:
        r=score(mclose,mopen,hclose,float(x["shock_bps"]),float(x["lag_gap_bps"]),
                int(x["horizon_min"]),OOS_START,OOS_END)
        passed=oos_pass(r)
        row={
          "shock_bps":x["shock_bps"],"lag_gap_bps":x["lag_gap_bps"],
          "horizon_min":x["horizon_min"],
          "status":"OOS_PASS" if passed else "OOS_FAIL",
          "oos":compact(r),
          "observations":r["observations"]
        }
        oos.append(row)
        if passed: survivors.append(row)

    report={
      "family_id":RULE["family_id"],"version":RULE["version"],
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(RULE_PATH),
      "source_binding":RULE["source_binding"],
      "coverage":coverage,
      "discovery_cells":cells,
      "pre_holm_eligible_count":pre_holm,
      "holm_selected_count":len(selected),
      "holm_selected":[{
        "shock_bps":x["shock_bps"],"lag_gap_bps":x["lag_gap_bps"],
        "horizon_min":x["horizon_min"],"n":x["discovery"]["n"],
        "wins":x["discovery"]["wins"],"win_rate":x["discovery"]["win_rate"],
        "mean_gross_bps":x["discovery"]["mean_gross_bps"],
        "p":x["discovery"]["p_value_vs_50"],"holm_cutoff":x.get("holm_cutoff")
      } for x in selected],
      "oos_results":oos,
      "oos_survivors":survivors,
      "verdict":"WTI_CROSSVENUE_OOS_SIGNAL_CANDIDATES_SURVIVE"
                if survivors else
                "NO_WTI_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V18_GATE",
      "post_0900_oct4_opened":False,
      "parameter_rescue_authorized":False,
      "private_endpoints_used":False,"account_reads":False,"wallets_used":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False
    }
    (OUT/"MEXC_HL_WTI_LEADLAG_CLOSEOUT_V18.json").write_text(
      json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    rows=[]
    selected_keys={(x["shock_bps"],x["lag_gap_bps"],x["horizon_min"]) for x in selected}
    for x in cells:
        r=x["discovery"]; key=(x["shock_bps"],x["lag_gap_bps"],x["horizon_min"])
        rows.append({
          "stage":"DISCOVERY","shock_bps":x["shock_bps"],"lag_gap_bps":x["lag_gap_bps"],
          "horizon_min":x["horizon_min"],"n":r["n"],"wins":r["wins"],
          "win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
          "p_value_vs_50":r["p_value_vs_50"],"eligible":x["eligible"],
          "selected":key in selected_keys
        })
    for x in oos:
        r=x["oos"]
        rows.append({
          "stage":"OOS","shock_bps":x["shock_bps"],"lag_gap_bps":x["lag_gap_bps"],
          "horizon_min":x["horizon_min"],"n":r["n"],"wins":r["wins"],
          "win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
          "p_value_vs_50":r["p_value_vs_50"],
          "eligible":x["status"]=="OOS_PASS","selected":True
        })
    if rows:
        with (OUT/"MEXC_HL_WTI_LEADLAG_MATRIX_V18.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    print(json.dumps({
      "verdict":report["verdict"],
      "alignment_ratio":alignment,
      "discovery_overlap_rows":drows,
      "oos_overlap_rows":orows,
      "pre_holm_eligible_count":pre_holm,
      "holm_selected_count":len(selected),
      "holm_selected":report["holm_selected"],
      "oos_survivor_count":len(survivors),
      "oos_survivors":[{
        "shock_bps":x["shock_bps"],"lag_gap_bps":x["lag_gap_bps"],
        "horizon_min":x["horizon_min"],"n":x["oos"]["n"],
        "wins":x["oos"]["wins"],"win_rate":x["oos"]["win_rate"],
        "mean_gross_bps":x["oos"]["mean_gross_bps"],
        "p":x["oos"]["p_value_vs_50"],
        "economic_hurdles_cleared":x["oos"]["economic_hurdles_cleared"],
        "cost_scenarios_mean_net_bps":x["oos"]["cost_scenarios_mean_net_bps"]
      } for x in survivors],
      "post_0900_oct4_opened":False,
      "live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
