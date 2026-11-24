#!/usr/bin/env python3
"""Source collection for BACKES-004; public GETs only; no orders or private APIs."""
import concurrent.futures as cf
import datetime as dt
import hashlib
import importlib.util
import json
import math
import pathlib
import time
import urllib.parse
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"results"
START=dt.date(2018,1,1)
END=dt.date(2026,11,22)
N=(END-START).days//7+1
SOURCE=HERE.parent/"backes-diamante-002"/"rotation_backtest.py"
spec=importlib.util.spec_from_file_location("frozen_backes_002",SOURCE)
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
CUTOFF_NEXT=END+dt.timedelta(days=1)

def get_json(url,receipts,max_attempts=3):
    for attempt in range(max_attempts):
        try:
            begin=dt.datetime.now(dt.timezone.utc).isoformat()
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-BACKES004-PublicDataReadOnly/1.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=35) as f:
                raw=f.read(8_000_000)
            if len(raw)>=8_000_000:raise ValueError("OVER_SIZE_PUBLIC_API")
            end=dt.datetime.now(dt.timezone.utc).isoformat()
            receipts.append({"url":url,"begin_utc":begin,"end_utc":end,
                             "raw_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
            obj=json.loads(raw)
            if isinstance(obj,dict) and "message" in obj and "result" not in obj:
                raise ValueError("API_MESSAGE "+str(obj.get("message"))[:100])
            return obj
        except Exception as e:
            if attempt==max_attempts-1:raise
            time.sleep(1+attempt*3)

def validate(o,h,l,c):
    if not all(math.isfinite(x) and x>0 for x in (o,h,l,c)):
        raise ValueError("bad or nonpositive price")
    if l>min(o,c,h) or h<max(o,c,l):
        raise ValueError("OHLC invariant violated")
    return {"open":o,"high":h,"low":l,"close":c}

def weeks_from_daily(daily,symbol):
    if len(daily)!=N*7:raise ValueError(symbol+" daily count "+str(len(daily))+" expected "+str(N*7))
    weeks=[]
    for i in range(N):
        monday=START+dt.timedelta(days=7*i)
        vals=[]
        for j in range(7):
            date=monday+dt.timedelta(days=j)
            if date not in daily:raise ValueError(symbol+" missing daily "+str(date))
            vals.append(daily[date])
        weeks.append({"date":str(monday),"open":vals[0]["open"],
                      "high":max(x["high"] for x in vals),
                      "low":min(x["low"] for x in vals),
                      "close":vals[-1]["close"]})
    return weeks

def collect_coinbase(receipts):
    out={}
    for symbol,original in (("BTC","BTC-USD"),("ETH","ETH-USD"),("RATIO","ETH-BTC")):
        daily={}
        d=START
        while d<CUTOFF_NEXT:
            e=min(d+dt.timedelta(days=200),CUTOFF_NEXT)
            p={"start":str(d)+"T00:00:00Z","end":str(e)+"T00:00:00Z","granularity":86400}
            url="https://api.exchange.coinbase.com/products/"+original+"/candles?"+urllib.parse.urlencode(p)
            rows=get_json(url,receipts)
            if not isinstance(rows,list):raise ValueError("Coinbase non-list "+original)
            for candle in rows:
                if not isinstance(candle,list) or len(candle)<6:raise ValueError("Coinbase bad candle")
                date=dt.datetime.fromtimestamp(int(candle[0]),dt.timezone.utc)
                if date.time()!=dt.time():raise ValueError("Coinbase not UTC 00")
                day=date.date()
                if START<=day<CUTOFF_NEXT and d<=day<e:
                    o,h,l,c=float(candle[3]),float(candle[2]),float(candle[1]),float(candle[4])
                    obj=validate(o,h,l,c)
                    if day in daily and obj!=daily[day]:raise ValueError("Coinbase duplicate disagree")
                    daily[day]=obj
            d=e
        out[symbol]=weeks_from_daily(daily,"Coinbase "+original)
    return out

def collect_kraken(receipts):
    out={}
    pair_names={"BTC":"XBTUSD","ETH":"ETHUSD","RATIO":"ETHXBT"}
    since=int(dt.datetime(2017,12,25,tzinfo=dt.timezone.utc).timestamp())
    for symbol,pair in pair_names.items():
        url="https://api.kraken.com/0/public/OHLC?"+urllib.parse.urlencode(
            {"pair":pair,"interval":10080,"since":since})
        resp=get_json(url,receipts)
        if resp.get("error"):raise ValueError("Kraken error "+repr(resp["error"]))
        data=resp.get("result",{})
        keys=[k for k in data if k!="last"]
        if len(keys)!=1:raise ValueError("Kraken pair mismatch "+pair+" "+str(keys))
        candles=data[keys[0]]
        raw={}
        for candle in candles:
            date=dt.datetime.fromtimestamp(int(candle[0]),dt.timezone.utc)
            # 10080m candles are expected Monday 00 UTC; if not, we refuse to re-anchor.
            if date.weekday()!=0 or date.time()!=dt.time():
                raise ValueError("Kraken week anchor != Monday UTC: "+str(date))
            day=date.date()
            if START<=day<CUTOFF_NEXT:
                v=validate(float(candle[1]),float(candle[2]),float(candle[3]),float(candle[4]))
                if day in raw:raise ValueError("Kraken duplicate "+str(day))
                raw[day]=v
        if len(raw)!=N:raise ValueError("Kraken "+pair+" weeks "+str(len(raw))+" expected "+str(N))
        out[symbol]=[]
        for i in range(N):
            day=START+dt.timedelta(days=7*i)
            if day not in raw:raise ValueError("Kraken missing week "+str(day))
            out[symbol].append({"date":str(day),**raw[day]})
    return out

def collect_binance(receipts):
    entries=[];errors=[]
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        futures={pool.submit(base.download,j):j for j in base.jobs()}
        for f in cf.as_completed(futures):
            try:entries.append(f.result())
            except Exception as exc:errors.append(repr(futures[f])+": "+str(exc))
    if errors:raise ValueError("Binance downloads "+repr(errors[:3]))
    if len(entries)!=384:raise ValueError("Binance files !=384")
    receipts.extend([{"url":x["url"],"raw_sha256":x["sha256"],"bytes":x["bytes"],
                      "file":x["file"]} for x in sorted(entries,key=lambda x:x["file"])])
    return {"BTC":base.parse(entries,"BTCUSDT"),
            "ETH":base.parse(entries,"ETHUSDT"),
            "RATIO":base.parse(entries,"ETHBTC")}

def verify_venue(venue,data):
    if set(data)!={"BTC","ETH","RATIO"}:raise ValueError("missing pairs")
    for key,arr in data.items():
        if len(arr)!=N:raise ValueError("missing weeks in "+key)
        for i,row in enumerate(arr):
            expected=START+dt.timedelta(days=7*i)
            if row["date"]!=str(expected):raise ValueError("bad week "+venue+" "+key)
            validate(*[float(row[k]) for k in ("open","high","low","close")])
    for a,b,c in zip(data["BTC"],data["ETH"],data["RATIO"]):
        for k in ("open","close"):
            implied=b[k]/a[k]
            if not .80<c[k]/implied<1.20:
                raise ValueError("cross rate differs >20pct "+venue+" "+a["date"]+" "+k)
    return {"weeks":N,"start":str(START),"end":str(END),
            "ratio_source":"direct ETHBTC traded market",
            "numeraire":"USDT" if venue=="Binance" else "USD"}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    all_venues={};source={};receipts={};errors={}
    for venue,fn in (("Coinbase",collect_coinbase),("Kraken",collect_kraken),("Binance",collect_binance)):
        rr=[];begin=dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            data=fn(rr)
            source[venue]=verify_venue(venue,data)
            all_venues[venue]=data
            print("SOURCE_PASS",venue,source[venue]["weeks"],"weeks",len(rr),"receipts")
        except Exception as e:
            source[venue]={"status":"SOURCE_BLOCKED"}
            errors[venue]=type(e).__name__+": "+str(e)
            print("SOURCE_BLOCKED",venue,errors[venue][:300])
        receipts[venue]=rr
        (OUT/"SOURCE_STATUS.json").write_text(json.dumps({"source":source,"errors":errors,
             "request_receipts":receipts,"utc_started_by_venue":begin},indent=2)+"\n")
        (OUT/"WEEKLY_DATA.json").write_text(json.dumps(all_venues,separators=(",",":"))+"\n")
    if not all_venues:raise RuntimeError("SOURCE_BLOCKED_ALL_EXCHANGES")
    print("READY_FOR_AUDIT",len(all_venues),"sources")
if __name__=="__main__":main()
