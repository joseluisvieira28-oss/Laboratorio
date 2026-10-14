#!/usr/bin/env python3
"""NO-TRADE Windows/Linux offline gate: 100 USDT three original CONVEX slots.

This file cannot import any broker SDK, read credentials, open a socket or
submit orders. Every result is PRELIVE_ONLY / NO_LIVE_GO. The example price
and instrument minimums are SYNTHETIC and not a current MEXC quote/spec.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
import json
from pathlib import Path

EXPECTED_SYMBOLS = ("SOL_USDT", "SOL_USDT", "BNB_USDT")
EXPECTED_TFS = (5, 60, 240)
STOP_FRACTION = Decimal("0.04")
EQUITY = Decimal("100")
ONE_TRADE_RISK = Decimal("0.50")
GLOBAL_RISK = Decimal("1.50")
SOL_RISK = Decimal("1.00")
LEVERAGE = Decimal("10")
ONE = Decimal("1")
BPS = Decimal("10000")


class Blocked(ValueError):
    pass


def dec(x, label):
    try:
        n = Decimal(str(x))
    except (ValueError, InvalidOperation):
        raise Blocked("BAD_DECIMAL_" + label)
    if not n.is_finite():
        raise Blocked("NONFINITE_" + label)
    return n


def positive(x, label):
    n = dec(x, label)
    if n <= 0:
        raise Blocked("NONPOSITIVE_" + label)
    return n


def step_floor(x, step):
    step = positive(step, "QTY_STEP")
    return (dec(x, "RAW_QTY") / step).to_integral_value(rounding=ROUND_FLOOR)*step


def preflight_config(cfg):
    if cfg.get("armed") is not False or cfg.get("can_send_orders") is not False or cfg.get("uses_api_key") is not False:
        raise Blocked("UNARMED_ONLY")
    if cfg.get("status") != "NO_LIVE_GO":
        raise Blocked("LIVE_AUTHORITY_NEVER_PRESENT")
    if dec(cfg.get("operator_declared_equity_usdt"), "EQUITY") != EQUITY:
        raise Blocked("UNMATCHED_OPERATOR_EQUITY")
    if cfg.get("operator_declared_open_positions") != 0 or cfg.get("account_state_independently_verified") is not False:
        raise Blocked("ACCOUNT_DECLARATION_ONLY_NOT_VERIFICATION")
    if cfg.get("leverage_requested") != 10 or cfg.get("margin_mode_requested") != "ISOLATED":
        raise Blocked("UNEXPECTED_LEVERAGE_OR_MARGIN_MODE")
    if (dec(cfg.get("max_modeled_risk_per_trade_usdt"), "TRADE_LIMIT") != ONE_TRADE_RISK or
        dec(cfg.get("max_aggregate_modeled_risk_usdt"), "GLOBAL_LIMIT") != GLOBAL_RISK or
        dec(cfg.get("max_sol_modeled_risk_usdt"), "SOL_LIMIT") != SOL_RISK):
        raise Blocked("CHANGED_SAFETY_BUDGET")
    slots=cfg.get("strategy_slots",[])
    if len(slots)!=3 or tuple(x["symbol"] for x in slots)!=EXPECTED_SYMBOLS:
        raise Blocked("UNEXPECTED_STRATEGY_OR_SYMBOL_COUNT")
    if tuple(x["tf_minutes"] for x in slots)!=EXPECTED_TFS or any(
        x.get("direction")!="LONG" or x.get("original_stop_price_fraction")!="0.04"
        or x.get("original_exit_policy_preserved") is not True for x in slots
    ):
        raise Blocked("ORIGINAL_SCIENCE_CHANGED")
    if cfg.get("sol_collision_policy")!="ONE_PHYSICAL_SOL_POSITION_AT_A_TIME_UNTIL_BROKER_NETTING_VERIFIED":
        raise Blocked("SOL_NETTING_POLICY_CHANGED")
    if not isinstance(cfg.get("verified_live_gates"),dict) or any(
        v is not False for v in cfg["verified_live_gates"].values()
    ):
        raise Blocked("CANNOT_SELF_CERTIFY_LIVE_GATES")
    return True


def modeled_long_quantity(*, quote_ask, contract_step_base,
                          minimum_contracts, maximum_contracts,
                          fresh_contract_notional_min, equity_remaining_margin,
                          limit_risk_cash=ONE_TRADE_RISK):
    """Returns quantized PURE hypothetical model, never an order size authority.

    Stop taken from ADVERSE modeled entry, not market mid. Includes costs on
    both legs + signed worst-cost funding reserve. No gap bound is guaranteed.
    """
    ask=positive(quote_ask,"ASK")
    step=positive(contract_step_base,"CONTRACT_STEP_BASE")
    min_contracts=positive(minimum_contracts,"MIN_CONTRACTS")
    max_contracts=positive(maximum_contracts,"MAX_CONTRACTS")
    min_n=positive(fresh_contract_notional_min,"MIN_NOTIONAL")
    margin=positive(equity_remaining_margin,"MARGIN")
    risk=positive(limit_risk_cash,"MODEL_RISK")
    if risk>ONE_TRADE_RISK:
        raise Blocked("RISK_ABOVE_FROZEN_PER_TRADE_LIMIT")
    if min_contracts % 1 or max_contracts % 1 or max_contracts < min_contracts:
        raise Blocked("INVALID_CONTRACT_INTEGER_BOUNDS")
    # Illustrative 8 bps each taker, 2 bps each adverse slip, +5bp funding reserve.
    f=Decimal("8")/BPS
    s=Decimal("2")/BPS
    fund=Decimal("5")/BPS
    adverse_entry=ask*(ONE+s)
    # 4% ORIGINAL stop on actual modeled entry. No leverage ROI substitution.
    stop=adverse_entry*(ONE-STOP_FRACTION)
    adverse_exit=stop*(ONE-s)
    risk_per_base=(adverse_entry-adverse_exit)+(adverse_entry*f)+(
        adverse_exit*f)+(adverse_entry*fund)
    risk_per_contract=risk_per_base*step
    # Margin reserve on ADVERSE entry, not assumed unused book mid.
    count_by_risk=(risk/risk_per_contract).to_integral_value(rounding=ROUND_FLOOR)
    count_by_margin=(margin*LEVERAGE/(adverse_entry*step)).to_integral_value(rounding=ROUND_FLOOR)
    contracts=int(min(count_by_risk,count_by_margin,max_contracts))
    if contracts < min_contracts:
        raise Blocked("MIN_CONTRACT_EXCEEDS_RISK_OR_MARGIN")
    qty=step*contracts
    notional=adverse_entry*qty
    if notional < min_n:
        raise Blocked("MIN_NOTIONAL_EXCEEDS_RISK_BUDGET")
    cash_risk=risk_per_base*qty
    if cash_risk>risk or notional/LEVERAGE>margin:
        raise Blocked("CALCULATION_OVER_BUDGET")
    return {"contracts":contracts, "base_quantity":str(qty),
            "hypothetical_entry_price":str(adverse_entry),
            "hypothetical_initial_stop":str(stop),
            "modeled_max_loss_at_stop_usdt":str(cash_risk),
            "modeled_notional_usdt":str(notional),
            "modeled_initial_margin_usdt":str(notional/LEVERAGE),
            "not_a_hard_loss_cap":True,
            "current_book_and_account_fee_verified":False,
            "not_an_order":True}


def check_collisions(active_slots):
    """One-way same-symbol positions NET at exchange; can't claim 3 physical slots."""
    names=[s["symbol"] for s in active_slots]
    if len(names)!=len(set(names)):
        raise Blocked("DUPLICATE_PHYSICAL_SYMBOL_POSITION_REQUIRES_VERIFIED_NETTING")
    total=sum((positive(s["risk_usdt"],"ACTIVE_RISK") for s in active_slots), Decimal("0"))
    sol=sum((positive(s["risk_usdt"],"SOL_RISK") for s in active_slots
             if s["symbol"]=="SOL_USDT"),Decimal("0"))
    if total>GLOBAL_RISK or sol>SOL_RISK or any(
        positive(s["risk_usdt"],"SLOT_RISK")>ONE_TRADE_RISK for s in active_slots
    ):
        raise Blocked("ACCOUNT_GLOBAL_OR_SYMBOL_RISK_LIMIT")
    return {"combined_risk_usdt":str(total),"combined_SOL_risk_usdt":str(sol)}


def diagnostic(cfg, sample=False):
    preflight_config(cfg)
    out={
        "result":"NO_LIVE_GO",
        "equity_usdt":"100",
        "zero_positions":"OPERATOR_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        "requested_leverage":"10x ISOLATED",
        "slots": [dict(id=x["id"],symbol=x["symbol"],tf_minutes=x["tf_minutes"]) for x in cfg["strategy_slots"]],
        "per_slot_modeled_cash_risk_budget":"0.50",
        "total_modeled_cash_risk_budget":"1.50",
        "sol_simultaneous_physical_orders":"BLOCKED_UNTIL_NETTING_AND_STOPS_PROVEN",
        "current_MEXC_exchange_quotations":"NOT_CHECKED",
        "current_MEXC_contract_lots":"NOT_CHECKED",
        "account_fee_schedule":"NOT_CHECKED",
        "stop_broker_ack":"NOT_CHECKED",
        "crash_recovery":"NOT_CHECKED",
        "execution_authority":"NONE",
        "live_gates_not_proven":sorted(cfg["verified_live_gates"].keys()),
    }
    if sample:
        out["synthetic_do_not_trade_examples"]={}
        for name, ask,step,minn in (("SOL_USDT","110","0.1","1"),
                                   ("BNB_USDT","750","0.01","1")):
            try:
                out["synthetic_do_not_trade_examples"][name]=modeled_long_quantity(
                    quote_ask=ask,contract_step_base=step,minimum_contracts=minn,
                    maximum_contracts="100000",fresh_contract_notional_min="1",
                    equity_remaining_margin="100"
                )
            except Blocked as exc:
                out["synthetic_do_not_trade_examples"][name]={"blocked":str(exc)}
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--config",type=Path,default=Path(__file__).with_name("prelive_100usdt_configuration.json"))
    p.add_argument("--synthetic-only",action="store_true")
    args=p.parse_args()
    try:
        cfg=json.loads(args.config.read_text(encoding="utf-8-sig"))
        output=diagnostic(cfg,args.synthetic_only)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        output={"result":"NO_LIVE_GO","local_preflight":"FAIL_CLOSED","reason":str(exc)}
    print(json.dumps(output,indent=2,ensure_ascii=False,sort_keys=True))
    # An unsuccessful LIVE gate is intentional: this is not an executable trader.
    return 0


if __name__=="__main__":
    raise SystemExit(main())
