#!/usr/bin/env python3
"""Offline-only Hypedexer CSV/JSON export audit — NO trading, NO return/outcome computation.
Intentionally never outputs SOURCE_PASS from an unproven third-party file alone."""
import argparse
import csv
import datetime as dt
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
from pathlib import Path

AF = "0x" + "fe" * 20
SPOT = "@107"
MAX_BYTES = 120_000_000
MAX_ROWS = 3_000_000

def read_rows(path):
    compressed = path.name.lower().endswith(".gz")
    suffix = path.name.lower()[:-3] if compressed else path.name.lower()
    op = gzip.open if compressed else open
    if suffix.endswith(".csv"):
        with op(path, "rt", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                yield row
    elif suffix.endswith(".json"):
        with op(path, "rt", encoding="utf-8-sig") as fh:
            obj = json.load(fh)
        if isinstance(obj, dict):
            obj = obj.get("data", obj.get("fills", []))
        if not isinstance(obj, list):
            raise ValueError("JSON_export_must_be_array")
        for row in obj:
            yield row
    else:
        raise ValueError("unsupported_export_extension")

def parse_utc_millis(value):
    if value is None:
        return None
    try:
        v=str(value).strip()
        if v.isdigit():
            n=int(v)
            return n if n >= 10**12 else n*1000 if n >= 10**9 else None
        return int(dt.datetime.fromisoformat(v.replace("Z","+00:00")).timestamp()*1000)
    except (ValueError,OverflowError,TypeError):
        return None

def file_sha256(path):
    h=hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def audit_file(path, from_day="2026-07-10", to_day="2026-10-09"):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("export_too_large_for_bounded_offline_review")
    first=dt.date.fromisoformat(from_day)
    last=dt.date.fromisoformat(to_day)
    if first>last:
        raise ValueError("reversed_date_range")
    counts={
        "source_wallet_expected": AF,
        "source_wallet_proven_from_file":False,
        "official_spot_pair":SPOT,
        "file_name":path.name,
        "file_bytes":path.stat().st_size,
        "file_sha256":file_sha256(path),
        "record_count":0,"eligible_af_hype_buy_rows":0,
        "missing_tid":0,"duplicate_strong_id":0,"bad_timestamp":0,
        "outside_window":0,"wrong_coin":0,"nonbuy_side":0,
        "unclassified_side":0,"bad_notional":0,
        "daily_counts":{},"total_hype":"0","total_usdc":"0",
        "SOURCE_PASS":False,
        "source_status":"UNVERIFIED_PENDING_PRIMARY_CROSSCHECK_AND_PIT_PROVENANCE"
    }
    strong=set()
    qty=Decimal(0)
    ntl=Decimal(0)
    distinct_wallet_values=set()
    for row in read_rows(path):
        counts["record_count"]+=1
        if counts["record_count"]>MAX_ROWS:
            raise ValueError("export_exceeds_row_guard")
        if not isinstance(row,dict):
            counts["bad_notional"]+=1
            continue
        wallet=row.get("user",row.get("wallet",row.get("address")))
        if wallet:
            distinct_wallet_values.add(str(wallet).lower())
        ts=parse_utc_millis(row.get("time",row.get("timestamp")))
        if ts is None:
            counts["bad_timestamp"]+=1
            continue
        day=dt.datetime.fromtimestamp(ts/1000,dt.timezone.utc).date()
        if not(first<=day<=last):
            counts["outside_window"]+=1
            continue
        if str(row.get("coin",row.get("market",""))).strip()!=SPOT:
            counts["wrong_coin"]+=1
            continue
        s=str(row.get("side",row.get("dir",""))).strip().lower()
        if s not in ("b","buy","spot buy","buy spot","spotbuy"):
            if s in ("a","sell","spot sell","sell spot"):
                counts["nonbuy_side"]+=1
            else:
                counts["unclassified_side"]+=1
            continue
        try:
            sz=Decimal(str(row.get("sz",row.get("size"))))
            px=Decimal(str(row.get("px",row.get("price"))))
            if not all(v.is_finite() and v>0 for v in (px,sz)):
                raise InvalidOperation
        except (InvalidOperation,ValueError,TypeError):
            counts["bad_notional"]+=1
            continue
        tid=row.get("tid",row.get("trade_id",row.get("tradeId")))
        h=row.get("hash",row.get("tx_hash"))
        if tid in (None,"") or not h:
            counts["missing_tid"]+=1
            # Do not count source rows without strong identity as verified.
            continue
        k=(str(h).lower(),str(tid))
        if k in strong:
            counts["duplicate_strong_id"]+=1
            continue
        strong.add(k)
        counts["eligible_af_hype_buy_rows"]+=1
        counts["daily_counts"][day.isoformat()]=counts["daily_counts"].get(day.isoformat(),0)+1
        qty+=sz
        ntl+=sz*px
    counts["source_wallet_proven_from_file"]=(distinct_wallet_values=={AF})
    counts["wallet_address_values_found"]=len(distinct_wallet_values)
    counts["active_days_in_range"]=len(counts["daily_counts"])
    counts["date_span_inclusive_days"]=(last-first).days+1
    counts["total_hype"]=str(qty)
    counts["total_usdc"]=str(ntl)
    counts["important_note"]="This is a file-integrity review, not historical feed-completeness, first-seen timestamps, archive correctness, execution feasibility, predictive edge or a backtest. Missing trade IDs prevent strong fill identity."
    return counts

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--file", type=Path, required=True)
    p.add_argument("--from-day", default="2026-07-10")
    p.add_argument("--to-day", default="2026-10-09")
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    report=audit_file(a.file,a.from_day,a.to_day)
    payload=json.dumps(report,indent=2,sort_keys=True)+"\n"
    print(payload)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(payload,encoding="utf-8")
