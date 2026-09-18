#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,math,re,urllib.request,zipfile
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um/monthly/klines"
UA="CED1D-2025-SOURCE-GATE/0.2"

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def fetch(url,dst):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=90) as r, open(dst,"wb") as f:
        while True:
            b=r.read(1<<20)
            if not b: break
            f.write(b)

def norm_ms(v):
    n=int(v)
    while n>10**14: n//=1000
    return n

def month_bounds(m):
    y,mo=map(int,m.split("-"))
    start=dt.datetime(y,mo,1,tzinfo=dt.timezone.utc)
    end=dt.datetime(y+1,1,1,tzinfo=dt.timezone.utc) if mo==12 else dt.datetime(y,mo+1,1,tzinfo=dt.timezone.utc)
    return int(start.timestamp()*1000),int(end.timestamp()*1000)

def audit_csv(zf,member,e):
    start,end=month_bounds(e["month"])
    rows=0; seen=set(); prev=None
    violations={k:0 for k in ["column_count","parse","timestamp_outside_month","non_ascending","duplicate_open_time","ohlc","negative_volume","negative_quote_volume","negative_trades","negative_taker_buy_base","negative_taker_buy_quote"]}
    first=last=None
    with zf.open(member) as raw:
        for bline in raw:
            line=bline.decode("utf-8").strip()
            if not line: continue
            parts=next(csv.reader([line]))
            if len(parts)!=12:
                violations["column_count"]+=1; continue
            try:
                ot=norm_ms(parts[0]); o,h,l,c=map(float,parts[1:5]); vol=float(parts[5]); qv=float(parts[7]); trades=int(float(parts[8])); tb=float(parts[9]); tq=float(parts[10])
            except Exception:
                violations["parse"]+=1; continue
            rows+=1; first=ot if first is None else first; last=ot
            if not(start<=ot<end): violations["timestamp_outside_month"]+=1
            if prev is not None and ot<=prev: violations["non_ascending"]+=1
            if ot in seen: violations["duplicate_open_time"]+=1
            seen.add(ot); prev=ot
            if not all(math.isfinite(x) and x>0 for x in [o,h,l,c]) or l>min(o,c) or h<max(o,c) or l>h: violations["ohlc"]+=1
            if vol<0: violations["negative_volume"]+=1
            if qv<0: violations["negative_quote_volume"]+=1
            if trades<0: violations["negative_trades"]+=1
            if tb<0: violations["negative_taker_buy_base"]+=1
            if tq<0: violations["negative_taker_buy_quote"]+=1
    expected=int(e["expected_rows"])
    return {"rows":rows,"unique_open_times":len(seen),"first_open_time":first,"last_open_time":last,"violations":violations,"row_count_pass":rows==expected and len(seen)==expected}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",required=True); ap.add_argument("--output",required=True); ap.add_argument("--cache",required=True)
    a=ap.parse_args(); man=json.loads(Path(a.manifest).read_text()); out=Path(a.output); cache=Path(a.cache)
    out.mkdir(parents=True,exist_ok=True); cache.mkdir(parents=True,exist_ok=True)
    expected_count=int(man["expected_file_count"])
    if expected_count<=0 or len(man["entries"])!=expected_count or man["access_2026_plus"] or man["outcomes_authorized"]:
        raise SystemExit("MANIFEST_FIREWALL_FAIL")
    receipts=[]; failures=[]
    for i,e in enumerate(man["entries"],1):
        fn=e["filename"]; symbol=e["symbol"]; url=f"{BASE}/{symbol}/1m/{fn}"
        zpath=cache/fn; cpath=cache/(fn+".CHECKSUM")
        fetch(url,zpath); fetch(url+".CHECKSUM",cpath)
        actual=sha256_file(zpath); checktext=cpath.read_text(errors="replace")
        mm=re.search(r"([0-9a-fA-F]{64})",checktext); checksum_hash=mm.group(1) if mm else None
        rec={"symbol":symbol,"month":e["month"],"filename":fn,"url":url,"frozen_sha256":e["sha256"],"actual_sha256":actual,"official_checksum_sha256":checksum_hash}
        try:
            rec["sha_match"]=actual==e["sha256"]
            rec["checksum_match"]=checksum_hash is not None and checksum_hash.lower()==e["sha256"].lower()
            with zipfile.ZipFile(zpath) as zf:
                bad=zf.testzip(); names=zf.namelist()
                rec["zip_crc_pass"]=bad is None
                rec["member_set"]=names
                rec["member_pass"]=names==[e["csv_member"]]
                rec["csv_audit"]=audit_csv(zf,e["csv_member"],e) if rec["member_pass"] else None
            ok=rec["sha_match"] and rec["checksum_match"] and rec["zip_crc_pass"] and rec["member_pass"] and rec["csv_audit"]["row_count_pass"] and not any(rec["csv_audit"]["violations"].values())
        except Exception as ex:
            rec["exception"]=repr(ex); ok=False
        rec["pass"]=ok
        if not ok: failures.append(f"{symbol}:{e['month']}")
        receipts.append(rec)
        print(f"[{i:02d}/{expected_count}] {symbol} {e['month']} {'PASS' if ok else 'FAIL'}",flush=True)
    result={"document_id":"CED_1D_2025_SOURCE_GATE_RECEIPT_V0.2","status":"SOURCE_DATA_PASS" if not failures else "SOURCE_DATA_FAIL","manifest_document_id":man["document_id"],"file_count":len(receipts),"pass_count":sum(r["pass"] for r in receipts),"failures":failures,"confirmation_2025_outcomes_computed":False,"access_2026_plus":False,"receipts":receipts}
    raw=json.dumps(result,sort_keys=True,separators=(",",":")).encode(); result["fingerprint"]=hashlib.sha256(raw).hexdigest()
    (out/"CED_1D_2025_SOURCE_GATE_RECEIPT_V0.2.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"source_gate_summary.json").write_text(json.dumps({k:result[k] for k in ["status","file_count","pass_count","failures","fingerprint"]},indent=2)+"\n")
    if failures: raise SystemExit("SOURCE_DATA_FAIL:"+",".join(failures))
    print("SOURCE_DATA_PASS")

if __name__=="__main__": main()
