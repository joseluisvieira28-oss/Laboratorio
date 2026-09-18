from __future__ import annotations
import csv, hashlib, io, json, time, urllib.parse, urllib.request, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"cross_venue_diamond_replication_002_okx_full_source"
RAW=OUT/"raw"; RAW.mkdir(parents=True,exist_ok=True)
BASE="https://www.okx.com/api/v5/public/market-data-history"
UA="CROSS-VENUE-DIAMOND-REPLICATION-002 full-source/1.0"

CANDLE_MONTHS=[f"{y:04d}-{m:02d}" for y,m in [(2024,m) for m in range(9,13)]+[(2025,m) for m in range(1,13)]]
FUNDING_MONTHS=[f"2025-{m:02d}" for m in range(1,13)]
SEGMENTS={
  2:[("2024-09-01T00:00:00Z","2025-06-01T00:00:00Z"),("2025-07-01T00:00:00Z","2025-12-01T00:00:00Z")],
  3:[("2025-01-01T00:00:00Z","2025-10-01T00:00:00Z"),("2025-11-01T00:00:00Z","2025-12-01T00:00:00Z")],
}

def ms(x): return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)
def iso(t): return datetime.fromtimestamp(t/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")
def sha(b): return hashlib.sha256(b).hexdigest()

def query(module,beg,end):
    params={"module":str(module),"instType":"SWAP","dateAggrType":"monthly","begin":ms(beg),"end":ms(end),"instFamilyList":"AVAX-USDT"}
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(params),headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as r: body=json.loads(r.read().decode())
    if body.get("code")!="0": raise RuntimeError(f"PROVIDER:{body.get('code')}:{body.get('msg')}")
    refs=[]
    for d in body.get("data") or []:
      for detail in d.get("details") or []:
       for g in detail.get("groupDetails") or []:
        if g.get("url") and g.get("filename"): refs.append({"filename":g["filename"],"url":g["url"]})
    return refs

def required(name,module):
    months=CANDLE_MONTHS if module==2 else FUNDING_MONTHS
    stem="candlesticks" if module==2 else "fundingrates"
    return any(name==f"AVAX-USDT-SWAP-{stem}-{mo}.zip" for mo in months)

def download(url):
    if urlparse(url).scheme!="https": raise RuntimeError("NON_HTTPS")
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=120) as r: return r.read()

def ts_index(header):
    out=[]
    for i,x in enumerate(header):
      q=x.strip().lower().replace("_","")
      if q in {"ts","timestamp","opentime","fundingtime","time"} or q.endswith("timestamp"): out.append(i)
    if len(out)!=1: raise RuntimeError(f"AMBIGUOUS_TS:{header}:{out}")
    return out[0]

def parse_ts(x):
    q=x.strip().strip('"')
    if q.isdigit():
      n=int(q); return n*1000 if n<10_000_000_000 else n
    return int(datetime.fromisoformat(q.replace("Z","+00:00")).timestamp()*1000)

def inspect(name,b,module):
    z=zipfile.ZipFile(io.BytesIO(b))
    if z.testzip(): raise RuntimeError(f"ZIP_BAD:{name}")
    times=[]; schemas=[]; rows=0
    for member in [x for x in z.namelist() if not x.endswith("/")]:
      p=Path(member)
      if p.is_absolute() or ".." in p.parts: raise RuntimeError(f"UNSAFE:{member}")
      txt=z.read(member).decode("utf-8-sig","replace")
      try: dialect=csv.Sniffer().sniff(txt[:8192],delimiters=",;\t|")
      except Exception: dialect=csv.excel
      r=csv.reader(io.StringIO(txt),dialect)
      header=next(r); ti=ts_index(header); local=[]
      for row in r:
       if row and len(row)>ti:
        local.append(parse_ts(row[ti])); rows+=1
      times.extend(local); schemas.append({"member":member,"header":header,"timestamp_column":header[ti],"rows":len(local)})
    st=sorted(times); intervals=Counter((b-a)//1000 for a,b in zip(st,st[1:]) if b>=a)
    return {"filename":name,"sha256":sha(b),"bytes":len(b),"rows":rows,"members":schemas,
      "unique_timestamps":len(set(st)),"duplicates":len(st)-len(set(st)),
      "min_ts_utc":iso(st[0]),"max_ts_utc":iso(st[-1]),"min_ts":st[0],"max_ts":st[-1],
      "interval_seconds_top":intervals.most_common(10),
      "candle_non60":sum(v for k,v in intervals.items() if k!=60) if module==2 else None}

def main():
    payloads={2:{},3:{}}
    conflicts=[]
    for module in (2,3):
      for beg,end in SEGMENTS[module]:
        refs=query(module,beg,end)
        for ref in refs:
          name=Path(ref["filename"]).name
          if not required(name,module): continue
          b=download(ref["url"]); digest=sha(b)
          if name in payloads[module] and payloads[module][name]["sha256"]!=digest:
            conflicts.append(name); continue
          if name not in payloads[module]:
            (RAW/f"m{module}__{name}").write_bytes(b)
            payloads[module][name]={"bytes":b,"sha256":digest}
        time.sleep(0.6)

    expected2={f"AVAX-USDT-SWAP-candlesticks-{mo}.zip" for mo in CANDLE_MONTHS}
    expected3={f"AVAX-USDT-SWAP-fundingrates-{mo}.zip" for mo in FUNDING_MONTHS}
    files=[]
    for module,expected in ((2,expected2),(3,expected3)):
      missing=sorted(expected-set(payloads[module]))
      if missing: raise RuntimeError(f"MISSING_REQUIRED_M{module}:{missing}")
      for name in sorted(expected):
        files.append({"module":module,**inspect(name,payloads[module][name]["bytes"],module)})

    candles=sorted([x for x in files if x["module"]==2],key=lambda x:x["min_ts"])
    funding=sorted([x for x in files if x["module"]==3],key=lambda x:x["min_ts"])
    candle_boundary_gaps=[(b["min_ts"]-a["max_ts"])//1000 for a,b in zip(candles,candles[1:])]
    funding_boundary_gaps=[(b["min_ts"]-a["max_ts"])//1000 for a,b in zip(funding,funding[1:])]
    ok=(not conflicts and len(candles)==16 and len(funding)==12 and
        all(x["duplicates"]==0 and x["candle_non60"]==0 for x in candles) and
        all(x["duplicates"]==0 for x in funding) and
        all(x==60 for x in candle_boundary_gaps) and
        max(x["max_ts"] for x in files)<ms("2026-01-01T00:00:00Z"))
    cleanfiles=[]
    for x in files:
      y=dict(x); y.pop("min_ts"); y.pop("max_ts"); cleanfiles.append(y)
    receipt={"lab_id":"CROSS-VENUE-DIAMOND-REPLICATION-002","stage":"OKX_FULL_SOURCE_ACQUISITION_VALIDATION",
      "classification":"OKX_FULL_SOURCE_DATA_PASS" if ok else "OKX_FULL_SOURCE_DATA_FAIL",
      "required_candle_months":CANDLE_MONTHS,"required_funding_months":FUNDING_MONTHS,
      "files":cleanfiles,"candle_boundary_gap_seconds":candle_boundary_gaps,
      "funding_boundary_gap_seconds":funding_boundary_gaps,"conflicts":conflicts,
      "market_values_persisted":False,"signal_calculation_performed":False,
      "return_calculation_performed":False,"pnl_calculation_performed":False,"2026_plus_accessed":False}
    (OUT/"CROSS_VENUE_DIAMOND_REPLICATION_002_OKX_FULL_SOURCE_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"candle_files":len(candles),"funding_files":len(funding),
      "candle_min":candles[0]["min_ts_utc"],"candle_max":candles[-1]["max_ts_utc"],
      "funding_min":funding[0]["min_ts_utc"],"funding_max":funding[-1]["max_ts_utc"],
      "candle_boundary_gap_set":sorted(set(candle_boundary_gaps)),"funding_boundary_gap_set":sorted(set(funding_boundary_gaps))},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
