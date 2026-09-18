#!/usr/bin/env python3
"""Build canonical AAVE R1 audit receipt V0.2E from immutable V0.2A + V0.2D."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path

EXPECTED=77
RUN_A=35375172202
ART_A=10560482339
DIGEST_A="sha256:172012d26dc6d4a6f0ea2a534f039f6ce2f73c2361e7975414067c25d6686f9b"
RUN_B=35378340649
ART_B=10561865078
DIGEST_B="sha256:50b97f308e5f200f1d469d7e1d09757948f77ae7318dc30af90427d0b317d4ee"

def exactly_one(root:str,name:str)->dict:
    fs=list(Path(root).rglob(name))
    if len(fs)!=1:
        raise RuntimeError(f"expected exactly one {name}, found {len(fs)}")
    return json.loads(fs[0].read_text(encoding="utf-8"))

def target_digest(targets:list[dict])->str:
    return hashlib.sha256(
        "\n".join(
            f"{t['block']}|{t['user']}|{t['token']}|{t['replayed_scaled_balance']}"
            for t in targets
        ).encode()
    ).hexdigest()

def main()->int:
    outdir=Path("r1_v02e_output"); outdir.mkdir(parents=True,exist_ok=True)
    path=outdir/"AAVE_LIQUIDATION_OVERHANG_001_R1_AUDIT_CANONICAL_V0_2E.json"
    out={
      "classification":"RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE",
      "failure":"uninitialized",
      "safety":{
        "health_factor_computed":False,"overhang_computed":False,
        "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
        "accessed_2025_or_2026_market_outcomes":False,
        "live_trading":False,"exchange_mutation":False,
      }
    }
    try:
        a=exactly_one("downloaded_v02a","AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_2A.json")
        b=exactly_one("downloaded_v02d","AAVE_LIQUIDATION_OVERHANG_001_R1_TARGET_VALIDATION_V0_2D.json")
        targets=a.get("validation_targets")
        failures=a.get("validation_failures")
        if a.get("classification")!="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE":
            raise RuntimeError("V0.2A classification mismatch")
        if not isinstance(targets,list) or len(targets)!=EXPECTED:
            raise RuntimeError("V0.2A target count mismatch")
        if int(a.get("validation_target_count",-1))!=EXPECTED:
            raise RuntimeError("V0.2A validation_target_count mismatch")
        if int(a.get("validation_failure_count",-1))!=EXPECTED:
            raise RuntimeError("V0.2A validation_failure_count mismatch")
        if not isinstance(failures,list) or len(failures)!=EXPECTED:
            raise RuntimeError("V0.2A failure rows incomplete")
        if any(x.get("failure")!="INSUFFICIENT_ARCHIVE_RPC_QUORUM" for x in failures):
            raise RuntimeError("V0.2A contains non-quorum failure")
        digest=target_digest(targets)
        if digest!=a.get("target_digest_sha256"):
            raise RuntimeError("V0.2A target digest mismatch")

        if b.get("classification")!="R1_AUDIT_PASS":
            raise RuntimeError("V0.2D is not R1_AUDIT_PASS")
        if int(b.get("validation_target_count",-1))!=EXPECTED:
            raise RuntimeError("V0.2D target count mismatch")
        if int(b.get("validated_target_count",-1))!=EXPECTED:
            raise RuntimeError("V0.2D validated target count mismatch")
        if int(b.get("validation_failure_count",-1))!=0:
            raise RuntimeError("V0.2D has target failures")
        if b.get("target_digest_sha256")!=digest:
            raise RuntimeError("V0.2D target digest mismatch")
        if int(b.get("quorum_required",-1))!=2:
            raise RuntimeError("V0.2D quorum changed")
        if int(b.get("provider_count",-1))!=3:
            raise RuntimeError("V0.2D provider count mismatch")

        out=copy.deepcopy(a)
        out["phase"]="R1_SCALED_LEDGER_AUDIT_CANONICAL_RECONCILED_V0_2E_OUTCOME_BLIND"
        out["classification"]="R1_AUDIT_PASS"
        out["failure"]=None
        out["validation_failures"]=[]
        out["validation_failure_count"]=0
        out["validated_target_count"]=EXPECTED
        out["archive_rpc_stats"]=copy.deepcopy(b.get("archive_rpc_stats") or {})
        out["canonical_reconciliation"]={
          "authority":"AAVE_LIQUIDATION_OVERHANG_001_R1_AUDIT_RECONCILIATION_V0_2E",
          "deterministic_corpus":{
            "run_id":RUN_A,"artifact_id":ART_A,"artifact_digest":DIGEST_A,
            "original_classification":a.get("classification"),
          },
          "target_validation":{
            "run_id":RUN_B,"artifact_id":ART_B,"artifact_digest":DIGEST_B,
            "classification":b.get("classification"),
            "provider_set":b.get("provider_set"),
            "quorum_required":b.get("quorum_required"),
          },
          "target_digest_sha256":digest,
          "borrower_census_recomputed":False,
          "delta_replay_recomputed":False,
          "targets_recomputed":False,
        }
        safety=out.get("safety") or {}
        forbidden=[
          "health_factor_computed","overhang_computed","future_liquidation_outcome_computed",
          "market_prices_opened","market_returns_opened","returns_opened","pnl_opened",
          "accessed_2025_or_2026","live_trading","exchange_mutation"
        ]
        if any(bool(safety.get(k)) for k in forbidden):
            raise RuntimeError("upstream safety flag violation")
    except Exception as exc:
        out={
          "lab_id":"AAVE-LIQUIDATION-OVERHANG-001",
          "phase":"R1_SCALED_LEDGER_AUDIT_CANONICAL_RECONCILED_V0_2E_OUTCOME_BLIND",
          "classification":"RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE",
          "failure":f"{type(exc).__name__}: {str(exc)[:1500]}",
          "safety":{
            "health_factor_computed":False,"overhang_computed":False,
            "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
            "accessed_2025_or_2026_market_outcomes":False,
            "live_trading":False,"exchange_mutation":False,
          },
        }
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "classification":out["classification"],
      "sample_size":len(out.get("sample_borrowers") or []),
      "validation_targets":out.get("validation_target_count"),
      "validated_targets":out.get("validated_target_count"),
      "validation_failures":out.get("validation_failure_count"),
      "target_digest_sha256":out.get("target_digest_sha256"),
      "health_factor_computed":False,"overhang_computed":False,
      "returns_opened":False,"pnl_opened":False,
    },sort_keys=True))
    return 0 if out["classification"]=="R1_AUDIT_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
