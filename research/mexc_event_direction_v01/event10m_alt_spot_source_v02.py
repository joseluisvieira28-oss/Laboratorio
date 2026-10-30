#!/usr/bin/env python3
"""Dual independent crypto public SPOT orderbook source probes; zero outcomes."""
import datetime as dt,json,pathlib,time,concurrent.futures
from event10m_current_source_v01 import get_public,book_stats,mexc_depth
OUT=pathlib.Path("artifacts/event10m_spot_source_v02")
SYMS=("BTC_USDT","ETH_USDT")
def fetch_bybit(sym):
    out={"provider":"BYBIT_SPOT_PUBLIC_DEPTH","symbol":sym,"status":"SOURCE_BLOCKED"}
    try:
        url="https://api.bybit.com/v5/market/orderbook?category=spot&symbol="+sym.replace("_","")+"&limit=50"
        d,r=get_public(url)
        v=d.get("result") or {}
        if d.get("retCode")!=0 or v.get("s")!=sym.replace("_",""):
            raise ValueError("BYBIT_RESPONSE_SCHEMA")
        ts=int(d.get("time") or v.get("ts") or 0)
        age=r["received_ms"]-ts
        if not 0<=age<=5000:raise ValueError("BYBIT_STALE_OR_FUTURE_"+str(age))
        stats=book_stats(v.get("b"),v.get("a"))
        out.update(status="SPOT_BOOK_PRESENT",receipt=r,server_ms=ts,server_age_ms=age,stats=stats)
    except Exception as e:out["error"]=type(e).__name__+":"+str(e)[:200]
    return out
def fetch_okx(sym):
    out={"provider":"OKX_SPOT_PUBLIC_DEPTH","symbol":sym,"status":"SOURCE_BLOCKED"}
    try:
        inst=sym.replace("_","-")
        url="https://www.okx.com/api/v5/market/books?instId="+inst+"&sz=20"
        d,r=get_public(url)
        rows=d.get("data") or []
        if str(d.get("code"))!="0" or len(rows)!=1:raise ValueError("OKX_RESPONSE_SCHEMA")
        v=rows[0];ts=int(v.get("ts") or 0);age=r["received_ms"]-ts
        if not 0<=age<=5000:raise ValueError("OKX_STALE_OR_FUTURE_"+str(age))
        stats=book_stats(v.get("bids"),v.get("asks"))
        out.update(status="SPOT_BOOK_PRESENT",receipt=r,server_ms=ts,server_age_ms=age,stats=stats)
    except Exception as e:out["error"]=type(e).__name__+":"+str(e)[:200]
    return out
def sample(i):
    jobs=[(func,sym) for sym in SYMS for func in (fetch_bybit,fetch_okx,mexc_depth)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        result=list(pool.map(lambda a:a[0](a[1]),jobs))
    return {"shot":i,"received_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "books":result}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    a=sample(0);time.sleep(5);b=sample(1)
    result={"study":"CRYPTO_LAB_EVENT10M_BTC_ETH_INDEPENDENT_SPOT_ORDER_BOOK_GATE_V02",
     "source-only":True,"shots":[a,b],"outcomes_read":0,"forecasts_generated":0,
     "official_event_futures_settlement_parity":False,
     "protected_holdouts_opened":0,"orders_accounts":0}
    gates={}
    for sym in SYMS:
        market={}
        for venue in ("BYBIT_SPOT_PUBLIC_DEPTH","OKX_SPOT_PUBLIC_DEPTH","MEXC_FUTURES_DEPTH"):
            market[venue]=all(any(z.get("provider",z.get("venue"))==venue and z["symbol"]==sym and
                        z["status"] in ("SPOT_BOOK_PRESENT","ORDER_BOOK_PRESENT")
                        for z in shot["books"]) for shot in (a,b))
        market["independent_external_and_mexc"]=market["MEXC_FUTURES_DEPTH"] and (
            market["BYBIT_SPOT_PUBLIC_DEPTH"] or market["OKX_SPOT_PUBLIC_DEPTH"])
        gates[sym]=market
    result["per_asset_source_gates"]=gates
    result["gate"]="BOTH_ASSETS_HAVE_INDEPENDENT_BOOKS" if all(
        gates[s]["independent_external_and_mexc"] for s in SYMS) else "ONE_OR_MORE_ASSETS_BLOCKED"
    (OUT/"source_receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    text={"study":result["study"],"gate":result["gate"],"per_asset_source_gates":gates,
      "shots":[{"shot":x["shot"],"books":[{"provider":v.get("provider",v.get("venue")),
       "symbol":v["symbol"],"status":v["status"],"error":v.get("error"),
       "server_age_ms":v.get("server_age_ms"),
       "top5_imbalance":(v.get("stats") or {}).get("top5_signed_imbalance")}
        for v in x["books"]]} for x in (a,b)]}
    print(json.dumps(text,indent=2,sort_keys=True),flush=True)
    if result["gate"]!="BOTH_ASSETS_HAVE_INDEPENDENT_BOOKS":raise SystemExit(2)
if __name__=="__main__":main()
