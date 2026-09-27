#!/usr/bin/env python3
"""PREDICTION-SETTLEMENT-RV-001 source-readiness probe.

Proves fee metadata routes and an independent public USDT/USD basis route.
No strategy economics, PnL, outcomes, or optimization.
"""

from __future__ import annotations
import datetime as dt
import hashlib, json, sys, urllib.parse, urllib.request
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import source_probe as sp  # noqa

OUT=Path("artifacts/prediction_settlement_rv/readiness")
UA="CryptoLab-PSRV-Readiness/0.1"
COINBASE_TICKER="https://api.exchange.coinbase.com/products/USDT-USD/ticker"
POLY_EVENTS="https://gamma-api.polymarket.com/events"
KALSHI_BASE="https://api.elections.kalshi.com/trade-api/v2"

def now():
    return dt.datetime.now(dt.timezone.utc)

def iso(x):
    return x.astimezone(dt.timezone.utc).isoformat()

def get_json(url,params=None):
    if params:
        url += ("&" if "?" in url else "?")+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    st=now()
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read(); status=int(r.status); ctype=r.headers.get("content-type","")
    en=now()
    return json.loads(raw.decode()), {
        "url":url,"status":status,"content_type":ctype,
        "started_at_utc":iso(st),"finished_at_utc":iso(en),
        "raw_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)
    }

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    probe_now=now()
    kalshi,kf,series=sp.fetch_kalshi(probe_now)
    times=[sp.parse_iso(k["resolution_utc"]) for k in kalshi]
    times=[t for t in times if t]
    poly,pf=sp.fetch_poly_for_times(times,probe_now)
    pairs=sp.match(poly,kalshi)

    result={
        "schema":"PSRV_SOURCE_READINESS_V0.1",
        "generated_at_utc":iso(probe_now),
        "matched_pair_count":len(pairs),
        "economic_outputs_computed":False,
        "matured_outcomes_read":False,
        "orders":False,
        "authenticated_trading_endpoints":False,
    }
    fetches=[]

    # Independent USDT/USD causal-basis route.
    try:
        cb,meta=get_json(COINBASE_TICKER); fetches.append(meta)
        keys=sorted(cb.keys()) if isinstance(cb,dict) else []
        required={"bid","ask","time"}
        result["usdtusd_basis_route"]={
            "provider":"Coinbase Exchange",
            "product":"USDT-USD",
            "endpoint":COINBASE_TICKER,
            "schema_keys":keys,
            "required_fields_present":required.issubset(set(keys)),
            "raw_sha256":meta["raw_sha256"],
            "source_values_exposed":False,
        }
    except Exception as exc:
        result["usdtusd_basis_route"]={"required_fields_present":False,"error":type(exc).__name__+": "+str(exc)}

    result["polymarket_fee_metadata"]=[]
    result["kalshi_fee_metadata"]=[]

    if pairs:
        # Use only the first deterministic matched pair, never selected by price.
        pair=sorted(pairs,key=lambda x:(x["resolution_utc"],float(x["nominal_strike"])))[0]
        result["deterministic_fee_probe_pair"]={
            "resolution_utc":pair["resolution_utc"],
            "nominal_strike":pair["nominal_strike"],
            "polymarket_market_id":pair["polymarket_market_id"],
            "kalshi_ticker":pair["kalshi_ticker"],
        }

        # Polymarket: fetch the exact future event slug derived from time, then market ID.
        t=sp.parse_iso(pair["resolution_utc"])
        slug=sp.hourly_slug(t)
        ev,meta=get_json(POLY_EVENTS,{"slug":slug}); fetches.append(meta)
        events=ev if isinstance(ev,list) else ev.get("events",[])
        for e in events:
            for m in e.get("markets") or []:
                if str(m.get("id"))==str(pair["polymarket_market_id"]):
                    fee_keys=[k for k in m.keys() if "fee" in k.lower()]
                    result["polymarket_fee_metadata"].append({
                        "market_id":m.get("id"),
                        "fee_fields":{k:m.get(k) for k in sorted(fee_keys)},
                        "market_metadata_sha256":hashlib.sha256(json.dumps(m,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
                    })

        # Kalshi: exact future market metadata; select fee-named fields only.
        km,meta=get_json(f"{KALSHI_BASE}/markets/{urllib.parse.quote(pair['kalshi_ticker'])}"); fetches.append(meta)
        market=km.get("market",km) if isinstance(km,dict) else {}
        fee_keys=[k for k in market.keys() if "fee" in k.lower()]
        result["kalshi_fee_metadata"].append({
            "ticker":pair["kalshi_ticker"],
            "fee_fields":{k:market.get(k) for k in sorted(fee_keys)},
            "market_metadata_sha256":hashlib.sha256(json.dumps(market,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        })

    result["adjudication"]={
        "pair_route_reproducible":len(pairs)>0,
        "polymarket_fee_metadata_route_proven":bool(result["polymarket_fee_metadata"]),
        "kalshi_market_fee_fields_present":bool(result["kalshi_fee_metadata"] and result["kalshi_fee_metadata"][0]["fee_fields"]),
        "usdtusd_basis_route_proven":bool(result.get("usdtusd_basis_route",{}).get("required_fields_present")),
        "kalshi_official_fee_formula_requires_external_regulatory_receipt":True,
        "source_data_pass":False,
    }
    result["fetches"]=fetches
    raw=json.dumps(result,sort_keys=True,indent=2)
    (OUT/"readiness_receipt.json").write_text(raw,encoding="utf-8")
    print(json.dumps(result["adjudication"],indent=2,sort_keys=True))
    print("NO_SOURCE_VALUES_NO_OUTCOMES_NO_PNL")

if __name__=="__main__":
    main()
