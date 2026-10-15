from __future__ import annotations
import hashlib, json, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"cross_venue_diamond_replication_002_okx_raw_pilot"
RAW=OUT/"raw"
RAW.mkdir(parents=True,exist_ok=True)
BASE="https://www.okx.com/api/v5/public/market-data-history"
UA="CROSS-VENUE-DIAMOND-REPLICATION-002 raw-pilot/1.0"

def ms(x): return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)
def sha256(b): return hashlib.sha256(b).hexdigest()

def request_module(module):
    params={
      "module":str(module),"instType":"SWAP","dateAggrType":"monthly",
      "begin":ms("2025-01-01T00:00:00Z"),"end":ms("2025-02-01T00:00:00Z"),
      "instFamilyList":"AVAX-USDT",
    }
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(params),headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as r:
        body=json.loads(r.read().decode("utf-8","replace"))
    if body.get("code")!="0": raise RuntimeError(f"PROVIDER_CODE:{body.get('code')}:{body.get('msg')}")
    refs=[]
    for d in body.get("data") or []:
        for detail in d.get("details") or []:
            for g in detail.get("groupDetails") or []:
                url=g.get("url"); filename=g.get("filename")
                if not url or not filename: continue
                refs.append({
                  "url":url,"filename":filename,
                  "sizeMB":g.get("sizeMB"),"dateTs":g.get("dateTs"),
                  "instId":detail.get("instId"),"instFamily":detail.get("instFamily"),
                  "instType":detail.get("instType"),"ccy":detail.get("ccy"),
                })
    return refs

def magic_type(b,name):
    if b[:4]==b"PK\x03\x04": return "zip"
    if b[:2]==b"\x1f\x8b": return "gzip"
    if b[:6] in (b"7z\xbc\xaf\x27\x1c",): return "7z"
    ext=Path(name).suffix.lower().lstrip(".")
    return ext or "unknown"

def download(ref,module):
    u=urlparse(ref["url"])
    if u.scheme.lower()!="https": raise RuntimeError("NON_HTTPS_PROVIDER_URL")
    req=urllib.request.Request(ref["url"],headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=120) as r:
        b=r.read()
        final_url=r.geturl()
        status=r.status
    if not b: raise RuntimeError("ZERO_BYTE_PAYLOAD")
    safe=Path(ref["filename"]).name
    p=RAW/f"m{module}__{safe}"
    p.write_bytes(b)
    return {
      "module":module,"filename":safe,"provider_host":u.netloc,
      "final_host":urlparse(final_url).netloc,"http_status":status,
      "bytes":len(b),"sha256":sha256(b),"container_type":magic_type(b,safe),
      "provider_sizeMB":ref.get("sizeMB"),"dateTs":ref.get("dateTs"),
      "instId":ref.get("instId"),"instFamily":ref.get("instFamily"),"instType":ref.get("instType"),
    }

def main():
    receipt={
      "lab_id":"CROSS-VENUE-DIAMOND-REPLICATION-002",
      "stage":"OKX_JAN2025_RAW_PAYLOAD_ACQUISITION",
      "candidate":"CED1D-0031-AVAX20-CONTINUATION-H1",
      "window":["2025-01-01T00:00:00Z","2025-02-01T00:00:00Z"],
      "decompressed_or_market_rows_parsed":False,
      "signal_calculation_performed":False,"return_calculation_performed":False,"pnl_calculation_performed":False,
      "2026_plus_accessed":False,"modules":{}
    }
    ok=True
    seen={}
    for module in (2,3):
        refs=request_module(module)
        rows=[]
        for ref in refs:
            rec=download(ref,module)
            prior=seen.get(rec["filename"])
            if prior and prior!=rec["sha256"]: raise RuntimeError("CONFLICTING_DUPLICATE_FILENAME")
            seen[rec["filename"]]=rec["sha256"]
            rows.append(rec)
        receipt["modules"][str(module)]={"reference_count":len(refs),"payloads":rows,"pass":bool(rows)}
        ok=ok and bool(rows)
    receipt["classification"]="RAW_PAYLOAD_ACQUISITION_PASS" if ok else "RAW_PAYLOAD_ACQUISITION_BLOCKED"
    (OUT/"CROSS_VENUE_DIAMOND_REPLICATION_002_OKX_JAN2025_RAW_ACQUISITION_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"module_counts":{k:v["reference_count"] for k,v in receipt["modules"].items()},"payloads":[{"module":x["module"],"filename":x["filename"],"bytes":x["bytes"],"sha256":x["sha256"],"container_type":x["container_type"]} for v in receipt["modules"].values() for x in v["payloads"]]},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
