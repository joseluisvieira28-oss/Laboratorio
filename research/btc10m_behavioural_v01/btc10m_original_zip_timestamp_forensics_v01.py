#!/usr/bin/env python3
"""STRICT original official Binance 2023/2024 ZIP timestamp-only coverage, NO MARKET PRICE."""
import csv,datetime as dt,hashlib,io,json,pathlib,zipfile
from datetime import timezone
D=pathlib.Path("downloaded/original_source")
O=pathlib.Path("artifacts/btc10m_24zip_original_timestamp_audit")
O.mkdir(parents=True,exist_ok=True)
MONTHS=[f"{y}-{m:02d}" for y in (2023,2024) for m in range(1,13)]
def month_window(m):
    a=dt.datetime.strptime(m+"-01","%Y-%m-%d").replace(tzinfo=timezone.utc)
    b=dt.datetime(a.year+(a.month==12),1 if a.month==12 else a.month+1,1,tzinfo=timezone.utc)
    return int(a.timestamp()*1000),int(b.timestamp()*1000)
r={"study":"BTC10M_SOURCE_ONLY_24_ORIGINAL_ZIP_MONTHLY_TIMESTAMP_FORENSICS",
   "historic_outcomes_opened":0,"prices_opened":0,"fresh_market_http_calls":0,
   "source_original_artifact_id":13078359511,"months":[],"status":"SOURCE_QA_AUDIT_FAIL"}
try:
    for m in MONTHS:
        raw=(D/(m+".zip")).read_bytes()
        expected=(D/(m+".zip.CHECKSUM")).read_text("ascii").strip().split()[0].lower()
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("ZIP_CHECKSUM_MISMATCH_"+m)
        start,end=month_window(m)
        prev=None;missing=0;dups=0;gaps=[];off=0;count=0;first=None;last=None
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            members=[x for x in z.namelist() if x.endswith(".csv")]
            if len(members)!=1:raise ValueError("ZIP_CSV_MEMBER_COUNT_"+m)
            with io.TextIOWrapper(z.open(members[0]),encoding="utf-8-sig") as stream:
                for row in csv.reader(stream):
                    if not row:continue
                    if not row[0].isdigit():
                        if count==0:continue
                        raise ValueError("UNEXPECTED_NON_TIMESTAMP_"+m)
                    t=int(row[0])
                    if 10**15<=t<10**17:
                        if t%1000:raise ValueError("SUBMS_SOURCE_TS")
                        t//=1000
                    if not(start<=t<end) or t%60000:off+=1
                    if prev is not None:
                        if t<=prev:dups+=1
                        if t-prev>60000:
                            gap=(t-prev)//60000-1
                            gaps.append({"missing_minutes":int(gap),"first_missing_time_ms":int(prev+60000)})
                    first=t if first is None else first
                    last=t;prev=t;count+=1
        expected_minutes=(end-start)//60000
        missing=expected_minutes-count
        rec={"month":m,"zip_sha256_verified":True,"rows":count,"expected_minutes":expected_minutes,
            "missing_minutes":missing,"coverage":count/expected_minutes,
            "frozen_99p95_source_gate":count/expected_minutes>=0.9995,
            "first_timestamp_ms":first,"last_timestamp_ms":last,
            "duplicates_or_regressions":dups,"outside_month_or_misaligned":off,
            "gaps_count":len(gaps),"largest_gap_minutes":max((g["missing_minutes"] for g in gaps),default=0),
            "first_five_gaps":gaps[:5]}
        r["months"].append(rec)
        print("ORIGINAL_MONTH_TIMESTAMP_QA",json.dumps(rec,sort_keys=True),flush=True)
    r["status"]="ORIGINAL_24ZIP_TIMESTAMP_ONLY_SOURCE_QA_COMPLETE"
except Exception as exc:
    r["error"]=type(exc).__name__+":"+str(exc)[:220]
(O/"receipt.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
print("FINAL_TIMESTAMP_SOURCE_QA",json.dumps({"status":r["status"],"error":r.get("error"),
    "bad_months":[{"month":x["month"],"missing":x["missing_minutes"],
                  "coverage":x["coverage"],"largest_gap":x["largest_gap_minutes"]} for x in r["months"] if not x["frozen_99p95_source_gate"]]},sort_keys=True))
if r["status"]!="ORIGINAL_24ZIP_TIMESTAMP_ONLY_SOURCE_QA_COMPLETE":raise SystemExit(2)
