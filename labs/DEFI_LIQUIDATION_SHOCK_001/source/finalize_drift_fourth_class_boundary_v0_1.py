#!/usr/bin/env python3
import datetime as dt, hashlib, json, sys
from pathlib import Path

ROOT=Path(sys.argv[1])
BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
RAW=BASE/"DRIFT_FOURTH_CLASS_FIRST_CANDIDATE_RAW_RECEIPT_V0.1.json"
OUT=BASE/"DRIFT_FOURTH_CLASS_FIRST_SUCCESS_BOUNDARY_RECEIPT_V0.1.json"

LOWER=dt.datetime.fromisoformat("2022-11-04T15:17:54+00:00")
CANDIDATE_TS=dt.datetime.fromisoformat("2023-05-22T00:48:06+00:00")
TARGET_END=dt.datetime.fromisoformat("2023-06-01T00:00:00+00:00")
CLASS="liquidate_borrow_for_perp_pnl"
PREFIX="a911205acf94d11b"
EXPECTED_SIG="5kYZPtPTFhvdBZfaFMPXtWh2A9tQYHt8bbzKJazopc7pWWmpwdcn1DeT4yLjxaidn387VMK6g6rYX4KMMh7NPka6"
EXPECTED_SLOT=195239739

def parse(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def sha_file(p): return hashlib.sha256(p.read_bytes()).hexdigest()

manifests=[]
for mp in ROOT.rglob("MANIFEST.json"):
    try:m=json.loads(mp.read_text())
    except Exception: continue
    if m.get("protocol")=="drift":
        manifests.append((mp,m))

segments=[]
errors=[]
for mp,m in manifests:
    if m.get("classification")!="PARTITION_COMPLETE":
        continue
    base=mp.parent
    for ch in m.get("chunks",[]):
        s=parse(ch["start"]); e=parse(ch["end"])
        if e<=LOWER or s>=TARGET_END: continue
        fp=base/ch["file"]
        if not fp.exists():
            errors.append({"reason":"missing_chunk_file","manifest":str(mp),"file":ch["file"]}); continue
        actual=sha_file(fp)
        if actual!=ch.get("sha256"):
            errors.append({"reason":"chunk_sha_mismatch","manifest":str(mp),"file":ch["file"]}); continue
        rec=json.loads(fp.read_text())
        if rec.get("classification")!="SOURCE_CHUNK_PASS" or rec.get("stream_complete") is not True:
            errors.append({"reason":"chunk_not_pass","file":str(fp),"classification":rec.get("classification")}); continue
        if int(rec.get("anomaly_count") or 0)!=0:
            errors.append({"reason":"chunk_anomaly","file":str(fp),"anomaly_count":rec.get("anomaly_count")}); continue
        segments.append((s,e,fp,rec))

# deduplicate identical exact slices from original/recovery; require content-equivalent scientific rows if duplicates exist
by_range={}
for s,e,fp,rec in segments:
    k=(s,e)
    if k not in by_range:
        by_range[k]=(fp,rec)
    else:
        oldfp,old=by_range[k]
        if old.get("rows_sha256")!=rec.get("rows_sha256"):
            errors.append({"reason":"duplicate_slice_content_conflict","start":s.isoformat(),"end":e.isoformat(),
                           "a":str(oldfp),"b":str(fp)})

ordered=sorted((s,e,fp,rec) for (s,e),(fp,rec) in by_range.items())
cursor=LOWER
coverage=[]
earlier_success=[]
candidate_rows=[]
for s,e,fp,rec in ordered:
    if e<=cursor: continue
    if s>cursor:
        errors.append({"reason":"coverage_gap","expected_start":cursor.isoformat().replace("+00:00","Z"),
                       "observed_start":s.isoformat().replace("+00:00","Z")})
        break
    if s<cursor:
        # overlapping scientific coverage from different granularity is not admissible unless it ends <= cursor.
        errors.append({"reason":"coverage_overlap","cursor":cursor.isoformat().replace("+00:00","Z"),
                       "observed_start":s.isoformat().replace("+00:00","Z"),"observed_end":e.isoformat().replace("+00:00","Z")})
        break
    coverage.append({"start":s.isoformat().replace("+00:00","Z"),"end":e.isoformat().replace("+00:00","Z"),"file":str(fp)})
    for r in rec.get("rows") or []:
        if r.get("class")!=CLASS: continue
        if r.get("decoded_prefix_hex")!=PREFIX: continue
        if r.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":
            ts=parse(r["timestamp"])
            if ts<CANDIDATE_TS: earlier_success.append(r)
            if r.get("signature")==EXPECTED_SIG and r.get("slot")==EXPECTED_SLOT and ts==CANDIDATE_TS:
                candidate_rows.append(r)
    cursor=e
    if cursor>=TARGET_END: break

raw=json.loads(RAW.read_text()) if RAW.exists() else {}
raw_ok=(raw.get("classification")=="DRIFT_FOURTH_CLASS_FIRST_CANDIDATE_RAW_PASS"
        and (raw.get("expected") or {}).get("signature")==EXPECTED_SIG
        and (raw.get("expected") or {}).get("slot")==EXPECTED_SLOT
        and parse((raw.get("expected") or {}).get("timestamp"))==CANDIDATE_TS)

coverage_ok=(cursor>=TARGET_END and not any(e["reason"] in ("coverage_gap","coverage_overlap") for e in errors))
candidate_ok=(len(candidate_rows)>=1 and len(earlier_success)==0)
passed=(not errors and coverage_ok and candidate_ok and raw_ok)

receipt={
  "schema_version":"0.1",
  "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "class":CLASS,
  "discriminator":PREFIX,
  "classification":"DRIFT_LIQUIDATE_BORROW_FOR_PERP_PNL_FIRST_SUCCESS_BOUNDARY_SQD_PASS" if passed else "DRIFT_FOURTH_CLASS_FIRST_SUCCESS_BOUNDARY_BLOCKED_FAIL_CLOSED",
  "frozen_lower_boundary":"2022-11-04T15:17:54Z",
  "candidate_timestamp":"2023-05-22T00:48:06Z",
  "candidate_slot":EXPECTED_SLOT,
  "candidate_signature":EXPECTED_SIG,
  "coverage_verified_through":"2023-06-01T00:00:00Z" if coverage_ok else cursor.isoformat().replace("+00:00","Z"),
  "coverage_segment_count":len(coverage),
  "earlier_success_count":len(earlier_success),
  "candidate_row_count":len(candidate_rows),
  "raw_classification":raw.get("classification"),
  "errors":errors,
  "note":"This closes only the first-success boundary for the fourth frozen Drift class; it does not substitute for the full Drift census authority.",
  "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
              "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
              "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if not passed: raise SystemExit(2)
