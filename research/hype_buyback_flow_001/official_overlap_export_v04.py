#!/usr/bin/env python3
"""Official Hyperliquid -> uploaded CSV fixed 3-day overlap, source-only fail-closed."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

AF = "0x" + "fe"*20
assert len(AF) == 42
URL = "https://api.hyperliquid.xyz/info"
OUT = Path("research/hype_buyback_flow_001/receipts/export_overlap_v04")
OUT.mkdir(parents=True, exist_ok=True)
EXPECTED = {
    "2026-10-08": {"count":1422,"null_hash":130,"sha256":"7c2e7e75b3de52300c8ddf257526dede27990d1cf73176ea0804394b00261853"},
    "2026-10-09": {"count":583,"null_hash":34,"sha256":"8591df5328050ae5d470e78d16ca309458fee70c5c269af53109ee3db088e744"},
    "2026-10-10": {"count":420,"null_hash":47,"sha256":"050f9f22edd060a966df34864ea1a034b757f29d50a48db431adfa1eca28d740"}
}
assert list(EXPECTED.keys()) == ["2026-10-08","2026-10-09","2026-10-10"]

def checksum(items):
    cnt = Counter(items)
    blob = "\n".join("|".join(map(str,k)) + "|" + str(count) for k,count in sorted(cnt.items()))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

def canonical_valid(fills, start_ms, end_ms):
    records=[]
    diag={"raw_rows":len(fills),"filtered_other_coin":0,"filtered_other_side":0,
          "invalid_rows":0,"out_of_window":0,"zero_hash_rows":0,
          "valid_spot_buy_rows":0,"times_min_ms":None,"times_max_ms":None,
          "missing_tid":0}
    for f in fills:
        if not isinstance(f,dict):
            diag["invalid_rows"]+=1
            continue
        if f.get("coin")!="@107":
            diag["filtered_other_coin"]+=1
            continue
        if f.get("side")!="B":
            diag["filtered_other_side"]+=1
            continue
        t=f.get("time")
        if not isinstance(t,int):
            diag["invalid_rows"]+=1
            continue
        if t<start_ms or t>end_ms:
            diag["out_of_window"]+=1
            continue
        try:
            px=Decimal(str(f["px"]));sz=Decimal(str(f["sz"]))
            if not px.is_finite() or not sz.is_finite() or px<=0 or sz<=0:raise InvalidOperation
            hh=f.get("hash")
            if not isinstance(hh,str):raise ValueError("missing hash")
            hh=hh.lower()
        except (ValueError,TypeError,KeyError,InvalidOperation):
            diag["invalid_rows"]+=1
            continue
        if hh == "0x"+"0"*64:
            diag["zero_hash_rows"]+=1
        if f.get("tid") is None:
            diag["missing_tid"]+=1
        sec=datetime.fromtimestamp(t//1000,tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        records.append((hh, sec, str(px.normalize()), str(sz.normalize()),"@107","Buy"))
        diag["times_min_ms"]=min(diag["times_min_ms"],t) if diag["times_min_ms"] is not None else t
        diag["times_max_ms"]=max(diag["times_max_ms"],t) if diag["times_max_ms"] is not None else t
    diag["valid_spot_buy_rows"]=len(records)
    diag["exact_duplicate_group_overhang"]=sum(n-1 for n in Counter(records).values() if n>1)
    return diag, checksum(records)


def main():
    res={"candidate_id":"HYPE-BUYBACK-FLOW-001","phase":"SOURCE_ONLY",
         "zero_price_outcomes":True,"trading_authority":"NONE","paid_data":0,
         "source_url":URL,"official_wallet_42char":AF,
         "commit":os.getenv("GITHUB_SHA","UNSET"),"run_id":os.getenv("GITHUB_RUN_ID","LOCAL"),
         "csv_gzip_sha256":"eb431a39ed3a826950057a73912bfb2665d25d61e206d854a63ab204dc9b3e4f",
         "status":"UNRESOLVED","results":[]}
    for day, want in EXPECTED.items():
        start=datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
        end=start+timedelta(days=1)-timedelta(milliseconds=1)
        start_ms=int(start.timestamp()*1000)
        end_ms=int(end.timestamp()*1000)
        body={"type":"userFillsByTime","user":AF,"startTime":start_ms,
              "endTime":end_ms,"aggregateByTime":False}
        reqdata=json.dumps(body,sort_keys=True,separators=(",",":")).encode("utf-8")
        row={"utc_day":day,"requested_utc":datetime.now(timezone.utc).isoformat(),
             "expected_export_rows":want["count"],
             "expected_export_zero_hash_rows":want["null_hash"],
             "expected_export_multiset_sha256":want["sha256"],
             "request_sha256":hashlib.sha256(reqdata).hexdigest()}
        tick=time.monotonic()
        try:
            req=urllib.request.Request(URL,data=reqdata,method="POST",
                 headers={"Content-Type":"application/json","User-Agent":"CryptoLab-HYPE-OfficialOverlap/0.4"})
            with urllib.request.urlopen(req,timeout=18) as http:
                raw=http.read(3500000)
                row["http_code"]=http.status
            row["raw_sha256"]=hashlib.sha256(raw).hexdigest()
            row["raw_len"]=len(raw)
            (OUT/("official_"+day+".json")).write_bytes(raw)
            values=json.loads(raw)
            if not isinstance(values,list):raise ValueError("Non_array_fills")
            diag,digest=canonical_valid(values,start_ms,end_ms)
            row["official"] = diag
            row["official_multiset_sha256"]=digest
            row["at_api_max2000"]=len(values)>=2000
            row["exact_spot_hype_buy_multiset_match"]=bool(
                len(values)<2000 and diag["invalid_rows"]==0 and
                diag["out_of_window"]==0 and
                diag["valid_spot_buy_rows"]==want["count"] and
                diag["zero_hash_rows"]==want["null_hash"] and
                digest==want["sha256"])
        except urllib.error.HTTPError as ex:
            raw=ex.read(400)
            row.update({"http_code":ex.code,"http_error_sha256":hashlib.sha256(raw).hexdigest()})
        except (TimeoutError,urllib.error.URLError,ValueError,json.JSONDecodeError) as ex:
            row["error_type"]=type(ex).__name__
        row["latency_ms"]=round((time.monotonic()-tick)*1000,3)
        row["received_utc"]=datetime.now(timezone.utc).isoformat()
        res["results"].append(row)
    res["primary_overlap_3_days_verified"]=bool(all(x.get("exact_spot_hype_buy_multiset_match") for x in res["results"]))
    res["status"]="RECENT_OVERLAP_MATCH_3D_ONLY" if res["primary_overlap_3_days_verified"] else "SOURCE_DISAGREEMENT_OR_UNRESOLVED"
    res["ninety_day_historical_source_gate"]="NOT_PASSED_FILE_MISSING_TID_ZERO_HASH_PIT"
    res["no_alpha_economic_test_performed"]=True
    (OUT/"HYPE_EXPORT_PRIMARY_OVERLAP_RECEIPT_V04.json").write_text(json.dumps(res,indent=2,sort_keys=True)+"\n")
    print(json.dumps(res,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
