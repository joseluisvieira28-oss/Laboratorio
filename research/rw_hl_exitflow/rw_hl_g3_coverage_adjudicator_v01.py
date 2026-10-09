#!/usr/bin/env python3
"""RW-HL-EXITFLOW-001 G3 source ONLY fixed-window hour coverage adjudicator.

Immutable G3 starts 2026-10-10T00Z, 14 complete UTC days, 320/336
non-backfilled actual hour receipts, 100 public markets and >=95% coverage.
No economics, no return-based asset selection, no trading/account reads.
"""
from __future__ import annotations
from datetime import datetime,timezone,timedelta
from decimal import Decimal,InvalidOperation
import hashlib,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
AUTH=ROOT/"RW_HL_EXITFLOW_001_G3_SCHEDULER_ACTIVATION_2026-10-09.json"
FREEZE=ROOT/"RW_HL_EXITFLOW_001_G3_HOURLY_SOURCE_PREACTIVATION_FREEZE_2026-10-09.md"
SOURCES=ROOT/"forward_source"/"hourly"
OUTPUT=ROOT/"source_receipts"/"G3_HOURLY_COVERAGE_STATUS.json"

class SourceBlocked(Exception):pass

def parse_utc(v):
    if not isinstance(v,str) or not v.endswith("Z"):raise SourceBlocked("TIMESTAMP_NOT_UTC")
    try: dt=datetime.fromisoformat(v.replace("Z","+00:00"))
    except ValueError:raise SourceBlocked("TIMESTAMP_INVALID") from None
    if dt.utcoffset()!=timedelta(0):raise SourceBlocked("TIMESTAMP_OFFSET_INVALID")
    return dt

def frozen():
    z=json.loads(AUTH.read_text())
    if (z.get("lab_id")!="RW-HL-EXITFLOW-001" or z.get("stage")!="G3_SOURCE_COVERAGE_ACTIVATION"
       or z.get("first_complete_utc_day")!="2026-10-10"
       or z.get("window_end_exclusive")!="2026-10-24T00:00:00Z"
       or z.get("expected_utc_hours")!=336 or z.get("min_complete_unique_hours")!=320
       or z.get("min_distinct_utc_dates")!=14
       or z.get("minimum_valid_market_contexts_per_source_hour")!=100
       or z.get("required_market_context_coverage_fraction")!=0.95
       or z.get("no_backfill") is not True
       or z.get("economic_outcomes_authorized") is not False):
        raise SourceBlocked("ACTIVATION_FREEZE_MISMATCH")
    if "G3 HOURLY POINT-IN-TIME SOURCE" not in FREEZE.read_text():
        raise SourceBlocked("G3_SOURCE_FREEZE_MISSING")
    return z

def finite_nonneg(value,key,allow_zero=True):
    try: z=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError):
        raise SourceBlocked("SOURCE_NUMERIC_INVALID_"+key) from None
    if not z.is_finite() or (z<0 if allow_zero else z<=0):
        raise SourceBlocked("SOURCE_NUMERIC_RANGE_"+key)
    return z

def verify_record(obj,path,slot):
    if (obj.get("lab_id")!="RW-HL-EXITFLOW-001"
        or obj.get("record_type")!="PUBLIC_HL_HOURLY_SOURCE"
        or obj.get("source")!="HYPERLIQUID_PUBLIC_META_AND_ASSET_CTXS"
        or obj.get("no_backfill") is not True or obj.get("economic_outcomes_opened") is not False
        or obj.get("trading_authority")!="NONE"):
        raise SourceBlocked("SOURCE_IDENTITY_OR_TRADE_SEAL_INVALID")
    dt=parse_utc(obj.get("observed_at_utc"))
    if dt.replace(minute=0,second=0,microsecond=0)!=slot:
        raise SourceBlocked("SOURCE_ACTUAL_RECEIVE_HOUR_MISMATCH")
    if obj.get("source_hour_utc")!=slot.strftime("%Y-%m-%dT%H:00:00Z"):
        raise SourceBlocked("SOURCE_HOUR_VALUE_MISMATCH")
    if not str(obj.get("github_run_id","")).isdigit():
        raise SourceBlocked("SOURCE_ORIGIN_RUN_ID_INVALID")
    market=obj.get("market_data")
    if not isinstance(market,dict) or not isinstance(market.get("market_context"),list):
        raise SourceBlocked("SOURCE_MARKET_SCHEMA_INVALID")
    names=set()
    for row in market["market_context"]:
        if not isinstance(row,dict) or not {"coin","openInterest","markPx","funding"}<=row.keys():
            raise SourceBlocked("SOURCE_MARKET_COLUMNS_MISSING")
        name=row["coin"]
        if not isinstance(name,str) or not name or name in names:
            raise SourceBlocked("SOURCE_MARKET_DUPLICATE_OR_INVALID")
        names.add(name)
        finite_nonneg(row["openInterest"],"OI")
        finite_nonneg(row["markPx"],"MARK",allow_zero=False)
        # Funding is signed: just check finite, do not force sign.
        try:v=Decimal(str(row["funding"]))
        except (InvalidOperation,ValueError,TypeError):
            raise SourceBlocked("SOURCE_FUNDING_NONNUMERIC") from None
        if not v.is_finite():raise SourceBlocked("SOURCE_FUNDING_NONFINITE")
    if len(names)!=obj.get("market_count") or len(names)!=market.get("valid_public_markets"):
        raise SourceBlocked("SOURCE_MARKET_COUNTS_MISMATCH")
    return len(names)

def source_gate(now,root=SOURCES):
    authority=frozen()
    start=parse_utc("2026-10-10T00:00:00Z")
    end=parse_utc(authority["window_end_exclusive"])
    if now.tzinfo is None:raise SourceBlocked("NOW_NO_UTC")
    expected=336;slots={}
    failures=[]
    for path in sorted(Path(root).glob("????-??-??/[0-2][0-9].json")):
        date=path.parent.name
        hour=path.stem
        try:slot=parse_utc(f"{date}T{hour}:00:00Z")
        except SourceBlocked:
            failures.append("INVALID_PATH_UTC_HOUR");continue
        if not start<=slot<end:continue
        if slot in slots:
            failures.append("DUPLICATE_HOUR_PATH");continue
        try:
            obj=json.loads(path.read_bytes())
            n=verify_record(obj,path,slot)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            slots[slot]={"markets":n,"sha256":digest}
        except (SourceBlocked,ValueError,TypeError):
            failures.append("INVALID_RECEIPT_IN_SLOT_"+slot.strftime("%Y-%m-%dT%H"))
    dates={d.date() for d in slots}
    good_rows=sum(s["markets"]>=100 for s in slots.values())
    observed=len(slots)
    elapsed=min(expected,max(0,int((now-start).total_seconds()//3600)))
    # No economic interpretation before window expires.
    if now<end:
        decision="G3_FORWARD_INSUFFICIENT_UNTIL_2026_10_24_UTC"
    elif (observed>=320 and len(dates)>=14 and not failures and observed>0
          and good_rows/observed>=0.95):
        decision="G3_SOURCE_COVERAGE_PASS"
    else:
        decision="G3_SOURCE_COVERAGE_BLOCKED_OR_INSUFFICIENT"
    return {
      "lab_id":"RW-HL-EXITFLOW-001","classification":decision,
      "g3_window_utc":"2026-10-10T00:00:00Z/2026-10-24T00:00:00Z",
      "window_finished":now>=end,
      "expected_hours":expected,"hours_elapsed":elapsed,
      "valid_unique_hour_receipts":observed,
      "distinct_utc_dates":len(dates),
      "valid_ge100_market_hours":good_rows,
      "minimum_unique_hours":320,"minimum_days":14,
      "missing_elapsed_hours":max(0,elapsed-observed),
      "receipt_failures":failures,
      "economic_outcomes_unlocked":False,
      "source_hours_unbackfilled":True,
      "no_economic_verdict":True,
      "trading_authority":"NONE",
      "automation_context":"G3 source ready does not unlock economic outcomes; G4 freeze before source event classification."
    }

def main():
    now=datetime.now(timezone.utc)
    z=source_gate(now)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(z,indent=2,sort_keys=True)+"\n")
    print(json.dumps(z,indent=2,sort_keys=True))
    return 0 if z["classification"]!="G3_SOURCE_COVERAGE_BLOCKED_OR_INSUFFICIENT" else 2

if __name__=="__main__":
    try:raise SystemExit(main())
    except (SourceBlocked,OSError,ValueError,TypeError) as e:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True)
        fail={"classification":"G3_SOURCE_INTEGRITY_BLOCKED","reason":str(e),
              "economic_outcomes_unlocked":False,"trading_authority":"NONE"}
        OUTPUT.write_text(json.dumps(fail,indent=2)+"\n")
        print(json.dumps(fail),file=sys.stderr);raise SystemExit(2)
