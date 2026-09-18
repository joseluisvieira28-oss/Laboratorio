#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math,time,urllib.parse,urllib.request
from pathlib import Path

UA="CED1D-2025-FUNDING-GATE/0.1"

def fetch_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=60) as r:
        body=r.read()
    return body,json.loads(body)

def canonical(o):
    return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    man=json.loads(Path(a.manifest).read_text())
    if man["access_2026_plus"] or man["price_outcomes_accessed"]:
        raise SystemExit("FUNDING_MANIFEST_FIREWALL_FAIL")
    start=int(man["start_time_ms"]); end=int(man["end_time_ms"]); limit=int(man["pagination_limit"])
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    summary={}
    all_records={}
    failures=[]
    for symbol in man["symbols"]:
        cursor=start; page=0; raw_hashes=[]; records=[]
        while cursor<=end:
            q=urllib.parse.urlencode({"symbol":symbol,"startTime":cursor,"endTime":end,"limit":limit})
            body,data=fetch_json(man["endpoint"]+"?"+q)
            page+=1
            ph=hashlib.sha256(body).hexdigest(); raw_hashes.append({"page":page,"sha256":ph,"count":len(data),"startTime":cursor})
            (out/f"{symbol}_page_{page:03d}.json").write_bytes(body)
            if not isinstance(data,list):
                failures.append(f"{symbol}:NON_LIST_RESPONSE"); break
            if not data: break
            last_time=None
            for r in data:
                try:
                    s=str(r["symbol"]); ft=int(r["fundingTime"]); fr=float(r["fundingRate"])
                except Exception:
                    failures.append(f"{symbol}:SCHEMA"); continue
                if s!=symbol or not(start<=ft<=end) or not math.isfinite(fr):
                    failures.append(f"{symbol}:BAD_RECORD:{ft}"); continue
                if records and ft<=records[-1]["fundingTime"]:
                    failures.append(f"{symbol}:NON_ASCENDING:{ft}"); continue
                records.append({"symbol":symbol,"fundingTime":ft,"fundingRate":str(r["fundingRate"])})
                last_time=ft
            if last_time is None: break
            if len(data)<limit: break
            cursor=last_time+1
            time.sleep(0.1)
        dedup=len({r["fundingTime"] for r in records})==len(records)
        if not dedup: failures.append(f"{symbol}:DUPLICATE_TIME")
        all_records[symbol]=records
        summary[symbol]={
            "records":len(records),
            "first_funding_time":records[0]["fundingTime"] if records else None,
            "last_funding_time":records[-1]["fundingTime"] if records else None,
            "raw_pages":raw_hashes,
            "canonical_records_sha256":hashlib.sha256(canonical(records)).hexdigest(),
            "ascending_unique":dedup
        }
    receipt={
        "document_id":"CED_1D_2025_FUNDING_SOURCE_GATE_RECEIPT_V0.1",
        "status":"FUNDING_SOURCE_PASS" if not failures else "FUNDING_SOURCE_FAIL",
        "manifest_document_id":man["document_id"],
        "interval":{"start_time_ms":start,"end_time_ms":end},
        "symbols":summary,
        "failures":failures,
        "price_outcomes_computed":False,
        "access_2026_plus":False
    }
    receipt["fingerprint"]=hashlib.sha256(canonical(receipt)).hexdigest()
    (out/"funding_records_canonical.json").write_text(json.dumps(all_records,indent=2,sort_keys=True)+"\n")
    (out/"CED_1D_2025_FUNDING_SOURCE_GATE_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":receipt["status"],"summary":summary,"failures":failures,"fingerprint":receipt["fingerprint"]},indent=2))
    if failures or any(summary[s]["records"]==0 for s in man["symbols"]):
        raise SystemExit("FUNDING_SOURCE_FAIL")
    print("FUNDING_SOURCE_PASS")

if __name__=="__main__":
    main()
