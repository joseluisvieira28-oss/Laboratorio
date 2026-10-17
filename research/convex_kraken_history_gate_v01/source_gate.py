"""16 bounded anonymous Kraken historical source transport checks; no PnL."""
from __future__ import annotations
import argparse, datetime, hashlib, json, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

SYMBOLS=("PF_SOLUSD","PF_BNBUSD")
TYPES=("spreads","funding")
STARTS=("2023-01-03","2023-12-03","2024-06-03","2025-06-03")
SECONDS=86400
MAX_BYTES=2_000_000
BASE="https://futures.kraken.com/api/charts/v1/analytics"


def unix_utc(day):
    d=datetime.datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    return int(d.timestamp())


def classify(symbol, kind, day, *, status, raw=b"", error=""):
    start=unix_utc(day)
    if symbol not in SYMBOLS or kind not in TYPES or day not in STARTS:
        raise ValueError("UNREGISTERED_SOURCE_REQUEST")
    base={"symbol":symbol,"analytics":kind,"window_start":day,"http_status":status,
          "sha256":hashlib.sha256(raw).hexdigest() if raw else None,
          "raw_bytes":len(raw),"error":error[:100] or None,
          "status":"SOURCE_BLOCKED_OR_EMPTY","rows":0}
    if symbol=="PF_BNBUSD" and day=="2023-01-03":
        base["status"]="PRE_LISTING_INELIGIBLE"
        return base
    if status != 200 or not raw:
        return base
    try:
        doc=json.loads(raw.decode("utf-8"))
        result=doc["result"]
        stamps=result["timestamp"]
        if not isinstance(stamps,list):
            raise ValueError("TIMESTAMP_NOT_LIST")
        if not stamps:
            base["error"]="EMPTY_TIMESTAMPS"
            return base
        nums=[int(v) for v in stamps]
        if any(isinstance(v, bool) or not isinstance(v,int) for v in stamps):
            raise ValueError("NONINTEGER_TIMESTAMP")
        units={"milliseconds" if 10**12<=v<10**13 else "seconds" if 10**9<=v<10**10 else "invalid"
               for v in nums}
        if len(units)!=1 or "invalid" in units:
            raise ValueError("INVALID_OR_MIXED_EPOCH_UNIT")
        if "milliseconds" in units:
            if any(v%1000 for v in nums):
                raise ValueError("SUBSECOND_EPOCH_NOT_ALLOWED_IN_1D_SOURCE")
            nums=[v//1000 for v in nums]
        if not all(start<=v<start+5*SECONDS for v in nums):
            raise ValueError("RETURNED_TIMESTAMP_OUTSIDE_FROZEN_WINDOW")
        if nums!=sorted(nums) or len(nums)!=len(set(nums)):
            raise ValueError("TIMESTAMPS_NOT_STRICTLY_INCREASING")
        base.update({"status":"SOURCE_DATE_COVERAGE_CANDIDATE","rows":len(nums),
                     "first_utc":datetime.datetime.fromtimestamp(nums[0],datetime.timezone.utc).isoformat(),
                     "last_utc":datetime.datetime.fromtimestamp(nums[-1],datetime.timezone.utc).isoformat(),
                     "error":None})
    except Exception as exc:
        base["error"]=type(exc).__name__+":"+str(exc)[:70]
    return base


def probe(symbol,kind,day):
    start=unix_utc(day)
    url=(BASE+"/"+urllib.parse.quote(symbol,safe="")+"/"+urllib.parse.quote(kind,safe="")
         +"?"+urllib.parse.urlencode({"since":start,"interval":86400,"to":start+5*SECONDS}))
    request=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"ConvexLab-PublicSourceOnly/0.1"})
    status=0; raw=b""; err=""
    try:
        with urllib.request.urlopen(request, timeout=8) as resp:
            status=resp.status
            raw=resp.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES:
                raise ValueError("MAX_RESPONSE_BYTES_EXCEEDED")
    except urllib.error.HTTPError as exc:
        status=exc.code; err="HTTP_"+str(exc.code)
    except Exception as exc:
        err=type(exc).__name__+":"+str(exc)[:80]
    return classify(symbol,kind,day,status=status,raw=raw,error=err)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    observations=[]
    for symbol in SYMBOLS:
        for kind in TYPES:
            for day in STARTS:
                res=probe(symbol,kind,day)
                observations.append(res)
                print("SOURCE_GATE",json.dumps(res,sort_keys=True),flush=True)
                time.sleep(.2)
    result={"status":"SOURCE_ONLY_FINAL_NO_ECONOMIC_VERDICT",
            "expected_cases":16,"cases":len(observations),"probes":observations,
            "complete_historical_orderbook_proven":False,
            "actual_fills_proven":False,"independent_oos":False,
            "trading_authority":"NONE"}
    (a.output_dir/"KRAKEN_PUBLIC_ANALYTICS_16_SOURCE_PROBES.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("CLASS_COUNTS",dict(__import__("collections").Counter(v["status"] for v in observations)))
    print("VERDICT",result["status"])


if __name__=="__main__":
    main()
