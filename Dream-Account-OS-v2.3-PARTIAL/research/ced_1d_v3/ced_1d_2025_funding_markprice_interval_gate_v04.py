#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,urllib.request,zipfile
from pathlib import Path

SYMBOLS=("AVAXUSDT","SOLUSDT"); YEAR=2025
START_MS=1735689600000; END_MS=1767225599999; EXPECTED=1095
FUNDING_BASE="https://data.binance.vision/data/futures/um/monthly/fundingRate"
MARK_BASE="https://data.binance.vision/data/futures/um/monthly/markPriceKlines"
UA="CED1D-MARKPRICE-INTERVAL-SOURCE/0.4"

class E(RuntimeError): pass
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def h(b): return hashlib.sha256(b).hexdigest()
def fetch(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=120) as r:
            if r.status!=200: raise E(f"HTTP_{r.status}:{u}")
            return r.read()
    except Exception as e:
        if isinstance(e,E): raise
        raise E(f"FETCH:{type(e).__name__}:{e}:{u}") from e
def vz(u,out):
    b=fetch(u); c=fetch(u+".CHECKSUM").decode(errors="replace").strip().split()
    if not c: raise E(f"CHECKSUM_EMPTY:{u}")
    if h(b)!=c[0].lower(): raise E(f"CHECKSUM_MISMATCH:{u}")
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        if z.testzip() is not None: raise E(f"CRC:{u}")
        members=[x for x in z.namelist() if not x.endswith("/")]
        if len(members)!=1: raise E(f"MEMBERS:{u}:{len(members)}")
    name=u.rsplit("/",1)[-1]; (out/name).write_bytes(b); (out/(name+".CHECKSUM")).write_text(c[0].lower()+"  "+name+"\n")
    return b,h(b)
def rows(b):
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        m=[x for x in z.namelist() if not x.endswith("/")][0]
        return list(csv.reader(io.TextIOWrapper(z.open(m),encoding="utf-8")))
def nms(x):
    n=int(x)
    while n>10**14:n//=1000
    return n

def funding(symbol,out):
    rr=[]; files=[]
    for m in range(1,13):
        name=f"{symbol}-fundingRate-2025-{m:02d}.zip"; u=f"{FUNDING_BASE}/{symbol}/{name}"
        b,s=vz(u,out); a=rows(b)
        if [x.strip() for x in a[0]][:3]!=["calc_time","funding_interval_hours","last_funding_rate"]: raise E(f"FUNDING_SCHEMA:{name}")
        n=0
        for r in a[1:]:
            if not r or all(not str(x).strip() for x in r): continue
            ft=nms(r[0]); interval=float(r[1]); rate=float(r[2])
            if not START_MS<=ft<=END_MS or not math.isfinite(interval) or interval<=0 or not math.isfinite(rate): raise E(f"FUNDING_ROW:{name}:{r}")
            rr.append({"symbol":symbol,"fundingTime":ft,"fundingRate":str(r[2]),"fundingIntervalHours":interval,"providerCalcTimeRaw":str(r[0])}); n+=1
        files.append({"file":name,"sha256":s,"records":n})
    rr.sort(key=lambda x:x["fundingTime"])
    if len(rr)!=EXPECTED or len(rr)!=len({x["fundingTime"] for x in rr}): raise E(f"FUNDING_COUNT_OR_DUP:{symbol}:{len(rr)}")
    return rr,files

def mark(symbol,month,needed,out):
    name=f"{symbol}-1m-2025-{month:02d}.zip"; u=f"{MARK_BASE}/{symbol}/1m/{name}"
    b,s=vz(u,out); a=rows(b); start=1 if a and a[0] and str(a[0][0]).strip().lower() in {"open_time","open time"} else 0
    found={}; dup=set(); parsed=0
    for r in a[start:]:
        if not r or all(not str(x).strip() for x in r):continue
        if len(r)<5: raise E(f"MARK_SHORT:{name}")
        ot=nms(r[0]); op,hi,lo,cl=map(float,r[1:5])
        if any(not math.isfinite(x) or x<=0 for x in (op,hi,lo,cl)) or lo>op or lo>cl or hi<op or hi<cl or hi<lo: raise E(f"MARK_OHLC:{name}:{r[:5]}")
        parsed+=1
        if ot in needed:
            if ot in found: dup.add(ot)
            found[ot]={"open":str(r[1]),"high":str(r[2]),"low":str(r[3]),"close":str(r[4])}
    if dup: raise E(f"MARK_DUP:{symbol}:{month}:{sorted(dup)[:5]}")
    return found,{"file":name,"sha256":s,"rows_parsed":parsed,"matches":len(found)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--amendment",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args(); am=json.loads(Path(a.amendment).read_text()); out=Path(a.output)
    if out.exists(): raise SystemExit("OUTPUT_EXISTS")
    out.mkdir(parents=True)
    failures=[]; final={}; summaries={}
    for sym in SYMBOLS:
        try:
            fr,ff=funding(sym,out); got=h(canon(fr)); exp=am["funding_identity"]["canonical_records_sha256"][sym]
            if got!=exp: raise E(f"FUNDING_CANONICAL_HASH:{sym}:{got}:{exp}")
            bym={}
            for x in fr:
                import datetime
                mo=datetime.datetime.fromtimestamp(x["fundingTime"]/1000,datetime.timezone.utc).month
                bym.setdefault(mo,set()).add((x["fundingTime"]//60000)*60000)
            marks={}; mf=[]
            for mo in range(1,13):
                f,meta=mark(sym,mo,bym.get(mo,set()),out); overlap=set(marks)&set(f)
                if overlap: raise E(f"MARK_CROSS_MONTH_DUP:{sym}:{sorted(overlap)[:3]}")
                marks.update(f); mf.append(meta)
            paired=[]; missing=[]
            for x in fr:
                minute=(x["fundingTime"]//60000)*60000; candle=marks.get(minute)
                if candle is None: missing.append((x["fundingTime"],minute)); continue
                paired.append({**x,"settlementMinuteOpen":minute,"markOpen":candle["open"],"markHigh":candle["high"],"markLow":candle["low"],"markClose":candle["close"]})
            if missing: raise E(f"MARK_MINUTE_MISSING:{sym}:{len(missing)}:{missing[:5]}")
            if len(paired)!=EXPECTED: raise E(f"PAIR_COUNT:{sym}:{len(paired)}")
            final[sym]=paired; summaries[sym]={"funding_records":len(fr),"paired_records":len(paired),"funding_canonical_sha256":got,"paired_interval_sha256":h(canon(paired)),"funding_files":ff,"markprice_files":mf}
        except Exception as e:
            failures.append(f"{sym}:{type(e).__name__}:{e}")
    receipt={"document_id":"CED_1D_2025_FUNDING_MARKPRICE_INTERVAL_SOURCE_GATE_RECEIPT_V0.4","status":"FUNDING_MARKPRICE_INTERVAL_SOURCE_PASS" if not failures else "FUNDING_MARKPRICE_INTERVAL_SOURCE_FAIL","amendment":am["document_id"],"symbols":summaries,"failures":failures,"signals_computed":False,"returns_computed":False,"pnl_computed":False,"promotion_computed":False,"year_2026_accessed":False}
    receipt["fingerprint"]=h(canon(receipt))
    (out/"funding_markprice_interval_2025.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")
    (out/"CED_1D_2025_FUNDING_MARKPRICE_INTERVAL_SOURCE_GATE_RECEIPT_V0.4.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    if failures: raise SystemExit("FUNDING_MARKPRICE_INTERVAL_SOURCE_FAIL")
    print("FUNDING_MARKPRICE_INTERVAL_SOURCE_PASS")
if __name__=="__main__":main()
