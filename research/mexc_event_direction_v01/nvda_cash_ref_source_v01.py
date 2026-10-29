#!/usr/bin/env python3
"""Cash NVDA versus MEXC event index 1m source gate; NO market outcomes."""
import datetime as dt,hashlib,json,math,pathlib,urllib.parse,urllib.request
DAYS=(dt.date(2026,10,1),dt.date(2026,10,2))
OUT=pathlib.Path("artifacts/nvda_cash_ref_event10m_source_v01")
OUT.mkdir(parents=True,exist_ok=True)
def ts(day,h=0,m=0):
    return int(dt.datetime(day.year,day.month,day.day,h,m,tzinfo=dt.timezone.utc).timestamp())
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CashNVDA-SourceOnly/0.1","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as rsp:
        status=rsp.status;raw=rsp.read(2_000_001)
    if status!=200 or len(raw)>2_000_000:raise RuntimeError("HTTP_OR_BODY_BLOCK")
    return json.loads(raw),{"url":url,"http_status":status,"sha256":hashlib.sha256(raw).hexdigest(),
        "bytes":len(raw),"retrieved_utc":dt.datetime.now(dt.timezone.utc).isoformat()}
def yahoo():
    url="https://query1.finance.yahoo.com/v8/finance/chart/NVDA?"+urllib.parse.urlencode(
        {"period1":ts(DAYS[0]),"period2":ts(dt.date(2026,10,3)),"interval":"1m","includePrePost":"false"})
    raw,r=get(url)
    obj=raw.get("chart") or {}
    if obj.get("error") or not isinstance(obj.get("result"),list) or len(obj["result"])!=1:
        raise RuntimeError("YAHOO_RESPONSE_BLOCK")
    row=obj["result"][0];meta=row.get("meta") or {}
    times=row.get("timestamp") or []
    quotes=(row.get("indicators") or {}).get("quote") or []
    if not quotes or len(times)!=len(quotes[0].get("open") or []):
        raise RuntimeError("YAHOO_SCHEMA_BLOCK")
    opens=quotes[0]["open"];closes=quotes[0].get("close") or []
    if len(opens)!=len(closes):raise RuntimeError("YAHOO_QUOTES_BLOCK")
    r.update(provider="UNOFFICIAL_YAHOO_CASH_EQUITY",meta_symbol=meta.get("symbol"),
             timezone=meta.get("exchangeTimezoneName"),source_granularity=meta.get("dataGranularity"))
    if meta.get("symbol")!="NVDA":raise RuntimeError("YAHOO_SYMBOL_NOT_NVDA")
    for day in DAYS:
        a,b=ts(day,13,30),ts(day,14,15)
        selected=[(int(t),o,c) for t,o,c in zip(times,opens,closes) if a<=int(t)<b]
        valid=[x for x in selected if x[0]%60==0 and all(v is not None and math.isfinite(float(v))
                  and float(v)>0 for v in x[1:])]
        r[str(day)]={"returned":len(selected),"valid":len(valid),"unique":len(set(v[0] for v in valid))}
        if len(valid)<25 or len(set(v[0] for v in valid))!=len(valid):
            raise RuntimeError("YAHOO_INTRADAY_COVERAGE_BLOCKED_"+str(day))
    return r
def mexc(day):
    first,last=ts(day,13,20),ts(day,14,20)
    url="https://contract.mexc.com/api/v1/contract/kline/index_price/NVIDIA_USDT?"+urllib.parse.urlencode(
        {"interval":"Min1","start":first,"end":last})
    data,r=get(url)
    if data.get("success") is not True or not isinstance(data.get("data"),dict):
        raise RuntimeError("MEXC_SCHEMA_BLOCK")
    v=data["data"];times=v.get("time") or [];opens=v.get("open") or [];closes=v.get("close") or []
    if not times or len(times)!=len(opens) or len(times)!=len(closes):
        raise RuntimeError("MEXC_ARRAYS_BLOCK")
    valid=[int(t) for t,o,c in zip(times,opens,closes) if first<=int(t)<=last and int(t)%60==0
           and all(x is not None and math.isfinite(float(x)) and float(x)>0 for x in (o,c))]
    r.update(provider="MEXC_STANDARD_FUTURES_INDEX",internal_symbol="NVIDIA_USDT",
             day_utc=str(day),rows=len(times),valid=len(valid),unique=len(set(valid)))
    if len(valid)<50 or len(set(valid))!=len(valid):
        raise RuntimeError("MEXC_MIN1_COVERAGE_BLOCKED_"+str(day))
    return r
def main():
    report={"study":"NVDA_CASH_REFERENCE_EVENT10M_SOURCE_V01","gate":"STARTING",
    "days":[str(x) for x in DAYS],"prior_cashopen_study":"NO_CANDIDATE_PRESERVED",
    "nvda_v06_forward_oct05_30":"PROTECTED_NOT_ACCESSED","historical_price_outcomes_opened":0,
    "signals_generated":0,"cash_asof_receipt_proven":False,
    "event_contract_settlement_parity_proven":False,"private_calls_orders":0,"sources":[]}
    try:
        report["sources"].append(yahoo())
        for day in DAYS:report["sources"].append(mexc(day))
        report["gate"]="HISTORICAL_CASH_REFERENCE_SOURCE_FEASIBLE_ASOF_UNPROVEN"
    except Exception as exc:
        report["gate"]="SOURCE_BLOCKED";report["error"]=type(exc).__name__+":"+str(exc)[:240]
        raise
    finally:
        (OUT/"receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True),flush=True)
if __name__=="__main__":main()
