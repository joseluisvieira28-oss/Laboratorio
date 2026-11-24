#!/usr/bin/env python3
"""BACKES-006 two-venue read-only shadow ledger. Never places orders/trades.
Immutable 004 weekly history, 005 allocation logic, public Binance/Coinbase GETs.
Preflight past week is explicitly excluded from future economic evidence.
"""
import datetime as dt
import hashlib
import importlib.util
import json
import math
import pathlib
import sys
import urllib.parse
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"results"
INPUT=HERE/"inputs"
HISTORY_SHA="4e256e2f0d4359943f96e9b1eb87e7cfe8cd6d6ca07728db7d5aa2dd4800d828"
ECON_SHA="aa7305b470b3e4623965216608ef80c932682ac072b254c75b1200771454beb2"
FIRST=dt.date(2026,11,30)
LAST_IN_BASE=dt.date(2026,11,22)
FIRST_NEW=dt.date(2026,11,23)
MODELS=("ROT_TREND40_VOL20","MOM8_TREND40_VOL20")
REFS=("CASH","BTC","FROZEN002","HALF_ROT","BTC_TREND40")
P0=HERE.parent/"backes-diamante-005"/"evaluate.py"
spec=importlib.util.spec_from_file_location("frozen_b005",P0)
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

def now_utc():
    return dt.datetime.now(dt.timezone.utc)

def iso(t=None):
    return (t or now_utc()).isoformat()

def validate_mode(mode,target,now=None):
    now=now or now_utc()
    day=dt.date.fromisoformat(target)
    if day.weekday()!=0:raise ValueError("TIMING_BLOCKED not Monday")
    if mode=="preflight":
        if day!=FIRST_NEW:raise ValueError("preflight only fixed Monday 2026-11-23")
        if now.date()<=day:raise ValueError("LATE_PREFLIGHT must be after historical Monday")
        return day
    if mode!="prospective":raise ValueError("unknown mode")
    if day<FIRST or now.date()!=day or now.hour>=6 or now.hour<0:
        raise ValueError("TIMING_BLOCKED prospective must match current Monday UTC 00:00-06:00 and >= 2026-11-30")
    return day

def file_hash(path,expected):
    if not path.exists():raise ValueError("SOURCE_BLOCKED missing previous artifact file "+path.name)
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual!=expected:raise ValueError("SOURCE_BLOCKED archive content mismatch "+path.name)
    return actual

def load_history():
    file_hash(INPUT/"WEEKLY_DATA.json",HISTORY_SHA)
    file_hash(INPUT/"ECONOMIC.json",ECON_SHA)
    data=json.loads((INPUT/"WEEKLY_DATA.json").read_text())
    if set(data)!={"Binance","Coinbase"}:raise ValueError("SOURCE_BLOCKED expected two venues")
    for venue,weekly in data.items():
        p.b004.check_data(weekly)
        if dt.date.fromisoformat(weekly["BTC"][-1]["date"])+dt.timedelta(days=6)!=LAST_IN_BASE:
            raise ValueError("SOURCE_BLOCKED wrong immutable cutoff")
    return data

def get_json(url,receipts,tag):
    started=iso()
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Backes006-NoTrading/1.0",
                                              "Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as response:
        raw=response.read(4_000_000)
    ended=iso()
    if len(raw)>=4_000_000:raise ValueError("SOURCE_BLOCKED response oversize")
    receipts.append({"tag":tag,"url":url,"start_utc":started,"end_utc":ended,
                     "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()})
    return json.loads(raw)

def validate_daily(o,h,l,c):
    vals=[float(q) for q in (o,h,l,c)]
    o,h,l,c=vals
    if not all(math.isfinite(x) and x>0 for x in vals):
        raise ValueError("SOURCE_BLOCKED nonfinite or nonpositive price")
    if l>min(o,c) or h<max(o,c) or l>h:
        raise ValueError("SOURCE_BLOCKED invalid daily OHLC")
    return {"open":o,"high":h,"low":l,"close":c}

def day_ts(day):
    return int(dt.datetime.combine(day,dt.time(),dt.timezone.utc).timestamp()*1000)

def missing_daily_coinbase(symbol,start,end,receipts):
    product={"BTC":"BTC-USD","ETH":"ETH-USD","RATIO":"ETH-BTC"}[symbol]
    data={}
    while start<end:
        stop=min(start+dt.timedelta(days=80),end)
        q={"start":start.isoformat()+"T00:00:00Z",
           "end":stop.isoformat()+"T00:00:00Z","granularity":86400}
        url="https://api.exchange.coinbase.com/products/"+product+"/candles?"+urllib.parse.urlencode(q)
        rows=get_json(url,receipts,"Coinbase:"+product)
        if not isinstance(rows,list):raise ValueError("SOURCE_BLOCKED Coinbase not array")
        for r in rows:
            if not isinstance(r,list) or len(r)<6:raise ValueError("bad Coinbase candle")
            when=dt.datetime.fromtimestamp(int(r[0]),dt.timezone.utc)
            day=when.date()
            if when.time()!=dt.time():raise ValueError("SOURCE_BLOCKED non-midnight Coinbase")
            if start<=day<stop:
                v=validate_daily(r[3],r[2],r[1],r[4])
                if day in data and data[day]!=v:raise ValueError("SOURCE_BLOCKED conflicting Coinbase date")
                data[day]=v
        start=stop
    return data

def missing_daily_binance(symbol,start,end,receipts):
    pair={"BTC":"BTCUSDT","ETH":"ETHUSDT","RATIO":"ETHBTC"}[symbol]
    data={}
    while start<end:
        stop=min(start+dt.timedelta(days=300),end)
        q={"symbol":pair,"interval":"1d","startTime":day_ts(start),
           "endTime":day_ts(stop)-1,"limit":1000}
        url="https://data-api.binance.vision/api/v3/klines?"+urllib.parse.urlencode(q)
        rows=get_json(url,receipts,"Binance:"+pair)
        if not isinstance(rows,list):raise ValueError("SOURCE_BLOCKED Binance not array")
        for r in rows:
            when=dt.datetime.fromtimestamp(int(r[0])/1000,dt.timezone.utc)
            day=when.date()
            if when.time()!=dt.time():raise ValueError("SOURCE_BLOCKED non-midnight Binance")
            if start<=day<stop:
                if int(r[6])!=day_ts(day+dt.timedelta(days=1))-1:
                    raise ValueError("SOURCE_BLOCKED Binance candle not closed as expected")
                v=validate_daily(r[1],r[2],r[3],r[4])
                if day in data and data[day]!=v:raise ValueError("SOURCE_BLOCKED conflicting Binance date")
                data[day]=v
        start=stop
    return data

def extend(venue,data,target,receipts):
    day=LAST_IN_BASE+dt.timedelta(days=1)
    if target<day or (target-day).days%7:raise ValueError("SOURCE_BLOCKED non-weekly target")
    if target==day:return data
    extra={};needed=(target-day).days
    for symbol in ("BTC","ETH","RATIO"):
        extra[symbol]=(missing_daily_binance(symbol,day,target,receipts)
             if venue=="Binance" else missing_daily_coinbase(symbol,day,target,receipts))
        if len(extra[symbol])!=needed:raise ValueError(
           "SOURCE_BLOCKED "+venue+" "+symbol+" needs "+str(needed)+" daily, got "+str(len(extra[symbol])))
        for j in range(needed):
            d=day+dt.timedelta(days=j)
            if d not in extra[symbol]:raise ValueError("SOURCE_BLOCKED missing "+str(d))
    weekly={k:list(v) for k,v in data.items()}
    for monday_offset in range(0,needed,7):
        monday=day+dt.timedelta(days=monday_offset)
        for symbol in ("BTC","ETH","RATIO"):
            rows=[extra[symbol][monday+dt.timedelta(days=i)] for i in range(7)]
            weekly[symbol].append({"date":str(monday),"open":rows[0]["open"],
                "high":max(r["high"] for r in rows),"low":min(r["low"] for r in rows),
                "close":rows[-1]["close"]})
    for k,seq in weekly.items():
        if len(seq)!=464+needed//7:raise ValueError("SOURCE_BLOCKED missing week")
    for a,b,c in zip(weekly["BTC"][-needed//7:],weekly["ETH"][-needed//7:],
                      weekly["RATIO"][-needed//7:]):
        if a["date"]!=b["date"] or a["date"]!=c["date"]:raise ValueError("SOURCE_BLOCKED bad cross date")
        if not 0.8 < c["close"]/(b["close"]/a["close"]) < 1.2:
            raise ValueError("SOURCE_BLOCKED cross-rate >20pct")
    return weekly

def calculate(data,target):
    """Use exact frozen historic formula, no current-week price or lookahead."""
    n=len(data["BTC"])
    if n<41 or data["BTC"][-1]["date"]!=str(target-dt.timedelta(days=7)):
        raise ValueError("SOURCE_BLOCKED not last fully closed weekly bar")
    ratio=data["RATIO"]
    choice_rot=p.b004.b002.signals(ratio)[-1]
    choice_mom="ETH" if ratio[-1]["close"]>ratio[-9]["close"] else "BTC"
    gate=p.trend40(data,n)
    models={}
    for model,choice in (("ROT_TREND40_VOL20",choice_rot),("MOM8_TREND40_VOL20",choice_mom)):
        vol=p.annual_vol(data,choice,n)
        fraction=0 if not gate or vol is None else min(1.,.20/max(vol,.10))
        models[model]={"choice":choice,"trend40":gate,
          "vol12_annualized":vol,
          "target_weight_BTC":fraction if choice=="BTC" else 0.,
          "target_weight_ETH":fraction if choice=="ETH" else 0.,
          "target_weight_CASH":1-fraction}
    return {"target_monday":str(target),"last_complete_week":data["BTC"][-1]["date"],
       "n_completed_weeks":n,"btc_last_close":data["BTC"][-1]["close"],
       "btc_sma40":sum(z["close"] for z in data["BTC"][-40:])/40,
       "ethbtc_last_close":ratio[-1]["close"],
       "ethbtc_close_8w_ago":ratio[-9]["close"],
       "BTC_TREND40":gate,
       "frozen_002_signal":choice_rot,"mom8_signal":choice_mom,
       "models":models}

def price_book(venue,asset,receipts):
    if venue=="Binance":
        pair={"BTC":"BTCUSDT","ETH":"ETHUSDT","RATIO":"ETHBTC"}[asset]
        url="https://data-api.binance.vision/api/v3/ticker/bookTicker?"+urllib.parse.urlencode({"symbol":pair})
        o=get_json(url,receipts,"BOOK:"+venue+":"+pair)
        bid=float(o["bidPrice"]);ask=float(o["askPrice"])
        bqty=float(o["bidQty"]);aqty=float(o["askQty"])
    else:
        pair={"BTC":"BTC-USD","ETH":"ETH-USD","RATIO":"ETH-BTC"}[asset]
        url="https://api.exchange.coinbase.com/products/"+pair+"/book?level=1"
        o=get_json(url,receipts,"BOOK:"+venue+":"+pair)
        if not o.get("bids") or not o.get("asks"):raise ValueError("BOOK_BLOCKED empty Coinbase book")
        bid=float(o["bids"][0][0]);ask=float(o["asks"][0][0])
        bqty=float(o["bids"][0][1]);aqty=float(o["asks"][0][1])
    if not all(math.isfinite(x) for x in (bid,ask,bqty,aqty)):
        raise ValueError("BOOK_BLOCKED nonfinite book")
    if not 0<bid<=ask or bqty<=0 or aqty<=0 or ask/bid>1.03:
        raise ValueError("BOOK_BLOCKED crossed, zero, stale or wide market")
    return {"pair":pair,"bid":bid,"ask":ask,"bid_qty":bqty,"ask_qty":aqty,
       "best_bid_notional_quote":bid*bqty,
       "best_ask_notional_quote":ask*aqty,
       "spread_bps_mid":round(20000*(ask-bid)/(ask+bid),5),
       "receipt_time_utc":receipts[-1]["end_utc"]}

def main():
    if len(sys.argv)!=3:raise SystemExit("Usage: shadow.py preflight|prospective YYYY-MM-DD")
    mode,target=sys.argv[1:]
    OUT.mkdir(parents=True,exist_ok=True)
    record={"experiment":"BACKES-DIAMANTE-006","mode":mode,"target":target,
      "started_utc":iso(),"trades_executed":0,
      "proprietary_Augusto_Backes_strategy":False,
      "historical_archive_sha256":HISTORY_SHA,
      "forecast_reported_profit":None,"next_week_future_PnL":None,
      "status":"SOURCE_BLOCKED","receipts":[],"venues":{}}
    try:
        monday=validate_mode(mode,target)
        history=load_history()
        for venue,base in history.items():
            rows=[]
            try:
                extended=extend(venue,base,monday,rows)
                signal=calculate(extended,monday)
                signal["locked_utc"]=iso()
                # Book requests happen strictly AFTER the independently frozen signal
                # and are observations, not historical fill prices.
                books={k:price_book(venue,k,rows) for k in ("BTC","ETH","RATIO")}
                signal["books"]=books
                signal["quotes_complete_utc"]=iso()
                signal["quote_notionals_are_hypothetical"]=True
                signal["fee_scenarios_bps"]=[10,35,60,80,100]
                signal["routing_80bps_two_leg_stress"]=True
                signal["fills"]=0
                signal["status"]="OBSERVATION_ONLY"
                record["venues"][venue]=signal
            except Exception as exc:
                record["venues"][venue]={"status":"SOURCE_OR_BOOK_BLOCKED",
                     "error":type(exc).__name__+": "+str(exc)}
            record["receipts"].extend(rows)
        if all(record["venues"][v].get("status")=="OBSERVATION_ONLY"
               for v in ("Coinbase","Binance")):
            record["status"]="LATE_PREFLIGHT_ONLY" if mode=="preflight" else "PROSPECTIVE_SHADOW_CAPTURE"
        else:
            record["status"]="SOURCE_OR_BOOK_BLOCKED"
    except Exception as exc:
        record["error"]=type(exc).__name__+": "+str(exc)
        record["status"]="TIMING_BLOCKED" if "TIMING_BLOCKED" in str(exc) else "SOURCE_OR_TECH_BLOCKED"
    record["finished_utc"]=iso()
    record["valid_for_future_economic_sample"]=record["status"]=="PROSPECTIVE_SHADOW_CAPTURE"
    path=OUT/(target+"-"+mode+".json")
    path.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    summary=["# BACKES-006 — "+mode+" "+target,"",
      "- Status: **"+record["status"]+"**",
      "- Original 004 sources validated by SHA256, when available.",
      "- All book prices and spreads are captured AFTER the model decision.",
      "- No orders, no trades, no profit, no portfolio balances.",
      "- Past Monday LATE_PREFLIGHT never enters future economic sample.",
      "- True economic verdict: **NO-GO LIVE**; future evidence pending.",""]
    for venue,s in record["venues"].items():
        summary.append("## "+venue+": "+s["status"])
        if s["status"]=="OBSERVATION_ONLY":
            for k in MODELS:
                m=s["models"][k]
                summary.append("- "+k+": "+m["choice"]+" weight BTC "+
                    f"{m['target_weight_BTC']:.4f}, ETH {m['target_weight_ETH']:.4f}, CASH {m['target_weight_CASH']:.4f}")
            summary.append("- BTC best spread: "+str(s["books"]["BTC"]["spread_bps_mid"])+" bps; ETH best spread: "+
                str(s["books"]["ETH"]["spread_bps_mid"])+" bps")
        else:summary.append("- "+s["error"])
    (OUT/"RESULT.md").write_text("\n".join(summary)+"\n")
    print("BACKES006",record["status"],"mode",mode,"date",target,
        "venue_statuses",[(v,s["status"]) for v,s in record["venues"].items()])
    if record["status"] not in ("LATE_PREFLIGHT_ONLY","PROSPECTIVE_SHADOW_CAPTURE"):
        sys.exit(3)
if __name__=="__main__":main()
