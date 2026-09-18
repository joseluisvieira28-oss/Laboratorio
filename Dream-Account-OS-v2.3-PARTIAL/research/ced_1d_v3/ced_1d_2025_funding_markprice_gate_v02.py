#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,tempfile,urllib.parse,urllib.request,zipfile
from decimal import Decimal,InvalidOperation
from pathlib import Path

ARCHIVE_BASE="https://data.binance.vision/data/futures/um/monthly/fundingRate"
UA="CED1D-2025-FUNDING-MARKPRICE-GATE/0.2"

class GateError(RuntimeError): pass

def canonical(o):
    return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()

def sha(b): return hashlib.sha256(b).hexdigest()

def fetch(url,timeout=90):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            if r.status!=200: raise GateError(f"HTTP_{r.status}:{url}")
            return r.read()
    except Exception as exc:
        if isinstance(exc,GateError): raise
        raise GateError(f"FETCH_FAIL:{type(exc).__name__}:{exc}:{url}") from exc

def norm_ms(v):
    n=int(v)
    while n>10**14: n//=1000
    return n

def archive_records(symbol,out):
    rows=[]; archives=[]
    for month in range(1,13):
        name=f"{symbol}-fundingRate-2025-{month:02d}.zip"
        url=f"{ARCHIVE_BASE}/{symbol}/{name}"
        raw=fetch(url); check=fetch(url+".CHECKSUM").decode("utf-8").strip().split()
        if not check: raise GateError(f"EMPTY_CHECKSUM:{name}")
        expected=check[0].lower(); actual=sha(raw)
        if actual!=expected: raise GateError(f"ARCHIVE_CHECKSUM_MISMATCH:{name}")
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            if zf.testzip() is not None: raise GateError(f"ARCHIVE_CRC_FAIL:{name}")
            members=[n for n in zf.namelist() if not n.endswith("/")]
            if len(members)!=1: raise GateError(f"ARCHIVE_MEMBER_COUNT:{name}:{len(members)}")
            cr=list(csv.reader(io.TextIOWrapper(zf.open(members[0]),encoding="utf-8")))
        if not cr or [x.strip() for x in cr[0]][:3]!=["calc_time","funding_interval_hours","last_funding_rate"]:
            raise GateError(f"ARCHIVE_SCHEMA_FAIL:{name}")
        n=0
        for row in cr[1:]:
            if not row or all(not str(x).strip() for x in row): continue
            ft=norm_ms(row[0]); interval=float(row[1])
            try: Decimal(str(row[2]))
            except InvalidOperation: raise GateError(f"ARCHIVE_RATE_PARSE_FAIL:{name}")
            rows.append({
                "symbol":symbol,
                "fundingTime":ft,
                "fundingRate":str(row[2]),
                "fundingIntervalHours":interval,
                "providerCalcTimeRaw":str(row[0])
            }); n+=1
        archives.append({"file":name,"sha256":actual,"records":n})
    rows.sort(key=lambda x:x["fundingTime"])
    if len(rows)!=len({x["fundingTime"] for x in rows}): raise GateError(f"ARCHIVE_DUPLICATE_TIME:{symbol}")
    return rows,archives

def rest_page(base,symbol,start,end,limit):
    q=urllib.parse.urlencode({"symbol":symbol,"startTime":start,"endTime":end,"limit":limit})
    url=base+"/fapi/v1/fundingRate?"+q
    raw=fetch(url)
    try: data=json.loads(raw)
    except Exception as exc: raise GateError(f"REST_JSON_FAIL:{base}:{exc}")
    if not isinstance(data,list): raise GateError(f"REST_NOT_LIST:{base}:{data}")
    return url,raw,data

def choose_mirror(man):
    errors=[]
    symbol=man["mark_price_recovery"]["symbols"][0]
    start=man["mark_price_recovery"]["start_time_ms"]
    end=man["mark_price_recovery"]["end_time_ms"]
    limit=man["mark_price_recovery"]["limit"]
    for base in man["mark_price_recovery"]["fixed_mirror_order"]:
        try:
            url,raw,data=rest_page(base,symbol,start,end,limit)
            if not data: raise GateError("EMPTY_PROBE")
            need={"symbol","fundingTime","fundingRate","markPrice"}
            if not need.issubset(data[0]): raise GateError(f"MISSING_FIELDS:{sorted(need-set(data[0]))}")
            return base,{"probe_url":url,"probe_raw_sha256":sha(raw),"probe_rows":len(data)}
        except Exception as exc:
            errors.append({"base":base,"error":f"{type(exc).__name__}:{exc}"})
    raise GateError("NO_MARKPRICE_MIRROR_AVAILABLE:"+json.dumps(errors,separators=(",",":")))

def rest_all(base,symbol,start,end,limit,out):
    records=[]; pages=[]; cur=start; page=0
    while cur<=end:
        url,raw,data=rest_page(base,symbol,cur,end,limit)
        page+=1
        (out/f"{symbol}_rest_page_{page:03d}.json").write_bytes(raw)
        pages.append({"page":page,"url":url,"sha256":sha(raw),"records":len(data)})
        if not data: break
        last=None
        for row in data:
            need={"symbol","fundingTime","fundingRate","markPrice"}
            if not need.issubset(row): raise GateError(f"REST_REQUIRED_FIELD_MISSING:{symbol}:{row}")
            if str(row["symbol"])!=symbol: raise GateError(f"REST_SYMBOL_DRIFT:{symbol}:{row}")
            ft=int(row["fundingTime"])
            if not(start<=ft<=end): raise GateError(f"REST_TIME_OUTSIDE_2025:{symbol}:{ft}")
            try:
                rate=Decimal(str(row["fundingRate"])); mark=float(row["markPrice"])
            except Exception: raise GateError(f"REST_NUMERIC_PARSE_FAIL:{symbol}:{row}")
            if not math.isfinite(mark) or mark<=0: raise GateError(f"REST_MARK_INVALID:{symbol}:{row}")
            records.append({"symbol":symbol,"fundingTime":ft,"fundingRate":str(row["fundingRate"]),"markPrice":str(row["markPrice"])})
            last=ft
        if len(data)<limit: break
        if last is None or last<cur: raise GateError(f"REST_PAGINATION_STALL:{symbol}:{cur}:{last}")
        cur=last+1
    records.sort(key=lambda x:x["fundingTime"])
    if len(records)!=len({x["fundingTime"] for x in records}): raise GateError(f"REST_DUPLICATE_TIME:{symbol}")
    return records,pages

def crosscheck(symbol,arc,rest,tol_ms):
    if len(arc)!=len(rest): raise GateError(f"RECORD_COUNT_MISMATCH:{symbol}:{len(arc)}:{len(rest)}")
    enriched=[]
    max_dt=0
    for i,(a,r) in enumerate(zip(arc,rest)):
        dt=abs(int(a["fundingTime"])-int(r["fundingTime"])); max_dt=max(max_dt,dt)
        if dt>tol_ms: raise GateError(f"SETTLEMENT_TIME_MISMATCH:{symbol}:{i}:{a['fundingTime']}:{r['fundingTime']}:{dt}")
        if Decimal(a["fundingRate"])!=Decimal(r["fundingRate"]):
            raise GateError(f"FUNDING_RATE_MISMATCH:{symbol}:{i}:{a['fundingRate']}:{r['fundingRate']}")
        enriched.append({
            "symbol":symbol,
            "fundingTime":int(r["fundingTime"]),
            "fundingRate":str(r["fundingRate"]),
            "markPrice":str(r["markPrice"]),
            "fundingIntervalHours":a["fundingIntervalHours"],
            "archiveCalcTime":int(a["fundingTime"]),
            "archiveProviderCalcTimeRaw":a["providerCalcTimeRaw"]
        })
    return enriched,max_dt

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--amendment",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args(); man=json.loads(Path(a.amendment).read_text())
    if man["status"]!="FROZEN_BEFORE_2025_ECONOMIC_OUTCOMES" or man["governance"]["access_2026_plus"]:
        raise SystemExit("AMENDMENT_FIREWALL_FAIL")
    out=Path(a.output)
    if out.exists(): raise SystemExit("OUTPUT_ALREADY_EXISTS")
    out.mkdir(parents=True)
    arcmap={}; archives={}
    for symbol in man["mark_price_recovery"]["symbols"]:
        rows,ar=archive_records(symbol,out); arcmap[symbol]=rows; archives[symbol]=ar
        got=sha(canonical(rows)); exp=man["archive_identity"][symbol]["canonical_records_sha256"]
        if got!=exp: raise SystemExit(f"ARCHIVE_CANONICAL_HASH_MISMATCH:{symbol}:{got}:{exp}")
        if len(rows)!=man["archive_identity"][symbol]["records"]: raise SystemExit(f"ARCHIVE_COUNT_DRIFT:{symbol}")
    base,probe=choose_mirror(man)
    enriched={}; summaries={}
    tol=int(man["mark_price_recovery"]["crosscheck_rule"].get("timestamp_tolerance_ms",1000))
    for symbol in man["mark_price_recovery"]["symbols"]:
        rest,pages=rest_all(base,symbol,man["mark_price_recovery"]["start_time_ms"],man["mark_price_recovery"]["end_time_ms"],man["mark_price_recovery"]["limit"],out)
        rows,max_dt=crosscheck(symbol,arcmap[symbol],rest,tol)
        enriched[symbol]=rows
        summaries[symbol]={
            "records":len(rows),"max_archive_vs_rest_time_delta_ms":max_dt,
            "enriched_sha256":sha(canonical(rows)),"pages":pages
        }
    (out/"funding_records_with_markprice_canonical.json").write_text(json.dumps(enriched,indent=2,sort_keys=True)+"\n")
    receipt={
        "document_id":"CED_1D_2025_FUNDING_MARKPRICE_SOURCE_GATE_RECEIPT_V0.2",
        "status":"FUNDING_MARKPRICE_SOURCE_PASS",
        "amendment_document_id":man["document_id"],
        "selected_mirror":base,
        "probe":probe,
        "symbols":summaries,
        "signals_computed":False,"returns_computed":False,"pnl_computed":False,"promotion_computed":False,
        "access_2026_plus":False,"live_trading":False,"exchange_mutation":False
    }
    receipt["fingerprint"]=sha(canonical(receipt))
    (out/"CED_1D_2025_FUNDING_MARKPRICE_SOURCE_GATE_RECEIPT_V0.2.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    print("FUNDING_MARKPRICE_SOURCE_PASS")

if __name__=="__main__": main()
