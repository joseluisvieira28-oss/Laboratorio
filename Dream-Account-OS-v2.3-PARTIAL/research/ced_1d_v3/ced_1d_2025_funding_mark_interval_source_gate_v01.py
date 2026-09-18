#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,urllib.request,zipfile
from pathlib import Path

MARK_BASE="https://data.binance.vision/data/futures/um/monthly/markPriceKlines"
FUND_BASE="https://data.binance.vision/data/futures/um/monthly/fundingRate"
UA="CED1D-2025-MARK-BINDING-GATE/0.1"
SYMBOLS=("AVAXUSDT","SOLUSDT")
HEADER_ALIASES={"open_time","opentime","timestamp","time","start_time"}

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def canonical(o): return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=90) as r:
        if r.status!=200: raise RuntimeError(f"HTTP_{r.status}:{url}")
        return r.read()
def norm_ms(v):
    n=int(v)
    while n>10**14: n//=1000
    return n
def norm_header(s): return re.sub(r"[^a-z0-9_]+","",s.strip().lower().replace(" ","_"))

def get_zip(url,expected_sha=None):
    raw=fetch(url); checksum=fetch(url+".CHECKSUM").decode("utf-8",errors="replace").strip().split()
    if not checksum: raise RuntimeError(f"EMPTY_CHECKSUM:{url}")
    published=checksum[0].lower(); actual=sha256_bytes(raw)
    if published!=actual: raise RuntimeError(f"PROVIDER_CHECKSUM_MISMATCH:{url}")
    if expected_sha is not None and actual!=expected_sha.lower(): raise RuntimeError(f"PINNED_SHA_MISMATCH:{url}:{actual}:{expected_sha}")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        bad=zf.testzip()
        if bad is not None: raise RuntimeError(f"ZIP_CRC_FAIL:{url}:{bad}")
        members=[n for n in zf.namelist() if not n.endswith("/")]
        if len(members)!=1: raise RuntimeError(f"ZIP_MEMBER_COUNT:{url}:{len(members)}")
        payload=zf.read(members[0])
    return raw,payload,members[0],actual

def parse_funding(payload,symbol):
    rows=list(csv.reader(io.StringIO(payload.decode("utf-8-sig"))))
    if not rows: raise RuntimeError("EMPTY_FUNDING_CSV")
    header=[x.strip() for x in rows[0]]
    if header[:3]!=["calc_time","funding_interval_hours","last_funding_rate"]:
        raise RuntimeError(f"FUNDING_SCHEMA:{symbol}:{header[:3]}")
    out=[]
    for row in rows[1:]:
        if not row or all(not str(x).strip() for x in row): continue
        if len(row)<3: raise RuntimeError(f"FUNDING_SHORT_ROW:{symbol}")
        ft=norm_ms(row[0]); interval=float(row[1]); rate=float(row[2])
        if not math.isfinite(interval) or interval<=0 or not math.isfinite(rate): raise RuntimeError(f"FUNDING_BAD_NUMERIC:{symbol}:{row[:3]}")
        out.append({"symbol":symbol,"fundingTime":ft,"fundingRate":str(row[2]),"fundingIntervalHours":interval})
    return out

def parse_mark(payload,symbol):
    rdr=csv.reader(io.StringIO(payload.decode("utf-8-sig")))
    out={}; first_nonempty=True; header_rows=0
    for row in rdr:
        if not row or all(not str(x).strip() for x in row): continue
        if first_nonempty:
            first_nonempty=False
            if len(row)>=5 and norm_header(row[0]) in HEADER_ALIASES:
                header_rows=1; continue
        if len(row)<5: raise RuntimeError(f"MARK_SHORT_ROW:{symbol}:{row}")
        try:
            t=norm_ms(row[0]); o,h,l,c=map(float,row[1:5])
        except Exception as e:
            raise RuntimeError(f"MARK_PARSE:{symbol}:{row[:5]}:{e}")
        if t in out: raise RuntimeError(f"MARK_DUPLICATE:{symbol}:{t}")
        if not all(math.isfinite(x) and x>0 for x in (o,h,l,c)) or l>min(o,c) or h<max(o,c) or l>h:
            raise RuntimeError(f"MARK_OHLC:{symbol}:{t}")
        out[t]={"open":o,"high":h,"low":l,"close":c}
    if not out: raise RuntimeError(f"MARK_EMPTY:{symbol}")
    return out,header_rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--funding-manifest",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args(); man=json.loads(Path(a.funding_manifest).read_text()); out=Path(a.output)
    if out.exists(): raise RuntimeError("OUTPUT_ALREADY_EXISTS")
    out.mkdir(parents=True)
    failures=[]; symbol_receipts={}; all_bindings={}
    for symbol in SYMBOLS:
        fund=[]; fund_arch=[]; mark_by_minute={}; mark_arch=[]
        pinned=man["archive_sha256"][symbol]
        if len(pinned)!=12: raise RuntimeError(f"PIN_COUNT:{symbol}")
        for month in range(1,13):
            ym=f"2025-{month:02d}"
            fname=f"{symbol}-fundingRate-{ym}.zip"; furl=f"{FUND_BASE}/{symbol}/{fname}"
            fraw,fpayload,fmember,fsha=get_zip(furl,pinned[month-1])
            (out/fname).write_bytes(fraw)
            records=parse_funding(fpayload,symbol); fund.extend(records)
            fund_arch.append({"month":ym,"file":fname,"sha256":fsha,"member":fmember,"records":len(records)})
            mname=f"{symbol}-1m-{ym}.zip"; murl=f"{MARK_BASE}/{symbol}/1m/{mname}"
            mraw,mpayload,mmember,msha=get_zip(murl)
            (out/mname).write_bytes(mraw)
            marks,header_rows=parse_mark(mpayload,symbol)
            overlap=set(mark_by_minute).intersection(marks)
            if overlap: raise RuntimeError(f"CROSS_MONTH_MARK_DUPLICATE:{symbol}:{min(overlap)}")
            mark_by_minute.update(marks)
            mark_arch.append({"month":ym,"file":mname,"sha256":msha,"member":mmember,"rows":len(marks),"header_rows":header_rows})
        fund.sort(key=lambda x:x["fundingTime"])
        if len(fund)!=1095: failures.append(f"{symbol}:FUNDING_COUNT:{len(fund)}")
        if len({x["fundingTime"] for x in fund})!=len(fund): failures.append(f"{symbol}:FUNDING_DUP")
        got_hash=sha256_bytes(canonical(fund))
        if got_hash!=man["canonical_records_sha256"][symbol]:
            failures.append(f"{symbol}:CANONICAL_FUNDING_HASH:{got_hash}")
        bindings=[]; missing=[]
        for r in fund:
            minute=(r["fundingTime"]//60000)*60000
            k=mark_by_minute.get(minute)
            if k is None:
                missing.append({"fundingTime":r["fundingTime"],"minute":minute}); continue
            bindings.append({**r,"markMinuteOpen":minute,"markLow":k["low"],"markHigh":k["high"]})
        if missing: failures.append(f"{symbol}:UNBOUND_SETTLEMENTS:{len(missing)}")
        all_bindings[symbol]=bindings
        symbol_receipts[symbol]={
            "funding_records":len(fund),"funding_canonical_sha256":got_hash,
            "funding_archives":fund_arch,"mark_archives":mark_arch,
            "mark_unique_minutes":len(mark_by_minute),"bound_settlements":len(bindings),
            "missing_settlements":missing,
            "binding_sha256":sha256_bytes(canonical(bindings))
        }
    receipt={"document_id":"CED_1D_2025_FUNDING_MARK_INTERVAL_SOURCE_GATE_RECEIPT_V0.1",
             "status":"FUNDING_MARK_INTERVAL_SOURCE_PASS" if not failures else "FUNDING_MARK_INTERVAL_SOURCE_FAIL",
             "funding_manifest_document_id":man["document_id"],"symbols":symbol_receipts,"failures":failures,
             "strategy_signals_computed":False,"strategy_returns_computed":False,"strategy_pnl_computed":False,
             "access_2026_plus":False,"live_trading":False}
    receipt["fingerprint"]=sha256_bytes(canonical(receipt))
    (out/"funding_mark_interval_bindings.json").write_text(json.dumps(all_bindings,indent=2,sort_keys=True)+"\n")
    (out/"FUNDING_MARK_INTERVAL_SOURCE_GATE_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":receipt["status"],"failures":failures,"fingerprint":receipt["fingerprint"],"symbols":{s:{"bound":v["bound_settlements"],"missing":len(v["missing_settlements"]),"mark_minutes":v["mark_unique_minutes"]} for s,v in symbol_receipts.items()}},indent=2))
    if failures: raise SystemExit("SOURCE_FAIL")
if __name__=="__main__": main()
