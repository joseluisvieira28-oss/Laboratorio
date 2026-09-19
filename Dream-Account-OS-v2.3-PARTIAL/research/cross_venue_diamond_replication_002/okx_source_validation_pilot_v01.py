from __future__ import annotations
import csv, hashlib, io, json, urllib.parse, urllib.request, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"cross_venue_diamond_replication_002_okx_source_validation_pilot"
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://www.okx.com/api/v5/public/market-data-history"
UA="CROSS-VENUE-DIAMOND-REPLICATION-002 source-validation-pilot/1.0"

EXPECTED={
"AVAX-USDT-SWAP-candlesticks-2025-01.zip":"3990132d74c9bfc34ab908974c934dd1ebe70e6fc51592d9c209c9aec4165803",
"AVAX-USDT-SWAP-candlesticks-2025-02.zip":"efb25ed5cb34a7059710fbd548af71524cde908dea04ffd295e417126a47a861",
"AVAX-USDT-SWAP-fundingrates-2025-01.zip":"35fc508327f5f3c7b9ea183818760ac88037dd51b1f13ced2ef1165c36b8b35a",
"AVAX-USDT-SWAP-fundingrates-2025-02.zip":"eeeae487ea582a7df2fa9a3b56af54a4e1112373dbde8d4312745b50659863cd",
}

def ms(x): return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)
def h(b): return hashlib.sha256(b).hexdigest()
def iso(t): return datetime.fromtimestamp(t/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")

def refs(module):
    params={"module":str(module),"instType":"SWAP","dateAggrType":"monthly",
      "begin":ms("2025-01-01T00:00:00Z"),"end":ms("2025-02-01T00:00:00Z"),"instFamilyList":"AVAX-USDT"}
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(params),headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as r: body=json.loads(r.read().decode())
    if body.get("code")!="0": raise RuntimeError("PROVIDER_ERROR")
    out=[]
    for d in body.get("data") or []:
      for detail in d.get("details") or []:
       for g in detail.get("groupDetails") or []:
        if g.get("url") and g.get("filename"): out.append((g["filename"],g["url"]))
    return out

def download(url):
    if urlparse(url).scheme!="https": raise RuntimeError("NON_HTTPS")
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=120) as r: return r.read()

def timestamp_index(header):
    candidates=[]
    for i,x in enumerate(header):
        q=x.strip().lower().replace("_","")
        if q in {"ts","timestamp","opentime","fundingtime","time"} or q.endswith("timestamp"):
            candidates.append(i)
    if len(candidates)!=1: raise RuntimeError(f"TIMESTAMP_COLUMN_AMBIGUOUS:{header}:{candidates}")
    return candidates[0]

def parse_ts(s):
    x=s.strip().strip('"')
    if x.isdigit():
        n=int(x)
        if n<10_000_000_000: n*=1000
        return n
    return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)

def inspect_zip(name,b,is_candle):
    digest=h(b)
    if EXPECTED.get(name)!=digest: raise RuntimeError(f"HASH_MISMATCH:{name}:{digest}")
    z=zipfile.ZipFile(io.BytesIO(b))
    bad=z.testzip()
    if bad: raise RuntimeError(f"ZIP_INTEGRITY_FAIL:{name}:{bad}")
    members=[x for x in z.namelist() if not x.endswith("/")]
    if not members: raise RuntimeError(f"EMPTY_ZIP:{name}")
    rows_total=0; all_ts=[]; schemas=[]
    for m in members:
        p=Path(m)
        if p.is_absolute() or ".." in p.parts: raise RuntimeError(f"UNSAFE_MEMBER:{m}")
        raw=z.read(m)
        txt=raw.decode("utf-8-sig","replace")
        sample=txt[:8192]
        try: dialect=csv.Sniffer().sniff(sample,delimiters=",;\t|")
        except Exception: dialect=csv.excel
        reader=csv.reader(io.StringIO(txt),dialect)
        try: header=next(reader)
        except StopIteration: raise RuntimeError(f"EMPTY_MEMBER:{m}")
        ti=timestamp_index(header)
        n=0; ts=[]
        for row in reader:
            if not row or len(row)<=ti: continue
            ts.append(parse_ts(row[ti])); n+=1
        rows_total+=n; all_ts.extend(ts)
        schemas.append({"member":m,"header":header,"timestamp_column":header[ti],"rows":n})
    st=sorted(all_ts)
    dup=len(st)-len(set(st))
    intervals=Counter((b-a)//1000 for a,b in zip(st,st[1:]) if b>=a)
    candle_non60=sum(v for k,v in intervals.items() if k!=60) if is_candle else None
    return {
      "filename":name,"sha256":digest,"members":schemas,"rows":rows_total,
      "unique_timestamps":len(set(st)),"duplicate_timestamps":dup,
      "min_ts_utc":iso(st[0]) if st else None,"max_ts_utc":iso(st[-1]) if st else None,
      "interval_seconds_top":intervals.most_common(10),
      "candle_non_60s_intervals":candle_non60,
      "no_2026":bool(st) and st[-1] < ms("2026-01-01T00:00:00Z"),
    }

def main():
    files=[]
    for module in (2,3):
      for name,url in refs(module):
        if name not in EXPECTED: continue
        files.append(inspect_zip(name,download(url),module==2))
    names={x["filename"] for x in files}
    ok=(names==set(EXPECTED) and all(x["duplicate_timestamps"]==0 and x["no_2026"] for x in files)
        and all(x["candle_non_60s_intervals"]==0 for x in files if "candlesticks" in x["filename"]))
    receipt={"lab_id":"CROSS-VENUE-DIAMOND-REPLICATION-002","stage":"OKX_SOURCE_VALIDATION_PILOT",
      "classification":"SOURCE_VALIDATION_PILOT_PASS" if ok else "SOURCE_VALIDATION_PILOT_FAIL",
      "files":files,"market_values_persisted":False,"signal_calculation_performed":False,
      "return_calculation_performed":False,"pnl_calculation_performed":False,"2026_plus_accessed":False}
    (OUT/"CROSS_VENUE_DIAMOND_REPLICATION_002_OKX_SOURCE_VALIDATION_PILOT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
