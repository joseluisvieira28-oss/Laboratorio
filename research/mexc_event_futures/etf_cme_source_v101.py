#!/usr/bin/env python3
import json, os, time
from datetime import datetime, timezone
import requests

BASE="https://contract.mexc.com"
SYMBOL="BTC_USDT"
DATES={
 "2022":"2022-06-15",
 "2023":"2023-06-15",
 "2024":"2024-06-15",
 "2025":"2025-06-15",
 "2026_CONTROL":"2026-07-15",
}
INTERVALS=["Min5","Min15","Min30","Min60","Hour4","Day1"]
ROUTES={
 "index":f"/api/v1/contract/kline/index_price/{SYMBOL}",
 "contract":f"/api/v1/contract/kline/{SYMBOL}",
 "fair":f"/api/v1/contract/kline/fair_price/{SYMBOL}",
}
HEADERS={"User-Agent":"crypto-lab-event-futures-etf-source-v1.0.1"}

def ts(day):
    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())

def probe(route, interval, start, end):
    try:
        r=requests.get(BASE+route,params={"interval":interval,"start":start,"end":end},headers=HEADERS,timeout=25)
        payload=r.json() if r.content else None
        d=(payload or {}).get("data") or {} if isinstance(payload,dict) else {}
        times=d.get("time") or []
        vals=[]
        for x in times:
            try: vals.append(int(x))
            except Exception: pass
        inside=[x for x in vals if start<=x<=end]
        return {
          "status_code":r.status_code,
          "success":bool(isinstance(payload,dict) and payload.get("success") is True),
          "rows":len(vals),
          "first":min(vals) if vals else None,
          "last":max(vals) if vals else None,
          "rows_in_requested_window":len(inside),
          "window_match":bool(inside),
          "url":r.url,
          "code":payload.get("code") if isinstance(payload,dict) else None,
          "message":payload.get("message") if isinstance(payload,dict) else None,
        }
    except Exception as e:
        return {"error":repr(e),"window_match":False}

def main():
    out={
      "lab":"ETF_CME_EVENT_FUTURES_SOURCE_REMEDIATION_V1.0.1",
      "mode":"SOURCE_ONLY",
      "results":{},
      "authenticated_requests":0,
      "orders":0,
      "account_mutations":0,
    }
    for label,day in DATES.items():
        start=ts(day)
        end=start+24*3600
        out["results"][label]={}
        for rname,route in ROUTES.items():
            out["results"][label][rname]={}
            for interval in INTERVALS:
                out["results"][label][rname][interval]=probe(route,interval,start,end)
                time.sleep(0.10)

    summary={}
    for label,routes in out["results"].items():
        hits=[]
        for rname,ints in routes.items():
            for interval,v in ints.items():
                if v.get("window_match"):
                    hits.append({"route":rname,"interval":interval,"rows":v.get("rows"),"first":v.get("first"),"last":v.get("last")})
        summary[label]=hits
    out["historical_window_hits"]=summary
    old_labels=["2022","2023","2024","2025"]
    out["verdict"]="HISTORICAL_MEXC_ROUTE_AVAILABLE" if any(summary[x] for x in old_labels) else "HISTORICAL_MEXC_ROUTE_UNAVAILABLE_ON_PROBED_ROUTES"

    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    p="artifacts/mexc_event_futures/etf_cme_source_v101.json"
    with open(p,"w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps({"verdict":out["verdict"],"historical_window_hits":summary},indent=2,sort_keys=True))
    print("WROTE",p)

if __name__=="__main__":
    main()
