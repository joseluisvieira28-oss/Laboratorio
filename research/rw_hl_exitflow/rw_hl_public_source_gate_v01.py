"""Source-only read probe for Hyperliquid public market info. No outcome testing."""
import json,hashlib,time,math
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"source_receipts"
API="https://api.hyperliquid.xyz/info"
class Blocked(Exception):pass

def canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()

def public_info(body):
    if body not in (
      {"type":"metaAndAssetCtxs"},
      {"type":"fundingHistory","coin":"BTC","startTime":1704067200000,"endTime":1704153600000}):
        raise Blocked("UNAUTHORIZED_PUBLIC_QUERY")
    req=Request(API,data=canon(body),headers={"Content-Type":"application/json",
        "User-Agent":"CryptoLab-RW-HL-SourceOnly/0.1"},method="POST")
    try:
        with urlopen(req,timeout=45) as r:
            if r.status!=200:raise Blocked("BAD_SOURCE_HTTP")
            data=r.read(3_000_001)
    except HTTPError as e:
        raise Blocked("SOURCE_HTTP_"+str(e.code)) from None
    except (URLError,TimeoutError):
        raise Blocked("SOURCE_TRANSPORT") from None
    if len(data)>3_000_000:raise Blocked("SOURCE_OVERSIZE")
    try:return json.loads(data)
    except ValueError:raise Blocked("SOURCE_JSON") from None

def numeric(value,key,strict=False):
    if value is None or isinstance(value,bool):raise Blocked(key+"_MISSING")
    try:v=float(value)
    except (ValueError,TypeError):raise Blocked(key+"_NON_NUMERIC") from None
    if not math.isfinite(v) or (v<=0 if strict else v<0):raise Blocked(key+"_INVALID")
    return v

def parse_public_market(data):
    if not isinstance(data,list) or len(data)!=2:raise Blocked("JOIN_SCHEMA")
    meta,contexts=data
    if not isinstance(meta,dict) or not isinstance(meta.get("universe"),list) or not isinstance(contexts,list):
        raise Blocked("UNIVERSE_SCHEMA")
    rows=meta["universe"]
    if len(rows)!=len(contexts) or len(rows)<5:raise Blocked("JOIN_LENGTH")
    used=set();active=[];skipped=0
    for m,c in zip(rows,contexts):
        if not isinstance(m,dict) or not isinstance(m.get("name"),str):raise Blocked("BAD_META")
        name=m["name"]
        if not name or name in used:raise Blocked("DUPLICATE_MARKET_ID")
        used.add(name)
        if m.get("isDelisted") is True or c is None:
            skipped+=1;continue
        if not isinstance(c,dict):raise Blocked("BAD_CONTEXT")
        if any(k not in c for k in ("openInterest","markPx","funding")):
            skipped+=1;continue
        numeric(c["openInterest"],"OI");numeric(c["markPx"],"MARK",True)
        try: funding=float(c["funding"])
        except (ValueError,TypeError):raise Blocked("BAD_FUNDING") from None
        if not math.isfinite(funding):raise Blocked("BAD_FUNDING")
        active.append({"coin":name,"openInterest":c["openInterest"],"markPx":c["markPx"],
            "funding":c["funding"],"dayNtlVlm":c.get("dayNtlVlm")})
    if len(active)<5:raise Blocked("TOO_FEW_VALID_MARKETS")
    return {"total_listed":len(rows),"valid_public_markets":len(active),
            "missing_or_delisted":skipped,"market_context":active}

def probe():
    freeze=(ROOT/"RW_HL_EXITFLOW_001_PREOBS_SOURCE_AUTHORITY_2026-10-09.md").read_text()
    if "NO ECONOMIC HYPOTHESIS AUTHORIZED FOR RETURNS" not in freeze:raise Blocked("FREEZE_MISSING")
    OUT.mkdir(parents=True,exist_ok=True);summary=[]
    for i in range(2):
        if i:time.sleep(75)
        observed=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
        values=parse_public_market(public_info({"type":"metaAndAssetCtxs"}))
        obj={"lab_id":"RW-HL-EXITFLOW-001","received_utc":observed,
             "source_only":True,"trading_authority":"NONE","values":values}
        path=OUT/f"live_public_{i+1}.json"
        path.write_bytes(canon(obj)+b"\n")
        summary.append({"received_utc":observed,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "valid_markets":values["valid_public_markets"]})
        print("SOURCE_SNAPSHOT_PASS",i+1,values["valid_public_markets"],flush=True)
    old=public_info({"type":"fundingHistory","coin":"BTC",
        "startTime":1704067200000,"endTime":1704153600000})
    if not isinstance(old,list):raise Blocked("FUNDING_HISTORY_SCHEMA")
    times=[]
    for row in old:
        if not isinstance(row,dict) or not {"time","coin","fundingRate"}<=set(row):
            raise Blocked("FUNDING_ROW_SCHEMA")
        if row["coin"]!="BTC" or not 1704067200000<=row["time"]<=1704153600000:
            raise Blocked("FUNDING_ROW_BOUNDARY")
        times.append(row["time"])
    if times!=sorted(set(times)):raise Blocked("FUNDING_ORDER")
    rec={"lab_id":"RW-HL-EXITFLOW-001","state":"LIVE_PUBLIC_SOURCE_FEASIBLE",
        "two_snapshots":summary,"historical_2024_BTC_funding_rows":len(times),
        "market_reads":3,"historical_OI_available_by_same_API":False,
        "historical_HL_OI_archive_requires_requester_payment":True,
        "historical_OI_archive_accessed":False,
        "price_returns_computed":False,"live_trading_authority":"NONE"}
    (OUT/"SOURCE_GATE.json").write_bytes(canon(rec)+b"\n")
    print(json.dumps(rec),flush=True)

if __name__=="__main__":
    try:probe()
    except (Blocked,OSError,ValueError) as e:
        OUT.mkdir(parents=True,exist_ok=True)
        r={"state":"SOURCE_BLOCKED","reason":str(e),"live_trading_authority":"NONE"}
        (OUT/"SOURCE_GATE.json").write_bytes(canon(r)+b"\n")
        print(json.dumps(r),flush=True)
        raise SystemExit(2)
