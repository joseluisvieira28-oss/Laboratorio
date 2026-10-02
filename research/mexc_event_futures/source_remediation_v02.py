#!/usr/bin/env python3
"""
SOURCE-ONLY diagnostics for MEXC Event Futures proxy history.
No strategy outcomes, no EV, no directional tests.
"""
import json, os, time
from datetime import datetime, timezone
import requests

BASES = ["https://contract.mexc.com", "https://api.mexc.com"]
SYMBOLS = {
    "BTCUSDT": "BTC_USDT",
    "ETHUSDT": "ETH_USDT",
    "NVDAUSDT": "NVIDIA_USDT",
    "MUUSDT": "MUSTOCK_USDT",
    "SPCXUSDT": "SPCXSTOCK_USDT",
}
INTERVALS = ["Min1","Min5","Min15","Min30","Min60","Hour4","Day1"]

OLD_START = int(datetime(2026,7,15,0,0,tzinfo=timezone.utc).timestamp())
OLD_END = int(datetime(2026,7,16,0,0,tzinfo=timezone.utc).timestamp())
RECENT_END = int(datetime(2026,10,2,12,0,tzinfo=timezone.utc).timestamp())
RECENT_START = RECENT_END - 24*3600

def request_json(url, params):
    try:
        r=requests.get(url, params=params, timeout=25)
        payload=r.json() if r.content else None
        return {"status_code":r.status_code,"url":r.url,"payload":payload}
    except Exception as e:
        return {"error":repr(e),"url":url}

def extract_times(resp):
    j=resp.get("payload")
    if not isinstance(j,dict) or j.get("success") is not True:
        return []
    d=j.get("data") or {}
    vals=d.get("time") or []
    out=[]
    for x in vals:
        try: out.append(int(x))
        except Exception: pass
    return out

def summarize(resp, expected_start, expected_end):
    ts=extract_times(resp)
    in_window=[t for t in ts if expected_start <= t <= expected_end]
    return {
        "status_code":resp.get("status_code"),
        "url":resp.get("url"),
        "success":bool(isinstance(resp.get("payload"),dict) and resp["payload"].get("success") is True),
        "rows":len(ts),
        "first":min(ts) if ts else None,
        "last":max(ts) if ts else None,
        "rows_in_requested_window":len(in_window),
        "window_match":bool(in_window),
        "error":resp.get("error"),
        "message":(resp.get("payload") or {}).get("message") if isinstance(resp.get("payload"),dict) else None,
        "code":(resp.get("payload") or {}).get("code") if isinstance(resp.get("payload"),dict) else None,
    }

def main():
    out={
        "lab":"MEXC_EVENT_FUTURES_SOURCE_REMEDIATION_V0.2",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "mode":"SOURCE_ONLY",
        "old_window_utc":[OLD_START,OLD_END],
        "recent_window_utc":[RECENT_START,RECENT_END],
        "results":{},
    }

    for display,symbol in SYMBOLS.items():
        out["results"][display]={}
        for base in BASES:
            base_key=base.replace("https://","")
            out["results"][display][base_key]={}
            for route_name,route in [
                ("index",f"/api/v1/contract/kline/index_price/{symbol}"),
                ("contract",f"/api/v1/contract/kline/{symbol}"),
                ("fair",f"/api/v1/contract/kline/fair_price/{symbol}"),
            ]:
                rr={}
                for interval in INTERVALS:
                    tests={}
                    # Documented seconds
                    resp=request_json(base+route,{"interval":interval,"start":OLD_START,"end":OLD_END})
                    tests["old_seconds"]=summarize(resp,OLD_START,OLD_END)
                    time.sleep(0.11)
                    # Milliseconds diagnostic (some examples elsewhere use ms for regular kline)
                    resp=request_json(base+route,{"interval":interval,"start":OLD_START*1000,"end":OLD_END*1000})
                    tests["old_milliseconds"]=summarize(resp,OLD_START,OLD_END)
                    time.sleep(0.11)
                    # Recent control in documented seconds
                    resp=request_json(base+route,{"interval":interval,"start":RECENT_START,"end":RECENT_END})
                    tests["recent_seconds"]=summarize(resp,RECENT_START,RECENT_END)
                    time.sleep(0.11)
                    rr[interval]=tests
                out["results"][display][base_key][route_name]=rr

    old_hits=[]
    for asset,bases in out["results"].items():
        for base,routes in bases.items():
            for route,ints in routes.items():
                for interval,tests in ints.items():
                    for mode,summary in tests.items():
                        if mode.startswith("old_") and summary.get("window_match"):
                            old_hits.append({
                                "asset":asset,"base":base,"route":route,
                                "interval":interval,"parameter_mode":mode,
                                "rows":summary.get("rows"),
                                "first":summary.get("first"),"last":summary.get("last"),
                            })
    out["historical_routes_with_window_match"]=old_hits
    out["verdict"]="HISTORICAL_ROUTE_FOUND" if old_hits else "HISTORICAL_SOURCE_BLOCKED_ON_PROBED_ROUTES"

    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    p="artifacts/mexc_event_futures/source_remediation_v02.json"
    with open(p,"w",encoding="utf-8") as f:
        json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps({
        "verdict":out["verdict"],
        "historical_route_count":len(old_hits),
        "historical_routes_with_window_match":old_hits[:100],
    },indent=2))
    print("WROTE",p)

if __name__=="__main__":
    main()
