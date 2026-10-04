#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests

HERE=Path(__file__).resolve().parent
CFG=json.loads((HERE/"BITGET_MAKER_MICROSTRUCTURE_SOURCE_CONFIG_V0.1.json").read_text())
OUT=Path("artifacts/cross_venue_stock/bitget_maker_microstructure_source_v01")
UA="CryptoLab-Bitget-MakerMicrostructure-SourceGate/0.1.1"

def h(b): return hashlib.sha256(b).hexdigest()
def ms(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)
def req(url,params=None,timeout=60,retries=4):
    last=None
    for i in range(retries):
        try:
            return requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
        except Exception as e:
            last=e; time.sleep(.5*(i+1))
    raise last

def trade_probe(symbol):
    day=CFG["burned_source_date"]
    start=ms(day+"T14:30:00Z"); end=ms(day+"T19:00:00Z")
    chunk=15*60*1000
    rows=0; first=None; last=None; hashes=[]; codes=[]; sides=set()
    t=start
    while t<end:
        e=min(t+chunk-1,end)
        r=req("https://api.bitget.com/api/v2/mix/market/fills-history",{
          "symbol":symbol,"productType":"USDT-FUTURES","startTime":str(t),
          "endTime":str(e),"limit":"1000"})
        hashes.append(h(r.content)); recs=[]; code=None
        if r.status_code==200:
            try:
                j=r.json(); code=j.get("code"); recs=j.get("data") or []
            except Exception: pass
        codes.append({"http":r.status_code,"code":code,"n":len(recs)})
        for x in recs:
            try:
                ts=int(x["ts"]); float(x["price"]); float(x["size"])
                sides.add(str(x.get("side")))
                first=ts if first is None else min(first,ts)
                last=ts if last is None else max(last,ts)
                rows+=1
            except Exception: pass
        t=e+1; time.sleep(.03)
    return {"rows":rows,"first_ts_ms":first,"last_ts_ms":last,"sides":sorted(sides),
      "chunk_sha256":hashes,"chunks":codes,
      "schema_ok":rows>0 and first is not None and last is not None}

def extract_interesting(base,text):
    out=set()
    patterns=[
      r'''["']([^"']*data-download[^"']*)["']''',
      r'''["']([^"']*historical[^"']*depth[^"']*)["']''',
      r'''["']([^"']*depth[^"']*historical[^"']*)["']''',
      r'''["']([^"']*transaction-record[^"']*)["']''',
      r'''["']([^"']*(?:download|history)[^"']*api[^"']*)["']''',
      r'''https?://[^"'\\\s]{5,300}'''
    ]
    for pat in patterns:
        for m in re.findall(pat,text,re.I):
            x=m if isinstance(m,str) else m[0]
            x=x.replace("\\/","/")
            if len(x)>500: continue
            low=x.lower()
            if any(k in low for k in ("depth","data-download","transaction-record","download","historical")):
                try: out.add(urljoin(base,x))
                except Exception: out.add(x)
    return out

def archive_discovery():
    seeds=[
      "https://www.bitget.com/data-download",
      "https://www.bitget.com/asia/data-download/futures-historical-transaction-record",
      "https://www.bitget.com/data-download/futures-historical-transaction-record"
    ]
    pages=[]; discovered=set(); scripts=set(); bundle_hits=[]
    for url in seeds:
        try:r=req(url,timeout=50)
        except Exception as e:
            pages.append({"url":url,"error":str(e)}); continue
        text=r.text if ("text" in r.headers.get("content-type","") or "html" in r.headers.get("content-type","")) else ""
        discovered.update(extract_interesting(url,text))
        for x in re.findall(r'''<script[^>]+src=["']([^"']+)["']''',text,re.I):
            scripts.add(urljoin(url,x))
        for x in re.findall(r'''(?:href|src)=["']([^"']+)["']''',text,re.I):
            y=urljoin(url,x)
            if any(k in y.lower() for k in ("depth","historical","transaction","data-download")):
                discovered.add(y)
        pages.append({"url":url,"http":r.status_code,"content_type":r.headers.get("content-type"),
          "bytes":len(r.content),"sha256":h(r.content),"script_count":len(scripts)})
    # Technical-only bundle inspection. No market outcomes or prices are opened.
    for u in sorted(scripts)[:60]:
        try:r=req(u,timeout=40)
        except Exception: continue
        ct=r.headers.get("content-type","")
        if r.status_code!=200 or len(r.content)>12_000_000: continue
        text=r.text
        hits=extract_interesting(u,text)
        if hits:
            discovered.update(hits)
            bundle_hits.append({"url":u,"sha256":h(r.content),"bytes":len(r.content),
                                "hits":sorted(hits)[:50]})
    # Probe only route surfaces discovered/guessed; do not download market files.
    guesses=[
      "https://www.bitget.com/data-download/futures-historical-depth-data",
      "https://www.bitget.com/data-download/futures-historical-depth",
      "https://www.bitget.com/data-download/futures-depth-data",
      "https://www.bitget.com/data-download/futures-order-book-depth",
      "https://www.bitget.com/asia/data-download/futures-historical-depth-data",
      "https://www.bitget.com/asia/data-download/futures-historical-depth",
      "https://www.bitget.com/asia/data-download/futures-depth-data",
      "https://www.bitget.com/asia/data-download/futures-order-book-depth"
    ]
    probes=[]
    for url in guesses:
        try:r=req(url,timeout=30)
        except Exception as e:
            probes.append({"url":url,"error":str(e)});continue
        probes.append({"url":url,"http":r.status_code,"final_url":r.url,
                       "content_type":r.headers.get("content-type"),"bytes":len(r.content),
                       "sha256":h(r.content)})
        if r.status_code==200:
            discovered.update(extract_interesting(r.url,r.text))
    return {"pages":pages,"script_count":len(scripts),"bundle_hits":bundle_hits,
            "route_probes":probes,"discovered_urls":sorted(discovered)[:500]}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    trades={}
    for s in CFG["candidates"]:
        p=trade_probe(s); trades[s]=p
        print(s,"trades",p["rows"],"schema",p["schema_ok"],"first",p["first_ts_ms"],"last",p["last_ts_ms"])
    arc=archive_discovery()
    all_trade=all(x["schema_ok"] for x in trades.values())
    depth_hints=[u for u in arc["discovered_urls"] if "depth" in u.lower()]
    depth_surface=bool(depth_hints or any(p.get("http")==200 and "depth" in p["url"] for p in arc["route_probes"]))
    verdict=("BITGET_TRADE_SOURCE_PASS__DEPTH_ARCHIVE_SURFACE_DISCOVERED"
             if all_trade and depth_surface else
             "BITGET_TRADE_SOURCE_PASS__DEPTH_ARCHIVE_DISCOVERY_PENDING"
             if all_trade else "BITGET_MICROSTRUCTURE_SOURCE_BLOCKED")
    rep={"gate_id":CFG["gate_id"],"technical_amendment":"V0.1.1_bundle_discovery",
      "source_only":True,"burned_source_date":CFG["burned_source_date"],"trade_probes":trades,
      "archive_discovery":arc,"depth_url_hints":depth_hints,"verdict":verdict,
      "microstructure_outcomes_opened":0,"private_endpoints_used":False,"account_reads":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False}
    (OUT/"BITGET_MAKER_MICROSTRUCTURE_SOURCE_GATE_V01.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({"verdict":verdict,"trade_source_pass":all_trade,
      "depth_surface":depth_surface,"depth_hint_count":len(depth_hints),
      "depth_hints":depth_hints[:30],
      "bundle_hit_count":len(arc["bundle_hits"]),
      "route_probes":arc["route_probes"]},indent=2))

if __name__=="__main__": main()
