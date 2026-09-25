from __future__ import annotations

import argparse,hashlib,json,math
from pathlib import Path
from typing import Any

POLICY="TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24"

class AuthorityBuildError(RuntimeError): pass

def _load(p:str|Path)->dict[str,Any]:
    out=json.loads(Path(p).read_text(encoding="utf-8"))
    if not isinstance(out,dict): raise AuthorityBuildError(f"JSON object required: {p}")
    return out

def _id(prefix:str,key:str)->str:
    return prefix+"-"+hashlib.sha256(key.encode()).hexdigest()[:20]

def _base_checks(signal:dict[str,Any])->None:
    if signal.get("strategy_id")!="OPTIONS-SPOTPERP-001-V2.1": raise AuthorityBuildError("SIGNAL_STRATEGY_MISMATCH")
    if signal.get("canonical") is not True or signal.get("source_healthy") is not True or signal.get("radar_motor_healthy") is not True:
        raise AuthorityBuildError("SIGNAL_NOT_EXECUTION_CANONICAL_HEALTHY")
    if signal.get("information_safe_time_passed") is not True: raise AuthorityBuildError("INFORMATION_SAFE_TIME_NOT_PASSED")
    if float(signal.get("materialization_latency_seconds",999))>30: raise AuthorityBuildError("SIGNAL_TOO_LATE_NO_CHASE")

def build_long(*,template:dict[str,Any],signal:dict[str,Any],spot_preflight:dict[str,Any])->dict[str,Any]:
    _base_checks(signal)
    if signal.get("signal_direction")!="LONG": raise AuthorityBuildError("SIGNAL_NOT_LONG")
    if template.get("status")!="TEMPLATE_NOT_AUTHORITY" or template.get("policy_id")!=POLICY: raise AuthorityBuildError("LONG_TEMPLATE_INVALID")
    if spot_preflight.get("pass") is not True: raise AuthorityBuildError("SPOT_PREFLIGHT_NOT_PASS")
    cand=((spot_preflight.get("candidate_feasibility") or {}).get("OPTIONS-SPOTPERP-001-V2.1-LONG") or {})
    if cand.get("pass") is not True: raise AuthorityBuildError("SPOT_CANDIDATE_FEASIBILITY_NOT_PASS")
    key=str(signal["immutable_signal_key"])
    out=dict(template)
    out.update({
        "status":"ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY",
        "signal_identity":key,
        "entry_target_utc":signal["entry_target_utc"],
        "exit_target_utc":signal["exit_target_utc"],
        "client_order_id":_id("optl",key),
        "duplicate_protection_key":"OPTIONS_V21_LONG:"+key,
        "authority_instance_sha256":None
    })
    canonical=dict(out); canonical.pop("authority_instance_sha256",None)
    out["authority_instance_sha256"]=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return out

def build_short(*,template:dict[str,Any],signal:dict[str,Any],futures_preflight:dict[str,Any])->dict[str,Any]:
    _base_checks(signal)
    if signal.get("signal_direction")!="SHORT": raise AuthorityBuildError("SIGNAL_NOT_SHORT")
    if template.get("status")!="TEMPLATE_NOT_AUTHORITY" or template.get("policy_id")!=POLICY: raise AuthorityBuildError("SHORT_TEMPLATE_INVALID")
    if futures_preflight.get("pass") is not True: raise AuthorityBuildError("FUTURES_PREFLIGHT_NOT_PASS")
    checks=futures_preflight.get("checks") or {}; contract=checks.get("contract") or {}; fees=checks.get("fees") or {}; funding=checks.get("funding") or {}
    min_vol=float(contract.get("min_contract_volume"))
    step=float(contract.get("contract_volume_step"))
    if min_vol<=0 or step<=0: raise AuthorityBuildError("FUTURES_CONTRACT_VOLUME_INVALID")
    volume=int(math.ceil(min_vol))
    if abs((volume-min_vol)/step-round((volume-min_vol)/step))>1e-9: raise AuthorityBuildError("FUTURES_MIN_VOLUME_NOT_INTEGER_STEP_COMPATIBLE")
    reference=float(contract.get("reference_price"))
    notional=volume*float(contract.get("contract_size_base"))*reference
    if notional>10.0+1e-12: raise AuthorityBuildError("FUTURES_VENUE_MINIMUM_ABOVE_10_USDT_CAP")
    taker=float(fees.get("effective_taker_fee_bps_for_execution_model"))
    rate=abs(float(funding.get("funding_rate",0) or 0))*10000.0
    cycle=float(funding.get("collect_cycle_hours",8) or 8)
    settlements=max(1,int(math.ceil(24.0/cycle)))
    projected=2.0*taker+rate*settlements
    if projected>20.0: raise AuthorityBuildError("FUTURES_PROJECTED_FRICTION_ABOVE_STRESS20")
    key=str(signal["immutable_signal_key"])
    out=dict(template)
    out.update({
        "status":"ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY",
        "signal_identity":key,
        "entry_target_utc":signal["entry_target_utc"],
        "exit_target_utc":signal["exit_target_utc"],
        "volume_contracts":volume,
        "external_oid":_id("opts",key),
        "duplicate_protection_key":"OPTIONS_V21_SHORT:"+key,
        "reference_entry_price":reference,
        "projected_round_trip_bps":projected,
        "implementation_mapping_review_status":"ACCEPTED_PRE_ORDER",
        "authority_instance_sha256":None
    })
    canonical=dict(out); canonical.pop("authority_instance_sha256",None)
    out["authority_instance_sha256"]=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return out

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--signal",required=True)
    ap.add_argument("--long-template",default="OPTIONS_SPOTPERP_001_V21_MICROLIVE_LONG_SPOT_AUTHORITY_TEMPLATE_V0.3.json")
    ap.add_argument("--short-template",default="OPTIONS_SPOTPERP_001_V21_MICROLIVE_SHORT_AUTHORITY_TEMPLATE_V0.3.json")
    ap.add_argument("--spot-preflight",default="mexc_spot_preflight_receipt.json")
    ap.add_argument("--futures-preflight",default="mexc_authenticated_preflight_receipt.json")
    ap.add_argument("--out",default="options_v21_active_micro_live_authority.json")
    args=ap.parse_args()
    try:
        signal=_load(args.signal); direction=str(signal.get("signal_direction"))
        if direction=="LONG":
            authority=build_long(template=_load(args.long_template),signal=signal,spot_preflight=_load(args.spot_preflight))
        elif direction=="SHORT":
            authority=build_short(template=_load(args.short_template),signal=signal,futures_preflight=_load(args.futures_preflight))
        else:
            raise AuthorityBuildError("SIGNAL_FLAT_OR_UNKNOWN")
    except Exception as exc:
        print(json.dumps({"status":"FAIL_CLOSED","blocker":f"{type(exc).__name__}:{exc}"},indent=2)); return 2
    Path(args.out).write_text(json.dumps(authority,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"ACTIVE_AUTHORITY_BUILT_NOT_EXECUTED","direction":direction,"authority_sha256":authority["authority_instance_sha256"],"out":str(Path(args.out).resolve())},indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())
