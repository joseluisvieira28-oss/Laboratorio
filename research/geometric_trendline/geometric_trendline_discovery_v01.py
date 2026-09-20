#!/usr/bin/env python3
from __future__ import annotations

import csv, hashlib, io, json, math, random, re, statistics, sys, time, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geometric_trendline_core_v01 import (
    Bar, PRIMARY_H, discover_events_in_segment, evaluate_event_responses,
    utc_iso_week, utc_year_month,
)

LAB_ID="GEOMETRIC-TRENDLINE-001"
MVE_ID="GTL-THIRDTOUCH-REJECTION-1H-001"
BASE="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m"
START_YEAR,START_MONTH=2021,1
END_YEAR,END_MONTH=2024,12
EXPECTED_MONTHS=48
BOOTSTRAP_REPS=10000
BOOTSTRAP_SEED=20260920
OUTDIR=Path("research/geometric_trendline/discovery_output")
RECEIPT=OUTDIR/"GEOMETRIC_TRENDLINE_001_DISCOVERY_2021_2024_RECEIPT_V0_1.json"
EVENTS_CSV=OUTDIR/"GEOMETRIC_TRENDLINE_001_DISCOVERY_EVENTS_V0_1.csv"
SOURCE_MANIFEST=OUTDIR/"GEOMETRIC_TRENDLINE_001_SOURCE_MANIFEST_V0_1.json"

def months():
    y,m=START_YEAR,START_MONTH
    while (y,m)<=(END_YEAR,END_MONTH):
        yield y,m
        m+=1
        if m==13: y,m=y+1,1

def http_get(url,attempts=4):
    last=None
    for k in range(attempts):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-GTL/0.1"})
            with urllib.request.urlopen(req,timeout=60) as r:
                if not (200<=int(r.status)<300): raise RuntimeError(f"HTTP {r.status}")
                return r.read()
        except Exception as e:
            last=e
            if k+1<attempts: time.sleep(2**k)
    raise RuntimeError(f"GET failed {url}: {type(last).__name__}: {last}")

def month_start_ms(y,m):
    return int(datetime(y,m,1,tzinfo=timezone.utc).timestamp()*1000)

def next_month_start_ms(y,m):
    if m==12: dt=datetime(y+1,1,1,tzinfo=timezone.utc)
    else: dt=datetime(y,m+1,1,tzinfo=timezone.utc)
    return int(dt.timestamp()*1000)

def parse_checksum(raw,expected_name):
    line=raw.decode("utf-8","strict").strip().splitlines()[0]
    mm=re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)",line)
    if not mm or mm.group(2).strip()!=expected_name:
        raise RuntimeError(f"invalid checksum binding for {expected_name}: {line!r}")
    return mm.group(1).lower()

def aggregate_month_zip(zip_bytes,y,m):
    start_ms,end_ms=month_start_ms(y,m),next_month_start_ms(y,m)
    bars=[]; invalid_hours=[]; rows_seen=0
    with zipfile.ZipFile(io.BytesIO(zip_bytes),"r") as zf:
        members=[n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(members)!=1: raise RuntimeError(f"expected one CSV member, got {members}")
        with zf.open(members[0],"r") as fh:
            reader=csv.reader(io.TextIOWrapper(fh,encoding="utf-8",newline=""))
            cur_hour=None; state=None
            def finalize():
                nonlocal state
                if state is None: return
                valid=(state["count"]==60 and state["first_ts"]==state["hour"] and state["last_ts"]==state["hour"]+59*60000 and not state["bad_sequence"])
                if valid:
                    bars.append(Bar(state["hour"],state["open"],state["high"],state["low"],state["close"],state["volume"]))
                else:
                    invalid_hours.append({"hour_ts_ms":state["hour"],"count":state["count"],"first_ts":state["first_ts"],"last_ts":state["last_ts"],"bad_sequence":state["bad_sequence"]})
                state=None
            for row in reader:
                if not row or not row[0].strip().isdigit(): continue
                if len(row)<6: raise RuntimeError("malformed kline row")
                ts=int(row[0])
                if ts>=100000000000000: raise RuntimeError("unexpected microsecond timestamp in frozen 2021-2024 source")
                if not (start_ms<=ts<end_ms): raise RuntimeError(f"row outside frozen month: {ts}")
                if ts>=1735689600000: raise RuntimeError("protected 2025+ timestamp encountered")
                rows_seen+=1
                hour=(ts//3600000)*3600000
                o,h,l,c,v=map(float,row[1:6])
                if cur_hour is None or hour!=cur_hour:
                    finalize(); cur_hour=hour
                    state={"hour":hour,"count":0,"first_ts":ts,"last_ts":ts,"expected_ts":hour,"bad_sequence":False,"open":o,"high":h,"low":l,"close":c,"volume":0.0}
                if ts!=state["expected_ts"]: state["bad_sequence"]=True
                state["count"]+=1; state["last_ts"]=ts; state["expected_ts"]=ts+60000
                state["high"]=max(state["high"],h); state["low"]=min(state["low"],l); state["close"]=c; state["volume"]+=v
            finalize()
    return bars,invalid_hours,rows_seen

def build_segments(all_bars):
    ordered=sorted(all_bars,key=lambda b:b.ts_ms)
    if len({b.ts_ms for b in ordered})!=len(ordered): raise RuntimeError("duplicate valid 1H timestamps")
    segments=[]; cur=[]; prev=None
    for b in ordered:
        if prev is None or b.ts_ms==prev+3600000: cur.append(b)
        else:
            if cur: segments.append(cur)
            cur=[b]
        prev=b.ts_ms
    if cur: segments.append(cur)
    return segments

def type7_percentile(values,p):
    xs=sorted(values)
    if not xs: return None
    if len(xs)==1: return xs[0]
    h=(len(xs)-1)*p; lo=int(math.floor(h)); hi=int(math.ceil(h))
    if lo==hi: return xs[lo]
    f=h-lo
    return xs[lo]*(1-f)+xs[hi]*f

def clustered_bootstrap_ci(rows):
    clusters=defaultdict(list)
    for r in rows: clusters[utc_iso_week(int(r["ts_ms"]))].append(float(r[f"response_{PRIMARY_H}h_bps"]))
    keys=sorted(clusters)
    if not keys: return None,None,0
    rng=random.Random(BOOTSTRAP_SEED); means=[]
    for _ in range(BOOTSTRAP_REPS):
        vals=[]
        for _j in range(len(keys)): vals.extend(clusters[keys[rng.randrange(len(keys))]])
        means.append(statistics.fmean(vals))
    return type7_percentile(means,.025),type7_percentile(means,.975),len(keys)

def mean_or_none(xs):
    vals=[float(x) for x in xs if x is not None]
    return statistics.fmean(vals) if vals else None

def sha256_json(obj):
    raw=json.dumps(obj,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def main():
    OUTDIR.mkdir(parents=True,exist_ok=True)
    source_rows=[]; all_bars=[]; invalid_total=0; minute_rows_total=0
    for y,m in months():
        fn=f"BTCUSDT-1m-{y:04d}-{m:02d}.zip"
        expected_sha=parse_checksum(http_get(f"{BASE}/{fn}.CHECKSUM"),fn)
        zip_bytes=http_get(f"{BASE}/{fn}")
        observed_sha=hashlib.sha256(zip_bytes).hexdigest()
        if observed_sha!=expected_sha: raise RuntimeError(f"checksum mismatch {fn}")
        month_bars,invalid_hours,row_count=aggregate_month_zip(zip_bytes,y,m)
        minute_rows_total+=row_count; invalid_total+=len(invalid_hours); all_bars.extend(month_bars)
        source_rows.append({"month":f"{y:04d}-{m:02d}","filename":fn,"sha256":observed_sha,"zip_bytes":len(zip_bytes),"minute_rows":row_count,"valid_1h_bars":len(month_bars),"invalid_1h_hours":len(invalid_hours),"invalid_hour_examples":invalid_hours[:5]})
        print(f"SOURCE {y:04d}-{m:02d} PASS rows={row_count} valid_1h={len(month_bars)} invalid_1h={len(invalid_hours)}")
    if len(source_rows)!=EXPECTED_MONTHS: raise RuntimeError("month count mismatch")

    source_manifest={"lab_id":LAB_ID,"mve_id":MVE_ID,"source":"Binance Data Vision official Spot BTCUSDT monthly 1m","window":"2021-01 through 2024-12","months_expected":EXPECTED_MONTHS,"months_verified":len(source_rows),"minute_rows_total":minute_rows_total,"valid_1h_bars_total":len(all_bars),"invalid_1h_hours_total":invalid_total,"rows":source_rows,"guards":{"2025_accessed":False,"2026_accessed":False,"alternate_source_used":False}}
    source_manifest["manifest_sha256"]=sha256_json(source_manifest)
    SOURCE_MANIFEST.write_text(json.dumps(source_manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    segments=build_segments(all_bars)
    if not segments: raise RuntimeError("no valid 1H segments")
    all_event_rows=[]; aggregate_stats=defaultdict(int)
    for seg_id,seg in enumerate(segments):
        events,stats=discover_events_in_segment(seg)
        for k,v in stats.items(): aggregate_stats[k]+=int(v)
        rows=evaluate_event_responses(seg,events,horizons=(1,3,6,12,24))
        for r in rows: r["segment_id"]=seg_id; all_event_rows.append(r)

    pk=f"response_{PRIMARY_H}h_bps"
    primary_rows=[r for r in all_event_rows if r[pk] is not None]
    support_rows=[r for r in primary_rows if r["side"]=="support"]
    resistance_rows=[r for r in primary_rows if r["side"]=="resistance"]
    months_present=sorted({utc_year_month(int(r["ts_ms"])) for r in primary_rows})
    sample_gate={"total_gte_200":len(primary_rows)>=200,"support_gte_75":len(support_rows)>=75,"resistance_gte_75":len(resistance_rows)>=75,"months_gte_36":len(months_present)>=36}
    sample_pass=all(sample_gate.values())
    global_mean=mean_or_none([r[pk] for r in primary_rows]); support_mean=mean_or_none([r[pk] for r in support_rows]); resistance_mean=mean_or_none([r[pk] for r in resistance_rows])
    ci_low,ci_high,bootstrap_weeks=clustered_bootstrap_ci(primary_rows) if primary_rows else (None,None,0)

    by_year={}
    for year in (2021,2022,2023,2024):
        vals=[r[pk] for r in primary_rows if utc_year_month(int(r["ts_ms"]))[0]==year]
        by_year[str(year)]={"n":len(vals),"mean_bps":mean_or_none(vals)}
    positive_years=sum(1 for v in by_year.values() if v["mean_bps"] is not None and v["mean_bps"]>0)
    pass_gate={"sample_viability":sample_pass,"global_mean_gt_0":global_mean is not None and global_mean>0,"bootstrap_lower_gt_0":ci_low is not None and ci_low>0,"support_mean_gt_0":support_mean is not None and support_mean>0,"resistance_mean_gt_0":resistance_mean is not None and resistance_mean>0,"positive_years_gte_3":positive_years>=3}
    if not sample_pass: classification="DISCOVERY_INSUFFICIENT_SAMPLE"
    elif all(pass_gate.values()): classification="DISCOVERY_MECHANISM_PASS"
    else: classification="DISCOVERY_FAIL_NO_PROMOTION"

    diagnostic_means={}
    for h in (1,3,12,24):
        key=f"response_{h}h_bps"
        diagnostic_means[f"{h}h"]={"n":sum(1 for r in all_event_rows if r[key] is not None),"mean_bps":mean_or_none([r[key] for r in all_event_rows])}

    fields=["segment_id","ts_ms","side","direction","event_close","line_price","p1_idx","p2_idx","p1_price","p2_price","response_1h_bps","response_3h_bps","response_6h_bps","response_12h_bps","response_24h_bps"]
    with EVENTS_CSV.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader()
        for r in all_event_rows: w.writerow({k:r.get(k) for k in fields})

    receipt={"schema_version":"0.1","lab_id":LAB_ID,"mve_id":MVE_ID,"protocol":"GEOMETRIC_TRENDLINE_001_PREDISCOVERY_PROTOCOL_V0_1","classification":classification,
      "source":{"months_expected":EXPECTED_MONTHS,"months_verified":len(source_rows),"minute_rows_total":minute_rows_total,"valid_1h_bars_total":len(all_bars),"invalid_1h_hours_total":invalid_total,"segments":len(segments),"source_manifest_sha256":source_manifest["manifest_sha256"]},
      "event_generation":dict(sorted(aggregate_stats.items())),
      "primary":{"horizon_hours":PRIMARY_H,"n":len(primary_rows),"support_n":len(support_rows),"resistance_n":len(resistance_rows),"months_with_events":len(months_present),"global_mean_bps":global_mean,"support_mean_bps":support_mean,"resistance_mean_bps":resistance_mean,"bootstrap_ci95_low_bps":ci_low,"bootstrap_ci95_high_bps":ci_high,"bootstrap_weeks":bootstrap_weeks,"bootstrap_reps":BOOTSTRAP_REPS,"bootstrap_seed":BOOTSTRAP_SEED,"bootstrap_percentile":"linear_type7","by_year":by_year,"positive_years":positive_years,"sample_gate":sample_gate,"pass_gate":pass_gate},
      "secondary_diagnostics_not_promotion_gates":diagnostic_means,
      "guards":{"2025_accessed":False,"2026_accessed":False,"live_trading":False,"exchange_mutation":False,"orders_created":False,"wallets_used":False,"pnl_computed":False,"fees_slippage_modeled":False,"post_outcome_retuning":False,"main_merge":False},
      "post_outcome_rule":"NO RESCUE / NO RETUNING. Exact V0.1 MVE verdict is immutable."}
    RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":classification,"n":len(primary_rows),"support_n":len(support_rows),"resistance_n":len(resistance_rows),"global_mean_bps":global_mean,"ci95_low_bps":ci_low,"ci95_high_bps":ci_high,"positive_years":positive_years,"sample_gate":sample_gate,"pass_gate":pass_gate},indent=2,sort_keys=True))

if __name__=="__main__":
    main()
