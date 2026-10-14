#!/usr/bin/env python3
"""One-shot 2022-2024 Bitwise index-rebalance mechanism Discovery."""

from __future__ import annotations
import csv
import datetime as dt
import hashlib
import io
import json
import math
import random
import statistics
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

OUT=Path("artifacts/crypto_index_rebalance_flow")
UA="CryptoLab-Bitwise-Discovery/0.1"
BASE="https://data.binance.vision/data/spot/daily/klines/{symbol}/1m/{symbol}-1m-{date}.zip"
SEED=230911
BOOT=10000
EXCLUDED={("2024-09-29","MATIC","REMOVE")}
EXPECTED_EVENT_SET_SHA="fffaa5aab3ba17456358af230c3aeda10a74ba55078b6c98b3d1585916db5a17"

def get(url:str)->bytes:
    assert "/2025-" not in url and "/2026-" not in url, "HOLDOUT_FIREWALL"
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=45) as r:
        return r.read()

def verify_and_load(symbol:str,day:str,cache:dict)->tuple[bytes,dict]:
    key=(symbol,day)
    if key in cache:
        return cache[key]
    url=BASE.format(symbol=symbol,date=day)
    checksum_raw=get(url+".CHECKSUM")
    checksum_text=checksum_raw.decode("utf-8","replace").strip()
    expected=checksum_text.split()[0].lower()
    raw=get(url)
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected:
        raise RuntimeError(f"CHECKSUM_MISMATCH {symbol} {day}: {actual} != {expected}")
    meta={"symbol":symbol,"date":day,"url":url,"bytes":len(raw),"sha256":actual,"checksum_text_sha256":hashlib.sha256(checksum_raw).hexdigest()}
    cache[key]=(raw,meta)
    return raw,meta

def exact_open(raw:bytes,target_ms:int)->float|None:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if not n.endswith("/") and "__MACOSX" not in n]
        if len(names)!=1:
            raise RuntimeError("UNEXPECTED_ZIP_CONTENTS "+repr(names))
        with z.open(names[0]) as f:
            reader=csv.reader(io.TextIOWrapper(f,encoding="utf-8"))
            for row in reader:
                if not row:
                    continue
                try:
                    ts=int(row[0])
                except ValueError:
                    continue
                if ts==target_ms:
                    return float(row[1])
    return None

def t0_utc(date_s:str)->dt.datetime:
    d=dt.date.fromisoformat(date_s)
    local=dt.datetime(d.year,d.month,d.day,16,0,0,tzinfo=ZoneInfo("America/New_York"))
    return local.astimezone(dt.timezone.utc)

def pctile(xs:list[float],q:float)->float:
    ys=sorted(xs)
    if not ys:
        raise ValueError("empty percentile")
    pos=(len(ys)-1)*q
    lo=math.floor(pos); hi=math.ceil(pos)
    if lo==hi:
        return ys[lo]
    w=pos-lo
    return ys[lo]*(1-w)+ys[hi]*w

def bootstrap_ci(rows:list[dict],field:str)->tuple[float,float]:
    rng=random.Random(SEED)
    vals=[r[field] for r in rows]
    n=len(vals)
    stats=[]
    for _ in range(BOOT):
        sample=[vals[rng.randrange(n)] for _ in range(n)]
        stats.append(statistics.mean(sample))
    return pctile(stats,0.025),pctile(stats,0.975)

def main()->int:
    OUT.mkdir(parents=True,exist_ok=True)

    # Source normalization is deterministic and outcome-blind.
    import subprocess,sys
    subprocess.run([sys.executable,"research/crypto_index_rebalance_flow/event_normalization.py"],check=True)
    norm=json.loads((OUT/"event_normalization_v0.1.json").read_text())
    if norm.get("event_set_sha256")!=EXPECTED_EVENT_SET_SHA:
        raise RuntimeError("EVENT_SET_IDENTITY_MISMATCH")

    events=[
        e for e in norm["events"]
        if e["period_role"]=="DISCOVERY_SOURCE"
        and (e["rebalance_date"],e["ticker"],e["direction"]) not in EXCLUDED
    ]
    assert len(events)==68
    assert all(e["rebalance_date"].startswith(("2022-","2023-","2024-")) for e in events)

    file_cache={}
    file_manifest={}
    boundary_cache={}
    legs=[]
    boundary_exclusions=[]

    for e in events:
        date=e["rebalance_date"]
        symbol=e["ticker"]+"USDT"
        center=t0_utc(date)
        times={"pre":center-dt.timedelta(hours=24),"t0":center,"post":center+dt.timedelta(hours=24)}
        prices={}
        for label,t in times.items():
            day=t.date().isoformat()
            target_ms=int(t.timestamp()*1000)
            for sym,keyprefix in ((symbol,"asset"),("BTCUSDT","btc")):
                ck=(sym,day,target_ms)
                if ck not in boundary_cache:
                    raw,meta=verify_and_load(sym,day,file_cache)
                    file_manifest[(sym,day)]=meta
                    boundary_cache[ck]=exact_open(raw,target_ms)
                prices[f"{keyprefix}_{label}"]=boundary_cache[ck]

        missing=[k for k,v in prices.items() if v is None]
        if missing:
            boundary_exclusions.append({**e,"missing_boundaries":missing})
            continue

        apre=math.log(prices["asset_t0"]/prices["asset_pre"])
        bpre=math.log(prices["btc_t0"]/prices["btc_pre"])
        apost=math.log(prices["asset_post"]/prices["asset_t0"])
        bpost=math.log(prices["btc_post"]/prices["btc_t0"])
        sign=1.0 if e["direction"]=="ADD" else -1.0
        legs.append({
            **e,
            "t0_utc":center.isoformat(),
            "signed_pre_bps":sign*(apre-bpre)*10000.0,
            "signed_post_bps":sign*(apost-bpost)*10000.0,
        })

    dates=sorted({e["rebalance_date"] for e in legs})
    years=sorted({int(d[:4]) for d in dates})
    dates_by_year=Counter(int(d[:4]) for d in dates)
    dirs=Counter(e["direction"] for e in legs)
    sample_gates={
        "min_50_valid_legs":len(legs)>=50,
        "min_20_dates":len(dates)>=20,
        "all_three_years":years==[2022,2023,2024],
        "min_5_dates_each_year":all(dates_by_year[y]>=5 for y in (2022,2023,2024)),
        "both_directions":dirs["ADD"]>0 and dirs["REMOVE"]>0,
    }

    result={
        "schema":"BITWISE_REBALANCE_DISCOVERY_V0.1",
        "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "discovery_period":"2022-2024",
        "event_set_sha256":EXPECTED_EVENT_SET_SHA,
        "source_eligibility_set_sha256":"0d4b35b68a1a119c91db45b5454d6856afc79b6e7e6018304d7b66030ccc723c",
        "source_exclusions":[{"rebalance_date":"2024-09-29","ticker":"MATIC","direction":"REMOVE","reason":"SOURCE_COVERAGE_404"}],
        "boundary_exclusions":boundary_exclusions,
        "valid_event_legs":len(legs),
        "valid_rebalance_dates":len(dates),
        "dates_by_year":dict(sorted(dates_by_year.items())),
        "direction_counts":dict(dirs),
        "sample_gates":sample_gates,
        "2025_market_data_opened":False,
        "2026_market_data_opened":False,
        "pnl_computed":False,
        "cost_tuning_performed":False,
        "file_manifest":list(file_manifest.values()),
    }

    if not all(sample_gates.values()):
        result["classification"]="DISCOVERY_BLOCKED_DATA_INTEGRITY"
        result["event_legs"]=legs
        (OUT/"historical_discovery_v0.1.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
        print(json.dumps({"classification":result["classification"],"sample_gates":sample_gates,"valid_event_legs":len(legs)},indent=2))
        return 2

    bydate=defaultdict(lambda:{"pre":[],"post":[]})
    for e in legs:
        bydate[e["rebalance_date"]]["pre"].append(e["signed_pre_bps"])
        bydate[e["rebalance_date"]]["post"].append(e["signed_post_bps"])
    date_rows=[]
    for d in sorted(bydate):
        date_rows.append({
            "rebalance_date":d,
            "year":int(d[:4]),
            "date_pre_bps":statistics.mean(bydate[d]["pre"]),
            "date_post_bps":statistics.mean(bydate[d]["post"]),
            "event_leg_count":len(bydate[d]["pre"]),
        })

    mean_pre=statistics.mean(r["date_pre_bps"] for r in date_rows)
    mean_post=statistics.mean(r["date_post_bps"] for r in date_rows)
    med_pre=statistics.median(r["date_pre_bps"] for r in date_rows)
    med_post=statistics.median(r["date_post_bps"] for r in date_rows)
    ci_pre=bootstrap_ci(date_rows,"date_pre_bps")
    ci_post=bootstrap_ci(date_rows,"date_post_bps")

    yearly={}
    for y in (2022,2023,2024):
        rr=[r for r in date_rows if r["year"]==y]
        yearly[str(y)]={
            "n_dates":len(rr),
            "mean_pre_bps":statistics.mean(r["date_pre_bps"] for r in rr),
            "mean_post_bps":statistics.mean(r["date_post_bps"] for r in rr),
        }
    stable_years=sum(v["mean_pre_bps"]>0 and v["mean_post_bps"]<0 for v in yearly.values())

    lodo=[]
    for omitted in date_rows:
        rr=[r for r in date_rows if r["rebalance_date"]!=omitted["rebalance_date"]]
        p=statistics.mean(r["date_pre_bps"] for r in rr)
        q=statistics.mean(r["date_post_bps"] for r in rr)
        lodo.append({"omitted":omitted["rebalance_date"],"mean_pre_bps":p,"mean_post_bps":q,"joint_sign_ok":p>0 and q<0})
    lodo_fraction=sum(r["joint_sign_ok"] for r in lodo)/len(lodo)

    def concentration(field:str)->float:
        vals=[abs(r[field]) for r in date_rows]
        s=sum(vals)
        return max(vals)/s if s else 1.0

    cpre=concentration("date_pre_bps")
    cpost=concentration("date_post_bps")

    sci_gates={
        "A_pre_materiality_20bps":mean_pre>=20.0,
        "B_pre_bootstrap_lower_gt0":ci_pre[0]>0.0,
        "C_post_materiality_minus20bps":mean_post<=-20.0,
        "D_post_bootstrap_upper_lt0":ci_post[1]<0.0,
        "E_min_2_of_3_years_joint_sign":stable_years>=2,
        "F_lodo_joint_sign_ge_80pct":lodo_fraction>=0.80,
        "G_pre_concentration_le_25pct":cpre<=0.25,
        "G_post_concentration_le_25pct":cpost<=0.25,
    }
    classification="DISCOVERY_MECHANISM_PASS_CANDIDATE" if all(sci_gates.values()) else "DISCOVERY_FAIL_NO_PROMOTION"

    direction_diag={}
    for direction in ("ADD","REMOVE"):
        rr=[e for e in legs if e["direction"]==direction]
        direction_diag[direction]={
            "n_legs":len(rr),
            "mean_signed_pre_bps":statistics.mean(e["signed_pre_bps"] for e in rr),
            "mean_signed_post_bps":statistics.mean(e["signed_post_bps"] for e in rr),
        }

    result.update({
        "classification":classification,
        "primary":{
            "n_date_rows":len(date_rows),
            "mean_pre_bps":mean_pre,
            "median_pre_bps":med_pre,
            "bootstrap95_pre_bps":{"lower":ci_pre[0],"upper":ci_pre[1],"reps":BOOT,"seed":SEED},
            "mean_post_bps":mean_post,
            "median_post_bps":med_post,
            "bootstrap95_post_bps":{"lower":ci_post[0],"upper":ci_post[1],"reps":BOOT,"seed":SEED},
            "stable_joint_sign_years":stable_years,
            "lodo_joint_sign_fraction":lodo_fraction,
            "pre_abs_concentration":cpre,
            "post_abs_concentration":cpost,
        },
        "scientific_gates":sci_gates,
        "yearly":yearly,
        "direction_diagnostics":direction_diag,
        "date_rows":date_rows,
        "leave_one_date_out":lodo,
        "event_legs":legs,
    })
    (OUT/"historical_discovery_v0.1.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({
        "classification":classification,
        "valid_event_legs":len(legs),
        "valid_rebalance_dates":len(date_rows),
        "primary":result["primary"],
        "scientific_gates":sci_gates,
        "yearly":yearly,
        "direction_diagnostics":direction_diag,
        "2025_market_data_opened":False,
    },indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
