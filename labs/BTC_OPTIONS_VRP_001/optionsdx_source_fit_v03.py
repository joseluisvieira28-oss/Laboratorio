#!/usr/bin/env python3
"""optionsDX public-sample execution-fit probe; source-only and value-redacted."""
from __future__ import annotations
import csv, datetime as dt, io, json, pathlib, statistics, urllib.request
from collections import defaultdict

A=pathlib.Path("labs/BTC_OPTIONS_VRP_001/OPTIONSDX_SOURCE_FIT_AUTHORITY_V0.3.json")
OUT=pathlib.Path("artifacts/btc_options_vrp_optionsdx_source_fit_v03")
OUT.mkdir(parents=True,exist_ok=True)

def norm(s):
    s=(s or "").strip()
    if s.startswith("[") and s.endswith("]"): s=s[1:-1]
    return s.strip().upper().replace(" ","_").replace("-","_")

def positive(v):
    try: return float(v)>0
    except Exception: return False

def main():
    a=json.loads(A.read_text())
    assert a["status"]=="FROZEN_SOURCE_ONLY_PUBLIC_SAMPLE_EXECUTION_FIT"
    assert all(v is False for k,v in a["safety"].items() if k.endswith("_authorized"))
    req=urllib.request.Request(a["public_sample_url"],headers={"User-Agent":"SRC-Crypto-Lab/1.0"})
    with urllib.request.urlopen(req,timeout=90) as resp: raw=resp.read()
    rd=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    mp={norm(c):c for c in (rd.fieldnames or [])}
    need=["QUOTE_UNIXTIME","INSTRUMENT_NAME","EXPIRY_UNIX","DTE","OPTION_RIGHT","STRIKE","BID_SIZE","BID_PRICE","ASK_PRICE","ASK_SIZE"]
    missing=[x for x in need if x not in mp]
    if missing:
        rec={"classification":"SOURCE_ROUTE_SCHEMA_INSUFFICIENT","missing":missing,"outcomes_opened":False}
        (OUT/"OPTIONSDX_SOURCE_FIT_RECEIPT_V0.3.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
        print(json.dumps(rec)); return 2

    checks=a["frozen_fit_checks"]
    by_ts=defaultdict(dict)
    unique_ts=set()
    rows=0
    for row in rd:
        rows+=1
        try:
            ts=int(float(row[mp["QUOTE_UNIXTIME"]]))
            when=dt.datetime.fromtimestamp(ts,tz=dt.timezone.utc)
            dte=float(row[mp["DTE"]])
            strike=float(row[mp["STRIKE"]])
        except Exception:
            continue
        unique_ts.add(ts)
        if not (checks["dte_min"] <= dte <= checks["dte_max"]): continue
        tod=when.time()
        if not (dt.time(8,0) <= tod <= dt.time(12,0)): continue
        right=(row[mp["OPTION_RIGHT"]] or "").strip().lower()
        if right not in {"call","put"}: continue
        if not all(positive(row[mp[x]]) for x in ["BID_SIZE","BID_PRICE","ASK_PRICE","ASK_SIZE"]): continue
        try: expiry=int(float(row[mp["EXPIRY_UNIX"]]))
        except Exception: continue
        key=(expiry,strike)
        by_ts[ts].setdefault(key,set()).add(right)

    allts=sorted(unique_ts)
    intervals=[b-a for a,b in zip(allts,allts[1:]) if b>a]
    candidate_counts={}
    for ts, pairs in by_ts.items():
        candidate_counts[ts]=sum(1 for rights in pairs.values() if {"call","put"} <= rights)
    window_ts=sorted(candidate_counts)
    with_candidates=[ts for ts,c in candidate_counts.items() if c>0]
    near=[]
    for ts in with_candidates:
        when=dt.datetime.fromtimestamp(ts,tz=dt.timezone.utc)
        anchor=when.replace(hour=8,minute=0,second=0,microsecond=0)
        if 0 <= (when-anchor).total_seconds() <= checks["near_anchor_minutes"]*60:
            near.append(ts)

    rec={
      "lab_id":a["lab_id"],"probe_id":a["probe_id"],
      "classification":"OPTIONSDX_PUBLIC_SAMPLE_EXECUTION_FIT_PASS" if window_ts and with_candidates and near else "OPTIONSDX_PUBLIC_SAMPLE_EXECUTION_FIT_FAIL",
      "sample_rows":rows,
      "unique_quote_timestamps":len(allts),
      "median_unique_timestamp_interval_seconds":statistics.median(intervals) if intervals else None,
      "window_timestamps_with_25_35dte_executable_rows":len(window_ts),
      "window_timestamps_with_same_strike_call_put_pairs":len(with_candidates),
      "near_0800_timestamps_with_candidate_pair":len(near),
      "max_candidate_pairs_at_any_window_timestamp":max(candidate_counts.values()) if candidate_counts else 0,
      "option_values_emitted":False,
      "outcomes_opened":False,
      "returns_computed":False,
      "pnl_computed":False,
      "safety":a["safety"]
    }
    (OUT/"OPTIONSDX_SOURCE_FIT_RECEIPT_V0.3.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,sort_keys=True))
    return 0 if rec["classification"]=="OPTIONSDX_PUBLIC_SAMPLE_EXECUTION_FIT_PASS" else 2

if __name__=="__main__": raise SystemExit(main())
