#!/usr/bin/env python3
"""As-of NVDA cash equity vs MEXC stock-index freshness source probe. No price outcomes."""
import datetime as dt,hashlib,json,math,pathlib,urllib.parse,urllib.request
from zoneinfo import ZoneInfo
OUT=pathlib.Path("artifacts/nvda_cash_ref_event10m_fresh_v02")
OUT.mkdir(parents=True,exist_ok=True)
UTC=dt.timezone.utc
def now():
    return dt.datetime.now(UTC)
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-NVDA-Freshness-ReadOnly/0.2","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as resp:
        status=resp.status;body=resp.read(2_000_001)
    if status!=200 or len(body)>2_000_000:raise RuntimeError("HTTP_OR_SIZE_BLOCKED")
    return json.loads(body),{"url":url,"status":status,"raw_sha256":hashlib.sha256(body).hexdigest(),
    "received_at_utc":now().isoformat(),"raw_bytes":len(body)}
def last_complete(times,values,recv):
    obs=[]
    for t,v in zip(times,values):
        try:t=int(t);v=float(v)
        except (ValueError,TypeError):continue
        if math.isfinite(v) and v>0 and t%60==0 and t+60<=recv-5:
            obs.append(t)
    if not obs:raise ValueError("NO_CLOSED_1M_CANDLE")
    return max(obs)
def yahoo():
    url="https://query1.finance.yahoo.com/v8/finance/chart/NVDA?range=1d&interval=1m&includePrePost=false"
    obj,r=get(url)
    chart=obj.get("chart") or {};results=chart.get("result") or []
    if chart.get("error") or len(results)!=1:raise RuntimeError("BAD_YAHOO_RESPONSE")
    item=results[0];metadata=item.get("meta") or {}
    if metadata.get("symbol")!="NVDA":raise ValueError("WRONG_STOCK")
    quote=(item.get("indicators") or {}).get("quote") or []
    if not quote:raise ValueError("NO_EQUITY_QUOTE")
    times=item.get("timestamp") or [];closes=quote[0].get("close") or []
    receipt=int(dt.datetime.fromisoformat(r["received_at_utc"]).timestamp())
    latest=last_complete(times,closes,receipt)
    r.update(provider="UNOFFICIAL_YAHOO_CASH",symbol=metadata.get("symbol"),
      exchange_data_delayed_by=metadata.get("exchangeDataDelayedBy"),
      exchange_name=metadata.get("exchangeName"),last_completed_candle_start_utc=latest,
      close_freshness_seconds=receipt-(latest+60),
      cash_last_bar_returned_count=len(times))
    return r
def mexc():
    current=int(now().timestamp())
    start=(current-1200)//60*60
    end=(current-60)//60*60
    url="https://contract.mexc.com/api/v1/contract/kline/index_price/NVIDIA_USDT?"+urllib.parse.urlencode(
        {"interval":"Min1","start":start,"end":end})
    obj,r=get(url)
    if obj.get("success") is not True or not isinstance(obj.get("data"),dict):
        raise RuntimeError("MEXC_INDEX_BAD_SCHEMA")
    data=obj["data"];times=data.get("time") or [];closes=data.get("close") or []
    if len(times)!=len(closes):raise ValueError("MEXC_SOURCE_ARRAYS")
    receipt=int(dt.datetime.fromisoformat(r["received_at_utc"]).timestamp())
    latest=last_complete(times,closes,receipt)
    r.update(provider="MEXC_PUBLIC_STANDARD_FUTURES_INDEX",
      last_completed_candle_start_utc=latest,close_freshness_seconds=receipt-(latest+60),
      source_rows=len(times))
    return r
def main():
    t=now();ny=t.astimezone(ZoneInfo("America/New_York"))
    report={"study":"NVDA_CASH_REFERENCE_SOURCE_FRESHNESS_V02",
      "observed_at_utc":t.isoformat(),"ny_market_clock":ny.isoformat(),
      "historical_or_future_price_outcomes_opened":0,"orders_or_accounts":0,
      "protected_oct05_oct30_nvda_forward_read":False,
      "actual_exchange_primary_feed_custody_proven":False,
      "mexc_event_execution_parity_proven":False,
      "gate":"STARTING","sources":[]}
    try:
        minutes=ny.hour*60+ny.minute
        if not(ny.weekday()<5 and 580<=minutes<=950):
            raise RuntimeError("NOT_INSIDE_FROZEN_NY_REGULAR_SESSION")
        report["sources"]=[yahoo(),mexc()]
        for src in report["sources"]:
            freshness=src["close_freshness_seconds"]
            if freshness<0 or freshness>120:
                raise RuntimeError("STALE_PUBLIC_REFERENCE_"+src["provider"]+"_lag"+str(freshness))
        report["gate"]="SINGLE_ASOF_FRESHNESS_SMOKE_PASS__NOT_CUSTODY"
    except Exception as ex:
        report["gate"]="SOURCE_FRESHNESS_BLOCKED"
        report["error"]=type(ex).__name__+":"+str(ex)[:200]
        raise
    finally:
        (OUT/"freshness_receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True),flush=True)
if __name__=="__main__":main()
