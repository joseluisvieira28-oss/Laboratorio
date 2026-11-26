#!/usr/bin/env python3
"""Real Bybit perpetual OHLC + open interest. Read-only public API, no accounts."""
import datetime as dt
import hashlib
import json
import math
import pathlib
import time
import urllib.parse
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"results"
START=dt.datetime(2026,11,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2026,11,25,tzinfo=dt.timezone.utc)
N=int((END-START).total_seconds()/3600)
MS=3600000
BASE="https://api.bybit.com/v5/market/"
SYMBOLS=("BTCUSDT","ETHUSDT")

def ms(t):
    return int(t.timestamp()*1000)

def get(path,params,receipts,attempts=3):
    url=BASE+path+"?"+urllib.parse.urlencode(params)
    for attempt in range(attempts):
        try:
            t1=dt.datetime.now(dt.timezone.utc).isoformat()
            request=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-LIQMAP001-Public-ReadOnly/1.0",
                                                         "Accept":"application/json"})
            with urllib.request.urlopen(request,timeout=30) as f:
                raw=f.read(3_000_000)
            t2=dt.datetime.now(dt.timezone.utc).isoformat()
            if len(raw)>=3_000_000:raise ValueError("source response too large")
            payload=json.loads(raw)
            if payload.get("retCode")!=0:raise ValueError("Bybit "+str(payload.get("retCode"))+" "+str(payload.get("retMsg")))
            receipts.append({"url":url,"start_utc":t1,"end_utc":t2,"bytes":len(raw),
                             "raw_sha256":hashlib.sha256(raw).hexdigest()})
            return payload["result"]
        except Exception:
            if attempt==attempts-1:raise
            time.sleep(1.5*(attempt+1))

def candles(symbol,receipts):
    params={"category":"linear","symbol":symbol,"interval":"60",
            "start":ms(START),"end":ms(END)-1,"limit":1000}
    result=get("kline",params,receipts)
    output={}
    for r in result["list"]:
        t=int(r[0])
        if ms(START)<=t<ms(END):
            o,h,l,c=map(float,r[1:5])
            if not all(math.isfinite(x) and x>0 for x in (o,h,l,c)) or not(l<=min(o,c)<=max(o,c)<=h):
                raise ValueError("bad OHLC "+str(t))
            if t in output:raise ValueError("duplicate kline")
            output[t]={"t":t,"o":o,"h":h,"l":l,"c":c}
    return output

def interest(symbol,receipts):
    # Bybit open interest supports public cursor-based pagination.
    # Restrict endTime to the prior completed hour; fail closed on history limits.
    params={"category":"linear","symbol":symbol,"intervalTime":"1h",
            "startTime":ms(START),"endTime":ms(END)-1,"limit":200}
    output={};cursor=None;seen=set()
    for page in range(12):
        p=dict(params)
        if cursor:p["cursor"]=cursor
        result=get("open-interest",p,receipts)
        for r in result["list"]:
            t=int(r["timestamp"])
            if ms(START)<=t<ms(END):
                # From 2026-06-11 Bybit exposes openInterest BOTH sides and
                # singleOpenInterest single-side. Normalize to single-side here
                # to avoid inflating absolute values; signal uses DELTA only.
                raw=float(r["singleOpenInterest"] if "singleOpenInterest" in r else r["openInterest"])
                if not math.isfinite(raw) or raw<=0:raise ValueError("nonpositive OI")
                if t in output and output[t]!=raw:raise ValueError("conflicting OI duplicate")
                output[t]=raw
        nxt=result.get("nextPageCursor","")
        if not nxt:break
        if nxt in seen:raise ValueError("cursor loop")
        seen.add(nxt);cursor=nxt
    else:raise ValueError("OI exceeded pagination cap")
    return output

def align(candles,oi):
    expected=[ms(START)+i*MS for i in range(N)]
    # Bybit documents OI timestamp; it may be sampling at end of hour.
    # Check exact offset rather than silently joining nearest.
    offsets={}
    for offset in (0,MS):
        matched=sum((x+offset) in oi for x in expected)
        offsets[str(offset)]=matched
    offset=max((0,MS),key=lambda x:offsets[str(x)])
    if len(candles)!=N or offsets[str(offset)]!=N:
        raise ValueError("SOURCE_BLOCKED candles="+str(len(candles))+" OI="+str(len(oi))+
              " OI_offset_matching="+json.dumps(offsets)+" required="+str(N))
    arr=[]
    for t in expected:
        if t not in candles or t+offset not in oi:raise ValueError("missing hourly candle/OI")
        arr.append({**candles[t],"oi":oi[t+offset],"oi_obs_time":t+offset})
    return arr,offset

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    payload={"study":"LIQMAP-DIAMANTE-001","window_start":START.isoformat(),"window_end_exclusive":END.isoformat(),
        "expected_hourly_bars":N,"provider":"Bybit v5 linear futures official public GET",
        "accounts_used":0,"orders":0,"data":{},"status":{},"receipts":{}}
    for s in SYMBOLS:
        rr=[]
        try:
            bar=candles(s,rr)
            op=interest(s,rr)
            arr,offset=align(bar,op)
            payload["data"][s]=arr
            payload["status"][s]={"status":"SOURCE_PASS","n":len(arr),
                "oi_timestamp_offset_ms":offset,
                "first":arr[0]["t"],"last":arr[-1]["t"]}
            print("SOURCE_PASS",s,"n",len(arr),"offset",offset,"receipts",len(rr),flush=True)
        except Exception as e:
            payload["status"][s]={"status":"SOURCE_BLOCKED","reason":type(e).__name__+": "+str(e)}
            print("SOURCE_BLOCKED",s,str(e)[:350],flush=True)
        payload["receipts"][s]=rr
        (OUT/"sources.json").write_text(json.dumps(payload,indent=2)+"\n")
    if len(payload["data"])!=2:
        raise RuntimeError("SOURCE_BLOCKED: fewer than two full historical futures markets")
if __name__=="__main__":main()
