"""Offline deterministic risk budget: published BTC-CONVEX causal exits only.
The code does NOT regenerate signals or simulate a new PAYOFF-40-10 strategy.
Original source: GitHub Actions run 35911267608, artifact 10772639953.
"""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from math import prod
from pathlib import Path

SOURCE_SHA = "b03c2513a5787e4d5ceeedb149c3a722a83961443baa1dba0068298c8da403c3"
EQUITY = 10000.0
MARGIN_SHARE = .10
LEV = 2.0
SCENARIOS = {
    "ILLUSTRATIVE_MEXC_FEE_ONLY":(.0008,0),
    "ILLUSTRATIVE_MEXC_FEE_2BPS_SLIP":(.0008,.0002),
    "ILLUSTRATIVE_MEXC_FEE_5BPS_SLIP":(.0008,.0005),
    "PARENT_FEE_2BPS_SLIP":(.001,.0002),
    "PARENT_FEE_5BPS_SLIP":(.001,.0005),
}

def pnl_margin(entry,exit,fee,slip):
    if min(entry,exit)<=0 or not 0<=fee<1 or not 0<=slip<1:
        raise ValueError("INVALID_INPUT")
    ratio=(exit*(1-slip))/(entry*(1+slip))
    return LEV*((1-fee)*ratio-(1+fee))

def replay(trades,fee,slip):
    equity=EQUITY
    peak=EQUITY
    drawdown=0
    pnl=[]
    year=[]
    last_exit=-1
    for t in trades:
        start,end=int(t["entry_t"]),int(t["exit_t"])
        if start<last_exit or end<start:raise ValueError("CAUSAL_SEQUENCE_BLOCKED")
        last_exit=end
        net=pnl_margin(float(t["entry"]),float(t["exit"]),fee,slip)
        if 1+MARGIN_SHARE*net<=0:raise ValueError("HYPOTHETICAL_INSOLVENCY")
        equity*=1+MARGIN_SHARE*net
        peak=max(equity,peak)
        drawdown=min(drawdown,equity/peak-1)
        pnl.append(net)
        year.append(datetime.fromtimestamp(start/1000,timezone.utc).year)
    if len(pnl)!=93:raise ValueError("WRONG_SOURCE_COUNT")
    win=[x for x in pnl if x>0];loss=[x for x in pnl if x<0]
    yr={str(y):100*(prod(1+MARGIN_SHARE*r for r,z in zip(pnl,year) if z==y)-1) for y in sorted(set(year))}
    return dict(n=len(pnl),wins=len(win),losses=len(loss),
                closed_return_equity_pct=100*(equity/EQUITY-1),
                max_closed_equity_drawdown_pct=100*drawdown,
                average_win_on_margin_pct=100*sum(win)/len(win),
                average_loss_on_margin_pct=100*sum(loss)/len(loss),
                closed_exit_40pct_margin_count=sum(r>=.4 for r in pnl),
                observed_year_returns_pct=yr)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("causal_replay_json",type=Path)
    args=ap.parse_args()
    data=args.causal_replay_json.read_bytes()
    h=hashlib.sha256(data).hexdigest()
    if h!=SOURCE_SHA:raise SystemExit("SOURCE_SHA_MISMATCH:"+h)
    source=json.loads(data)
    if source.get("probe")!="CAUSAL_1H_REPLAY_V0.1" or source.get("causal_result",{}).get("closed_trades")!=93:
        raise SystemExit("SOURCE_IDENTITY_BLOCKED")
    result={
        "classification":"HISTORICAL_POST_OUTCOME_FIXED_EXITS_ONLY",
        "source_sha256":h,"initial_equity":EQUITY,
        "margin_fraction":MARGIN_SHARE,"leverage":LEV,
        "full_cost_status":"UNPROVEN_FUNDING_AND_EXECUTION_MISSING",
        "is_4to1_strategy_result":False,
        "scenarios":{label:replay(source["trades"],f,s) for label,(f,s) in SCENARIOS.items()},
    }
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":main()
