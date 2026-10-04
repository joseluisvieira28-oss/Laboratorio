#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
RULE=json.loads((HERE/"BITGET_MAKER_MICROSTRUCTURE_RULE_V0.2.json").read_text())
BIND=json.loads((HERE/"BITGET_MAKER_MICROSTRUCTURE_SOURCE_BINDING_V0.2.json").read_text())
IN=Path("artifacts/cross_venue_stock/bitget_maker_v02/assets")
OUT=Path("artifacts/cross_venue_stock/bitget_maker_v02")

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    receipts=[json.loads(p.read_text()) for p in IN.glob("*.json")]
    expected=set(BIND["candidates"]);got={x["symbol"] for x in receipts}
    if got!=expected:
        raise SystemExit(f"FAIL_CLOSED_RECEIPT_SET_MISMATCH missing={sorted(expected-got)} extra={sorted(got-expected)}")
    ordered=sorted(receipts,key=lambda x:x["result"]["p_value_one_sided_binomial_vs_50"] if x["result"]["p_value_one_sided_binomial_vs_50"] is not None else 1.0)
    alpha=RULE["execution_gate"]["family_wise_alpha"];m=len(ordered);still=True
    for rank,x in enumerate(ordered,1):
        p=x["result"]["p_value_one_sided_binomial_vs_50"]
        cutoff=alpha/(m-rank+1)
        reject=bool(still and p is not None and p<=cutoff)
        x["holm_rank"]=rank;x["holm_cutoff"]=cutoff;x["holm_reject"]=reject
        if not reject:still=False
    survivors=[]
    for x in receipts:
        x["execution_pass"]=bool(x["pre_holm_eligible"] and x["holm_reject"])
        if x["execution_pass"]:
            x["verdict"]="MAKER_EXECUTION_FEASIBILITY_SURVIVOR__FORWARD_VALIDATION_REQUIRED"
            survivors.append(x)
        elif x["result"]["entered_positions_with_data_failure"]>0 or x["result"]["placement_observability"]<RULE["execution_gate"]["min_parent_signal_quote_observability"]:
            x["verdict"]="MICROSTRUCTURE_DATA_BLOCKED"
        else:
            x["verdict"]="MAKER_EXECUTION_FEASIBILITY_FAIL"
    overall=("MAKER_EXECUTION_FEASIBILITY_SURVIVORS_FOUND__FORWARD_VALIDATION_REQUIRED"
             if survivors else
             "NO_MAKER_EXECUTION_SURVIVOR_AT_FROZEN_V02_GATE")
    def slim(x):
        r=x["result"]
        return {"symbol":x["symbol"],"verdict":x["verdict"],"execution_pass":x["execution_pass"],
          "signals":r["parent_signal_count"],"observability":r["placement_observability"],
          "entries":r["entered_positions"],"entry_fill_rate":r["entry_fill_rate"],
          "closed":r["closed_positions"],"maker_exits":r["maker_exit_count"],
          "forced_taker_exits":r["forced_taker_exit_count"],
          "maker_exit_rate":r["maker_exit_rate_among_closed"],
          "mean_net_bps":r["mean_realized_net_bps"],"median_net_bps":r["median_realized_net_bps"],
          "win_rate":r["win_rate"],"thirds":r["chronological_third_mean_net_bps"],
          "p":r["p_value_one_sided_binomial_vs_50"],"holm_cutoff":x["holm_cutoff"],
          "per_parent_signal_bps":r["mean_net_bps_per_parent_signal_with_unfilled_zero"]}
    report={"family_id":RULE["family_id"],"candidate_count":len(receipts),
      "rule_sha256":sha(HERE/"BITGET_MAKER_MICROSTRUCTURE_RULE_V0.2.json"),
      "binding_sha256":sha(HERE/"BITGET_MAKER_MICROSTRUCTURE_SOURCE_BINDING_V0.2.json"),
      "survivor_count":len(survivors),"overall_verdict":overall,
      "survivors":[slim(x) for x in survivors],
      "results":[slim(x) for x in sorted(receipts,key=lambda z:z["symbol"])],
      "conditional_execution_test_not_independent_oos":True,
      "no_post_outcome_tuning":True,"private_endpoints_used":False,"account_reads":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"BITGET_MAKER_MICROSTRUCTURE_CLOSEOUT_V02.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
