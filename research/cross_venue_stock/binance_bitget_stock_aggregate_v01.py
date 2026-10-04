#!/usr/bin/env python3
"""Aggregate 68 frozen Binance<->Bitget asset-route tests and apply Holm + costs."""
from __future__ import annotations
import json,hashlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
RULE=json.loads((HERE/"BINANCE_BITGET_STOCK_RULE_V0.1.json").read_text())
BIND=json.loads((HERE/"BINANCE_BITGET_STOCK_SOURCE_BINDING_V0.1.json").read_text())
IN=Path("artifacts/cross_venue_stock/binance_bitget_v01/assets")
OUT=Path("artifacts/cross_venue_stock/binance_bitget_v01")

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prereq(r):
    g=RULE["scientific_gate"]
    return bool(r and r["n"]>=g["min_n"] and
      r["distinct_signal_sessions"]>=g["min_distinct_signal_sessions"] and
      r["mean_gross_signed_bps"] is not None and r["mean_gross_signed_bps"]>0 and
      r["median_gross_signed_bps"] is not None and r["median_gross_signed_bps"]>0 and
      r["win_rate"] is not None and r["win_rate"]>g["win_rate_gt"] and
      all(x is not None and x>0 for x in r["chronological_third_means_bps"]))

def main():
    expected=set(BIND["candidates"])
    receipts=[json.loads(p.read_text()) for p in IN.glob("*.json")]
    got={x["symbol"] for x in receipts}
    if got!=expected:
        raise SystemExit(f"FAIL_CLOSED_RECEIPT_SET_MISMATCH missing={sorted(expected-got)} extra={sorted(got-expected)}")
    tests=[]
    route_map={x["route_id"]:x for x in RULE["routes"]}
    for rec in receipts:
        for route_id in BIND["target_routes"]:
            r=rec.get("routes",{}).get(route_id)
            tests.append({
              "symbol":rec["symbol"],"route_id":route_id,"source_complete":rec["source_complete"],
              "result":r,"pre_holm_eligible":bool(rec["source_complete"] and prereq(r))
            })
    if len(tests)!=68:raise SystemExit(f"FAIL_CLOSED_TEST_COUNT_{len(tests)}")
    ordered=sorted(tests,key=lambda x:(x["result"]["p_value_one_sided_binomial_vs_50"] if x.get("result") else 1.0))
    alpha=RULE["scientific_gate"]["family_wise_alpha"];m=len(ordered);still=True
    for rank,x in enumerate(ordered,1):
        cutoff=alpha/(m-rank+1)
        p=x["result"]["p_value_one_sided_binomial_vs_50"] if x.get("result") else 1.0
        reject=bool(still and p is not None and p<=cutoff)
        x["holm_rank"]=rank;x["holm_cutoff"]=cutoff;x["holm_reject"]=reject
        if not reject:still=False
    for x in tests:
        x["scientific_pass"]=bool(x["pre_holm_eligible"] and x["holm_reject"])
        fees=route_map[x["route_id"]]["roundtrip_fee_bps"]
        r=x.get("result")
        if r:
            x["mean_net_bps"]={k:r["mean_gross_signed_bps"]-v for k,v in fees.items()}
        else:x["mean_net_bps"]={k:None for k in fees}
        x["maker_only_candidate"]=bool(x["scientific_pass"] and x["mean_net_bps"]["maker_maker"]>0)
        x["hybrid_execution_candidate"]=bool(x["scientific_pass"] and x["mean_net_bps"]["maker_taker"]>0)
        x["immediate_execution_candidate"]=bool(x["scientific_pass"] and x["mean_net_bps"]["taker_taker"]>0)
        if not x["source_complete"]:v="SOURCE_BLOCKED"
        elif not x["scientific_pass"]:v="NO_SCIENTIFIC_SURVIVOR"
        elif x["immediate_execution_candidate"]:v="SCIENTIFIC_AND_TAKER_TAKER_FEE_SURVIVOR"
        elif x["hybrid_execution_candidate"]:v="SCIENTIFIC_AND_HYBRID_FEE_SURVIVOR"
        elif x["maker_only_candidate"]:v="SCIENTIFIC_AND_MAKER_ONLY_FEE_SURVIVOR"
        else:v="SCIENTIFIC_SURVIVOR__FEE_BLOCKED"
        x["verdict"]=v
    sci=[x for x in tests if x["scientific_pass"]]
    maker=[x for x in tests if x["maker_only_candidate"]]
    hybrid=[x for x in tests if x["hybrid_execution_candidate"]]
    immediate=[x for x in tests if x["immediate_execution_candidate"]]
    if immediate:overall="IMMEDIATE_EXECUTION_FEE_SURVIVORS_FOUND__MICROSTRUCTURE_REQUIRED"
    elif hybrid:overall="HYBRID_EXECUTION_FEE_SURVIVORS_FOUND__FILL_MODEL_REQUIRED"
    elif maker:overall="MAKER_ONLY_FEE_SURVIVORS_FOUND__FILL_MODEL_REQUIRED"
    elif sci:overall="SCIENTIFIC_SURVIVORS_FOUND__ALL_FEE_BLOCKED"
    else:overall="NO_CROSS_VENUE_SURVIVOR_AT_FROZEN_V01_GATE"
    def slim(x):
        r=x["result"]
        return {"symbol":x["symbol"],"route_id":x["route_id"],"n":r["n"],"wins":r["wins"],
          "win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_signed_bps"],
          "median_bps":r["median_gross_signed_bps"],"thirds":r["chronological_third_means_bps"],
          "p":r["p_value_one_sided_binomial_vs_50"],"holm_cutoff":x["holm_cutoff"],
          "scientific_pass":x["scientific_pass"],"mean_net_bps":x["mean_net_bps"],"verdict":x["verdict"]}
    top=sorted([x for x in tests if x.get("result")],key=lambda x:x["result"]["mean_gross_signed_bps"],reverse=True)
    report={"family_id":RULE["family_id"],"test_count":len(tests),
      "rule_sha256":sha(HERE/"BINANCE_BITGET_STOCK_RULE_V0.1.json"),
      "binding_sha256":sha(HERE/"BINANCE_BITGET_STOCK_SOURCE_BINDING_V0.1.json"),
      "scientific_pass_count":len(sci),"maker_only_candidate_count":len(maker),
      "hybrid_execution_candidate_count":len(hybrid),"immediate_execution_candidate_count":len(immediate),
      "overall_verdict":overall,"tests":tests,
      "no_post_outcome_rescue":True,"private_endpoints_used":False,"account_reads":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"BINANCE_BITGET_STOCK_CLOSEOUT_V01.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps({"overall_verdict":overall,
      "scientific_pass_count":len(sci),
      "maker_only_candidate_count":len(maker),
      "hybrid_execution_candidate_count":len(hybrid),
      "immediate_execution_candidate_count":len(immediate),
      "immediate_execution_candidates":[slim(x) for x in immediate],
      "hybrid_execution_candidates":[slim(x) for x in hybrid],
      "maker_only_candidates":[slim(x) for x in maker],
      "top_12_by_gross":[slim(x) for x in top[:12]]},indent=2))

if __name__=="__main__":main()
