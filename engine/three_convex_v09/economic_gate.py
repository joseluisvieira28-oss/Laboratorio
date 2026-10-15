"""Frozen 2026 V09 economic GO evidence gate (no historical holdout opened).

This is NOT a trading strategy and it cannot provide brokerage provenance by
trusting a self-authored JSON file. It rejects unverified source receipts and
requires enough forward observations before a statistical decision can exist.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from math import sqrt
from datetime import datetime,timezone

START_ISO="2026-10-16T00:00:00+00:00"
LANES=("SOL_CONVEX_NATIVE_5M","SOL_CONVEX_1H","BNB_CONVEX_4H")

class EconomicHalt(ValueError):pass

def D(x):
    try:y=Decimal(str(x))
    except (InvalidOperation,ValueError,TypeError):raise EconomicHalt("INVALID_NET_PNL") from None
    if not y.is_finite():raise EconomicHalt("NONFINITE_NET_PNL")
    return y

def economic_verdict(receipts,*,now_iso,freeze_git_sha,
                     independent_venue_validation=False):
    if not isinstance(receipts,list):
        raise EconomicHalt("FORWARD_LEDGER_NOT_LIST")
    if not isinstance(freeze_git_sha,str) or len(freeze_git_sha)!=40:
        raise EconomicHalt("MISSING_PREOUTCOME_FREEZE_COMMIT")
    if independent_venue_validation is not True:
        return {"verdict":"NO_GO","reason":"INDEPENDENT_EXCHANGE_COST_AND_FILL_RECEIPTS_NOT_VERIFIED",
                "source_freeze":freeze_git_sha,"trade_count":len(receipts)}
    if len(receipts)<90:
        return {"verdict":"NO_GO","reason":"INSUFFICIENT_PROSPECTIVE_90_CLOSED_TRADES",
                "trade_count":len(receipts)}
    try:
        start=datetime.fromisoformat(START_ISO)
        current=datetime.fromisoformat(now_iso)
    except (TypeError,ValueError):raise EconomicHalt("INVALID_UTC_CLOCK") from None
    if current.tzinfo is None or current.utcoffset()!=timezone.utc.utcoffset(current):
        raise EconomicHalt("NON_UTC_CLOCK")
    if current-start < __import__("datetime").timedelta(days=60):
        return {"verdict":"NO_GO","reason":"MINIMUM_60_DAYS_FORWARD_NOT_ELAPSED",
                "trade_count":len(receipts)}
    lane_counts={name:0 for name in LANES}
    seen=set()
    nets=[]
    last_exit=start
    for t in receipts:
        if not isinstance(t,dict):
            raise EconomicHalt("BAD_TRADE_RECEIPT")
        needed=("lane","entry_utc","exit_utc","external_oid","realized_net_usdt",
                "fee_receipt_independently_confirmed","funding_independently_confirmed",
                "fill_and_close_independently_confirmed","frozen_strategy_id")
        if any(x not in t for x in needed):
            raise EconomicHalt("MISSING_TRADE_RECEIPT_EVIDENCE")
        if t["lane"] not in lane_counts or t["frozen_strategy_id"]!="CONVEX_V5_MICRO_1LOT_10X_V09":
            raise EconomicHalt("STRATEGY_FORK_OR_LANE_UNDECLARED")
        if not all(t[k] is True for k in ("fee_receipt_independently_confirmed",
                            "funding_independently_confirmed",
                            "fill_and_close_independently_confirmed")):
            raise EconomicHalt("REAL_VENUE_COST_COMPONENTS_NOT_VERIFIED")
        if t["external_oid"] in seen:raise EconomicHalt("DUPLICATE_EXCHANGE_ORDER")
        seen.add(t["external_oid"])
        try:
            entry=datetime.fromisoformat(t["entry_utc"])
            exit_t=datetime.fromisoformat(t["exit_utc"])
        except (ValueError,TypeError):raise EconomicHalt("BAD_TRADE_TIMESTAMPS") from None
        if entry.tzinfo is None or exit_t.tzinfo is None or entry<start or not entry<exit_t<=current:
            raise EconomicHalt("PRE_FREEZE_OR_IMPOSSIBLE_FORWARD_TRADE")
        lane_counts[t["lane"]]+=1
        nets.append(D(t["realized_net_usdt"]))
        if exit_t>last_exit:last_exit=exit_t
    if any(c<20 for c in lane_counts.values()):
        return {"verdict":"NO_GO","reason":"AT_LEAST_20_REAL_CLOSED_TRADES_PER_LANE_REQUIRED",
                "lane_counts":lane_counts}
    # Conservative parametric screening only. Autocorrelation, selection and
    # heavy tails additionally require a pre-registered block bootstrap.
    vals=[float(v) for v in nets]
    n=len(vals)
    mean=sum(vals)/n
    variance=sum((a-mean)**2 for a in vals)/(n-1)
    bound=mean-2.394*sqrt(variance/n)   # simultaneous conservative one-sided 3-lane screen
    if bound<=0:
        return {"verdict":"NO_GO","reason":"LOWER_CONFIDENCE_BOUND_ON_NET_PNL_NOT_POSITIVE",
                "trades":n,"mean_net_usdt":str(mean),"screen_lower_bound":str(bound)}
    return {"verdict":"CONDITIONAL_ECONOMIC_SCREEN_ONLY",
            "reason":"SERIAL_CORRELATION_BOOTSTRAP_SOURCE_CUSTODY_AND_REAL_LIVE_PROTECTION_STILL_REQUIRED",
            "trades":n,"mean_net_usdt":str(mean),
            "screen_lower_bound":str(bound),"authorizes_real_orders":False}
