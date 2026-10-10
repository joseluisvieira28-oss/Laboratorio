#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, hashlib, json, pathlib, statistics, urllib.parse, urllib.request

BASE="https://history.deribit.com/api/v2/public"
OUT=pathlib.Path("artifacts/btc_options_vrp_usdc_tape_source_v01")
DATES=["2026-09-03","2026-09-10","2026-09-17","2026-09-24","2026-10-01","2026-10-07"]
REQ=("timestamp","instrument_name","direction","amount")

def ms(s):
    return int(dt.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)

def get(endpoint,params):
    url=BASE+endpoint+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-VRP-USDC-Tape-SourceOnly/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read()
    obj=json.loads(raw.decode())
    if "error" in obj: raise RuntimeError(obj["error"])
    return obj["result"],hashlib.sha256(raw).hexdigest()

def trades(result):
    if isinstance(result,dict) and isinstance(result.get("trades"),list): return result["trades"]
    if isinstance(result,list): return result
    raise RuntimeError("unexpected response")

def quantile(xs,p):
    if not xs:return None
    ys=sorted(xs); i=(len(ys)-1)*p; lo=int(i); hi=min(lo+1,len(ys)-1); w=i-lo
    return ys[lo]*(1-w)+ys[hi]*w

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]; manifest=[]
    for day in DATES:
        start=f"{day}T06:00:00Z"; end=f"{day}T10:00:00Z"
        payload,sha=get("/get_last_trades_by_currency_and_time",{
            "currency":"USDC","kind":"option","start_timestamp":ms(start),"end_timestamp":ms(end),
            "count":1000,"sorting":"asc","include_old":"true"
        })
        all_t=trades(payload)
        btc=[t for t in all_t if str(t.get("instrument_name","")).startswith("BTC_USDC-") and ms(start)<=int(t.get("timestamp",-1))<=ms(end)]
        cov=sum(1 for t in btc for k in REQ if t.get(k) is not None)/(len(btc)*len(REQ)) if btc else 1.0
        amounts=[float(t["amount"]) for t in btc if t.get("amount") is not None]
        rec={
            "date":day,"window_start":start,"window_end":end,
            "raw_payload_sha256":sha,"all_usdc_option_records_returned":len(all_t),
            "btc_usdc_trade_count":len(btc),
            "unique_instruments":len({t.get("instrument_name") for t in btc}),
            "buy_count":sum(str(t.get("direction","")).lower()=="buy" for t in btc),
            "sell_count":sum(str(t.get("direction","")).lower()=="sell" for t in btc),
            "amount_gte_0_01_count":sum(float(t.get("amount",0))>=0.01 for t in btc),
            "required_field_coverage":cov,
            "amount_min":min(amounts) if amounts else None,
            "amount_median":statistics.median(amounts) if amounts else None,
            "amount_q90":quantile(amounts,0.9),
            "amount_max":max(amounts) if amounts else None,
            "economic_values_retained":False
        }
        rows.append(rec)
        for t in btc:
            manifest.append({
                "timestamp":int(t["timestamp"]),
                "instrument_name":t["instrument_name"],
                "direction":t["direction"],
                "amount":float(t["amount"]),
                "trade_id":t.get("trade_id"),
                "block_trade":t.get("block_trade_id") is not None
            })
    all_nonempty=all(r["btc_usdc_trade_count"]>0 for r in rows)
    min_cov=min(r["required_field_coverage"] for r in rows)
    classification="SOURCE_ROUTE_PRESENT" if all_nonempty and min_cov>=0.95 else "SOURCE_ROUTE_SPARSE"
    result={
        "classification":classification,
        "windows":rows,
        "aggregate":{
            "btc_usdc_trade_count":sum(r["btc_usdc_trade_count"] for r in rows),
            "unique_instruments":len({x["instrument_name"] for x in manifest}),
            "buy_count":sum(str(x["direction"]).lower()=="buy" for x in manifest),
            "sell_count":sum(str(x["direction"]).lower()=="sell" for x in manifest),
            "amount_gte_0_01_count":sum(x["amount"]>=0.01 for x in manifest),
            "min_required_field_coverage":min_cov
        },
        "prices_retained":False,"pnl_computed":False,"returns_computed":False,
        "authenticated":False,"orders":False,"wallets":False
    }
    # Manifest intentionally excludes price/mark/index/IV.
    (OUT/"source_manifest.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in manifest)+"\n")
    (OUT/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
