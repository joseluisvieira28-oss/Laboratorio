"""Bounded public OKX historical L2/funding catalogue gate, NO outcome data.
The only allowed network calls are six documented public GET requests.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
import argparse

ENDPOINT="https://www.okx.com/api/v5/public/market-data-history"
SYMS=("SOL-USDT","BNB-USDT")
DATES=("2023-12-03","2024-06-03")
CATS=("4","3")
LIMIT_BYTES=1_000_000

def epoch_ms(day):
    return int(dt.datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()*1000)

def inputs():
    for fam in SYMS:
        for day in DATES:
            yield fam,"4","daily",day
        yield fam,"3","monthly","2024-06-01"

def classify(family,mod,aggregate,day,http_status=0,raw=b"",error=""):
    if (family,mod,aggregate,day) not in set(inputs()):
        raise ValueError("UNFROZEN_REQUEST")
    out={"family":family,"module":mod,"aggregation":aggregate,"date":day,
         "http":http_status,"bytes":len(raw),
         "response_sha256":hashlib.sha256(raw).hexdigest() if raw else None,
         "status":"SOURCE_BLOCKED","api_code":None,"data_items":0,"schema_keys":[],
         "link_hostnames":[],"error":error[:120]}
    if http_status!=200 or not raw:
        return out
    try:
        obj=json.loads(raw.decode("utf-8"))
        if not isinstance(obj,dict):raise ValueError("NOT_JSON_OBJECT")
        out["schema_keys"]=sorted(obj.keys())[:15]
        out["api_code"]=str(obj.get("code","MISSING"))
        data=obj.get("data")
        if not isinstance(data,list):raise ValueError("DATA_NOT_ARRAY")
        out["data_items"]=len(data)
        # Never emit raw URLs or market data. Only characterize valid HTTPS URL hostnames.
        # File origin is *not* treated as verified by mere hostname.
        hosts=set()
        for item in data[:50]:
            if isinstance(item,dict):
                for key,val in item.items():
                    if isinstance(val,str) and ("url" in key.lower() or "href" in key.lower()):
                        parsed=urllib.parse.urlsplit(val)
                        if parsed.scheme=="https" and parsed.hostname:
                            hosts.add(parsed.hostname.lower())
        out["link_hostnames"]=sorted(hosts)
        if out["api_code"]!="0":
            out["error"]="NONZERO_API_CODE"
        elif not data:
            out["error"]="EMPTY_DATA_LIST"
        else:
            # Listing response may be download links or statistics: not verified usable market records.
            out["status"]="CATALOGUE_NONEMPTY_NOT_DATA_VERIFIED"
            out["error"]=""
    except Exception as exc:
        out["error"]=type(exc).__name__+":"+str(exc)[:90]
    return out

def single_call(family,mod,agg,day):
    stamp=epoch_ms(day)
    query=urllib.parse.urlencode({
        "module":mod,"instType":"SWAP","instFamilyList":family,
        "dateAggrType":agg,"begin":str(stamp),"end":str(stamp)
    })
    url=ENDPOINT+"?"+query
    req=urllib.request.Request(url,headers={
        "Accept":"application/json",
        "User-Agent":"CryptoLab-Research-Public-Source-Only/1.0"
    })
    status=0; raw=b""; error=""
    try:
        with urllib.request.urlopen(req,timeout=8) as h:
            status=int(h.status); raw=h.read(LIMIT_BYTES+1)
            if len(raw)>LIMIT_BYTES:raise ValueError("RESPONSE_SIZE_CAP")
    except urllib.error.HTTPError as exc:
        status=exc.code; error="HTTP_"+str(exc.code)
    except Exception as exc:
        error=type(exc).__name__+":"+str(exc)[:100]
        raw=b""
    return classify(family,mod,agg,day,status,raw,error)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    vals=[]
    for spec in inputs():
        x=single_call(*spec)
        vals.append(x); print("OKX_SOURCE_GATE",json.dumps(x,sort_keys=True),flush=True)
    report={
        "status":"SOURCE_ONLY_NOT_ECONOMIC",
        "frozen_cases":6,"observed_cases":len(vals),
        "class_counts":dict(Counter(x["status"] for x in vals)),
        "probes":vals,"market_prices_observed":False,
        "historical_orderbook_downloaded":False,
        "historical_fill_verified":False,"trading_authority":"NONE"
    }
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"OKX_6_PUBLIC_CATALOGUE_SOURCE_RECEIPTS.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("SOURCE_VERDICT",json.dumps({k:v for k,v in report.items() if k!="probes"},sort_keys=True))

if __name__=="__main__":
    main()
