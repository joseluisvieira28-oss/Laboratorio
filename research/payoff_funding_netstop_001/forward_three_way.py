#!/usr/bin/env python3
"""Three-way synchronized prospective shadow only (no orders or accounts).

Input MUST be fully post-2026-10-14 UTC, verified by prior public-source
collector and independent strict forward boundary validator.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"payoff_failure_execution_forward"))
sys.path.insert(0,str(ROOT/"payoff_funding_netstop_001"))
import forward_boundary_gate as gate
from forward_child_replay import replay_forward_child

def compare(source):
    if source.get("source_mode")!="CHECKSUM_VERIFIED_DAILY_ARCHIVE_PLUS_PUBLIC_FUNDING_ENDPOINT":
        raise ValueError("SOURCE_PROVENANCE_NOT_CERTIFIED")
    if source.get("trading_authority")!="NONE":
        raise ValueError("TRADING_AUTHORITY_MUST_BE_NONE")
    if not source.get("manifests") or not source.get("funding_manifests"):
        raise ValueError("ARCHIVE_OR_FUNDING_RECEIPTS_MISSING")
    # The existing paired engine uses exactly the same bars and economics.
    parent_and_payoff=gate.run(source)  # fail closed on 200h post-boundary warmup
    bars,marks,funds,end=gate.validate(source)
    begin=gate.BOUNDARY+gate.WARMUP
    output={"classification":"PROSPECTIVE_RESEARCH_ONLY_NOT_A_PROMOTION",
            "live_trading_authority":"NONE",
            "first_eligible_forward_boundary_utc":"2026-10-14T00:00:00Z",
            "200_post_boundary_warmup_hours":200,
            "last_closed_bar_open_ms":end,
            "source_manifest_sha256":hashlib.sha256(json.dumps(
                source["manifests"],sort_keys=True).encode()).hexdigest(),
            "funding_manifest_sha256":hashlib.sha256(json.dumps(
                source["funding_manifests"],sort_keys=True).encode()).hexdigest(),
            "source_independent_confirmation":"NOT_YET_REVIEWED",
            "unknowns":["historical venue min_notional/tick/maintenance",
                        "real bid-ask liquidity and actual fill prices",
                        "real adverse slippage and stop gaps",
                        "mark-based liquidation and private account status",
                        "independent forward statistical sample"],
            "scenarios":{}}
    for name,(fee,slip) in gate.engine.CONFIGS.items():
        pair=parent_and_payoff["results"][name]
        child=replay_forward_child(bars,funds,marks,fee,slip,begin,end)
        output["scenarios"][name]={
            "PARENT":pair["PARENT"],
            "PAYOFF_4R":pair["PAYOFF"],
            "NETSTOP_CHILD":child}
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    raw=a.source.read_bytes()
    source=json.loads(raw)
    result=compare(source)
    result["source_payload_sha256"]=hashlib.sha256(raw).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for name,models in result["scenarios"].items():
        print("FORWARD_SHADOW",name,json.dumps({
            model:{"n":entry.get("trades_closed",entry.get("closed")),
                   "equity_return":entry.get("closed_equity_return"),
                   "unresolved":len(entry.get("unresolved_at_cutoff",[]))}
            for model,entry in models.items()},sort_keys=True))
    print("NO_ORDERS / NO_LIVE_GO / PROSPECTIVE_READ_ONLY")

if __name__=="__main__":main()
