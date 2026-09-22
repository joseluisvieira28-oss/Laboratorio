#!/usr/bin/env python3
import json, urllib.request, urllib.parse, urllib.error, time
from pathlib import Path

PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
START=1734220800
END=1734307200
LIMIT=1000
EXPECTED_BIGQUERY_DISTINCT_TX=43681
MAX_PAGES=100
OUT=Path("dls_kamino_solanafm_probe_v01")
OUT.mkdir(exist_ok=True)

def fetch(page):
    qs=urllib.parse.urlencode({"utcFrom":START,"utcTo":END,"limit":LIMIT,"page":page})
    url=f"https://api.solana.fm/v0/accounts/{PROGRAM}/transactions?{qs}"
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-source-only/0.1","Accept":"application/json"})
    last=None
    for i in range(8):
        try:
            with urllib.request.urlopen(req,timeout=45) as r:
                raw=r.read()
                return r.status,dict(r.headers),raw
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code in (429,500,502,503,504):
                time.sleep(min(30,2*(i+1))); continue
            return e.code,dict(e.headers),raw
        except Exception as e:
            last=repr(e); time.sleep(min(30,2*(i+1)))
    raise RuntimeError(f"transport exhausted {last}")

def extract_rows(obj):
    if isinstance(obj,list): return obj
    if isinstance(obj,dict):
        for k in ("result","data","transactions"):
            if isinstance(obj.get(k),list): return obj[k]
    raise ValueError("unrecognized response shape")

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "purpose":"SolanaFM metadata-only calibration against already-known 2024-12-15 BigQuery program transaction count",
 "program_id":PROGRAM,"utc_from":START,"utc_to":END,"page_limit":LIMIT,
 "expected_bigquery_distinct_transactions":EXPECTED_BIGQUERY_DISTINCT_TX,
 "prices":False,"returns":False,"pnl":False,"direction":False,"market_outcomes":False
}
seen=set(); min_ts=None; max_ts=None; pages=0; http_statuses=[]
try:
    for page in range(1,MAX_PAGES+1):
        status,headers,raw=fetch(page)
        http_statuses.append(status)
        (OUT/f"page_{page:03d}.json").write_bytes(raw)
        pages=page
        if status!=200:
            receipt.update(classification="SOLANAFM_CALIBRATION_ACCESS_BLOCKED",http_status=status,pages_completed=page-1)
            break
        obj=json.loads(raw)
        rows=extract_rows(obj)
        if not rows:
            receipt.update(classification="SOLANAFM_CALIBRATION_COMPLETE")
            break
        for row in rows:
            sig=row.get("signature") or row.get("transactionSignature") or row.get("txHash")
            if isinstance(sig,str): seen.add(sig)
            ts=row.get("timestamp")
            if ts is None: ts=row.get("blockTime")
            if ts is not None:
                try:
                    ts=int(ts)
                    min_ts=ts if min_ts is None else min(min_ts,ts)
                    max_ts=ts if max_ts is None else max(max_ts,ts)
                except Exception: pass
        if len(rows)<LIMIT:
            receipt.update(classification="SOLANAFM_CALIBRATION_COMPLETE")
            break
        time.sleep(0.15)
    else:
        receipt.update(classification="SOLANAFM_CALIBRATION_MAX_PAGES_BLOCKED")
except Exception as e:
    receipt.update(classification="SOLANAFM_CALIBRATION_TRANSPORT_OR_SCHEMA_BLOCKED",error=repr(e))

receipt.update(
 pages_completed=pages,
 unique_signatures=len(seen),
 min_timestamp=min_ts,max_timestamp=max_ts,
 count_delta_vs_bigquery=len(seen)-EXPECTED_BIGQUERY_DISTINCT_TX,
 exact_count_match=(len(seen)==EXPECTED_BIGQUERY_DISTINCT_TX),
 http_statuses=sorted(set(http_statuses))
)
if receipt.get("classification")=="SOLANAFM_CALIBRATION_COMPLETE":
    receipt["routing"]="ELIGIBLE_FOR_SEPARATE_PROSPECTIVE_TRANSPORT_FREEZE" if receipt["exact_count_match"] else "NOT_ELIGIBLE_FOR_ZERO-CANDIDATE_AUTHORITY_WITHOUT_FURTHER_RECONCILIATION"
(OUT/"DLS_KAMINO_SOLANAFM_CALIBRATION_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
