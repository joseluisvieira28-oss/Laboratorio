#!/usr/bin/env python3
import hashlib, json, os, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)
BASE="https://data.binance.vision/data/spot/monthly/klines"
SYMBOLS=["BTCUSDT","ETHUSDT","LINKUSDT","UNIUSDT","COMPUSDT"]
MONTHS=[f"{y}-{m:02d}" for y in (2023,2024) for m in range(1,13)]

rows=[]
for sym in SYMBOLS:
    for ym in MONTHS:
        url=f"{BASE}/{sym}/1m/{sym}-1m-{ym}.zip"
        rec={"symbol":sym,"month":ym,"url":url}
        try:
            req=Request(url,method="HEAD",headers={"User-Agent":"CryptoLab-CompoundPersistence-SourceGate-V0.1"})
            with urlopen(req,timeout=45) as r:
                rec["http_status"]=r.status
                rec["content_length"]=int(r.headers.get("Content-Length") or 0)
                rec["etag"]=r.headers.get("ETag")
                rec["available"]=r.status==200 and rec["content_length"]>0
        except HTTPError as e:
            rec["http_status"]=e.code; rec["available"]=False; rec["error"]=repr(e)
        except Exception as e:
            rec["available"]=False; rec["error"]=repr(e)
        rows.append(rec)

available=sum(1 for x in rows if x.get("available"))
status="SOURCE_COVERAGE_PASS" if available==len(rows) else "SOURCE_COVERAGE_PARTIAL"
receipt={
 "lab_id":"COMPOUND-INVENTORY-PERSISTENCE-001",
 "protocol":"COMPOUND_INVENTORY_PERSISTENCE_001_SOURCE_MECHANISM_FREEZE_V0.1",
 "status":status,
 "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "required_objects":len(rows),
 "available_objects":available,
 "symbols":SYMBOLS,
 "months":MONTHS,
 "objects":rows,
 "firewall":{
   "source_only":True,"price_rows_emitted":False,"returns_computed":False,
   "pnl_computed":False,"protected_2025_opened":False,"live_trading":False,
   "orders":False,"exchange_mutation":False,"capital":False,"paid_data":False
 }
}
pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
receipt["receipt_sha256_pre_self_field"]=hashlib.sha256(pre).hexdigest()
out=os.path.join(OUTDIR,"COMPOUND_INVENTORY_PERSISTENCE_SOURCE_COVERAGE_V0.1.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps({"status":status,"available":available,"required":len(rows),"receipt_sha256_pre_self_field":receipt["receipt_sha256_pre_self_field"]},indent=2,sort_keys=True))
print(f"receipt={out}")
