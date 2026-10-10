#!/usr/bin/env python3
"""RW-HL G2 immutable source-only OI/funding variability census.

Counts only; never calculates or reads returns, mark changes, outcomes, PnL.
The exact three source receipts and thresholds were frozen BEFORE the count.
"""
from __future__ import annotations
from decimal import Decimal,InvalidOperation
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
import sys
from verify_first_public_source_artifact_v01 import verify_dir

ROOT=Path(__file__).resolve().parent
FREEZE=ROOT/"RW_HL_EXITFLOW_001_G2_SOURCE_VARIATION_FREEZE_2026-10-09.json"
OUT=ROOT/"source_receipts"/"G2_SOURCE_VARIATION_RECEIPT.json"

class SourceError(Exception): pass

def to_num(obj,name):
    try:
        if isinstance(obj,bool) or obj is None:raise InvalidOperation
        x=Decimal(str(obj))
    except (InvalidOperation,ValueError,TypeError):
        raise SourceError("BAD_DECIMAL_"+name) from None
    if not x.is_finite():raise SourceError("NONFINITE_"+name)
    return x

def verify_freeze(data):
    expected={
        "lab_id":"RW-HL-EXITFLOW-001",
        "stage":"G2_PROSPECTIVE_SOURCE_VARIABILITY_ONLY",
        "source_run_id":37939142048,
        "source_terminal_chain_sha256":"3c9d8c54d00d20be035f8add10123a75002d42b87d32006ed757e701b7fa2c31",
    }
    if any(data.get(k)!=v for k,v in expected.items()):raise SourceError("SOURCE_IDENTITY_FREEZE_CHANGED")
    g=data["source_gate_preregistered"]
    if (g["min_common_market_fraction"]!=.95 or
        g["min_positive_OI_mark_funding_triples_per_snapshot"]!=100 or
        g["min_assets_negative_funding_last"]!=5 or
        g["min_assets_OI_changing_first_last"]!=10 or
        g["min_assets_OI_rising_with_negative_funding_last"]!=1 or
        data.get("count_only") is not True or data.get("computed_future_price_returns") is not False):
        raise SourceError("FROZEN_G2_GATE_CHANGED")
    return g

def census(freeze,rows):
    gates=verify_freeze(freeze)
    if len(rows)!=3:raise SourceError("NOT_THREE_SNAPSHOTS")
    times=freeze["source_timestamp_order"]
    parsed=[];name_sets=[];all_counts=[]
    for i,row in enumerate(rows):
        if (row.get("lab_id")!="RW-HL-EXITFLOW-001" or row.get("ordinal")!=i+1
           or row.get("trading_authority")!="NONE" or row.get("historical_outcome") is not False
           or row.get("read_utc")!=times[i]):
            raise SourceError("SNAPSHOT_IDENTITY_MISMATCH")
        market=row["context"]["market_context"]
        if len(market)!=row["context"]["valid_public_markets"]:
            raise SourceError("MARKET_COUNT_BINDING_FAIL")
        markets={}
        for item in market:
            name=item["coin"]
            if not name or name in markets:raise SourceError("COIN_IDENTITY_DUPLICATED")
            oi=to_num(item["openInterest"],"OI")
            funding=to_num(item["funding"],"FUNDING")
            if oi<0:raise SourceError("NEGATIVE_OI")
            # markPx checked by frozen source parser but never evaluated as future price outcome here.
            markets[name]=(oi,funding)
        parsed.append(markets)
        name_sets.append(set(markets))
        all_counts.append(len(markets))
    common=set.intersection(*name_sets)
    union=set.union(*name_sets)
    if not common:raise SourceError("ZERO_COMMON_MARKETS")
    first=parsed[0];last=parsed[2]
    positive_oi=sum(first[c][0]>0 and last[c][0]>0 for c in common)
    oi_changed=sum(first[c][0]!=last[c][0] for c in common)
    negfund=sum(last[c][1]<0 for c in common)
    oi_up_negfund=sum(first[c][0]>0 and last[c][0]>first[c][0] and last[c][1]<0 for c in common)
    sign_changed=sum((first[c][1]<0)!=(last[c][1]<0) for c in common)
    results={
       "MARKET_COMPLETENESS":all(n>=gates["min_positive_OI_mark_funding_triples_per_snapshot"] for n in all_counts),
       "UNIVERSE_INTERSECTION":len(common)/len(union)>=gates["min_common_market_fraction"],
       "NEGATIVE_FUNDING_SOURCE":negfund>=gates["min_assets_negative_funding_last"],
       "OI_MOVEMENT_SOURCE":oi_changed>=gates["min_assets_OI_changing_first_last"],
       "OI_UP_NEGATIVE_FUNDING_COOCCURRENCE":oi_up_negfund>=gates["min_assets_OI_rising_with_negative_funding_last"],
    }
    return {
      "lab_id":"RW-HL-EXITFLOW-001",
      "state":"PROSPECTIVE_SOURCE_VARIATION_PASS_NOT_EDGE" if all(results.values()) else "PROSPECTIVE_SOURCE_VARIATION_INSUFFICIENT",
      "phase":"G2_SOURCE_COUNT_ONLY",
      "snapshot_valid_market_counts":all_counts,
      "intersection_market_count":len(common),"union_market_count":len(union),
      "OI_positive_common_markets":positive_oi,
      "OI_changed_common_markets":oi_changed,
      "negative_funding_last_common_markets":negfund,
      "OI_rising_and_funding_negative_common_markets":oi_up_negfund,
      "funding_negative_sign_flip_common_markets":sign_changed,
      "gates":results,"source_snapshot_count":3,
      "source_lifetime_minutes_approximately":2,
      "economic_outcomes_unlocked":False,
      "future_price_returns_read":False,"historical_2023_2024_OI_available":False,
      "economic_edge_assessed":False,"trading_authority":"NONE",
      "caveat":"OI changes do not reveal which trader opens which side; negative funding does not prove informed sellers. Two-minute count is source feasibility, NOT predictive signal."
    }

def run():
    f=json.loads(FREEZE.read_text())
    root=ROOT.parent.parent/f["source_receipt_path"]
    verified=verify_dir(root)
    if verified["last_chain"]!=f["source_terminal_chain_sha256"]:
        raise SourceError("SHA_CHAIN_LOCK_MISMATCH")
    rows=[json.loads((root/f"SNAPSHOT_{i:02d}.json").read_text()) for i in (1,2,3)]
    ans=census(f,rows)
    ans["source_receipt_sha256"]=hashlib.sha256((root/"CAPTURE_RECEIPT.json").read_bytes()).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(ans,indent=2,sort_keys=True)+"\n")
    print(json.dumps(ans,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    try:raise SystemExit(run())
    except (SourceError,ValueError,KeyError,TypeError,FileNotFoundError) as e:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps({"state":"SOURCE_VARIATION_INTEGRITY_BLOCKED","reason":str(e),
           "economic_outcomes_unlocked":False,"trading_authority":"NONE"},indent=2)+"\n")
        print("SOURCE_VARIATION_INTEGRITY_BLOCKED",str(e),file=sys.stderr)
        raise SystemExit(2)
