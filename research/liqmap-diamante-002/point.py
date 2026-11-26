#!/usr/bin/env python3
"""LIQMAP-002: one immutable future daily BTC liquidation-map prediction.
NO TRADES. All market reads are public GET / Hyperliquid public POST info only.
"""
import datetime as dt
import hashlib
import json
import math
import pathlib
import sys
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent
OBS=HERE/"observations"
OUT=HERE/"run_results"
SOURCE="https://raw.githubusercontent.com/rdemb/hyperquant-data/main/liq-map/BTC.json"
STATUS="https://raw.githubusercontent.com/rdemb/hyperquant-data/main/status.json"
HL="https://api.hyperliquid.xyz/info"
ONE_H=3600000
FIRST=dt.date(2026,11,27)
LAST=dt.date(2027,1,26)

def utc():
    return dt.datetime.now(dt.timezone.utc)

def millis(d):
    return int(d.timestamp()*1000)

def receipt(url, raw, began, ended):
    return {"url":url,"start_utc":began.isoformat(),"end_utc":ended.isoformat(),
            "raw_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def get(url):
    began=utc()
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-LIQMAP002-Falsification-ReadOnly/1.0",
                    "Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as res:
        body=res.read(3_000_000)
    ended=utc()
    if len(body)>=3_000_000:raise ValueError("SOURCE_BLOCKED size limit")
    return json.loads(body),receipt(url,body,began,ended),body

def hl_candles(start_ms,end_ms):
    body=json.dumps({"type":"candleSnapshot","req":{"coin":"BTC","interval":"1h",
        "startTime":start_ms,"endTime":end_ms}},sort_keys=True).encode()
    began=utc()
    req=urllib.request.Request(HL,data=body,headers={"Content-Type":"application/json",
        "User-Agent":"CryptoLab-LIQMAP002-Falsification-ReadOnly/1.0"},method="POST")
    with urllib.request.urlopen(req,timeout=35) as r:
        raw=r.read(300000)
    ended=utc()
    if len(raw)>=300000:raise ValueError("PRICE_SOURCE_BLOCKED size limit")
    data=json.loads(raw)
    if not isinstance(data,list):raise ValueError("PRICE_SOURCE_BLOCKED not array")
    receipt_data=receipt(HL+"#candleSnapshot:"+str(start_ms)+":"+str(end_ms),raw,began,ended)
    receipt_data["request_sha256"]=hashlib.sha256(body).hexdigest()
    return data,receipt_data,raw

def clean_candles(rows,first,n,now_ms=None):
    wanted={first+i*ONE_H for i in range(n)}
    m={}
    for r in rows:
        t=int(r["t"])
        if t not in wanted:continue
        if t in m:raise ValueError("PRICE_SOURCE_BLOCKED duplicate hour")
        a,b,c,d=(float(r[k]) for k in ("o","h","l","c"))
        if not all(math.isfinite(x) and x>0 for x in (a,b,c,d)) or not (c<=b and c>=d and d<=a<=b and d<=c):
            # the condition above also validates that the close and open are within high/low;
            # see required final invariant below.
            raise ValueError("PRICE_SOURCE_BLOCKED bad OHLC")
        if not (d<=a<=b and d<=float(r["c"])<=b):raise ValueError("bad OHLC")
        if int(r["T"]) != t+ONE_H-1:raise ValueError("PRICE_SOURCE_BLOCKED bad candle end")
        if now_ms is not None and int(r["T"])>now_ms:raise ValueError("PRICE_SOURCE_BLOCKED unfinished candle")
        m[t]={"t":t,"o":a,"h":b,"l":d,"c":float(r["c"])}
    if len(m)!=n or any(t not in m for t in wanted):
        raise ValueError("PRICE_SOURCE_BLOCKED missing full 1h candles "+str(len(m))+"/"+str(n))
    return [m[first+i*ONE_H] for i in range(n)]

def band_from_map(snapshot):
    if snapshot.get("coin")!="BTC":raise ValueError("SOURCE_BLOCKED wrong symbol")
    mark=float(snapshot["markPx"])
    if not math.isfinite(mark) or mark<=0:raise ValueError("SOURCE_BLOCKED invalid mark")
    coverage=snapshot.get("coverage",{})
    share=float(coverage.get("share",0))
    age=float(snapshot.get("ageMin",{}).get("ntlP50",100000))
    if not math.isfinite(share) or share<.30:raise ValueError("SOURCE_BLOCKED coverage <30%")
    if not math.isfinite(age) or age>15:raise ValueError("SOURCE_BLOCKED stale weighted positions >15m")
    n=0;by_bin={}
    for side in ("longs","shorts"):
        for r in snapshot.get(side,[]):
            p=float(r["px"]);value=float(r["ntlUsd"])
            if not math.isfinite(p) or not math.isfinite(value) or p<=0 or value<=0:
                continue
            n+=1
            if side=="longs" and p>=mark:continue
            if side=="shorts" and p<=mark:continue
            key=math.floor(math.log(p)/.005)
            centre=math.exp((key+.5)*.005)
            d=math.log(centre/mark)
            if abs(d)<.005 or abs(d)>.05:continue
            if side=="longs" and d>=0:continue
            if side=="shorts" and d<=0:continue
            by_bin[key]=by_bin.get(key,0.)+value*math.exp(-abs(d)/.03)
    if n<30:raise ValueError("SOURCE_BLOCKED too few market levels")
    if not by_bin:
        return {"signal":"NO_SIGNAL","mark":mark,"coverage":share,
            "notional_weighted_age_minutes":age,"valid_levels":n}
    best=min(by_bin,key=lambda k:(-by_bin[k],k))
    target=math.exp((best+.5)*.005)
    side="UP" if target>mark else "DOWN"
    return {"signal":side,"mark":mark,"coverage":share,
      "notional_weighted_age_minutes":age,"valid_levels":n,
      "target":target,"mirror":mark*mark/target,
      "distance_log":abs(math.log(target/mark)),
      "score_usd_adjusted_not_liquidations":by_bin[best]}

def validate_time(mode,date,now):
    if mode=="preflight":return "LATE_PREFLIGHT_NOT_ECONOMIC"
    d=dt.date.fromisoformat(date)
    if mode!="future" or not(FIRST<=d<=LAST) or d!=now.date() or now.hour>=15:
        raise ValueError("TIMING_BLOCKED no future backfill or late capture")
    return "FUTURE_PENDING_OUTCOME"

def main():
    if len(sys.argv)!=3:raise SystemExit("usage: point.py preflight|future YYYY-MM-DD")
    mode,date=sys.argv[1:]
    OUT.mkdir(parents=True,exist_ok=True)
    now=utc()
    record={"experiment":"LIQMAP-DIAMANTE-002","mode":mode,"requested_date":date,
       "process_started_utc":now.isoformat(),"trades":0,"payments":0,
       "source":"HyperQuant public aggregated Hyperliquid BTC open positions",
       "status":"SOURCE_BLOCKED","receipts":[],"is_future_economic_observation":False}
    try:
        gate=validate_time(mode,date,now)
        mapdata,mr,raw=get(SOURCE)
        record["receipts"].append(mr)
        (OUT/"source_map_raw.json").write_bytes(raw)
        source_asof=dt.datetime.fromtimestamp(int(mapdata["asOf"])/1000,dt.timezone.utc)
        if not dt.timedelta(seconds=-60)<=mr_end_to_date(mr)-source_asof<=dt.timedelta(minutes=20):
            raise ValueError("SOURCE_BLOCKED map age >20 min or future")
        record["map_source_asof_utc"]=source_asof.isoformat()
        record["map_source_age_minutes"]=(mr_end_to_date(mr)-source_asof).total_seconds()/60
        candidate=band_from_map(mapdata)
        # Source status is an independent optional diagnostic, never a prediction.
        try:
            status,sr,sraw=get(STATUS)
            record["receipts"].append(sr)
            record["provider_diagnostics"]={"asOf":status.get("asOf"),
               "coverage":status.get("coverage"),"apiErrors":status.get("apiErrors"),
               "ageNtlP50Min":status.get("ageNtlP50Min")}
            (OUT/"source_status_raw.json").write_bytes(sraw)
        except Exception as e:
            record["provider_diagnostics"]={"status":"STATUS_SOURCE_BLOCKED","error":str(e)}
        # MOM24 uses ONLY full hourly price candles CLOSED before the present decision.
        clock=utc()
        hour=millis(clock)//ONE_H*ONE_H
        start=hour-26*ONE_H
        data,cr,raw=hl_candles(start,hour-1)
        record["receipts"].append(cr)
        (OUT/"source_prior_candles_raw.json").write_bytes(raw)
        bars=clean_candles(data,start,26,now_ms=millis(clock)-1000)
        direction="UP" if bars[-1]["c"]>bars[-25]["c"] else "DOWN"
        record["prior_momentum24_direction"]=direction
        record["prior_last_complete_h1_utc"]=dt.datetime.fromtimestamp(
             bars[-1]["t"]/1000,dt.timezone.utc).isoformat()
        record["prior_candle_24h_close_delta_pct"]=100*(bars[-1]["c"]/bars[-25]["c"]-1)
        record["forecast"]=candidate
        record["captured_utc"]=utc().isoformat()
        record["status"]=gate if candidate["signal"]!="NO_SIGNAL" else "NO_SIGNAL"
        record["is_future_economic_observation"]=mode=="future"
    except Exception as exc:
        record["status"]="TIMING_BLOCKED" if "TIMING_BLOCKED" in str(exc) else "SOURCE_OR_CONTROL_BLOCKED"
        record["error"]=type(exc).__name__+": "+str(exc)
    record["finished_utc"]=utc().isoformat()
    target=OUT/("CAPTURE_"+date+".json")
    target.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    if mode=="future":
        OBS.mkdir(parents=True,exist_ok=True)
        dest=OBS/(date+".json")
        if dest.exists():raise RuntimeError("DUPLICATE_CAPTURE no overwrites, abort")
        dest.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    print("LIQMAP002_CAPTURE",date,record["status"],
          "source",record.get("map_source_age_minutes"),"signal",record.get("forecast",{}).get("signal"),
          "controlled",record.get("prior_momentum24_direction"),flush=True)

def mr_end_to_date(r):
    return dt.datetime.fromisoformat(r["end_utc"])

if __name__=="__main__":main()
