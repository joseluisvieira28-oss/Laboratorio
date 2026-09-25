#!/usr/bin/env python3
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path

UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-Source-Gate/0.1"}

def get(url, timeout=30):
    req=urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read()

def head(url, timeout=30):
    req=urllib.request.Request(url, headers=UA, method="HEAD")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, dict(r.headers)

def json_get(url):
    s,h,b=get(url)
    return s,h,json.loads(b.decode("utf-8"))

def bybit_listing(symbol="BTCUSDT"):
    url=f"https://quote-saver.bycsi.com/orderbook/linear/{symbol}/"
    status,headers,body=get(url)
    text=body.decode("utf-8","replace")
    files=sorted(set(re.findall(r'href="([^"]+_ob(?:200|500)\.data\.zip)"', text)))
    dates=[]
    depths={}
    for f in files:
        m=re.match(r"(\d{4}-\d{2}-\d{2})_"+re.escape(symbol)+r"_ob(200|500)\.data\.zip",f)
        if not m: continue
        d=dt.date.fromisoformat(m.group(1)); dates.append(d)
        depths[m.group(2)]=depths.get(m.group(2),0)+1
    missing=[]
    if dates:
        have=set(dates)
        cur=min(dates)
        while cur<=max(dates):
            if cur not in have: missing.append(cur.isoformat())
            cur += dt.timedelta(days=1)
    chosen=files[len(files)//2] if files else None
    head_info=None
    if chosen:
        hs,hh=head(url+chosen)
        head_info={"file":chosen,"status":hs,"content_length":hh.get("Content-Length"),"accept_ranges":hh.get("Accept-Ranges"),"last_modified":hh.get("Last-Modified")}
    return {
      "url":url,"http_status":status,"files":len(files),
      "earliest":min(dates).isoformat() if dates else None,
      "latest":max(dates).isoformat() if dates else None,
      "missing_days":len(missing),"missing_sample":missing[:20],
      "depth_file_counts":depths,"head_probe":head_info
    }

def bybit_live():
    url="https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSDT&limit=50"
    try:
        s,h,j=json_get(url)
        r=j.get("result",{})
        return {"ok":True,"status":s,"symbol":r.get("s"),"u":r.get("u"),"seq":r.get("seq"),"ts":r.get("ts"),"cts":r.get("cts"),"bid_levels":len(r.get("b",[])),"ask_levels":len(r.get("a",[]))}
    except Exception as e:
        return {"ok":False,"error":repr(e)}

def mexc_live():
    out={}
    urls={
      "depth":"https://contract.mexc.com/api/v1/contract/depth/BTC_USDT?limit=20",
      "detail":"https://contract.mexc.com/api/v1/contract/detail?symbol=BTC_USDT"
    }
    for k,u in urls.items():
        try:
            s,h,j=json_get(u)
            if k=="depth":
                d=j.get("data",j)
                out[k]={"ok":True,"status":s,"version":d.get("version"),"timestamp":d.get("timestamp"),"bid_levels":len(d.get("bids",[])),"ask_levels":len(d.get("asks",[]))}
            else:
                data=j.get("data",[])
                row=data[0] if isinstance(data,list) and data else data
                out[k]={"ok":True,"status":s,"symbol":row.get("symbol") if isinstance(row,dict) else None,"apiAllowed":row.get("apiAllowed") if isinstance(row,dict) else None}
        except Exception as e:
            out[k]={"ok":False,"error":repr(e)}
    return out

def main():
    receipt={
      "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "purpose":"SOURCE/DATA FEASIBILITY ONLY — no outcomes",
      "bybit_historical_listing":bybit_listing(),
      "bybit_live_orderbook":bybit_live(),
      "mexc_public_market_data":mexc_live(),
    }
    # Conservative gate:
    listing=receipt["bybit_historical_listing"]
    bybit_hist = listing["files"]>0 and listing["earliest"] is not None
    receipt["gate"]={
      "BYBIT_ARCHIVE_DISCOVERABLE":"PASS" if bybit_hist else "BLOCKED",
      "BYBIT_RAW_REPLAY_INTEGRITY":"NOT_TESTED",
      "MEXC_FORWARD_MARKET_DATA":"PASS" if receipt["mexc_public_market_data"]["depth"].get("ok") else "BLOCKED",
      "OUTCOME_TESTING":"BLOCKED"
    }
    Path("research/microstructure_scalping/receipts").mkdir(parents=True,exist_ok=True)
    p=Path("research/microstructure_scalping/receipts/source_probe_v01.json")
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    # Only fail if historical archive discovery itself is unavailable.
    return 0 if bybit_hist else 2

if __name__=="__main__":
    sys.exit(main())
