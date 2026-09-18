from __future__ import annotations

from typing import Any

OPERATIONAL_MIN_RESOLVED = 10
TIER1_MIN_RESOLVED = 50
TIER1_BLOCK_SIZE = 10
TIER1_MIN_NONNEGATIVE_BLOCKS = 3
TIER1_MAX_POSITIVE_TRADE_SHARE = 0.40


def _pf(values:list[float])->float|None:
    pos=sum(x for x in values if x>0)
    neg=-sum(x for x in values if x<0)
    if neg==0:
        return None if pos==0 else float("inf")
    return pos/neg


def _dd(values:list[float])->float:
    eq=peak=0.0
    worst=0.0
    for x in values:
        eq+=x
        peak=max(peak,eq)
        worst=min(worst,eq-peak)
    return worst


def _key(payload:dict[str,Any])->str:
    value=payload.get("event_key")
    return value if isinstance(value,str) else ""


def _positive_concentration(values:list[float])->float|None:
    positives=[x for x in values if x>0]
    total=sum(positives)
    if total<=0:
        return None
    return max(positives)/total


def evaluate_options_v21_forward(store)->dict[str,Any]:
    signals=store.read_payloads("OPTIONS_V21_FORWARD_SIGNAL_DAY")
    resolutions=store.read_payloads("OPTIONS_V21_FORWARD_RESOLUTION")

    valid=[x for x in signals if (x.get("signal") or {}).get("valid")]
    directional=[x for x in valid if int((x.get("signal") or {}).get("position") or 0)!=0]

    signal_keys=[_key(x) for x in signals]
    directional_keys={_key(x) for x in directional if _key(x)}
    resolution_keys=[_key(x) for x in resolutions]

    duplicate_signal_keys=len(signal_keys)-len(set(signal_keys))
    duplicate_resolution_keys=len(resolution_keys)-len(set(resolution_keys))
    resolution_without_directional_signal=sum(
        1 for key in resolution_keys if not key or key not in directional_keys
    )

    ordered_resolutions=sorted(
        resolutions,
        key=lambda x:(str(x.get("signal_date") or ""), _key(x)),
    )
    base=[float(x["base_net_bps"]) for x in ordered_resolutions]
    stress=[float(x["stress_net_bps"]) for x in ordered_resolutions]

    integrity_pass=(
        duplicate_signal_keys==0
        and duplicate_resolution_keys==0
        and resolution_without_directional_signal==0
    )
    operational_ready=len(resolutions)>=OPERATIONAL_MIN_RESOLVED and integrity_pass

    first50=ordered_resolutions[:TIER1_MIN_RESOLVED]
    first50_base=[float(x["base_net_bps"]) for x in first50]
    first50_stress=[float(x["stress_net_bps"]) for x in first50]
    first50_pf=_pf(first50_base)
    first50_mean=(sum(first50_base)/len(first50_base)) if first50_base else None
    blocks=[
        first50_base[i:i+TIER1_BLOCK_SIZE]
        for i in range(0,len(first50_base),TIER1_BLOCK_SIZE)
        if len(first50_base[i:i+TIER1_BLOCK_SIZE])==TIER1_BLOCK_SIZE
    ]
    block_means=[sum(x)/len(x) for x in blocks]
    nonnegative_blocks=sum(x>=0 for x in block_means)
    concentration=_positive_concentration(first50_base)

    tier1_window_locked=len(first50)==TIER1_MIN_RESOLVED
    tier1_base_mean_pass=first50_mean is not None and first50_mean>0
    tier1_pf_pass=first50_pf is not None and first50_pf>1
    tier1_temporal_pass=(
        len(blocks)==5 and nonnegative_blocks>=TIER1_MIN_NONNEGATIVE_BLOCKS
    )
    tier1_concentration_pass=(
        concentration is not None and concentration<=TIER1_MAX_POSITIVE_TRADE_SHARE
    )
    tier1_statistical_pass=(
        tier1_window_locked
        and integrity_pass
        and tier1_base_mean_pass
        and tier1_pf_pass
        and tier1_temporal_pass
        and tier1_concentration_pass
    )

    if not tier1_window_locked:
        classification="FORWARD_EVIDENCE_ACCUMULATING_TIER1_GATE_FROZEN"
    elif tier1_statistical_pass:
        classification="TIER1_FORWARD_EVIDENCE_STATISTICALLY_PASS__OPERATIONAL_AND_EXECUTION_AUDIT_REQUIRED"
    else:
        classification="TIER1_FORWARD_EVIDENCE_FAIL__NO_RESCUE_UNDER_THIS_GATE"

    return {
        "strategy_id":"OPTIONS-SPOTPERP-001-V2.1",
        "classification":classification,
        "signal_days_observed":len(signals),
        "valid_signal_days":len(valid),
        "directional_signal_days":len(directional),
        "resolved_forward_trades":len(resolutions),
        "base_net_mean_bps":sum(base)/len(base) if base else None,
        "base_profit_factor":_pf(base),
        "base_total_bps":sum(base),
        "base_max_additive_drawdown_bps":_dd(base),
        "stress_net_mean_bps":sum(stress)/len(stress) if stress else None,
        "stress_profit_factor":_pf(stress),
        "stress_total_bps":sum(stress),
        "integrity":{
            "duplicate_signal_keys":duplicate_signal_keys,
            "duplicate_resolution_keys":duplicate_resolution_keys,
            "resolution_without_directional_signal":resolution_without_directional_signal,
            "pass":integrity_pass,
        },
        "operational_shadow_readiness":{
            "minimum_resolved_forward_trades":OPERATIONAL_MIN_RESOLVED,
            "sample_ready":operational_ready,
            "automatic_micro_live_authorization":False,
        },
        "tier1_forward_gate":{
            "authority":"OPTIONS_SPOTPERP_001_V21_FORWARD_EVIDENCE_GATE_V0.1.json",
            "minimum_resolved_forward_trades":TIER1_MIN_RESOLVED,
            "first_50_window_locked":tier1_window_locked,
            "evaluated_trade_count":len(first50),
            "base10_mean_bps":first50_mean,
            "base10_profit_factor":first50_pf,
            "five_consecutive_10_trade_block_means_bps":block_means,
            "nonnegative_blocks":nonnegative_blocks,
            "minimum_nonnegative_blocks":TIER1_MIN_NONNEGATIVE_BLOCKS,
            "largest_single_positive_base10_trade_share":concentration,
            "maximum_positive_trade_share":TIER1_MAX_POSITIVE_TRADE_SHARE,
            "stress20_mean_bps":sum(first50_stress)/len(first50_stress) if first50_stress else None,
            "stress20_profit_factor":_pf(first50_stress),
            "stress20_is_fragility_diagnostic_not_automatic_veto":True,
            "statistical_gate_pass":tier1_statistical_pass,
            "automatic_tier1_promotion":False,
            "operational_and_execution_audit_still_required":True,
        },
        "tier2_reference_2025":{
            "trades":363,
            "base10_net_mean_bps":5.0427663334042565,
            "base10_profit_factor":1.06915099179292,
            "stress20_net_mean_bps":-4.675937838259077,
            "stress20_profit_factor":0.940166394773683,
        },
        "tier1_gate_frozen":True,
        "micro_live_authorized":False,
        "live_capital_enabled":False,
    }
