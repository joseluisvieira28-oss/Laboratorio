#!/usr/bin/env python3
"""Historical source-only completeness audit for exactly NVDA Oct1/2, no outcomes."""
import datetime as dt,hashlib,json,math,pathlib,urllib.parse,urllib.request
DAYS=("2026-10-01","2026-10-02")
START=dt.datetime(2026,10,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2026,10,3,tzinfo=dt.timezone.utc)
OUT=pathlib.Path("artifacts/nvda_event10m_oct01_02")
def ts(date,h=0,m=0):return int(dt.datetime.fromisoformat(date+"T00:00:00+00:00").timestamp())+h*3600+m*60
def get(url):
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-Frozen-Oct01-02-NVDA-SourceOnly/0.1"})
    with urllib.request.urlopen(req,timeout=40) as resp:
        status=resp.status;body=resp.read(3_000_001)
    if status!=200 or len(body)>3_000_000:raise RuntimeError("HTTP_OR_BODY_BLOCKED")
    return json.loads(body),{"url":url,"http_status":status,"response_sha256":hashlib.sha256(body).hexdigest(),"raw_bytes":len(body)}
def clean(t,v):
    try:
        t=int(t);v=float(v)
        if t%60 or not math.isfinite(v) or v<=0:return False
        return True
    except (ValueError,TypeError):return False
def unique_bars(times,opens,closes):
    if not isinstance(times,list) or not isinstance(opens,list) or not isinstance(closes,list) or not(len(times)==len(opens)==len(closes)):
        raise RuntimeError("SCHEMA_1M_BAR_ARRAYS")
    out={}
    for t,o,c in zip(times,opens,closes):
        if t is None:continue
        if not(clean(t,o) and clean(t,c)):continue
        t=int(t)
        if t in out:raise RuntimeError("DUPLICATE_1M")
        out[t]=True
    return out
def required(day):
    # 09:35 .. 11:25 America/New_York EDT (UTC-4), 12 fixed slots.
    slots=[ts(day,13,35)+600*i for i in range(12)]
    needed_cash={t-4*60 for t in slots}|{t-60 for t in slots}
    needed_index=needed_cash|set(slots)|{t+600 for t in slots}
    return slots,needed_cash,needed_index
def yahoo():
    url="https://query1.finance.yahoo.com/v8/finance/chart/NVDA?"+urllib.parse.urlencode({
        "period1":int(START.timestamp()),"period2":int(END.timestamp()),
        "interval":"1m","includePrePost":"false"})
    obj,rec=get(url)
    chart=obj.get("chart") or {}
    rows=chart.get("result") or []
    if chart.get("error") or len(rows)!=1:raise RuntimeError("YAHOO_SOURCE_RESPONSE_INVALID")
    item=rows[0]
    meta=item.get("meta") or {}
    if meta.get("symbol")!="NVDA":raise RuntimeError("WRONG_CASH_SYMBOL")
    quote=(item.get("indicators") or {}).get("quote") or []
    if len(quote)!=1:raise RuntimeError("NO_CASH_PRICE_QUOTE")
    price=quote[0]
    bars=unique_bars(item.get("timestamp"),price.get("open"),price.get("close"))
    rec.update(source="YAHOO_UNOFFICIAL_STOCK_CASH",symbol=meta.get("symbol"),
       granularity=meta.get("dataGranularity"),exchange_timezone=meta.get("exchangeTimezoneName"))
    rec["days"]={}
    for day in DAYS:
        _,needed,_=required(day)
        rec["days"][day]={"required_feature_bar_starts":len(needed),
          "feature_bars_present":len(needed&bars.keys()),
          "missing_required_feature_bars":len(needed-bars.keys())}
    return rec
def mexc(day):
    # MEXC 13:20 through 15:40 UTC, fully encompasses all frozen 12 slots+10m targets.
    start=ts(day,13,20);end=ts(day,15,40)
    url="https://contract.mexc.com/api/v1/contract/kline/index_price/NVIDIA_USDT?"+urllib.parse.urlencode({
        "interval":"Min1","start":start,"end":end})
    obj,rec=get(url)
    if obj.get("success") is not True or not isinstance(obj.get("data"),dict):
        raise RuntimeError("MEXC_INDEX_SOURCE_BLOCKED")
    data=obj["data"];bars=unique_bars(data.get("time"),data.get("open"),data.get("close"))
    _,_,needed=required(day)
    rec.update(source="MEXC_STANDARD_FUTURES_INDEX_NOT_EVENT_EXECUTED_PRICE",
      symbol="NVIDIA_USDT",day=day,returned_valid_bars=len(bars),
      required_bar_starts=len(needed),present_required_bar_starts=len(needed&bars.keys()),
      missing_required_bar_starts=len(needed-bars.keys()))
    return rec
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"study":"NVIDIA_EVENT10M_OCT01_02_HIST_SOURCE_ONLY",
      "stage":"NO_OUTCOMES_OPENED","protected_oct05_to_oct30_forward":"UNTOUCHED",
      "protected_september_holdout":"UNTOUCHED","directional_signal_calculated":False,
      "actual_event_payouts_observed":False,"source_receipts":[],"gate":"SOURCE_BLOCKED"}
    try:
        report["source_receipts"].append(yahoo())
        for d in DAYS:report["source_receipts"].append(mexc(d))
        no_missing=all(not p["missing_required_feature_bars"] for p in report["source_receipts"][0]["days"].values())
        no_missing &=all(not p["missing_required_bar_starts"] for p in report["source_receipts"][1:])
        report["gate"]="HISTORICAL_SOURCE_REQUIRED_SLOTS_PASS" if no_missing else "HISTORICAL_SOURCE_REQUIRED_SLOTS_INCOMPLETE"
    except Exception as e:
        report["error"]=type(e).__name__+":"+str(e)[:250]
    finally:
        (OUT/"source_only_receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    if report["gate"]!="HISTORICAL_SOURCE_REQUIRED_SLOTS_PASS":raise SystemExit(2)
if __name__=="__main__":main()
