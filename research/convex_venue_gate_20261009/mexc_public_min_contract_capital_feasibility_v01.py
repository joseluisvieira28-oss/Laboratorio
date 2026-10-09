#!/usr/bin/env python3
"""MEXC contract minimum-order feasibility from frozen PUBLIC read-only receipt.
No current account reads, capital actions, or claimed executable historic fills.
"""
import json, math, sys, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
IN=HERE/"VENUE_SOURCE_GATE_RESULT_2026_10_09.json"
OUT=HERE/"MEXC_MIN_CONTRACT_CAPITAL_FEASIBILITY_RESULT_V01.json"
EXPECTED=("ETH_USDT","SOL_USDT","BNB_USDT")
BALANCES=(100.,250.,1000.,10000.)
RISKS=(.0025,.005)
PLANNED=.0424
MAX_ALLOC=.95
API_TAKER_BPS_PER_SIDE=8.0
def valid(v,label):
 a=float(v)
 if not math.isfinite(a) or a<=0:raise ValueError("INVALID_"+label)
 return a
def floating_step(a,step):
 return int(math.floor((a+1e-10)/step))*step
def main():
 try:
  raw=json.loads(IN.read_text())
  if raw.get("status")!="SOURCE_GATE_EXECUTED__NO_HISTORICAL_MEXC_EXECUTION_APPROVAL":
   raise ValueError("SOURCE_RECEIPT_IDENTITY_FAIL")
  items={x["symbol"]:x for x in raw.get("mexc_public_api_observations",[])}
  if set(items)!=set(EXPECTED):raise ValueError("SYMBOL_SCOPE_DIFFERENT")
  results={}
  for symbol in EXPECTED:
   orig=items[symbol]
   c=orig.get("contract_now",{});q=orig.get("depth_now",{})
   if c.get("status")!="CURRENT_METADATA_ONLY" or q.get("status")!="LIVE_SNAPSHOT_ONLY_NOT_2021_25_HISTORY":
    results[symbol]={"status":"SOURCE_BLOCKED_CURRENT_CONTRACT_OR_BBO"};continue
   if c.get("symbol")!=symbol:raise ValueError("CONTRACT_SYMBOL_ID_MISMATCH")
   size=valid(c.get("contractSize"),"CONTRACT_SIZE")
   min_contracts=valid(c.get("minVol"),"MIN_VOL")
   step=valid(c.get("volUnit"),"VOL_UNIT")
   ask=valid(q.get("best_ask"),"BEST_ASK")
   bid=valid(q.get("best_bid"),"BEST_BID")
   if ask<bid:raise ValueError("CROSSED_BBO")
   if abs(round(min_contracts/step)*step-min_contracts)>1e-8:raise ValueError("MIN_VOL_NOT_MULTIPLE_OF_STEP")
   raw_taker=c.get("takerFeeRate")
   raw_maker=c.get("makerFeeRate")
   min_notional=ask*size*min_contracts
   info={"source_status":"CURRENT_PUBLIC_CONTRACT_BBO_ONLY_NOT_HISTORIC",
         "symbol":symbol,"contract_size_underlying":size,"min_contracts":min_contracts,"vol_unit":step,
         "current_best_ask":ask,"current_best_bid":bid,"timestamp_ms":q.get("timestamp"),
         "timestamp_iso":q.get("timestamp_iso"),
         "current_spread_bps":q.get("spread_bps"),
         "min_contract_notional_usdt":round(min_notional,6),
         "contract_api_allowed_metadata":c.get("apiAllowed"),
         "market_contract_state":c.get("state"),
         "fee_metadata":{"makerFeeRate":raw_maker,"takerFeeRate":raw_taker},
         "official_futures_API_taker_fee_per_side_bps":API_TAKER_BPS_PER_SIDE,
         "metadata_taker_bps_per_side":(float(raw_taker)*10000 if raw_taker is not None else None),
         "fee_metadata_conflicts_official_bulletin":(raw_taker is not None and abs(float(raw_taker)*10000-API_TAKER_BPS_PER_SIDE)>1e-8),
         "hypothetical_capital_levels":{}}
   for risk in RISKS:
    rname=f"{risk*100:.2f}pct"
    threshold=min_notional*PLANNED/risk
    info["hypothetical_capital_levels"][rname]={
       "minimum_equity_for_one_contract_at_risk_rule_usdt":round(threshold,6),
       "accounts":{}
    }
    for capital in BALANCES:
     planned_notional=min(capital*risk/PLANNED,capital*MAX_ALLOC)
     raw_contracts=planned_notional/(ask*size)
     qty=floating_step(raw_contracts,step)
     allowed=qty+1e-9>=min_contracts
     actual_notional=qty*ask*size if allowed else 0.
     # No up-rounding, ever.
     if actual_notional>planned_notional+1e-7:raise ValueError("ROUNDED_TRADE_EXCEEDS_RISK_NOTIONAL")
     planned_risk=actual_notional*PLANNED
     info["hypothetical_capital_levels"][rname]["accounts"][str(int(capital))]={
       "hypothetical_account_usdt":capital,
       "max_risk_budget_usdt":round(capital*risk,6),
       "max_risk_sized_notional_usdt":round(planned_notional,6),
       "status":"MINIMUM_CONTRACT_SIZE_FEASIBLE_IN_MODEL" if allowed else "NOT_TRADABLE_UNDER_PLANNED_RISK",
       "contracts_rounded_down":round(qty,8) if allowed else 0,
       "rounded_trade_notional_usdt":round(actual_notional,6),
       "planned_stop_cost_risk_usdt":round(planned_risk,6),
       "not_verified_order_execution":True,
     }
   results[symbol]=info
  out={"status":"MEXC_PUBLIC_MIN_CONTRACT_HYPOTHETICAL_FEASIBILITY_COMPUTED",
       "original_source_gate_run":37919451421,
       "symbol_results":results,
       "risk_fracs":RISKS,"capital_levels_usdt":BALANCES,
       "risk_denom":PLANNED,"max_notional_equity_fraction":MAX_ALLOC,
       "fee_rule":"OFFICIAL_API_FEE_BULLETIN_WINS_OVER_UNVERIFIED_CONTRACT_METADATA",
       "execution_profitability":"NOT_ESTABLISHED",
       "min_contract_eligibility_is_not_an_order_acceptance_confirmation":True,
       "no_private_account_reads":True,
       "no_lived_trades_or_2026_outcomes":True,
       "live_go":False}
  OUT.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
  print("MEXC_MIN_CONTRACT_CAPITAL_GATE",json.dumps({
    "status":out["status"],
    "coins":[{"symbol":k,"min_notional_usdt":v.get("min_contract_notional_usdt"),
      "r025":v.get("hypothetical_capital_levels",{}).get("0.25pct"),
      "fee_conflict":v.get("fee_metadata_conflicts_official_bulletin")}
        for k,v in results.items()]
  },sort_keys=True),flush=True)
 except Exception as exc:
  OUT.write_text(json.dumps({"status":"FAIL_CLOSED","reason":repr(exc),"live_go":False},indent=2)+"\n")
  traceback.print_exc()
  sys.exit(2)
if __name__=="__main__":main()
