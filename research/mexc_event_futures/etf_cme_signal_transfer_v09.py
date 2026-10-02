#!/usr/bin/env python3
"""
MEXC Event Futures V0.9 — immutable ETF-CME-INSTFLOW signal transfer
using Binance BTCUSDT 5m spot-open history as a cross-source proxy.

Research only. No trading. No auth. No 2026 data.
"""
import csv, io, json, math, time, zipfile, hashlib
from datetime import datetime, timezone
from pathlib import Path
import requests
from scipy.stats import binomtest

HORIZONS=[10,30,60,1440]
P0=1/1.8
PAYOUT=0.80
BH_Q=0.05
Z95=1.959963984540054
MIN_DISC_N=300
MIN_OOS_N=45
MIN_COVERAGE=0.95
UTC=timezone.utc
NO_2026=int(datetime(2026,1,1,tzinfo=UTC).timestamp())

def find_one(root:Path,name:str)->Path:
    hits=list(root.rglob(name))
    if len(hits)!=1:
        raise RuntimeError(f"expected exactly one {name}, got {len(hits)}")
    return hits[0]

def read_parent(path:Path,expected:int,stage:str):
    rows=[]
    with path.open(newline="",encoding="utf-8") as f:
        rd=csv.DictReader(f)
        required={"entry","position"}
        if not required.issubset(set(rd.fieldnames or [])):
            raise RuntimeError(f"{stage}: required columns missing: {rd.fieldnames}")
        for r in rd:
            d=datetime.fromisoformat(r["entry"]).date()
            pos=int(float(r["position"]))
            if d.year>=2026:
                raise RuntimeError(f"{stage}: protected 2026 entry")
            rows.append({"entry_date":d,"position":pos})
    if len(rows)!=expected:
        raise RuntimeError(f"{stage}: expected {expected} rows, got {len(rows)}")
    return rows

def entry_ts(d):
    return int(datetime(d.year,d.month,d.day,tzinfo=UTC).timestamp())

def normalize_ts(raw:int)->int:
    if 1_000_000_000_000 <= raw < 10_000_000_000_000:
        return raw//1000
    if 1_000_000_000_000_000 <= raw < 10_000_000_000_000_000:
        return raw//1_000_000
    raise RuntimeError(f"unexpected timestamp magnitude: {raw}")

def month_pairs_for_needed(needed:set[int]):
    pairs=set()
    for t in needed:
        if t>=NO_2026:
            raise RuntimeError("FAIL-CLOSED needed 2026 timestamp")
        d=datetime.fromtimestamp(t,tz=UTC)
        pairs.add((d.year,d.month))
    return sorted(pairs)

def fetch_needed(needed:set[int]):
    sess=requests.Session()
    sess.headers.update({"User-Agent":"CryptoLab-EventFutures-V09-source-only"})
    found={}
    manifest=[]
    for y,m in month_pairs_for_needed(needed):
        if y>=2026:
            raise RuntimeError("FAIL-CLOSED attempted 2026 archive")
        name=f"BTCUSDT-5m-{y:04d}-{m:02d}.zip"
        url=f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/5m/{name}"
        blob=None
        last=None
        for attempt in range(5):
            try:
                r=sess.get(url,timeout=90)
                if r.status_code!=200:
                    raise RuntimeError(f"HTTP {r.status_code}")
                blob=r.content
                if not blob:
                    raise RuntimeError("empty archive")
                break
            except Exception as e:
                last=e
                if attempt==4:
                    raise RuntimeError(f"source fetch failed {name}: {last}")
                time.sleep(attempt+1)
        sha=hashlib.sha256(blob).hexdigest()
        rows=0
        first_ts=last_ts=None
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            bad=z.testzip()
            if bad is not None:
                raise RuntimeError(f"ZIP CRC failure {name}: {bad}")
            members=[n for n in z.namelist() if not n.endswith("/")]
            if len(members)!=1:
                raise RuntimeError(f"unexpected ZIP members {name}: {members}")
            with z.open(members[0]) as fh:
                rd=csv.reader(io.TextIOWrapper(fh,encoding="utf-8",newline=""))
                for row in rd:
                    if not row:
                        continue
                    rows+=1
                    ts=normalize_ts(int(row[0]))
                    if ts>=NO_2026:
                        raise RuntimeError("FAIL-CLOSED archive contains 2026 row")
                    if first_ts is None:first_ts=ts
                    last_ts=ts
                    if ts in needed:
                        px=float(row[1])
                        if not math.isfinite(px) or px<=0:
                            raise RuntimeError(f"invalid open price {name} {ts}")
                        if ts in found:
                            raise RuntimeError(f"duplicate needed timestamp {ts}")
                        found[ts]=px
        manifest.append({
            "file":name,"url":url,"sha256":sha,"bytes":len(blob),
            "rows":rows,"first_ts":first_ts,"last_ts":last_ts,
        })
        print(f"FETCHED {name} needed_found={len(found)}/{len(needed)}")
    return found,manifest

def wilson_lower(w,l):
    n=w+l
    if not n:return None
    p=w/n;z2=Z95*Z95
    return (p+z2/(2*n)-Z95*math.sqrt((p*(1-p)+z2/(4*n))/n))/(1+z2/n)

def exact_p(w,l):
    n=w+l
    return None if not n else float(binomtest(w,n,P0,alternative="greater").pvalue)

def evaluate(parent,prices,h):
    total=sum(1 for r in parent if r["position"]!=0)
    w=l=ties=missing=0
    years={};quarters={}
    for r in parent:
        pos=r["position"]
        if pos==0:continue
        t=entry_ts(r["entry_date"]);after=t+h*60
        if after>=NO_2026:
            raise RuntimeError("FAIL-CLOSED outcome crosses 2026")
        if t not in prices or after not in prices:
            missing+=1;continue
        d=prices[after]-prices[t]
        if d==0:
            ties+=1;continue
        win=(d>0 and pos>0) or (d<0 and pos<0)
        if win:w+=1
        else:l+=1
        y=str(r["entry_date"].year)
        ys=years.setdefault(y,[0,0]);ys[0 if win else 1]+=1
        q=(r["entry_date"].month-1)//3+1
        qk=f"{r['entry_date'].year}-Q{q}"
        qs=quarters.setdefault(qk,[0,0]);qs[0 if win else 1]+=1
    n=w+l; resolved=n+ties
    return {
        "parent_nonzero_signals":total,
        "wins":w,"losses":l,"ties":ties,"missing":missing,
        "resolved_including_ties":resolved,
        "coverage":resolved/total if total else 0.0,
        "non_ties":n,
        "accuracy":w/n if n else None,
        "wilson95_lower":wilson_lower(w,l),
        "p_value_vs_be80":exact_p(w,l),
        "annual_accuracy":{k:(a/(a+b) if a+b else None) for k,(a,b) in years.items()},
        "quarterly_accuracy":{k:(a/(a+b) if a+b else None) for k,(a,b) in quarters.items()},
        "ev80":((w*PAYOUT-l)/(w+l+ties)) if (w+l+ties) else None,
        "required_payout_for_ev0":(l/w if w else None),
    }

def disc_eligible(r):
    years=[r["annual_accuracy"].get(str(y)) for y in range(2018,2025)]
    source_ok=r["coverage"]>=MIN_COVERAGE
    stats_ok=(
        r["non_ties"]>=MIN_DISC_N and
        r["accuracy"] is not None and r["accuracy"]>P0 and
        r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50 and
        sum(1 for x in years if x is not None and x>0.50)>=5 and
        r["p_value_vs_be80"] is not None
    )
    return source_ok,stats_ok

def bh_select(cells):
    e=[x for x in cells if x["source_ok"] and x["stats_eligible"]]
    e.sort(key=lambda x:x["discovery"]["p_value_vs_be80"])
    m=len(e);cutoff=None
    for rank,x in enumerate(e,1):
        if x["discovery"]["p_value_vs_be80"] <= rank/m*BH_Q:
            cutoff=x["discovery"]["p_value_vs_be80"]
    return ([] if cutoff is None else [x for x in e if x["discovery"]["p_value_vs_be80"]<=cutoff]),m,cutoff

def oos_pass(r):
    qacc=list(r["quarterly_accuracy"].values())
    return (
        r["coverage"]>=MIN_COVERAGE and
        r["non_ties"]>=MIN_OOS_N and
        r["accuracy"] is not None and r["accuracy"]>P0 and
        r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50 and
        r["p_value_vs_be80"] is not None and r["p_value_vs_be80"]<0.05 and
        r["ev80"] is not None and r["ev80"]>0 and
        sum(1 for x in qacc if x is not None and x>0.50)>=3
    )

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--discovery-artifact",required=True)
    ap.add_argument("--oos-artifact",required=True)
    ap.add_argument("--output",default="artifacts/mexc_event_futures")
    a=ap.parse_args()
    outdir=Path(a.output);outdir.mkdir(parents=True,exist_ok=True)

    disc=read_parent(find_one(Path(a.discovery_artifact),"discovery_ledger.csv"),348,"DISCOVERY")
    oos=read_parent(find_one(Path(a.oos_artifact),"oos_2025_observations.csv"),50,"OOS2025")

    needed=set()
    for r in disc+oos:
        if r["position"]==0:continue
        t=entry_ts(r["entry_date"]);needed.add(t)
        for h in HORIZONS:needed.add(t+h*60)
    if max(needed)>=NO_2026:
        raise RuntimeError("FAIL-CLOSED source set crosses 2026")

    prices,manifest=fetch_needed(needed)

    cells=[]
    for h in HORIZONS:
        r=evaluate(disc,prices,h)
        source_ok,stats_ok=disc_eligible(r)
        cells.append({"horizon_min":h,"source_ok":source_ok,"stats_eligible":stats_ok,"discovery":r})

    selected,m,cutoff=bh_select(cells)
    oos_results=[];survivors=[]
    for c in selected:
        r=evaluate(oos,prices,c["horizon_min"])
        passed=oos_pass(r)
        item={"horizon_min":c["horizon_min"],"oos":r,"pass":passed}
        oos_results.append(item)
        if passed:
            survivors.append({"horizon_min":c["horizon_min"],"discovery":c["discovery"],"oos":r})

    if all(not c["source_ok"] for c in cells):
        verdict="SOURCE_BLOCKED_BINANCE_5M_HISTORY"
    elif any(not c["source_ok"] for c in cells):
        verdict="PARTIAL_SOURCE_BLOCK__NO_PROMOTION"
    elif survivors:
        verdict="CROSS_SOURCE_PROXY_CANDIDATE__ETF_CME_SIGNAL_TRANSFER"
    else:
        verdict="NO_PROXY_SURVIVOR_AT_FROZEN_V09_GATE"

    report={
        "lab":"MEXC_EVENT_FUTURES_ETF_CME_SIGNAL_TRANSFER_V0.9",
        "generated_at_utc":datetime.now(UTC).isoformat(),
        "source":"BINANCE_SPOT_BTCUSDT_MONTHLY_5M_OPEN_PROXY",
        "exact_event_futures":"NOT_PROVEN",
        "year_2026_accessed":False,
        "reference_payout":PAYOUT,
        "reference_break_even_accuracy":P0,
        "parent_discovery_rows":len(disc),
        "parent_oos_rows":len(oos),
        "parent_artifacts":{
            "discovery_run_id":34814321802,
            "discovery_artifact_id":10336122105,
            "oos_run_id":34815006815,
            "oos_artifact_id":10335473231,
        },
        "needed_price_points":len(needed),
        "resolved_price_points":len(prices),
        "source_manifest":manifest,
        "discovery_cells":cells,
        "bh_eligible_count":m,
        "bh_cutoff_p":cutoff,
        "bh_selected":[{"horizon_min":x["horizon_min"],"discovery":x["discovery"]} for x in selected],
        "oos_results":oos_results,
        "oos_survivors":survivors,
        "verdict":verdict,
        "promotion_status":"NO_EXACT_EVENT_FUTURES_PROMOTION",
    }
    p=outdir/"etf_cme_signal_transfer_v09.json"
    p.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    compact={
        "verdict":verdict,
        "archive_count":len(manifest),
        "needed_price_points":len(needed),
        "resolved_price_points":len(prices),
        "discovery_cells":[{
            "horizon_min":x["horizon_min"],"coverage":x["discovery"]["coverage"],
            "n":x["discovery"]["non_ties"],"accuracy":x["discovery"]["accuracy"],
            "wilson95_lower":x["discovery"]["wilson95_lower"],
            "p":x["discovery"]["p_value_vs_be80"],
            "annual_accuracy":x["discovery"]["annual_accuracy"],
            "ev80":x["discovery"]["ev80"],
            "source_ok":x["source_ok"],"stats_eligible":x["stats_eligible"],
        } for x in cells],
        "bh_eligible_count":m,"bh_selected_count":len(selected),"bh_cutoff_p":cutoff,
        "oos_results":[{
            "horizon_min":x["horizon_min"],"coverage":x["oos"]["coverage"],
            "n":x["oos"]["non_ties"],"accuracy":x["oos"]["accuracy"],
            "wilson95_lower":x["oos"]["wilson95_lower"],
            "p":x["oos"]["p_value_vs_be80"],"ev80":x["oos"]["ev80"],
            "quarterly_accuracy":x["oos"]["quarterly_accuracy"],"pass":x["pass"],
        } for x in oos_results],
        "oos_survivor_count":len(survivors),
        "year_2026_accessed":False,"exact_event_futures":"NOT_PROVEN",
    }
    print(json.dumps(compact,indent=2,sort_keys=True))
    print("WROTE",p)

if __name__=="__main__":
    main()
