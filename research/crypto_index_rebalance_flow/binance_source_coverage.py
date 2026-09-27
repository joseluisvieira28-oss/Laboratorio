#!/usr/bin/env python3
"""HEAD-only Binance Vision coverage gate for Bitwise 2022-2024 events."""

from __future__ import annotations
import collections
import datetime as dt
import json
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

OUT=Path("artifacts/crypto_index_rebalance_flow")
UA="CryptoLab-Bitwise-CoverageGate/0.1 source-only"
BASE="https://data.binance.vision/data/spot/daily/klines/{symbol}/1m/{symbol}-1m-{date}.zip"

def head(url:str)->dict:
    req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            return {"url":url,"status":int(r.status),"content_length":r.headers.get("Content-Length"),"body_bytes_read":0}
    except urllib.error.HTTPError as e:
        return {"url":url,"status":int(e.code),"content_length":None,"body_bytes_read":0}
    except Exception as e:
        return {"url":url,"status":None,"error":type(e).__name__+": "+str(e),"body_bytes_read":0}

def dates3(date_s:str)->list[str]:
    d=dt.date.fromisoformat(date_s)
    return [(d+dt.timedelta(days=i)).isoformat() for i in (-1,0,1)]

def main()->int:
    OUT.mkdir(parents=True,exist_ok=True)

    # Reproduce normalized source deterministically; it has no market access.
    subprocess.run([sys.executable,"research/crypto_index_rebalance_flow/event_normalization.py"],check=True)
    norm=json.loads((OUT/"event_normalization_v0.1.json").read_text())
    assert norm["result_sha256"]=="a44c3ca006f06a258314e683c44aeb31e5b1788145d9ffe4603e4994a33bb876"
    events=[e for e in norm["events"] if e["period_role"]=="DISCOVERY_SOURCE"]
    assert all(e["rebalance_date"].startswith(("2022-","2023-","2024-")) for e in events)

    urls=set()
    requirements={}
    for e in events:
        symbol=e["ticker"]+"USDT"
        req=[]
        for day in dates3(e["rebalance_date"]):
            for sym in (symbol,"BTCUSDT"):
                z=BASE.format(symbol=sym,date=day)
                for u in (z,z+".CHECKSUM"):
                    urls.add(u)
                    req.append(u)
        requirements[(e["rebalance_date"],e["ticker"],e["direction"])]=req

    results={}
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs={ex.submit(head,u):u for u in sorted(urls)}
        for f in as_completed(futs):
            u=futs[f]
            results[u]=f.result()

    # Hard firewall: URLs must contain only 2022-2024 dates.
    requested_2025=any("/2025-" in u for u in results)
    bodies=sum(int(r.get("body_bytes_read") or 0) for r in results.values())

    eligible=[]
    excluded=[]
    for e in events:
        key=(e["rebalance_date"],e["ticker"],e["direction"])
        missing=[u for u in requirements[key] if results[u].get("status")!=200]
        row={**e,"binance_symbol":e["ticker"]+"USDT"}
        if missing:
            row["source_eligible"]=False
            row["missing_or_failed_urls"]=[{"url":u,"status":results[u].get("status"),"error":results[u].get("error")} for u in missing]
            excluded.append(row)
        else:
            row["source_eligible"]=True
            eligible.append(row)

    dates=sorted({e["rebalance_date"] for e in eligible})
    years=sorted({int(d[:4]) for d in dates})
    dates_by_year=collections.Counter(int(d[:4]) for d in dates)
    directions=collections.Counter(e["direction"] for e in eligible)
    gates={
        "min_50_eligible_legs":len(eligible)>=50,
        "min_20_distinct_dates":len(dates)>=20,
        "all_three_years":years==[2022,2023,2024],
        "min_5_dates_each_year":all(dates_by_year[y]>=5 for y in (2022,2023,2024)),
        "both_directions":directions["ADD"]>0 and directions["REMOVE"]>0,
        "zero_2025_requests":not requested_2025,
        "zero_market_body_bytes":bodies==0,
    }
    classification="SOURCE_COVERAGE_PASS" if all(gates.values()) else "SOURCE_COVERAGE_INSUFFICIENT"
    out={
        "schema":"BITWISE_BINANCE_SOURCE_COVERAGE_V0.1",
        "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "normalization_result_sha256":norm["result_sha256"],
        "classification":classification,
        "eligible_events":eligible,
        "excluded_events":excluded,
        "eligible_event_legs":len(eligible),
        "excluded_event_legs":len(excluded),
        "eligible_rebalance_dates":len(dates),
        "eligible_dates_by_year":dict(sorted(dates_by_year.items())),
        "eligible_direction_counts":dict(directions),
        "unique_head_urls":len(results),
        "failed_head_urls":sum(r.get("status")!=200 for r in results.values()),
        "market_response_body_bytes_read":bodies,
        "requested_2025_market_data":requested_2025,
        "gates":gates,
        "head_results":results,
        "prices_read":False,
        "returns_computed":False,
        "pnl_computed":False,
    }
    (OUT/"binance_source_coverage_v0.1.json").write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({k:out[k] for k in [
        "classification","eligible_event_legs","excluded_event_legs","eligible_rebalance_dates",
        "eligible_dates_by_year","eligible_direction_counts","unique_head_urls","failed_head_urls","gates"]},indent=2,sort_keys=True))
    return 0 if classification=="SOURCE_COVERAGE_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
