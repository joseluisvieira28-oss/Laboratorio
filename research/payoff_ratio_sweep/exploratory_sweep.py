#!/usr/bin/env python3
"""PAYOFF 2/3/4/5R frozen *exploratory* sweep. No orders, no 2026, no tuning.

Deliberately reuse the 4R causal replay as-is: the only injection is the exact
entry-anchored TARGET bound. The 4R outcome must reproduce the original receipt.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "payoff_40_10_btc_001"))
import engine as core  # verified original 4R causal engine

TARGETS = {"2R": .20, "3R": .30, "4R": .40, "5R": .50}
LEGACY_4R_RETURNS = {"BASE": .283296092471792, "STRESS": .26323957585754676}


def fixed_bounds(entry: float, target_margin: float):
    """Nominal fee-anchored target; exact same stop for every variant."""
    if not (entry > 0 and target_margin in TARGETS.values()):
        raise ValueError("NONFROZEN_HYPOTHESIS")
    f = core.NOMINAL_FEE
    l = core.LEV
    target = entry * (1 + (target_margin / l + 2*f) / (1-f))
    stop = entry * (1 + (-.10 / l + 2*f) / (1-f))
    return target, stop


def replay_ratio(bars, funding, marks, scenario_fee, scenario_slip, ratio):
    if ratio not in TARGETS:
        raise ValueError("UNAUTHORIZED_RATIO")
    original = core.nominal_bounds
    try:
        core.nominal_bounds = lambda entry: fixed_bounds(entry, TARGETS[ratio])
        result = core.replay(bars, funding, marks, "PAYOFF",
                             scenario_fee, scenario_slip)
    finally:
        core.nominal_bounds = original
    return result


def measures(x):
    ledger = x["trade_ledger"]
    winners = [t for t in ledger if t["net_pnl"] > 0]
    losses = [t for t in ledger if t["net_pnl"] < 0]
    profit = sum(t["net_pnl"] for t in winners)
    loss = -sum(t["net_pnl"] for t in losses)
    avw = sum(t["margin_net_return"] for t in winners)/len(winners) if winners else None
    avl = sum(t["margin_net_return"] for t in losses)/len(losses) if losses else None
    threshold = -avl/(avw-avl) if avw is not None and avl is not None and avw>avl else None
    top3 = sorted((t["net_pnl"] for t in winners),reverse=True)[:3]
    exit_counts = x["exit_counts"]
    return {
        "closed":x["trades_closed"], "wins":x["wins"], "losses":x["losses"],
        "unresolved":len(x["unresolved_at_cutoff"]),
        "win_rate":x["win_rate"], "closed_equity_return":x["closed_equity_return"],
        "closed_equity_max_dd":x["closed_equity_max_dd"],
        "approx_mtm_max_dd":x["approx_mtm_max_dd"],
        "profit_factor":x["profit_factor"],
        "exit_counts":exit_counts,
        "target_reached":sum(v for k,v in exit_counts.items() if k.startswith("TARGET")),
        "stop_reached":sum(v for k,v in exit_counts.items() if k.startswith("STOP") or k.startswith("AMBIGUOUS")),
        "time_exits":sum(v for k,v in exit_counts.items() if k.startswith("TIME")),
        "actual_avg_win_on_margin":avw, "actual_avg_loss_on_margin":avl,
        "observed_break_even_win_rate":threshold,
        "top3_share_of_gross_wins":sum(top3)/profit if profit>0 else None,
        "funding_cash_total":x["funding_cash_total"],
        "funding_events":x["funding_events"],
        "hours_exposed":x["hours_exposed"],
        "mark_liquidation_warning_hours":x["mark_liquidation_warning_hours"],
        "historical_year_cash_returns":x["historical_year_cash_returns"],
        "ledger":ledger,
        "unresolved_at_cutoff":x["unresolved_at_cutoff"],
    }


def run(source):
    if source.get("status") != "SOURCE_OK":
        raise ValueError("SOURCE_NOT_VERIFIED")
    bars = source["bars"]
    if bars[0]["t"] > core.START-200*core.HOUR or bars[-1]["t"] < core.FINISH:
        raise ValueError("SOURCE_INCOMPLETE")
    if any(x["t"] >= 1767225600000 for x in bars):
        raise ValueError("SEALED_2026_CANDLES_FORBIDDEN")
    funds = {int(t):float(v) for t,v in source["funding"].items()}
    marks = {int(t):v for t,v in source["marks"].items()}
    payload = {
        "classification":"EXPLORATORY_IN_SAMPLE_ZERO_PROMOTION",
        "live_authority":"NONE",
        "source_scope":"Binance BTCUSDT public USD-M 1h 2020-02 through 2025-12 only",
        "one_change_only":"TARGET_MARGIN_GAIN_20_30_40_50_PCT",
        "source_manifests": source["manifests"],
        "price_barrier_percent":{k:{
            "target":100*(fixed_bounds(100,g)[0]/100-1),
            "stop":100*(fixed_bounds(100,g)[1]/100-1)
        } for k,g in TARGETS.items()},
        "scenarios":{},
    }
    for label,(fee,slip) in core.CONFIGS.items():
        baseline = core.replay(bars,funds,marks,"PARENT",fee,slip)
        variants = {}
        for label_r in TARGETS:
            variant = replay_ratio(bars,funds,marks,fee,slip,label_r)
            if label_r=="4R":
                if variant["trades_closed"]!=111 or variant["wins"]!=30:
                    raise RuntimeError("FOUR_R_COUNT_REGRESSION")
                if not math.isclose(variant["closed_equity_return"],
                                    LEGACY_4R_RETURNS[label],rel_tol=0,abs_tol=1e-10):
                    raise RuntimeError("FOUR_R_EQUITY_REGRESSION")
            variants[label_r] = measures(variant)
        payload["scenarios"][label]={"PARENT":measures(baseline),
                                      **variants}
    return payload


def report(payload):
    lines=["# PAYOFF 2R / 3R / 4R / 5R — DESCRIPTIVE HISTORICAL SWEEP",
           "", "**ZERO promotion: historical and already inspected.** No forward proof, no live GO.",
           "","Fixed -10% nominal margin stop, 2x leverage, 10% equity as margin,"
           " 60-day time-exit, same signals and positions recomputed causally, BASE/STRESS costs.",
           "",
           "| Scenario | Model | Closed | Wins | Targets | Stops | Time | Win % | Ret. % | PF | Closed DD % | Approx MTM DD % | Funding USDT |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for s in ("BASE","STRESS"):
        for name,r in payload["scenarios"][s].items():
            f=lambda n: "N/A" if n is None else f"{n:.2f}"
            lines.append(f"| {s} | {name} | {r['closed']} | {r['wins']} | {r['target_reached']} | {r['stop_reached']} | {r['time_exits']} | {f(100*r['win_rate'] if r['win_rate'] is not None else None)} | {f(100*r['closed_equity_return'])} | {f(r['profit_factor'])} | {f(100*r['closed_equity_max_dd'])} | {f(100*r['approx_mtm_max_dd'])} | {f(r['funding_cash_total'])} |")
    lines+=["", "## Year-by-year closed-equity returns (historical)",""]
    for s in ("BASE","STRESS"):
        lines.extend([f"### {s}","",
        "| Model | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |",
        "|---|---:|---:|---:|---:|---:|---:|"])
        for name,r in payload["scenarios"][s].items():
            yr=r["historical_year_cash_returns"]
            lines.append("| "+name+" | "+" | ".join(f"{100*yr.get(str(y),0):.2f}%" for y in range(2020,2026))+" |")
        lines.append("")
    lines.extend(["## Interpretation", "",
    "A high return in this table is NOT an independent profitable edge: all periods predate hypothesis freeze, no real exchange fills/tier/lot/book; actual stop losses may exceed nominal budget.",
    "Every ratio's original entry/exit sequence is recalculated; never reuse 4R's 111 positions to count alternative payoff touches.",
    "Non-identical 4R historic return would cause FAIL_CLOSED before publishing results.",
    "Do not select the best 2R/3R/4R/5R historical ratio as forward-qualified. Only separately frozen forward testing can promote.", ""])
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--markdown",required=True,type=Path)
    args=p.parse_args()
    data=json.loads(args.source.read_text())
    result=run(data)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    md=report(result)
    args.markdown.write_text(md)
    print(md)
    print("PAYOFF_SWEEP",json.dumps({s:{r:{
        "ret":v["closed_equity_return"],"pf":v["profit_factor"],"closed":v["closed"]}
        for r,v in details.items()} for s,details in result["scenarios"].items()},sort_keys=True))


if __name__=="__main__":
    main()
