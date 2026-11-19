#!/usr/bin/env python3
"""Inspect authorized Dune event-level CSV against frozen 36 windows; no PnL claims."""
import collections
import csv
import datetime as dt
import hashlib
import json
import pathlib
import sys

REQUIRED=("coin_id","observed_at","target_pool","block_time","tx_id",
          "trader_id","project_main_id","raw_leg_side","direct_pool_id_match")

def parsebool(v):
    return str(v).strip().lower() in ("true","t","1")

def row_time(value):
    return dt.datetime.fromisoformat(value.replace("Z","+00:00").replace(" ","T")).replace(
      tzinfo=dt.timezone.utc) if "+" not in value and not value.endswith("Z") else dt.datetime.fromisoformat(value.replace("Z","+00:00").replace(" ","T"))

def evaluate(rows,expected):
    expected_keys={(x["coin_id"],x["observed_at"]):x for x in expected}
    if len(expected_keys)!=len(expected):
        raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: duplicate frozen time/coin")
    matched=collections.defaultdict(list)
    unpooled=collections.Counter()
    invalid=collections.Counter()
    for r in rows:
        for k in REQUIRED:
            if k not in r:raise RuntimeError("SCHEMA_BLOCKED: missing "+k)
        when=str(r["observed_at"]).replace("T"," ")[:19]
        key=(r["coin_id"],when)
        if key not in expected_keys:
            invalid["unexpected_time_or_coin"]+=1
            continue
        if r["target_pool"]!=expected_keys[key]["pool"]:
            invalid["wrong_target_pool"]+=1
            continue
        if not r.get("tx_id") or not r.get("trader_id"):
            invalid["missing_tx_or_trader"]+=1
            continue
        if not parsebool(r["direct_pool_id_match"]):
            unpooled[key]+=1
            continue
        t=row_time(r["block_time"])
        obs=row_time(when)
        delta=(obs-t).total_seconds()
        if not 0<delta<=3600:
            invalid["lookahead_or_wrong_window"]+=1
            continue
        if r["raw_leg_side"] not in ("BUY","SELL"):
            invalid["ambiguous_leg"]+=1
            continue
        matched[key].append(r)
    final=[]
    for x in expected:
        key=(x["coin_id"],x["observed_at"])
        legs=matched[key]
        tx=collections.defaultdict(set)
        traders=collections.defaultdict(set)
        for leg in legs:
            tx[leg["tx_id"]].add(leg["raw_leg_side"])
            traders[leg["tx_id"]].add(leg["trader_id"])
        ambiguous=sum(len(sides)!=1 or len(traders[t])!=1 for t,sides in tx.items())
        buys=sum(sides=={"BUY"} and len(traders[t])==1 for t,sides in tx.items())
        sells=sum(sides=={"SELL"} and len(traders[t])==1 for t,sides in tx.items())
        # A ZERO might mean no source coverage, no matching venue mapping, incomplete SQL output.
        # Never claim true negative from an absent row; require independent source proof.
        status="COVERAGE_UNVERIFIED"
        if legs:
            status="PRELIMINARY_FLOW_PASS" if buys+sells>=20 and buys>=sells else "PRELIMINARY_FLOW_REJECT"
        final.append(dict(coin_id=x["coin_id"],observed_at=x["observed_at"],
            price_policy=x["policy"],legs=len(legs),unmapped_other_pool_legs=unpooled[key],
            economic_tx_buy=buys,economic_tx_sell=sells,ambiguous_tx=ambiguous,
            status=status,full_MEME006_historical_gate="UNKNOWN_OTHER_HISTORICAL_GATES"))
    return dict(candidate_count=len(final),status_counts=dict(collections.Counter(x["status"] for x in final)),
                invalid=dict(invalid),windows=final,
                financial_edge="NO_GO: CSV flow alone lacks historical execution/quality gates")

def main():
    manifest=json.loads(pathlib.Path(sys.argv[1]).read_text())
    expected=json.loads(pathlib.Path(sys.argv[2]).read_text())
    if hashlib.sha256(pathlib.Path(sys.argv[2]).read_bytes()).hexdigest()!=manifest["rows_sha256"]:
        raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: frozen windows")
    with open(sys.argv[3],newline="",encoding="utf8") as f:
        items=list(csv.DictReader(f))
    result=evaluate(items,expected)
    result["csv_sha256"]=hashlib.sha256(pathlib.Path(sys.argv[3]).read_bytes()).hexdigest()
    result["csv_rows"]=len(items)
    print(json.dumps(result,sort_keys=True,indent=2))
if __name__=="__main__":main()
