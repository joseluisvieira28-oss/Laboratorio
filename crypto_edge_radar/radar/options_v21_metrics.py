from __future__ import annotations

from typing import Any


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


def evaluate_options_v21_forward(store)->dict[str,Any]:
    signals=store.read_payloads("OPTIONS_V21_FORWARD_SIGNAL_DAY")
    resolutions=store.read_payloads("OPTIONS_V21_FORWARD_RESOLUTION")
    valid=[x for x in signals if (x.get("signal") or {}).get("valid")]
    directional=[x for x in valid if int((x.get("signal") or {}).get("position") or 0)!=0]
    base=[float(x["base_net_bps"]) for x in resolutions]
    stress=[float(x["stress_net_bps"]) for x in resolutions]
    return {
        "strategy_id":"OPTIONS-SPOTPERP-001-V2.1",
        "classification":"SHADOW_EVIDENCE_ACCUMULATING_NO_TIER1_GATE_FROZEN",
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
        "tier2_reference_2025":{
            "trades":363,
            "base10_net_mean_bps":5.0427663334042565,
            "base10_profit_factor":1.06915099179292,
            "stress20_net_mean_bps":-4.675937838259077,
            "stress20_profit_factor":0.940166394773683,
        },
        "tier1_gate_frozen":False,
        "micro_live_authorized":False,
        "live_capital_enabled":False,
    }
