"""Count-only pre-outcome eligibility firewall. No market data, no prices, no PnL.
A pass is *never* an authorization to inspect returns; it only permits the next gate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

FORBIDDEN = re.compile(
    r"(^|_)(pnl|profit|loss|return|returns|gross|net|sharpe|drawdown|winrate|"
    r"hit_rate|profit_factor|bootstrap|outcome|outcomes|future_price|exit_price|"
    r"target_hit|stop_hit|mae|mfe|equity|trade_result)($|_)", re.I
)
EXACT_KEYS = {"lab_id","stage","source_receipt_sha256","freeze_sha256",
              "source_observations_only","future_prices_opened",
              "group_raw_candidate_counts","frozen_minimum_executed_count"}

class GateInvalid(ValueError):
    pass

def sha_shape(v):
    return isinstance(v,str) and re.fullmatch(r"[0-9a-fA-F]{64}",v) is not None

def evaluate(d):
    if not isinstance(d,dict) or set(d)!=EXACT_KEYS:
        raise GateInvalid("SCHEMA_KEYS_EXACT_REQUIRED")
    if d["stage"]!="SOURCE_ONLY_PREOUTCOME_CENSUS":
        raise GateInvalid("WRONG_CENSUS_STAGE")
    if not isinstance(d["lab_id"],str) or not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{3,99}",d["lab_id"]):
        raise GateInvalid("INVALID_LAB_ID")
    if not (sha_shape(d["source_receipt_sha256"]) and sha_shape(d["freeze_sha256"])):
        raise GateInvalid("MISSING_SOURCE_AND_FREEZE_SHA_BINDING")
    if d["source_observations_only"] is not True or d["future_prices_opened"] is not False:
        raise GateInvalid("OUTCOME_FIREWALL_NOT_PROVED")
    groups=d["group_raw_candidate_counts"]
    floors=d["frozen_minimum_executed_count"]
    if not isinstance(groups,dict) or not isinstance(floors,dict) or not groups or set(groups)!=set(floors):
        raise GateInvalid("GROUP_NAMES_INCONSISTENT")
    if any(not isinstance(k,str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}",k) for k in groups):
        raise GateInvalid("INVALID_GROUP_NAMES")
    for key in groups:
        a=groups[key]
        b=floors[key]
        if (not isinstance(a,int) or isinstance(a,bool) or a<0
            or not isinstance(b,int) or isinstance(b,bool) or b<=0):
            raise GateInvalid("INVALID_COUNT_OR_FROZEN_FLOOR")
    short={key:{"raw_candidate_upper_bound":groups[key],"required_executed":floors[key]}
           for key in groups if groups[key]<floors[key]}
    classification=("SOURCE_SAMPLE_IMPOSSIBLE_DO_NOT_OPEN_OUTCOMES"
                    if short else "RAW_SIGNAL_UPPER_BOUND_PASSES_NEXT_GATE_REQUIRED")
    return {
        "lab_id":d["lab_id"],
        "classification":classification,
        "impossible_groups":short,
        "source_receipt_sha256":d["source_receipt_sha256"].lower(),
        "freeze_sha256":d["freeze_sha256"].lower(),
        "economic_outcome_access_authorized":False,
        "trading_authority":"NONE",
        "next_required_step":"CAUSAL_EXECUTION_ELIGIBILITY_AND_DATE_SPAN_CENSUS_BEFORE_OUTCOMES"
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("count_only_receipt")
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    raw=Path(args.count_only_receipt).read_text()
    # No ambiguous data-bearing enrichment: only strict counted identities accepted.
    data=json.loads(raw)
    result=evaluate(data)
    Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["classification"]=="SOURCE_SAMPLE_IMPOSSIBLE_DO_NOT_OPEN_OUTCOMES":
        raise SystemExit(3)  # Fail closed; caller may retain count-only receipt

if __name__=="__main__":
    main()
