#!/usr/bin/env python3
"""
MEXC-BITGET-NVDA-LEADLAG-001 V0.9

Frozen September Discovery -> Holm -> retrospective OOS.
Public/no-auth market data only.
No account reads, credentials, wallets, orders, mutation or live trading.
"""
from __future__ import annotations
import csv, hashlib, json, math, os, time
from datetime import datetime, timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_BITGET_NVDA_LEADLAG_RULE_V0.9.json"
RULE=json.loads(RULE_PATH.read_text(encoding="utf-8"))

MEXC="https://api.mexc.com"
BITGET="https://api.bitget.com"
UA="CryptoLab-MEXC-Bitget-NVDA-LeadLag/0.9"
STEP=60
OUT=Path("artifacts/mexc_global_assets/mexc_bitget_nvda_leadlag_v09")
RAW=OUT/"raw"

def ts(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

DISC_START=ts(RULE["windows"]["discovery_start"])
DISC_END=ts(RULE["windows"]["discovery_end"])
OOS_START=ts(RULE["windows"]["oos_start"])
OOS_END=ts(RULE["windows"]["oos_end"])
HARD_END=ts(RULE["windows"]["hard_fetch_end_exclusive"])
FETCH_OBS_START=DISC_START-STEP

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save_raw(prefix,seq,raw,meta):
    RAW.mkdir(parents=True,exist_ok=True)
    p=RAW/f"{prefix}_{seq:04d}.json"
    p.write_bytes(raw)
    (RAW/f"{prefix}_{seq:04d}.meta.json").write_text(
        json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def get(url,params,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
            raw=r.content
            if r.status_code!=200:
                raise RuntimeError(f"HTTP_{r.status_code}:{r.url}:{raw[:250]!r}")
            j=r.json()
            return raw,j,r.url
        except Exception as e:
            last=e
            time.sleep(0.8*(i+1))
    raise last

def fetch_mexc():
    close_obs={}
    open_raw={}
    hashes=[]
    # Need one previous closed minute for return calculation.
    raw_first=FETCH_OBS_START-STEP
    # Last permitted close observable is HARD_END-60, whose raw start is HARD_END-120.
    raw_last=HARD_END-2*STEP
    cur=raw_first
    seq=0
    span=1000*STEP
    while cur<=raw_last:
        e=min(cur+span,raw_last)
        raw,j,url=get(
            MEXC+f"/api/v1/contract/kline/{RULE['mexc_symbol']}",
            {"interval":"Min1","start":cur,"end":e}
        )
        seq+=1
        meta={"source":"MEXC","url":url,"requested_start":cur,"requested_end":e,
              "captured_at_utc":datetime.now(timezone.utc).isoformat(),
              "sha256":sha_bytes(raw),"bytes":len(raw)}
        save_raw("mexc",seq,raw,meta); hashes.append(meta["sha256"])
        if not isinstance(j,dict) or j.get("success") is not True:
            raise RuntimeError(f"MEXC_NON_SUCCESS:{j}")
        d=j.get("data") or {}
        times=d.get("time") or []
        opens=d.get("open") or []
        closes=d.get("close") or []
        if not (len(times)==len(opens)==len(closes)):
            raise RuntimeError("MEXC_KLINE_LENGTH_MISMATCH")
        for s,o,c in zip(times,opens,closes):
            try:
                raw_s=int(s)
            except Exception:
                continue
            if raw_s<cur or raw_s>e:
                raise RuntimeError("MEXC_TIMESTAMP_OUTSIDE_REQUEST")
            obs=raw_s+STEP
            if obs>=HARD_END:
                raise RuntimeError("MEXC_PROTECTED_OBSERVABLE_TIMESTAMP")
            if obs<FETCH_OBS_START:
                continue
            try:
                op=float(o); cp=float(c)
            except Exception:
                continue
            if op>0 and cp>0:
                open_raw[raw_s]=op
                close_obs[obs]=cp
        cur=e+STEP
        time.sleep(0.04)
    return close_obs,open_raw,{"requests":seq,"raw_sha256":hashes}

def fetch_bitget():
    close_obs={}
    hashes=[]
    # Request raw candle starts that map to observable closes from FETCH_OBS_START.
    raw_first=(FETCH_OBS_START-STEP)*1000
    raw_last=(HARD_END-2*STEP)*1000
    cur=raw_first
    seq=0
    span=900*STEP*1000
    while cur<=raw_last:
        e=min(cur+span,raw_last)
        raw,j,url=get(
            BITGET+"/api/v2/mix/market/candles",
            {
              "productType":"USDT-FUTURES",
              "symbol":RULE["bitget_symbol"],
              "granularity":"1m",
              "startTime":str(cur),
              "endTime":str(e),
              "limit":"1000"
            }
        )
        seq+=1
        meta={"source":"BITGET","url":url,"requested_start_ms":cur,"requested_end_ms":e,
              "captured_at_utc":datetime.now(timezone.utc).isoformat(),
              "sha256":sha_bytes(raw),"bytes":len(raw)}
        save_raw("bitget",seq,raw,meta); hashes.append(meta["sha256"])
        if not isinstance(j,dict) or j.get("code")!="00000":
            raise RuntimeError(f"BITGET_NON_SUCCESS:{j}")
        rows=j.get("data") or []
        for row in rows:
            if not isinstance(row,list) or len(row)<5:
                continue
            try: raw_ms=int(row[0])
            except Exception: continue
            # Bitget may round request boundaries. Fail only if returned source would
            # cross the protected global boundary; otherwise retain exact requested-window rows.
            obs=raw_ms//1000+STEP
            if obs>=HARD_END:
                raise RuntimeError("BITGET_PROTECTED_OBSERVABLE_TIMESTAMP")
            if raw_ms<cur or raw_ms>e:
                continue
            if obs<FETCH_OBS_START:
                continue
            try: cp=float(row[4])
            except Exception: continue
            if cp>0: close_obs[obs]=cp
        cur=e+STEP*1000
        time.sleep(0.04)
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

def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)

def score(mclose,mopen,bclose,shock,gap,hmin,start,end):
    h=hmin*STEP
    times=sorted(set(mclose)&set(bclose))
    vals=[]; shocks=[]; gaps=[]; longs=0; shorts=0
    next_allowed=start
    for t in times:
        if t<start or t>=end or t<next_allowed:
            continue
        prev=t-STEP
        if prev not in mclose or prev not in bclose:
            continue
        # Signal is known when candle closing at t is complete.
        # Entry proxy is the open of the new MEXC candle starting exactly at t.
        if t not in mopen:
            continue
        exit_t=t+h
        if exit_t>=end or exit_t not in mclose:
            continue
        br=10000.0*(bclose[t]/bclose[prev]-1.0)
        mr=10000.0*(mclose[t]/mclose[prev]-1.0)
        lg=br-mr
        if abs(br)<shock:
            continue
        if sgn(lg)!=sgn(br):
            continue
        if abs(lg)<gap:
            continue
        side=sgn(br)
        entry=mopen[t]
        exit_px=mclose[exit_t]
        gross=side*10000.0*(exit_px/entry-1.0)
        vals.append(gross); shocks.append(br); gaps.append(lg)
        if side>0: longs+=1
        else: shorts+=1
        next_allowed=exit_t

    n=len(vals); wins=sum(x>0 for x in vals)
    mg=mean(vals)
    return {
      "n":n,"wins":wins,"losses":n-wins,
      "longs":longs,"shorts":shorts,
      "win_rate":wins/n if n else None,
      "mean_gross_bps":mg,
      "median_gross_bps":median(vals),
      "p_value_vs_50":binom_tail_half(wins,n) if n else None,
      "third_means_gross_bps":thirds(vals),
      "half_means_gross_bps":halves(vals),
      "mean_abs_bitget_shock_bps":mean([abs(x) for x in shocks]),
      "median_abs_bitget_shock_bps":median([abs(x) for x in shocks]),
      "mean_abs_lag_gap_bps":mean([abs(x) for x in gaps]),
      "median_abs_lag_gap_bps":median([abs(x) for x in gaps]),
      "cost_scenarios_mean_net_bps":{
        str(c):(mg-float(c) if mg is not None else None)
        for c in RULE["cost_scenarios_roundtrip_bps"]
      },
      "economic_hurdles_cleared":{
        str(c):(mg>float(c) if mg is not None else False)
        for c in RULE["economic_hurdles_roundtrip_bps"]
      }
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
      and r["p_value_vs_50"] is not None and r["p_value_vs_50"]<g["exact_one_sided_binomial_p_lt"]
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

def main():
    forbidden={"MEXC_API_KEY","MEXC_SECRET_KEY","BITGET_API_KEY","ACCESS_KEY",
               "API_KEY","SECRET_KEY","PRIVATE_KEY"}
    if any(k.upper() in forbidden for k in os.environ):
        raise SystemExit("FAIL_CLOSED:CREDENTIAL_LIKE_ENV_DETECTED")
    if RULE.get("source_gate")!="MEXC_BITGET_NVDA_SOURCE_PASS":
        raise SystemExit("FAIL_CLOSED:SOURCE_GATE_NOT_PASS")
    if RULE.get("outcomes_opened_at_freeze")!=0:
        raise SystemExit("FAIL_CLOSED:OUTCOME_FREEZE_INVALID")
    if RULE.get("live_trading_authorized") is not False:
        raise SystemExit("FAIL_CLOSED:GOVERNANCE_INVALID")
    if OOS_END!=HARD_END:
        raise SystemExit("FAIL_CLOSED:HARD_BOUNDARY_MISMATCH")

    OUT.mkdir(parents=True,exist_ok=True)
    print("RULE_SHA256=",sha_file(RULE_PATH))
    print("HARD_FETCH_END_EXCLUSIVE=",RULE["windows"]["hard_fetch_end_exclusive"])

    mclose,mopen,ms=fetch_mexc()
    bclose,bs=fetch_bitget()
    overlap=sorted(set(mclose)&set(bclose))
    if not overlap:
        raise RuntimeError("ZERO_EXACT_CLOCK_OVERLAP")

    minrows=max(1,min(len(mclose),len(bclose)))
    alignment=len(overlap)/minrows
    drows=sum(1 for t in overlap if DISC_START-STEP<=t<DISC_END)
    orows=sum(1 for t in overlap if OOS_START-STEP<=t<OOS_END)
    print(json.dumps({
      "SOURCE_COVERAGE_ONLY":True,
      "SCORING_NOT_YET_STARTED":True,
      "mexc_close_rows":len(mclose),
      "mexc_open_rows":len(mopen),
      "bitget_close_rows":len(bclose),
      "exact_overlap_rows":len(overlap),
      "alignment_ratio":alignment,
      "discovery_overlap_rows":drows,
      "oos_overlap_rows":orows,
      "first_overlap_utc":datetime.fromtimestamp(overlap[0],tz=timezone.utc).isoformat(),
      "last_overlap_utc":datetime.fromtimestamp(overlap[-1],tz=timezone.utc).isoformat()
    },indent=2,sort_keys=True))
    if alignment<0.98:
        raise RuntimeError(f"CLOCK_ALIGNMENT_FAIL:{alignment}")
    if drows<1500 or orows<1000:
        raise RuntimeError(f"SOURCE_COVERAGE_INSUFFICIENT:D={drows}:OOS={orows}")

    cells=[]
    for shock in RULE["shock_thresholds_bps"]:
        for gap in RULE["lag_gap_thresholds_bps"]:
            for h in RULE["horizons_min"]:
                r=score(mclose,mopen,bclose,float(shock),float(gap),int(h),DISC_START,DISC_END)
                cells.append({
                  "shock_bps":shock,"lag_gap_bps":gap,"horizon_min":h,
                  "eligible":discovery_eligible(r),"discovery":r
                })

    selected,pre_holm=holm(cells)
    oos=[]; survivors=[]
    for x in selected:
        r=score(mclose,mopen,bclose,float(x["shock_bps"]),float(x["lag_gap_bps"]),
                int(x["horizon_min"]),OOS_START,OOS_END)
        passed=oos_pass(r)
        row={
          "shock_bps":x["shock_bps"],"lag_gap_bps":x["lag_gap_bps"],
          "horizon_min":x["horizon_min"],
          "status":"OOS_PASS" if passed else "OOS_FAIL",
          "oos":r
        }
        oos.append(row)
        if passed: survivors.append(row)

    report={
      "family_id":RULE["family_id"],"version":RULE["version"],
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(RULE_PATH),
      "source_gate":RULE["source_gate"],
      "hard_fetch_end_exclusive":RULE["windows"]["hard_fetch_end_exclusive"],
      "coverage":{
        "mexc_close_rows":len(mclose),"mexc_open_rows":len(mopen),
        "bitget_close_rows":len(bclose),"exact_overlap_rows":len(overlap),
        "alignment_ratio":alignment,"discovery_overlap_rows":drows,"oos_overlap_rows":orows,
        "first_overlap_utc":datetime.fromtimestamp(overlap[0],tz=timezone.utc).isoformat(),
        "last_overlap_utc":datetime.fromtimestamp(overlap[-1],tz=timezone.utc).isoformat(),
        "mexc_source":ms,"bitget_source":bs
      },
      "discovery_cells":cells,
      "pre_holm_eligible_count":pre_holm,
      "holm_selected_count":len(selected),
      "holm_selected":[{
        "shock_bps":x["shock_bps"],"lag_gap_bps":x["lag_gap_bps"],
        "horizon_min":x["horizon_min"],"n":x["discovery"]["n"],
        "mean_gross_bps":x["discovery"]["mean_gross_bps"],
        "win_rate":x["discovery"]["win_rate"],
        "p":x["discovery"]["p_value_vs_50"],
        "holm_cutoff":x.get("holm_cutoff")
      } for x in selected],
      "oos_results":oos,
      "oos_survivors":survivors,
      "verdict":"NVDA_CROSSVENUE_OOS_SIGNAL_CANDIDATES_SURVIVE"
                if survivors else
                "NO_NVDA_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V09_GATE",
      "october_holdout_opened":False,
      "parameter_rescue_authorized":False,
      "private_endpoints_used":False,"account_reads":False,"wallets_used":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False
    }
    (OUT/"MEXC_BITGET_NVDA_LEADLAG_CLOSEOUT_V09.json").write_text(
        json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    rows=[]
    selected_keys={(x["shock_bps"],x["lag_gap_bps"],x["horizon_min"]) for x in selected}
    for x in cells:
        r=x["discovery"]; key=(x["shock_bps"],x["lag_gap_bps"],x["horizon_min"])
        rows.append({
          "stage":"DISCOVERY","shock_bps":x["shock_bps"],"lag_gap_bps":x["lag_gap_bps"],
          "horizon_min":x["horizon_min"],"n":r["n"],"win_rate":r["win_rate"],
          "mean_gross_bps":r["mean_gross_bps"],"p_value_vs_50":r["p_value_vs_50"],
          "eligible":x["eligible"],"selected":key in selected_keys
        })
    for x in oos:
        r=x["oos"]
        rows.append({
          "stage":"OOS","shock_bps":x["shock_bps"],"lag_gap_bps":x["lag_gap_bps"],
          "horizon_min":x["horizon_min"],"n":r["n"],"win_rate":r["win_rate"],
          "mean_gross_bps":r["mean_gross_bps"],"p_value_vs_50":r["p_value_vs_50"],
          "eligible":x["status"]=="OOS_PASS","selected":True
        })
    if rows:
        with (OUT/"MEXC_BITGET_NVDA_LEADLAG_MATRIX_V09.csv").open("w",newline="",encoding="utf-8") as f:
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
         "mean_gross_bps":x["oos"]["mean_gross_bps"],
         "win_rate":x["oos"]["win_rate"],"p":x["oos"]["p_value_vs_50"],
         "economic_hurdles_cleared":x["oos"]["economic_hurdles_cleared"]
      } for x in survivors],
      "october_holdout_opened":False,
      "live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
