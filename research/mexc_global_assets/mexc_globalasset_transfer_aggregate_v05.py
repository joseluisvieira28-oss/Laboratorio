#!/usr/bin/env python3
"""Aggregate all 35 frozen V0.5 asset receipts, apply gates and Holm."""
from __future__ import annotations
import json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
RULE=json.loads((HERE/"MEXC_GLOBALASSET_TRANSFER_RULE_V0.5.json").read_text())
BIND=json.loads((HERE/"MEXC_GLOBALASSET_TRANSFER_SOURCE_BINDING_V0.5.json").read_text())
IN=Path("artifacts/mexc_global_assets/globalasset_transfer_v05/assets")
OUT=Path("artifacts/mexc_global_assets/globalasset_transfer_v05")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def eligible(x):
    r=x.get("result");g=RULE["scientific_gate"]
    return bool(x.get("source_complete") and r and r["n"]>=g["min_n"] and
      r["distinct_signal_sessions"]>=g["min_distinct_signal_sessions"] and
      r["mean_gross_signed_bps"]>0 and r["median_gross_signed_bps"]>0 and
      r["win_rate"]>g["win_rate_gt"] and all(v is not None and v>0 for v in r["chronological_third_means_bps"]))
def main():
    expected={x["target"] for x in BIND["candidates"]}
    files=list(IN.glob("*.json"));receipts=[json.loads(p.read_text()) for p in files]
    got={x["target"] for x in receipts}
    if got!=expected:raise SystemExit(f"FAIL_CLOSED_RECEIPT_SET_MISMATCH missing={sorted(expected-got)} extra={sorted(got-expected)}")
    for x in receipts:x["pre_holm_eligible"]=eligible(x)
    ordered=sorted(receipts,key=lambda x:(x["result"]["p_value_one_sided_binomial_vs_50"] if x.get("result") else 1.0))
    alpha=RULE["scientific_gate"]["family_wise_alpha"];m=len(ordered);still=True
    for rank,x in enumerate(ordered,1):
        cutoff=alpha/(m-rank+1);p=x["result"]["p_value_one_sided_binomial_vs_50"] if x.get("result") else 1.0
        x["holm_rank"]=rank;x["holm_cutoff"]=cutoff
        x["holm_reject"]=bool(still and p is not None and p<=cutoff)
        if not x["holm_reject"]:still=False
    for x in receipts:
        x["scientific_pass"]=bool(x["pre_holm_eligible"] and x["holm_reject"])
        r=x.get("result")
        x["fee_floor_survivor_12bps"]=bool(x["scientific_pass"] and r["mean_net_bps"]["12"]>0)
        x["robust_fee_survivor_16bps"]=bool(x["scientific_pass"] and r["mean_net_bps"]["16"]>0)
        if not x["source_complete"]:v="SOURCE_BLOCKED_HISTORICAL_COVERAGE"
        elif not x["scientific_pass"]:v="NO_SCIENTIFIC_TRANSFER_SURVIVOR"
        elif x["robust_fee_survivor_16bps"]:v="SCIENTIFIC_AND_ROBUST_API_FEE_SURVIVOR"
        elif x["fee_floor_survivor_12bps"]:v="SCIENTIFIC_AND_MAKER_MAKER_FEE_SURVIVOR_ONLY"
        else:v="SCIENTIFIC_SURVIVOR__STANDARD_MEXC_API_FEE_BLOCKED"
        x["verdict"]=v
    robust=[x for x in receipts if x["robust_fee_survivor_16bps"]]
    floor=[x for x in receipts if x["fee_floor_survivor_12bps"]]
    sci=[x for x in receipts if x["scientific_pass"]]
    if robust:overall="ROBUST_API_FEE_SURVIVORS_FOUND__MICROSTRUCTURE_REQUIRED"
    elif floor:overall="MAKER_MAKER_FEE_SURVIVORS_FOUND__FILL_RISK_UNPROVEN"
    elif sci:overall="SCIENTIFIC_TRANSFER_SURVIVORS_FOUND__STANDARD_API_FEE_BLOCKED"
    else:overall="NO_GLOBALASSET_TRANSFER_SURVIVOR_AT_FROZEN_V05_GATE"
    report={"family_id":RULE["family_id"],"candidate_count":len(receipts),
      "rule_sha256":sha(HERE/"MEXC_GLOBALASSET_TRANSFER_RULE_V0.5.json"),
      "binding_sha256":sha(HERE/"MEXC_GLOBALASSET_TRANSFER_SOURCE_BINDING_V0.5.json"),
      "scientific_pass_count":len(sci),"fee_floor_survivor_count":len(floor),
      "robust_fee_survivor_count":len(robust),"overall_verdict":overall,
      "results":sorted(receipts,key=lambda x:x["target"]),"no_post_outcome_rescue":True,
      "private_endpoints_used":False,"account_reads":False,"orders":False,"exchange_mutation":False,
      "live_trading_authorized":False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_GLOBALASSET_TRANSFER_CLOSEOUT_V05.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    top=sorted([x for x in receipts if x.get("result")],key=lambda x:x["result"]["mean_gross_signed_bps"],reverse=True)
    def slim(x):
        r=x["result"];return {"target":x["target"],"n":r["n"],"wins":r["wins"],"win_rate":r["win_rate"],
          "mean_gross_bps":r["mean_gross_signed_bps"],"median_bps":r["median_gross_signed_bps"],
          "thirds":r["chronological_third_means_bps"],"p":r["p_value_one_sided_binomial_vs_50"],
          "holm_cutoff":x["holm_cutoff"],"scientific_pass":x["scientific_pass"],
          "net12":r["mean_net_bps"]["12"],"net16":r["mean_net_bps"]["16"],"verdict":x["verdict"]}
    print(json.dumps({"overall_verdict":overall,"scientific_pass_count":len(sci),
      "fee_floor_survivor_count":len(floor),"robust_fee_survivor_count":len(robust),
      "robust_fee_survivors":[slim(x) for x in robust],
      "fee_floor_survivors":[slim(x) for x in floor],
      "top_12_by_gross":[slim(x) for x in top[:12]]},indent=2))
if __name__=="__main__":main()
