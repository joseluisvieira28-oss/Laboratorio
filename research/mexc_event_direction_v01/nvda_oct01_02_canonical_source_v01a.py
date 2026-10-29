#!/usr/bin/env python3
"""Historical required-bar canonical source gate; never calculate directions/outcomes."""
import datetime as dt,hashlib,json,math,pathlib,time
import nvda_oct01_02_source_gate_v01 as source
DAY=source.DAYS
OUT=pathlib.Path("artifacts/nvda_event10m_oct01_02")
def canonical(series,needed):
    ts=series.get("time");op=series.get("open");cl=series.get("close")
    if not isinstance(ts,list) or not isinstance(op,list) or not isinstance(cl,list) or not(len(ts)==len(op)==len(cl)):
        raise ValueError("SOURCE_CANONICAL_ARRAYS_INVALID")
    rows={}
    for t,o,c in zip(ts,op,cl):
        try:
            t=int(t)
        except (ValueError,TypeError):
            continue
        if t not in needed:continue
        if t in rows or t%60:raise ValueError("REQUIRED_TIMESTAMPS_DUPLICATED")
        try:o=float(o);c=float(c)
        except (ValueError,TypeError):raise ValueError("REQUIRED_PRICE_MISSING")
        if not(math.isfinite(o) and o>0 and math.isfinite(c) and c>0):
            raise ValueError("INVALID_REQUIRED_PRICE")
        rows[t]=[t,o,c]
    if set(rows)!=set(needed):raise ValueError("MISSING_REQUIRED_SOURCE_BAR")
    return hashlib.sha256(json.dumps([rows[t] for t in sorted(rows)],separators=(",",":"),allow_nan=False).encode()).hexdigest()

def collect():
    urls={}
    urls["YAHOO"]="https://query1.finance.yahoo.com/v8/finance/chart/NVDA?"+source.urllib.parse.urlencode(
       {"period1":int(source.START.timestamp()),"period2":int(source.END.timestamp()),"interval":"1m","includePrePost":"false"})
    for day in DAY:
        urls[day]="https://contract.mexc.com/api/v1/contract/kline/index_price/NVIDIA_USDT?"+source.urllib.parse.urlencode(
            {"interval":"Min1","start":source.ts(day,13,20),"end":source.ts(day,15,40)})
    result={}
    for key,url in urls.items():
        body,receipt=source.get(url)
        if key=="YAHOO":
            chart=body.get("chart") or {}
            rows=chart.get("result") or []
            if len(rows)!=1 or chart.get("error") or (rows[0].get("meta") or {}).get("symbol")!="NVDA":
                raise ValueError("WRONG_YAHOO_CASH")
            item=rows[0]
            quotes=(item.get("indicators") or {}).get("quote") or []
            if len(quotes)!=1:raise ValueError("YAHOO_QUOTE_MISSING")
            data={"time":item.get("timestamp"),"open":quotes[0].get("open"),"close":quotes[0].get("close")}
            sha={}
            for day in DAY:
                _,need,_=source.required(day)
                sha[day]=canonical(data,need)
        else:
            if body.get("success") is not True or not isinstance(body.get("data"),dict):
                raise ValueError("MEXC_INDEX_BAD_SCHEMA")
            _,_,need=source.required(key)
            sha={key:canonical(body["data"],need)}
        result[key]={"response_raw_sha256":receipt["response_sha256"],"canonical_by_day_sha256":sha,
                     "url":url,"status":receipt["http_status"]}
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"study":"NVDA_EVENT10M_OCT01_02_CANONICAL_SOURCE_V01A",
       "gate":"SOURCE_CANONICAL_BLOCKED","directional_signals_computed":0,
       "wins_losses_evaluated":0,"protected_september_read":False,
       "protected_Oct05_30_NVDA_forward_read":False,
       "attempts":[]}
    try:
        a=collect();time.sleep(1);b=collect()
        report["attempts"]=[a,b]
        if any(a[k]["canonical_by_day_sha256"]!=b[k]["canonical_by_day_sha256"] for k in a):
            raise ValueError("CANONICAL_PRICE_BARS_CHANGED_BETWEEN_SOURCE_REQUESTS")
        report["gate"]="CANONICAL_REQUIRED_BARS_REPRODUCIBLE_PASS"
        report["canonical_pinned"]={k:a[k]["canonical_by_day_sha256"] for k in a}
        report["raw_response_drift"]={k:a[k]["response_raw_sha256"]!=b[k]["response_raw_sha256"] for k in a}
    except Exception as e:
        report["error"]=type(e).__name__+":"+str(e)[:250]
    finally:
        (OUT/"canonical_source_v01a.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    if report["gate"]!="CANONICAL_REQUIRED_BARS_REPRODUCIBLE_PASS":raise SystemExit(2)
if __name__=="__main__":main()
