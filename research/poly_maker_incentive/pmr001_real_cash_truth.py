#!/usr/bin/env python3
"""PMR001 V03 — exact arithmetic for separately sourced REAL maker-reward PnL reports.
No orders, exchange reads, account credentials, inferred income, or statistical forecasting.
Third-party self-reports do NOT constitute independent ledger audits or returns for this lab.
"""
from __future__ import annotations
from decimal import Decimal
from pathlib import Path
import json
import os

SOURCES = (
    {
        "id": "CLYDESCAN-2026-08-17-15D",
        "source": "https://clydescan.com/results",
        "crosscheck": "https://clydescan.com/blog/how-much-can-you-earn-polymarket-liquidity-rewards",
        "claimed_period": "2026-08 15 payout days ending 2026-08-17",
        "gross_paid": "349.45",
        "inventory_pnl": "-479.35",
        "pnl_basis": "reported_realized_unwinds; current open inventory not independently marked in this figure",
        "approx_capital_at_risk": "3184.00",
        "independently_audited": False,
    },
    {
        "id": "TLAFARGUE-2026-07-09-40H",
        "source": "https://github.com/tlafargue/polymarket-research/blob/main/studies/2026-07-09-rewards-pilot-live.md",
        "crosscheck": "https://github.com/tlafargue/polymarket-research/blob/main/studies/FINDINGS.md",
        "claimed_period": "2026-07-07 to 2026-07-09 (~40 hours of quoting)",
        "gross_paid": "7.52",
        "inventory_pnl": "-18.33",
        "pnl_basis": "marked_inventory_pnl_at_pilot_close; final settlement still unknown",
        "approx_capital_at_risk": "190.00",
        "independently_audited": False,
    },
)
# Actual reward PROGRAM POOLS from local prospective SOURCE_PASS v02 PR #208;
# these are NOT income earned by the user or a venue-payout ledger.
MARKETS = (
    {"market_id": "562802", "description": "US House: Democrats", "program_total_usd_day": "222.0",
     "reward_eligible_min_shares": "50"},
    {"market_id": "562803", "description": "US House: Republicans", "program_total_usd_day": "278.0",
     "reward_eligible_min_shares": "50"},
    {"market_id": "608545", "description": "Ballon d'Or: Lamine Yamal", "program_total_usd_day": "9.0",
     "reward_eligible_min_shares": "50"},
)
SOURCE_V02="https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38412840289"
US_DOLLAR_DAILY_PAYOUT_FLOOR=Decimal("1.00")
ADVERSE_MOVE_SCENARIOS=(Decimal("0.00"),Decimal("0.01"),Decimal("0.05"),Decimal("0.10"))


def dec(v): return Decimal(str(v))


def external_account_truth(x):
    paid=dec(x["gross_paid"])
    inventory=dec(x["inventory_pnl"])
    if paid < 0 or inventory > 0:
        raise ValueError("Invalid negative reward or signed inventory loss source")
    net=paid + inventory
    return {
        "case_id":x["id"],"case_source":x["source"],
        "period":x["claimed_period"],
        "gross_rewards_paid_usd":str(paid),
        "inventory_pnl_usd":str(inventory),
        "net_reward_plus_inventory_usd":str(net),
        "pnl_basis":x["pnl_basis"],
        "minimum_reward_multiplier_for_zero_net":str(((-inventory)/paid).quantize(Decimal("0.0001"))) if paid else None,
        "approx_capital_at_risk_usd":x["approx_capital_at_risk"],
        "self_reported_not_independently_audited":True,
        "is_profit_proof_for_our_lab":False,
    }


def market_necessary_share(m, adverse_move):
    total=dec(m["program_total_usd_day"])
    quantity=dec(m["reward_eligible_min_shares"])
    loss=adverse_move*quantity
    # The daily >=$1 payment floor applies across the user's account, not per market.
    # Interpreted below as a conservative *single-market-alone* sufficiency test.
    # A positive individual contribution can still exist below $1 if the user earns
    # other rewards elsewhere, but none are observed here.
    target=max(US_DOLLAR_DAILY_PAYOUT_FLOOR,loss)
    if total<=0: raise ValueError("Cannot divide by non-positive market pool")
    ratio=target/total
    return {
        "market_id":m["market_id"],
        "scenario_one_adverse_fill_move_usd_per_share":str(adverse_move),
        "scenario_fill_size_shares":str(quantity),
        "scenario_one_leg_loss_usd":str(loss),
        "required_market_reward_share_pct_to_cover_loss_and_reach_1usd_floor":str((ratio*100).quantize(Decimal("0.0001"))),
        "possible_only_if_remainder_of_day_rewards_from_this_market":ratio<=1,
        "actual_individual_reward_share_pct":None,
        "actual_fill_likelihood":None,
        "actual_net_profit":None,
        "is_assumed_not_measured":True,
    }


def report():
    r=[external_account_truth(s) for s in SOURCES]
    assert all(dec(x["net_reward_plus_inventory_usd"])<0 for x in r)
    return {
        "verdict":"NO_VERIFIED_PROFIT_EVIDENCE_FOR_PMR001_OR_OUR_ACCOUNT",
        "decision":"NO_AUTOMATED_TRADING_OR_RADAR_PROMOTION",
        "independent_external_operator_cases":len(r),
        "operator_cases_independently_audited":0,
        "operator_claims":r,
        "our_prospective_book_source":SOURCE_V02,
        "our_observed_market_pool_data_not_own_rewards":list(MARKETS),
        "one_adverse_fill_break_even_sensitivity":{
            m["market_id"]:[market_necessary_share(m,loss)
                            for loss in ADVERSE_MOVE_SCENARIOS] for m in MARKETS},
        "critical_limitation":[
            "Published external PnL is self-reported: cannot certify exchange wallet source or independent inventory cost audit.",
            "First external case is realized unwind PnL; second uses marked inventory PnL; do not pool statistics.",
            "Our V01/V02 observations contain market-wide rewards and quoted books but ZERO our orders, fills, received payouts, inventory or user's portfolio.",
            "Actual competitiveness requires maker owner-scoring and full-day active rest time; anonymous books do not reveal reward allocation.",
            "The one-dollar payout threshold is at daily USER total level; single-market threshold illustration is sufficient but not necessary.",
            "Hypothetical adverse price move per filled share is not a forecast or actual execution cost.",
            "Polymarket legal/physical georestriction and eligible trading access NOT verified for user's location.",
        ],
        "claimed_profit_usd":None,
        "trading_authority":"NONE",
        "orders_created":False,
    }


if __name__=="__main__":
    obj=report()
    path=Path(os.environ.get("PMR001_V03_REPORT","PMR001_V03_REAL_CASH_TRUTH.json"))
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True))
