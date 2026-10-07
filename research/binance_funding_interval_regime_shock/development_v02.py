#!/usr/bin/env python3
from __future__ import annotations
import csv, io, json, math, os, random, statistics, time, zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

FAMILY="BINANCE-FUNDING-INTERVAL-REGIME-SHOCK-001"
SOURCE=Path("source_receipt/bfirs_v01_source_gate_report.json")
OUT=Path("bfirs_v02_development_report.json")
CACHE=Path(".bfirs_cache"); CACHE.mkdir(exist_ok=True)
CONTROLS=("BTCUSDT","ETHUSDT","BNBUSDT")
MIN_BARS=54
FLOOR=0.00020
BOOTSTRAPS=10000
SEED=26061007
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"Mozilla/5.0 CryptoLab-BFIRS-V02/1.0","Accept":"*/*"})

class DataError(Exception): pass

def dt_from_ms(ms:int)->datetime:
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc)

def ceil_next_minute(d:datetime)->datetime:
    d=d.astimezone(timezone.utc)
    base=d.replace(second=0,microsecond=0)
    return base+timedelta(minutes=1)

def month_keys(start:datetime,end:datetime):
    cur=datetime(start.year,start.month,1,tzinfo=timezone.utc)
    z=end-timedelta(microseconds=1)
    last=datetime(z.year,z.month,1,tzinfo=timezone.utc)
    out=[]
    while cur<=last:
        out.append(cur.strftime("%Y-%m"))
        cur=datetime(cur.year+1,1,1,tzinfo=timezone.utc) if cur.month==12 else datetime(cur.year,cur.month+1,1,tzinfo=timezone.utc)
    return out

def floor_ms(x:int)->int:
    return x//1000 if x>100_000_000_000_000 else x

def archive_url(symbol,ym):
    return f"https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines/{symbol}/1m/{symbol}-1m-{ym}.zip"

def download(symbol,ym):
    p=CACHE/f"{symbol}-premium-1m-{ym}.zip"
    if p.exists() and p.stat().st_size>0: return p
    u=archive_url(symbol,ym); last=None
    for i in range(5):
        try:
            r=SESSION.get(u,timeout=60)
            if r.status_code==200 and r.content[:2]==b"PK":
                tmp=p.with_suffix(".tmp"); tmp.write_bytes(r.content); os.replace(tmp,p); return p
            last=DataError(f"http_{r.status_code}")
            if r.status_code==404: break
        except Exception as e:
            last=e
        time.sleep(min(20,2**i))
    raise DataError(f"archive_unavailable:{symbol}:{ym}:{last}")

def read_window(path,start_ms,end_ms):
    out={}
    with zipfile.ZipFile(path) as zf:
        names=[n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(names)!=1: raise DataError(f"zip_members:{len(names)}")
        with zf.open(names[0]) as raw:
            txt=io.TextIOWrapper(raw,encoding="utf-8",newline="")
            for row in csv.reader(txt):
                if not row: continue
                try: ot=floor_ms(int(row[0]))
                except: continue
                if not(start_ms<=ot<end_ms): continue
                if ot in out: raise DataError(f"duplicate:{ot}")
                if len(row)<5: raise DataError("short_row")
                try: close=float(row[4])
                except: raise DataError("bad_close")
                out[ot]=close
    return out

def load(symbol,start,end):
    sm=int(start.timestamp()*1000); em=int(end.timestamp()*1000)
    out={}
    for ym in month_keys(start,end):
        part=read_window(download(symbol,ym),sm,em)
        if set(out).intersection(part): raise DataError("duplicate_across_archives")
        out.update(part)
    return out

def valid_metric(rows,start,end):
    expected=int((end-start).total_seconds()//60)
    if expected!=60: raise DataError(f"window_not_60:{expected}")
    if len(rows)<MIN_BARS: raise DataError(f"bars_lt_{MIN_BARS}:{len(rows)}")
    vals=[]
    for _,v in rows.items():
        if not math.isfinite(v): raise DataError("nonfinite_premium")
        vals.append(abs(v))
    return statistics.median(vals)

def raw_compression(symbol,t0):
    tm=ceil_next_minute(t0)
    b0=tm-timedelta(minutes=65); b1=tm-timedelta(minutes=5)
    p0=tm+timedelta(minutes=5); p1=tm+timedelta(minutes=65)
    pre=valid_metric(load(symbol,b0,b1),b0,b1)
    post=valid_metric(load(symbol,p0,p1),p0,p1)
    return {"pre_abs_median":pre,"post_abs_median":post,"C_raw":pre-post}

def median(xs): return statistics.median(xs)

def sign_test(vals):
    n=len(vals); k=sum(1 for x in vals if x>0)
    p=sum(math.comb(n,i) for i in range(k,n+1))/(2**n)
    return {"n":n,"successes":k,"failures_including_zero":n-k,"p_one_sided":p}

def percentile(a,q):
    if len(a)==1: return a[0]
    h=(len(a)-1)*q; lo=math.floor(h); hi=math.ceil(h)
    if lo==hi: return a[lo]
    w=h-lo
    return a[lo]*(1-w)+a[hi]*w

def bootstrap_ci(vals):
    rng=random.Random(SEED); n=len(vals); sims=[]
    for _ in range(BOOTSTRAPS):
        sims.append(median([vals[rng.randrange(n)] for __ in range(n)]))
    sims.sort()
    return [percentile(sims,0.025),percentile(sims,0.975)]

def main():
    src=json.load(open(SOURCE,encoding="utf-8"))
    assert src["family"]==FAMILY
    assert src["verdict"]=="SOURCE_GATE_PASS"
    assert src["outcome_access"]=="NONE"
    assert src["eligible_asset_events"]==35
    assert src["independent_clusters"]==30
    assert src["unique_contracts"]==27
    assert src["years"]==[2023,2024,2025]

    clusters=defaultdict(list)
    for e in src["eligible_events"]:
        k=f"{e['article_code']}@{e['effective_utc']}@{e['old_interval_hours']}to{e['new_interval_hours']}"
        clusters[k].append(e)

    events_out=[]; excluded=[]; cluster_out=[]
    for idx,(k,evs) in enumerate(sorted(clusters.items(),key=lambda kv:min(x["release_ms"] for x in kv[1])),start=1):
        releases={x["release_ms"] for x in evs}
        if len(releases)!=1: raise RuntimeError(f"release_conflict:{k}")
        t0=dt_from_ms(next(iter(releases)))
        treated={x["symbol"] for x in evs}
        control_syms=[c for c in CONTROLS if c not in treated]
        cvals={}; cerr={}
        for c in control_syms:
            try: cvals[c]=raw_compression(c,t0)
            except Exception as ex: cerr[c]=f"{type(ex).__name__}:{ex}"
        valid_controls=sorted(cvals)
        if len(valid_controls)<2:
            for e in evs:
                excluded.append({"cluster":k,"symbol":e["symbol"],"reason":"fewer_than_two_valid_controls","control_errors":cerr})
            print(f"CLUSTER_PROGRESS={idx}/{len(clusters)} analyzable=0 reason=controls")
            continue
        cmed=median([cvals[c]["C_raw"] for c in valid_controls])
        cres=[]
        for e in sorted(evs,key=lambda x:x["symbol"]):
            try:
                tr=raw_compression(e["symbol"],t0)
                ce=tr["C_raw"]-cmed
                rec={
                  "cluster":k,"article_code":e["article_code"],"release_ms":e["release_ms"],
                  "release_utc":t0.isoformat().replace("+00:00","Z"),
                  "effective_utc":e["effective_utc"],"symbol":e["symbol"],
                  "old_interval_hours":e["old_interval_hours"],"new_interval_hours":e["new_interval_hours"],
                  "controls":valid_controls,"treated":tr,"control_median_C_raw":cmed,"C_e":ce
                }
                events_out.append(rec); cres.append(rec)
            except Exception as ex:
                excluded.append({"cluster":k,"symbol":e["symbol"],"reason":f"{type(ex).__name__}:{ex}"})
        if cres:
            ck=median([x["C_e"] for x in cres])
            cluster_out.append({
              "cluster":k,"release_ms":next(iter(releases)),
              "release_utc":t0.isoformat().replace("+00:00","Z"),
              "year":t0.year,"analyzable_events":len(cres),
              "symbols":sorted(x["symbol"] for x in cres),"C_k":ck
            })
        print(f"CLUSTER_PROGRESS={idx}/{len(clusters)} analyzable={len(cres)}")

    n_events=len(events_out); n_clusters=len(cluster_out)
    assets=sorted({x["symbol"] for x in events_out})
    years=sorted({x["year"] for x in cluster_out})
    max_cluster=max((x["analyzable_events"] for x in cluster_out),default=0)
    conc=max_cluster/n_events if n_events else 1.0
    sample_gates={
      "clusters_ge_12":n_clusters>=12,
      "asset_events_ge_20":n_events>=20,
      "unique_contracts_ge_8":len(assets)>=8,
      "years_ge_2":len(years)>=2,
      "max_cluster_le_35pct":conc<=0.35,
      "analyzable_ge_80pct":n_events>=math.ceil(0.80*35),
    }

    cks=[x["C_k"] for x in cluster_out]
    if cks:
        med=median(cks); sign=sign_test(cks); boot=bootstrap_ci(cks)
        ordered=sorted(cluster_out,key=lambda x:x["release_ms"])
        split=len(ordered)//2
        early=[x["C_k"] for x in ordered[:split]]
        late=[x["C_k"] for x in ordered[split:]]
        early_med=median(early) if early else float("nan")
        late_med=median(late) if late else float("nan")
    else:
        med=float("nan"); sign={"n":0,"successes":0,"failures_including_zero":0,"p_one_sided":1.0}
        boot=[float("nan"),float("nan")]; early_med=late_med=float("nan")

    primary_gates={
      "median_C_ge_2bps":math.isfinite(med) and med>=FLOOR,
      "sign_test_p_lt_0_05":sign["p_one_sided"]<0.05,
      "bootstrap_ci_lower_gt_0":math.isfinite(boot[0]) and boot[0]>0,
      "early_half_median_gt_0":math.isfinite(early_med) and early_med>0,
      "late_half_median_gt_0":math.isfinite(late_med) and late_med>0,
    }
    verdict="SURVIVES_FUNDING_INTERVAL_DISCOVERY" if all(sample_gates.values()) and all(primary_gates.values()) else "NO_EDGE_DISCOVERY"

    report={
      "family":FAMILY,"stage":"V0.2_ONE_SHOT_DEVELOPMENT","verdict":verdict,
      "source_pin":{"workflow_run":37570814145,"head_sha":"71c3a50722f8c9d231f052dda2e550ec56cf9947",
                    "artifact_id":11460134993,"artifact_digest":"sha256:ffb8dc3d9ddcd70e71fd65b26f5be2163ddc9d15a041231f10338019fec5a4fb"},
      "governance":{"calendar":"2023-2025","year_2026_opened":False,"authenticated_endpoint_used":False,
                    "private_endpoint_used":False,"trading_or_order_mutation":False,"main_modified":False,"post_outcome_tuning":False},
      "source_events":35,"source_clusters":30,
      "analyzable_asset_events":n_events,"excluded_asset_events":len(excluded),
      "analyzable_clusters":n_clusters,"unique_analyzable_contracts":len(assets),"analyzable_years":years,
      "max_cluster_concentration":conc,"sample_gates":sample_gates,
      "primary_metrics":{"median_C_k":med,"economic_floor":FLOOR,"sign_test":sign,
                         "bootstrap_median_C_95ci":boot,"bootstrap_resamples":BOOTSTRAPS,"bootstrap_seed":SEED,
                         "early_half_median_C":early_med,"late_half_median_C":late_med},
      "primary_gates":primary_gates,
      "descriptive":{"median_treated_raw_C":median([x["treated"]["C_raw"] for x in events_out]) if events_out else None,
                     "year_counts":dict(Counter(x["year"] for x in cluster_out)),
                     "exclusion_reasons":dict(Counter(x["reason"].split(":",1)[0] for x in excluded))},
      "cluster_results":cluster_out,"event_results":events_out,"excluded":excluded
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print("BFIRS_V02_VERDICT="+verdict)
    print("ANALYZABLE_EVENTS="+str(n_events))
    print("EXCLUDED_EVENTS="+str(len(excluded)))
    print("ANALYZABLE_CLUSTERS="+str(n_clusters))
    print("UNIQUE_CONTRACTS="+str(len(assets)))
    print("YEARS="+json.dumps(years))
    print("MAX_CLUSTER_CONCENTRATION="+str(conc))
    print("MEDIAN_C_K="+str(med))
    print("SIGN_TEST="+json.dumps(sign,sort_keys=True))
    print("BOOTSTRAP_MEDIAN_C_95CI="+json.dumps(boot))
    print("EARLY_HALF_MEDIAN_C="+str(early_med))
    print("LATE_HALF_MEDIAN_C="+str(late_med))
    print("SAMPLE_GATES="+json.dumps(sample_gates,sort_keys=True))
    print("PRIMARY_GATES="+json.dumps(primary_gates,sort_keys=True))
    print("GOVERNANCE: research-only; 2026 closed; no trading/private endpoints/main mutation")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
