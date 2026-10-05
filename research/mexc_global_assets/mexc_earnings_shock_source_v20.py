#!/usr/bin/env python3
"""SEC earnings-event + market-data source gate. No strategy outcomes."""
from __future__ import annotations
import csv, io, json, time, zipfile, hashlib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
BASE_BIND=json.loads((HERE/"MEXC_GLOBALASSET_CASHOPEN_SOURCE_BINDING_V0.7.json").read_text())
OUT=Path("artifacts/mexc_global_assets/earnings_shock_v20_source")
SEC_UA="CryptoLab/2.0 research github.com/joseluisvieira28-oss/Laboratorio"
UA="CryptoLab-EarningsShock-Source/2.0"
START=date(2026,7,1); END=date(2026,8,31)

def H(b): return hashlib.sha256(b).hexdigest()
def sec(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def next_weekday(d):
    d=d+timedelta(days=1)
    while d.weekday()>=5: d+=timedelta(days=1)
    return d
def get(url,params=None,headers=None,timeout=60,retries=4):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers=headers or {"User-Agent":UA},timeout=timeout)
            if r.status_code!=200: raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
            return r
        except Exception as e:
            last=e; time.sleep(.8*(i+1))
    raise last

def market_transport(target,ext,d):
    ds=d.isoformat(); a=sec(ds+"T12:20:00Z"); b=sec(ds+"T13:40:00Z")
    mr=get(f"https://api.mexc.com/api/v1/contract/kline/{target}",{"interval":"Min1","start":str(a),"end":str(b)})
    mc=0
    try:
        j=mr.json();md=j.get("data") or {};mc=len(md.get("time") or [])
    except: pass
    br=get(f"https://data.binance.vision/data/futures/um/daily/klines/{ext}/1m/{ext}-1m-{ds}.zip",timeout=90)
    bc=0
    try:
        z=zipfile.ZipFile(io.BytesIO(br.content)); names=z.namelist()
        if len(names)==1:
            for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
                try:t=int(row[0])//1000;float(row[4])
                except:continue
                if a<=t<=b:bc+=1
    except: pass
    gr=get("https://api.bitget.com/api/v2/mix/market/history-candles",{
        "symbol":ext,"productType":"USDT-FUTURES","granularity":"1m",
        "startTime":str(a*1000),"endTime":str(b*1000),"limit":"100"})
    gc=0
    try: gc=len(gr.json().get("data") or [])
    except: pass
    return {
      "mexc_rows":mc,"binance_rows":bc,"bitget_rows":gc,
      "mexc_sha256":H(mr.content),"binance_sha256":H(br.content),"bitget_sha256":H(gr.content),
      "source_pass":mc>=75 and bc>=75 and gc>=75
    }

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    tickers_r=get("https://www.sec.gov/files/company_tickers.json",headers={"User-Agent":SEC_UA,"Accept-Encoding":"gzip, deflate"})
    tmap={}
    for v in tickers_r.json().values():
        tmap[str(v["ticker"]).upper()]=int(v["cik_str"])
    candidates=[]
    for c in BASE_BIND["candidates"]:
        ext=c["external_binance"]
        root=ext[:-4] if ext.endswith("USDT") else ext
        # MEXC names differ for COINBASE and ROBINHOOD, but ext root is the SEC ticker.
        cik=tmap.get(root.upper())
        candidates.append({"target":c["target"],"external":ext,"ticker":root.upper(),"cik":cik})

    events=[]
    for c in candidates:
        if not c["cik"]: continue
        cik10=f'{c["cik"]:010d}'
        try:
            r=get(f"https://data.sec.gov/submissions/CIK{cik10}.json",headers={"User-Agent":SEC_UA,"Accept-Encoding":"gzip, deflate"})
        except Exception as e:
            print(c["ticker"],"SEC_FAIL",repr(e)); continue
        recent=(r.json().get("filings") or {}).get("recent") or {}
        forms=recent.get("form") or []; dates=recent.get("filingDate") or []; items=recent.get("items") or []
        acc=recent.get("acceptanceDateTime") or []; accession=recent.get("accessionNumber") or []
        n=min(len(forms),len(dates))
        for i in range(n):
            if forms[i]!="8-K": continue
            it=items[i] if i<len(items) else ""
            if "2.02" not in str(it): continue
            fd=date.fromisoformat(dates[i])
            if fd<START or fd>END: continue
            session=next_weekday(fd)
            if session>END: continue
            ev={
              "target":c["target"],"external":c["external"],"ticker":c["ticker"],"cik":c["cik"],
              "filing_date":fd.isoformat(),"event_session":session.isoformat(),
              "items":it,"acceptance":acc[i] if i<len(acc) else None,
              "accession":accession[i] if i<len(accession) else None,
              "market_source":None
            }
            events.append(ev)
        time.sleep(.11)

    # Exact duplicate event sessions for one ticker collapse to first accession, source-only.
    uniq=[];seen=set()
    for e in sorted(events,key=lambda x:(x["event_session"],x["ticker"],x["filing_date"])):
        k=(e["ticker"],e["event_session"])
        if k in seen: continue
        seen.add(k);uniq.append(e)
    events=uniq

    for e in events:
        try:e["market_source"]=market_transport(e["target"],e["external"],date.fromisoformat(e["event_session"]))
        except Exception as ex:e["market_source"]={"source_pass":False,"error":repr(ex)}
        print(e["event_session"],e["ticker"],e["target"],e["market_source"].get("source_pass"))
        time.sleep(.05)

    passed=[e for e in events if e["market_source"].get("source_pass")]
    rep={
      "gate_id":"MEXC_EARNINGS_SHOCK_SOURCE_V2_0",
      "source_only":True,
      "event_authority":"SEC 8-K Item 2.02; session conservatively assigned to next weekday after filing date",
      "event_window":["2026-07-01","2026-08-31"],
      "candidate_count":len(candidates),
      "sec_event_count":len(events),
      "full_transport_event_count":len(passed),
      "events":events,
      "verdict":"EARNINGS_SHOCK_SOURCE_PASS" if len(passed)>=8 else ("EARNINGS_SHOCK_SOURCE_UNDERPOWERED" if passed else "EARNINGS_SHOCK_SOURCE_BLOCKED"),
      "outcomes_opened":0,
      "private_endpoints_used":False,"account_reads":False,"orders":False,"wallets":False,"live_trading":False
    }
    (OUT/"MEXC_EARNINGS_SHOCK_SOURCE_V20.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({"verdict":rep["verdict"],"sec_event_count":len(events),"full_transport_event_count":len(passed),
      "passed":[{"session":e["event_session"],"ticker":e["ticker"],"target":e["target"]} for e in passed]},indent=2))
if __name__=="__main__":main()
