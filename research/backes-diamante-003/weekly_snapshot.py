#!/usr/bin/env python3
"""Forward read-only snapshot of unchanged BACKES-002 signal AFTER weekly close.
Deliberately measures post-decision quotes, never fictional Monday 00:00 fills.
"""
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import sys
import urllib.parse
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"forward_results"
URL="https://data-api.binance.vision"
spec=importlib.util.spec_from_file_location("frozen_backes_002",HERE.parent/"backes-diamante-002"/"rotation_backtest.py")
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
START=dt.date(2026,11,30)

def get_api(path,params):
    url=URL+path+"?"+urllib.parse.urlencode(params)
    request=urllib.request.Request(url,headers={"User-Agent":"Backes-Diamante-003-Research-No-Trades"})
    begin=dt.datetime.now(dt.timezone.utc).isoformat()
    with urllib.request.urlopen(request,timeout=25) as response:
        raw=response.read(250000)
    end=dt.datetime.now(dt.timezone.utc).isoformat()
    return json.loads(raw),dict(url=url,t_begin=begin,t_end=end,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def verify_target(req,now):
    day=dt.date.fromisoformat(req)
    if day<START or day.weekday()!=0:raise ValueError("INVALID_REQUEST_DAY")
    if now.date()!=day or now.weekday()!=0:raise ValueError("NOT_PROSPECTIVE_WINDOW: date mismatch")
    if not (now.hour<6):raise ValueError("EXPIRED_WINDOW: timestamp after 06:00 UTC")
    return day

def weekly_closed(rows,target):
    closes=[]
    for r in rows:
        ms=int(r[0]);last_ms=int(r[6]);a=dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc)
        closed=dt.datetime.fromtimestamp(last_ms/1000,dt.timezone.utc)
        if a.weekday()!=0 or a.time()!=dt.time():raise ValueError("INVALID_WEEK_TIME")
        if last_ms< int(dt.datetime.combine(target,dt.time(),dt.timezone.utc).timestamp()*1000):
            closes.append((a.date(),{"date":str(a.date()),"open":float(r[1]),
                "high":float(r[2]),"low":float(r[3]),"close":float(r[4])},last_ms))
    if not closes:raise ValueError("SOURCE_BLOCKED: empty weeks")
    for prev,next_ in zip(closes,closes[1:]):
        if (next_[0]-prev[0]).days!=7:raise ValueError("SOURCE_BLOCKED: weekly gap")
    if closes[-1][0]!=target-dt.timedelta(days=7):
        raise ValueError("SOURCE_BLOCKED: missing latest fully closed week")
    if len(closes)<52:raise ValueError("SOURCE_BLOCKED: insufficient weekly history")
    return [x[1] for x in closes]

def calculate(rows,target):
    candles=weekly_closed(rows,target)
    old=base.signals(candles)
    return {"target_week_start_utc":str(target),"last_complete_week_start_utc":candles[-1]["date"],
            "last_complete_week_end_utc":str(target-dt.timedelta(days=1)),
            "signal":old[-1],"n_closed_weeks":len(candles)}

def main():
    if len(sys.argv)!=2:raise SystemExit("usage weekly_snapshot.py YYYY-MM-DD")
    target=sys.argv[1];OUT.mkdir(parents=True,exist_ok=True)
    now=dt.datetime.now(dt.timezone.utc)
    record={"research":"BACKES-DIAMANTE-003","request":target,
        "started_utc":now.isoformat(),"trading_orders":0,
        "frozen_base":"BACKES-002; native 1w SOURCE_VARIANT",
        "base_rule_source_sha":"b8895efb4a36c4c2c2e70fe2cab1738358eda2aa",
        "fills":"NONE; quotes are observations after decision",
        "status":"SOURCE_BLOCKED"}
    try:
        day=verify_target(target,now)
        candles,src=get_api("/api/v3/klines",{"symbol":"ETHBTC","interval":"1w","limit":600})
        s=calculate(candles,day)
        record["source_klines"]=src
        record.update(s)
        record["signal_locked_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
        quotes={}
        for symbol in ("BTCUSDT","ETHUSDT","ETHBTC"):
            q,metadata=get_api("/api/v3/ticker/bookTicker",{"symbol":symbol})
            bid=float(q["bidPrice"]);ask=float(q["askPrice"])
            if min(bid,ask)<=0 or ask<bid or (ask/bid-1)>.03:
                raise ValueError("SOURCE_BLOCKED invalid/stale spread")
            quotes[symbol]={"bid":bid,"ask":ask,"spread_bps":round((ask/bid-1)*10000,5),
                             "receipt":metadata}
        record["quotes"]=quotes
        record["capture_complete_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
        record["status"]="SHADOW_CAPTURE_ONLY"
    except Exception as e:
        record["error"]=type(e).__name__+": "+str(e)
    name=OUT/(target+".json")
    name.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    print("BACKES_003",target,record["status"],record.get("signal","N/A"))
    if record["status"]!="SHADOW_CAPTURE_ONLY":sys.exit(2)
if __name__=="__main__":main()
