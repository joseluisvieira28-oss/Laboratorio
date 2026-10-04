#!/usr/bin/env python3
"""
MEXC-HL-NAS100-DISLOCATION-001 V0.6

Frozen historical Discovery -> Holm -> retrospective OOS runner.
Public/no-auth market data only.
No accounts, wallets, private endpoints, orders, exchange mutation or live trading.
"""
from __future__ import annotations
import csv, hashlib, json, math, os, time
from datetime import datetime, timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_HL_NAS100_DISLOCATION_RULE_V0.6.json"
BIND_PATH=HERE/"MEXC_HL_NAS100_SOURCE_BINDING_V0.5.1.json"
RULE=json.loads(RULE_PATH.read_text(encoding="utf-8"))
BIND=json.loads(BIND_PATH.read_text(encoding="utf-8"))

BASE_MEXC="https://api.mexc.com"
BASE_HL="https://api.hyperliquid.xyz/info"
UA="CryptoLab-MEXC-HL-NAS100-Dislocation/0.6"
STEP=60
OUT=Path("artifacts/mexc_global_assets/mexc_hl_nas100_dislocation_v06")
RAW=OUT/"raw"

def ts(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

DISC_START=ts(RULE["windows"]["discovery_start"])
DISC_END=ts(RULE["windows"]["discovery_end"])
OOS_START=ts(RULE["windows"]["oos_start"])
OOS_END=ts(RULE["windows"]["oos_end"])
HARD_END=ts(RULE["windows"]["hard_fetch_end_exclusive"])

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save_raw(prefix, seq, raw, meta):
    RAW.mkdir(parents=True, exist_ok=True)
    p=RAW/f"{prefix}_{seq:04d}.json"
    p.write_bytes(raw)
    (RAW/f"{prefix}_{seq:04d}.meta.json").write_text(
        json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def get_mexc(params,retries=5):
    last=None
    url=f"{BASE_MEXC}/api/v1/contract/kline/{RULE['mexc_symbol']}"
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
            raw=r.content
            if r.status_code!=200:
                raise RuntimeError(f"MEXC_HTTP_{r.status_code}:{raw[:250]!r}")
            j=r.json()
            if not isinstance(j,dict) or j.get("success") is not True:
                raise RuntimeError(f"MEXC_NON_SUCCESS:{j}")
            return raw,j,r.url
        except Exception as e:
            last=e; time.sleep(0.8*(i+1))
    raise last

def post_hl(payload,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.post(BASE_HL,json=payload,headers={"User-Agent":UA,"Content-Type":"application/json"},timeout=30)
            raw=r.content
            if r.status_code!=200:
                raise RuntimeError(f"HL_HTTP_{r.status_code}:{raw[:250]!r}")
            j=r.json()
            if not isinstance(j,list):
                raise RuntimeError(f"HL_NON_LIST:{type(j).__name__}")
            return raw,j
        except Exception as e:
            last=e; time.sleep(0.8*(i+1))
    raise last

def fetch_mexc(start_obs,end_obs):
    if end_obs>HARD_END:
        raise RuntimeError("MEXC_HARD_FETCH_BOUNDARY_VIOLATION")
    out={}
    hashes=[]
    raw_first=start_obs-STEP
    raw_last=end_obs-2*STEP
    cur=raw_first
    seq=0
    span=1200*STEP
    while cur<=raw_last:
        e=min(cur+span,raw_last)
        raw,j,url=get_mexc({"interval":"Min1","start":cur,"end":e})
        seq+=1
        meta={"source":"MEXC","url":url,"requested_start":cur,"requested_end":e,
              "captured_at_utc":datetime.now(timezone.utc).isoformat(),"sha256":sha_bytes(raw),"bytes":len(raw)}
        save_raw("mexc",seq,raw,meta); hashes.append(meta["sha256"])
        d=j.get("data") or {}
        times=d.get("time") or []
        closes=d.get("close") or []
        if len(times)!=len(closes):
            raise RuntimeError("MEXC_KLINE_LENGTH_MISMATCH")
        for s,p in zip(times,closes):
            try: raw_s=int(s)
            except Exception: continue
            if raw_s<cur or raw_s>e:
                raise RuntimeError("MEXC_TIMESTAMP_OUTSIDE_REQUEST")
            obs=raw_s+STEP
            if obs>=HARD_END:
                raise RuntimeError("MEXC_PROTECTED_OBSERVABLE_TIMESTAMP")
            if obs<start_obs or obs>=end_obs:
                continue
            try: px=float(p)
            except Exception: continue
            if px>0: out[obs]=px
        cur=e+STEP
        time.sleep(0.05)
    return out,{"requests":seq,"raw_sha256":hashes}

def fetch_hl(start_obs,end_obs):
    if end_obs>HARD_END:
        raise RuntimeError("HL_HARD_FETCH_BOUNDARY_VIOLATION")
    out={}
    hashes=[]
    raw_first_ms=(start_obs-STEP)*1000
    raw_last_ms=(end_obs-2*STEP)*1000
    cur=raw_first_ms
    seq=0
    span=900*STEP*1000
    while cur<=raw_last_ms:
        e=min(cur+span,raw_last_ms)
        payload={"type":"candleSnapshot","req":{
            "coin":RULE["hyperliquid_coin"],"interval":"1m",
            "startTime":cur,"endTime":e
        }}
        raw,j=post_hl(payload)
        seq+=1
        meta={"source":"HYPERLIQUID","payload":payload,
              "captured_at_utc":datetime.now(timezone.utc).isoformat(),"sha256":sha_bytes(raw),"bytes":len(raw)}
        save_raw("hyperliquid",seq,raw,meta); hashes.append(meta["sha256"])
        for row in j:
            try: raw_t=int(row["t"])
            except Exception: continue
            if raw_t<cur or raw_t>e:
                raise RuntimeError("HL_TIMESTAMP_OUTSIDE_REQUEST")
            obs=raw_t//1000+STEP
            if obs>=HARD_END:
                raise RuntimeError("HL_PROTECTED_OBSERVABLE_TIMESTAMP")
            if obs<start_obs or obs>=end_obs:
                continue
            try: px=float(row["c"])
            except Exception: continue
            if px>0: out[obs]=px
        cur=e+STEP*1000
        time.sleep(0.05)
    return out,{"requests":seq,"raw_sha256":hashes}

def mean(xs):
    return sum(xs)/len(xs) if xs else None

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
    logs=[math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)-n*ln2 for k in range(w,n+1)]
    return min(1.0,math.exp(logsumexp(logs)))

def score(mexc,hl,threshold,horizon_min,start,end):
    h=horizon_min*60
    delay=RULE["entry_delay_min"]*60
    times=sorted(set(mexc)&set(hl))
    next_allowed=start
    vals=[]; gaps=[]; events=[]
    for t in times:
        if t<start or t>=end or t<next_allowed:
            continue
        entry_t=t+delay
        exit_t=entry_t+h
        if entry_t>=end or exit_t>=end:
            continue
        if entry_t not in mexc or exit_t not in mexc:
            continue
        gap=10000.0*(mexc[t]/hl[t]-1.0)
        if abs(gap)<threshold:
            continue
        side=-1.0 if gap>0 else 1.0
        gross=side*10000.0*(mexc[exit_t]/mexc[entry_t]-1.0)
        vals.append(gross); gaps.append(gap)
        events.append({"signal_t":t,"entry_t":entry_t,"exit_t":exit_t,"gap_bps":gap,"gross_bps":gross})
        next_allowed=exit_t
    n=len(vals); wins=sum(x>0 for x in vals)
    return {
      "n":n,"wins":wins,"losses":n-wins,
      "win_rate":wins/n if n else None,
      "mean_gross_bps":mean(vals),
      "median_gross_bps":median(vals),
      "p_value_vs_50":binom_tail_half(wins,n) if n else None,
      "third_means_gross_bps":thirds(vals),
      "half_means_gross_bps":halves(vals),
      "median_abs_entry_gap_bps":median([abs(x) for x in gaps]),
      "mean_abs_entry_gap_bps":mean([abs(x) for x in gaps]),
      "cost_scenarios_mean_net_bps":{
        str(c):(mean(vals)-float(c) if n else None) for c in RULE["cost_scenarios_roundtrip_bps"]
      },
      "economic_hurdles_cleared":{
        str(c):(mean(vals)>float(c) if n else False) for c in RULE["economic_hurdles_roundtrip_bps"]
      },
      "events":events
    }

def discovery_eligible(r):
    g=RULE["discovery_gate"]
    return (r["n"]>=g["min_n"]
            and r["mean_gross_bps"] is not None and r["mean_gross_bps"]>0
            and r["win_rate"] is not None and r["win_rate"]>0.5
            and r["p_value_vs_50"] is not None
            and all(x is not None and x>0 for x in r["third_means_gross_bps"]))

def oos_pass(r):
    g=RULE["oos_gate"]
    return (r["n"]>=g["min_n"]
            and r["mean_gross_bps"] is not None and r["mean_gross_bps"]>0
            and r["win_rate"] is not None and r["win_rate"]>0.5
            and r["p_value_vs_50"] is not None and r["p_value_vs_50"]<g["exact_one_sided_binomial_p_lt"]
            and all(x is not None and x>=0 for x in r["half_means_gross_bps"]))

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

def strip_events(r):
    x=dict(r); x.pop("events",None); return x

def main():
    forbidden={"MEXC_API_KEY","MEXC_SECRET_KEY","API_KEY","SECRET_KEY","PRIVATE_KEY"}
    if any(k.upper() in forbidden for k in os.environ):
        raise SystemExit("FAIL_CLOSED:CREDENTIAL_LIKE_ENV_DETECTED")
    if BIND.get("source_gate_verdict")!="HYPERLIQUID_NAS100_SOURCE_PASS__XYZ_XYZ100":
        raise SystemExit("FAIL_CLOSED:SOURCE_BINDING_NOT_PASS")
    if RULE.get("outcomes_opened_at_freeze")!=0 or RULE.get("live_trading_authorized") is not False:
        raise SystemExit("FAIL_CLOSED:RULE_GOVERNANCE_INVALID")
    if OOS_END!=HARD_END:
        raise SystemExit("FAIL_CLOSED:HARD_BOUNDARY_MISMATCH")

    OUT.mkdir(parents=True,exist_ok=True)
    print("RULE_SHA256=",sha_file(RULE_PATH))
    print("BINDING_SHA256=",sha_file(BIND_PATH))
    print("HARD_FETCH_END_EXCLUSIVE=",RULE["windows"]["hard_fetch_end_exclusive"])

    mexc,ms=fetch_mexc(DISC_START,OOS_END)
    hl,hs=fetch_hl(DISC_START,OOS_END)
    overlap=sorted(set(mexc)&set(hl))
    if not overlap:
        raise RuntimeError("ZERO_EXACT_CLOCK_OVERLAP")
    minrows=max(1,min(len(mexc),len(hl)))
    alignment=len(overlap)/minrows
    calendar=(OOS_END-DISC_START)//60
    calendar_cov=len(overlap)/calendar
    print(json.dumps({
      "SOURCE_COVERAGE_ONLY": True,
      "mexc_rows": len(mexc),
      "hl_rows": len(hl),
      "exact_overlap_rows": len(overlap),
      "alignment_ratio": alignment,
      "calendar_coverage_ratio": calendar_cov,
      "first_overlap_utc": datetime.fromtimestamp(overlap[0],tz=timezone.utc).isoformat(),
      "last_overlap_utc": datetime.fromtimestamp(overlap[-1],tz=timezone.utc).isoformat(),
      "SCORING_NOT_YET_STARTED": True
    }, indent=2, sort_keys=True))
    if alignment<0.98:
        raise RuntimeError(f"CLOCK_ALIGNMENT_FAIL:{alignment}")
    if calendar_cov<0.60:
        raise RuntimeError(f"CALENDAR_COVERAGE_TOO_SPARSE:{calendar_cov}")

    cells=[]
    for th in RULE["thresholds_bps"]:
        for h in RULE["horizons_min"]:
            r=score(mexc,hl,float(th),int(h),DISC_START,DISC_END)
            cells.append({"threshold_bps":th,"horizon_min":h,"eligible":discovery_eligible(r),"discovery":strip_events(r)})

    selected,pre_holm_count=holm(cells)
    oos=[]
    survivors=[]
    for x in selected:
        r=score(mexc,hl,float(x["threshold_bps"]),int(x["horizon_min"]),OOS_START,OOS_END)
        passed=oos_pass(r)
        row={"threshold_bps":x["threshold_bps"],"horizon_min":x["horizon_min"],
             "status":"OOS_PASS" if passed else "OOS_FAIL","oos":strip_events(r)}
        oos.append(row)
        if passed: survivors.append(row)

    report={
      "family_id":RULE["family_id"],"version":RULE["version"],
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(RULE_PATH),"binding_sha256":sha_file(BIND_PATH),
      "binding_verdict":BIND["source_gate_verdict"],
      "hard_fetch_end_exclusive":RULE["windows"]["hard_fetch_end_exclusive"],
      "coverage":{
        "mexc_rows":len(mexc),"hl_rows":len(hl),"exact_overlap_rows":len(overlap),
        "alignment_ratio":alignment,"calendar_coverage_ratio":calendar_cov,
        "first_overlap_utc":datetime.fromtimestamp(overlap[0],tz=timezone.utc).isoformat(),
        "last_overlap_utc":datetime.fromtimestamp(overlap[-1],tz=timezone.utc).isoformat(),
        "mexc_source":ms,"hyperliquid_source":hs
      },
      "discovery_cells":cells,
      "pre_holm_eligible_count":pre_holm_count,
      "holm_selected_count":len(selected),
      "holm_selected":[
        {"threshold_bps":x["threshold_bps"],"horizon_min":x["horizon_min"],
         "p":x["discovery"]["p_value_vs_50"],"holm_cutoff":x.get("holm_cutoff"),
         "n":x["discovery"]["n"],"mean_gross_bps":x["discovery"]["mean_gross_bps"],
         "win_rate":x["discovery"]["win_rate"]}
        for x in selected
      ],
      "oos_results":oos,
      "oos_survivors":survivors,
      "verdict":"NAS100_CROSSVENUE_OOS_SIGNAL_CANDIDATES_SURVIVE" if survivors else "NO_NAS100_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V06_GATE",
      "october_holdout_opened":False,
      "parameter_rescue_authorized":False,
      "private_endpoints_used":False,"account_reads":False,"wallets_used":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False
    }
    (OUT/"MEXC_HL_NAS100_DISLOCATION_CLOSEOUT_V06.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    flat=[]
    selected_keys={(x["threshold_bps"],x["horizon_min"]) for x in selected}
    for x in cells:
        r=x["discovery"]; flat.append({
          "stage":"DISCOVERY","threshold_bps":x["threshold_bps"],"horizon_min":x["horizon_min"],
          "n":r["n"],"win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
          "p_value_vs_50":r["p_value_vs_50"],"eligible":x["eligible"],
          "selected":(x["threshold_bps"],x["horizon_min"]) in selected_keys
        })
    for x in oos:
        r=x["oos"]; flat.append({
          "stage":"OOS","threshold_bps":x["threshold_bps"],"horizon_min":x["horizon_min"],
          "n":r["n"],"win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
          "p_value_vs_50":r["p_value_vs_50"],"eligible":x["status"]=="OOS_PASS","selected":True
        })
    if flat:
        with (OUT/"MEXC_HL_NAS100_DISLOCATION_MATRIX_V06.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(flat[0])); w.writeheader(); w.writerows(flat)

    print(json.dumps({
      "verdict":report["verdict"],
      "alignment_ratio":alignment,
      "calendar_coverage_ratio":calendar_cov,
      "pre_holm_eligible_count":pre_holm_count,
      "holm_selected_count":len(selected),
      "holm_selected":report["holm_selected"],
      "oos_survivor_count":len(survivors),
      "oos_survivors":[
        {"threshold_bps":x["threshold_bps"],"horizon_min":x["horizon_min"],
         "n":x["oos"]["n"],"mean_gross_bps":x["oos"]["mean_gross_bps"],
         "win_rate":x["oos"]["win_rate"],"p":x["oos"]["p_value_vs_50"],
         "economic_hurdles_cleared":x["oos"]["economic_hurdles_cleared"]}
        for x in survivors
      ],
      "october_holdout_opened":False,
      "live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
