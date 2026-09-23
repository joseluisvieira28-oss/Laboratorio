#!/usr/bin/env python3
import hashlib, json, math, urllib.request, urllib.error
from pathlib import Path

URL="https://api.solend.fi/history-v2/liquidation-attempts?start=1721417452&end=1721433600"
START=1721417452
END=1721433600
KNOWN_SIG="WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L"
KNOWN_SLOT=278496102
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE11_OFFICIAL_API_LOCATOR_V0.1.json")
RECEIPT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE11_OFFICIAL_API_LOCATOR_RECEIPT_V0.1.json")

def fail(cls,reason,extra=None):
    r={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":cls,"reason":reason}
    if extra: r.update(extra)
    RECEIPT.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2,sort_keys=True))
    raise SystemExit(0)

def norm_ts(v):
    if isinstance(v,bool): raise ValueError("boolean_timestamp")
    if isinstance(v,(int,float)) and math.isfinite(float(v)):
        x=float(v)
        if abs(x-round(x))>1e-9: raise ValueError("non_integer_timestamp")
        x=int(round(x))
        if 1_000_000_000 <= x < 10_000_000_000:
            return x
        if 1_000_000_000_000 <= x < 10_000_000_000_000:
            if x % 1000 != 0: raise ValueError("millisecond_timestamp_not_exact_second")
            return x//1000
    raise ValueError("unsupported_timestamp")

records=[]
schema_errors=[]

def walk(v,path="$"):
    if isinstance(v,dict):
        required={"signature","slot","success","timestamp"}
        if required.issubset(v.keys()):
            try:
                sig=v["signature"]
                slot=v["slot"]
                success=v["success"]
                ts=norm_ts(v["timestamp"])
                if not isinstance(sig,str) or not sig:
                    raise ValueError("invalid_signature")
                if isinstance(slot,bool) or not isinstance(slot,(int,float)) or int(slot)!=slot:
                    raise ValueError("invalid_slot")
                if not isinstance(success,bool):
                    raise ValueError("invalid_success")
                if START <= ts < END:
                    records.append({"signature":sig,"slot":int(slot),"success":success,"timestamp":ts})
            except Exception as e:
                schema_errors.append({"path":path,"error":type(e).__name__+":"+str(e)})
        for k,x in v.items():
            walk(x,path+"/"+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v):
            walk(x,path+f"/{i}")

try:
    req=urllib.request.Request(URL,headers={"Accept":"application/json","User-Agent":"crypto-lab-dls-official-locator/0.1"})
    with urllib.request.urlopen(req,timeout=60) as resp:
        raw=resp.read()
        status=int(resp.status)
except Exception as e:
    fail("SAVE11_OFFICIAL_API_LOCATOR_TRANSPORT_BLOCKED",type(e).__name__,{"detail":str(e)[:300]})

if status < 200 or status >= 300:
    fail("SAVE11_OFFICIAL_API_LOCATOR_TRANSPORT_BLOCKED","non_2xx",{"http_status":status})

try:
    obj=json.loads(raw)
except Exception as e:
    fail("SAVE11_OFFICIAL_API_LOCATOR_SCHEMA_FAIL_CLOSED","json_parse_error",{"error":type(e).__name__})

walk(obj)
if schema_errors:
    fail("SAVE11_OFFICIAL_API_LOCATOR_SCHEMA_FAIL_CLOSED","candidate_record_schema_error",{"schema_error_count":len(schema_errors),"sample":schema_errors[:5]})

by_sig={}
for r in records:
    prev=by_sig.get(r["signature"])
    if prev is None:
        by_sig[r["signature"]]=r
    elif prev!=r:
        fail("SAVE11_OFFICIAL_API_LOCATOR_SCHEMA_FAIL_CLOSED","conflicting_duplicate_signature",{"signature":r["signature"]})

rows=sorted(by_sig.values(),key=lambda r:(r["timestamp"],r["slot"],r["signature"]))
locator={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "provider":"Save/Solend official API","route":"/history-v2/liquidation-attempts",
 "window":{"start":START,"end":END,"semantics":"half_open"},
 "rows":rows
}
blob=json.dumps(rows,separators=(",",":"),sort_keys=True).encode()
locator_sha=hashlib.sha256(blob).hexdigest()
OUT.write_text(json.dumps(locator,indent=2,sort_keys=True)+"\n",encoding="utf-8")

known=by_sig.get(KNOWN_SIG)
if known is None or known["slot"]!=KNOWN_SLOT or known["timestamp"]!=START:
    cls="SAVE11_OFFICIAL_API_LOCATOR_BOUNDARY_MISS"
else:
    cls="SAVE11_OFFICIAL_API_LOCATOR_CHUNK_PASS"

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":cls,
 "http_status":status,"response_bytes":len(raw),
 "locator_rows":len(rows),"locator_sha256":locator_sha,
 "known_boundary_present":known is not None,
 "known_boundary_exact_match":bool(known is not None and known["slot"]==KNOWN_SLOT and known["timestamp"]==START),
 "success_true_rows":sum(1 for r in rows if r["success"]),
 "success_false_rows":sum(1 for r in rows if not r["success"]),
 "economic_values_persisted":False,
 "authority":"SECONDARY_LOCATOR_ONLY",
 "firewalls":{"prices":False,"amounts":False,"balances":False,"usd_values":False,"returns":False,"pnl":False,"direction":False,
              "market_outcomes":False,"live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
              "paid_source":False,"account_creation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
