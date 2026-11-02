#!/usr/bin/env python3
"""STRICT offline read-only economic quote gate. Never a trade signal or permission.
Input: manually timestamped and independently VERIFIED evidence; default ABSENT => BLOCK.
Does not perform any HTTP, exchange login, quote requests, orders, trading or wallet calls.
"""
from __future__ import annotations
import argparse
import datetime as dt
from decimal import Decimal,InvalidOperation
import json
import pathlib

OUT=pathlib.Path("artifacts/real_quote_economics_v01/shadow_economic_gate")
UTC=dt.timezone.utc
def dec(v):
    try:x=Decimal(str(v))
    except (InvalidOperation,TypeError,ValueError):raise ValueError("BAD_DECIMAL")
    if not x.is_finite():raise ValueError("NONFINITE_DECIMAL")
    return x
def parse_utc(v):
    if not isinstance(v,str):raise ValueError("MISSING_ISO_UTC_TIMESTAMP")
    when=dt.datetime.fromisoformat(v.replace("Z","+00:00"))
    if when.tzinfo is None or when.utcoffset()!=dt.timedelta():raise ValueError("TIMESTAMP_MUST_BE_EXPLICIT_UTC")
    return when
def result(status,reason,kind,details=None):
    return {"kind":kind,"status":status,"reason":reason,
            "execution_permission":"NEVER_FROM_THIS_RESEARCH_GATE",
            "source_and_outcome_provenance_required":True,
            "details":details or {}}
def strong_provenance(obj):
    for k in ("immutable_source_receipt_id","preoutcome_model_freeze_id","original_event_settlement_parity_receipt_id"):
        if not isinstance(obj.get(k),str) or len(obj[k])<12:return False
    return True
def event_gate(obj, now):
    kind="MEXC_EVENT_FUTURES_EXACT_10MIN"
    if obj.get("product")!="MEXC_EVENT_FUTURES_10M" or obj.get("horizon_minutes")!=10 or obj.get("side") not in ("UP","DOWN"):
        return result("BLOCK","WRONG_PRODUCT_HORIZON_OR_SIDE",kind)
    if not strong_provenance(obj):return result("BLOCK","NO_IMMUTABLE_INDEPENDENT_SETTLEMENT_OR_PAYOUT_PROVENANCE",kind)
    if not (obj.get("independent_outcome_validation") is True and obj.get("settlement_index_parity_proven") is True
      and obj.get("payout_captured_from_actual_event_futures_submission_area") is True):
        return result("BLOCK","MISSING_INDEPENDENT_VALIDATION_OR_REAL_MEXC_EVENT_INDEX_AND_PAYOUT",kind)
    if obj.get("model_family") in ("LOGIT_P60","FLOW55","FLOW60","TRIANGLE_FAIL_SAMPLE","OPTIONS_V21_MARKET_MARKET"):
        return result("BLOCK","PRIOR_REJECTED_MODEL_CANNOT_BE_REUSED_AS_VALIDATED_EDGE",kind)
    try:
        at=parse_utc(obj.get("quote_observed_at_utc"))
        if not dt.timedelta()<=now-at<=dt.timedelta(seconds=5):
            return result("BLOCK","STALE_NOT_REAL_TIME_PAYOUT_QUOTE",kind)
        n=int(obj.get("independently_scored_event_samples",0))
        days=int(obj.get("independent_utc_signal_days",0))
        if n<300 or days<20:return result("BLOCK","INSUFFICIENT_INDEPENDENT_EVENT_PAYOFF_SAMPLES",kind)
        p=dec(obj["conservative_probability_win_lower_97p5"])
        loss=dec(obj["conservative_probability_loss_upper_97p5"])
        q=dec(obj["offered_exact_side_payout_ratio"])
        extra=dec(obj.get("conservative_other_cost_per_stake","0"))
        if not(Decimal("0")<=p<=1 and Decimal("0")<=loss<=1
          and Decimal("0")<q<=3 and Decimal("0")<=extra<=1):
            return result("BLOCK","INVALID_PROBABILITY_PAYOUT_OR_COST_BOUNDS",kind)
        # Lower win and upper loss can sum >1 as separate confidence limits.
        ev=p*q-loss-extra
        if ev<=Decimal("0.02"):
            return result("BLOCK","CONSERVATIVE_EV_NOT_ABOVE_2PCT_RESEARCH_HURDLE",kind,
             {"lower_ev_per_stake":str(ev),"pwin_lower":str(p),"ploss_upper":str(loss),
              "fixed_observed_payout":str(q)})
        return result("RESEARCH_SHADOW_ONLY","POSITIVE_SYNTHETIC_OR_VERIFIED_EVIDENCE_TEST_REQUIRES_HUMAN_REVIEW",kind,
             {"lower_ev_per_stake":str(ev),"pwin_lower":str(p),"ploss_upper":str(loss),
              "fixed_observed_payout":str(q),"model_family":obj.get("model_family"),
              "not_authorization_to_execute_any_trade":True})
    except (KeyError,TypeError,ValueError,OverflowError) as e:
        return result("BLOCK","MISSING_OR_INVALID_VERIFIABLE_EVENT_QUOTE_FIELDS",kind,{"error_type":type(e).__name__})
def option_gate(obj,now):
    kind="KRAKEN_ACTUAL_RFQ_BTC_OPTIONS"
    if obj.get("product")!="KRAKEN_BTC_OPTIONS_RFQ":
        return result("BLOCK","NOT_ACTUAL_KRAKEN_OPTIONS_RFQ",kind)
    req=("option_instrument_id","option_expiry_utc","strike_usd","bid_usd_per_contract",
         "ask_usd_per_contract","rfq_quote_uid","independent_fair_value_lower_usd",
         "all_in_buy_exit_fee_usd_per_contract","settlement_index_reference")
    if any(not obj.get(k) for k in req):
        return result("BLOCK","TWO_SIDED_ACCEPTABLE_RFQ_AND_FAIR_VALUE_SOURCE_MISSING",kind)
    if not(obj.get("person_eligible_for_options_confirmed") is True
       and obj.get("independent_forward_and_execution_validation") is True
       and obj.get("bid_ask_held_executable_for_stated_size") is True):
        return result("BLOCK","ELIGIBILITY_RFQ_EXECUTABILITY_OR_UNBIASED_FAIR_VALUE_NOT_PROVEN",kind)
    try:
        at=parse_utc(obj.get("rfq_observed_at_utc"))
        if not dt.timedelta()<=now-at<=dt.timedelta(seconds=5):
            return result("BLOCK","RFQ_QUOTE_TOO_OLD",kind)
        expiry=parse_utc(obj["option_expiry_utc"])
        if expiry<=now:return result("BLOCK","RFQ_ALREADY_EXPIRED",kind)
        strike=dec(obj["strike_usd"])
        ask=dec(obj["ask_usd_per_contract"])
        bid=dec(obj["bid_usd_per_contract"])
        fair=dec(obj["independent_fair_value_lower_usd"])
        fees=dec(obj["all_in_buy_exit_fee_usd_per_contract"])
        if any(x<=0 for x in (strike,ask,bid,fair)) or fees<0 or bid>ask:
            return result("BLOCK","INVALID_REAL_QUOTE_PRICES_SPREAD_OR_FEES",kind)
        # This only studies theoretical PURCHASE at ask, NOT naked selling.
        edge=fair-ask-fees
        if edge<=0:return result("BLOCK","FAIR_VALUE_BELOW_REAL_RFQ_ASK_PLUS_ALL_COSTS",kind,
                                {"conservative_quote_edge_usd_per_contract":str(edge)})
        return result("RESEARCH_SHADOW_ONLY",
            "RFQ_BUY_VALUATION_ONLY_NOT_VERIFIED_FUTURE_NET_RETURN",kind,
            {"conservative_quote_edge_usd_per_contract":str(edge),
             "risk_of_fair_value_MODEL_ERROR":True,"not_authorization_to_execute_any_trade":True})
    except (KeyError,TypeError,ValueError,OverflowError) as e:
        return result("BLOCK","RFQ_DATA_PARSE_ERROR",kind,{"error_type":type(e).__name__})
def evaluate(obj,now=None):
    now=now or dt.datetime.now(UTC)
    if obj.get("product")=="MEXC_EVENT_FUTURES_10M":return event_gate(obj,now)
    if obj.get("product")=="KRAKEN_BTC_OPTIONS_RFQ":return option_gate(obj,now)
    return result("BLOCK","UNKNOWN_OR_WRONG_PRODUCT",str(obj.get("product","UNKNOWN")))
def selftest():
    now=dt.datetime(2026,11,2,13,0,tzinfo=UTC)
    stamp=now.isoformat()
    assert evaluate({},now)["status"]=="BLOCK"
    assert evaluate({"product":"MEXC_EVENT_FUTURES_10M","horizon_minutes":10,"side":"UP"},now)["status"]=="BLOCK"
    assert evaluate({"product":"KRAKEN_BTC_OPTIONS_RFQ"},now)["status"]=="BLOCK"
    # Only synthetic fixtures; NEVER substitute for source proof or actual payout.
    synthetic={"product":"MEXC_EVENT_FUTURES_10M","horizon_minutes":10,"side":"UP",
        "immutable_source_receipt_id":"SYNTHETIC_SOURCE_FIXTURE","preoutcome_model_freeze_id":"SYNTHETIC_NOT_REAL_MODEL",
        "original_event_settlement_parity_receipt_id":"SYNTHETIC_SETTLEMENT_PROOF",
        "independent_outcome_validation":True,"settlement_index_parity_proven":True,
        "payout_captured_from_actual_event_futures_submission_area":True,
        "model_family":"SYNTHETIC_NOT_TRADEABLE",
        "independently_scored_event_samples":400,"independent_utc_signal_days":50,
        "quote_observed_at_utc":stamp,
        "conservative_probability_win_lower_97p5":"0.65",
        "conservative_probability_loss_upper_97p5":"0.35",
        "offered_exact_side_payout_ratio":"0.80",
        "conservative_other_cost_per_stake":"0.01"}
    assert evaluate(synthetic,now)["status"]=="RESEARCH_SHADOW_ONLY"
    assert evaluate({**synthetic,"offered_exact_side_payout_ratio":"0.50"},now)["status"]=="BLOCK"
    assert evaluate({**synthetic,"model_family":"LOGIT_P60"},now)["status"]=="BLOCK"
    assert evaluate({**synthetic,"quote_observed_at_utc":"2026-11-02T12:00:00Z"},now)["status"]=="BLOCK"
    assert evaluate({**synthetic,"independently_scored_event_samples":2},now)["status"]=="BLOCK"
    assert evaluate({**synthetic,"settlement_index_parity_proven":False},now)["status"]=="BLOCK"
    assert evaluate({**synthetic,"horizon_minutes":15},now)["status"]=="BLOCK"
    assert evaluate({**synthetic,"payout_captured_from_actual_event_futures_submission_area":False},now)["status"]=="BLOCK"
    assert evaluate({**synthetic,"conservative_probability_win_lower_97p5":"nan"},now)["status"]=="BLOCK"
    opt={"product":"KRAKEN_BTC_OPTIONS_RFQ","option_instrument_id":"SYNTH-BTC-CALL",
      "option_expiry_utc":"2026-12-31T08:00:00Z","strike_usd":"100000",
      "bid_usd_per_contract":"9","ask_usd_per_contract":"10",
      "rfq_quote_uid":"SYNTHETIC_ONLY","independent_fair_value_lower_usd":"12",
      "all_in_buy_exit_fee_usd_per_contract":"1","settlement_index_reference":"BTCOPTRR",
      "person_eligible_for_options_confirmed":True,
      "independent_forward_and_execution_validation":True,
      "bid_ask_held_executable_for_stated_size":True,
      "rfq_observed_at_utc":stamp}
    assert evaluate(opt,now)["status"]=="RESEARCH_SHADOW_ONLY"
    assert evaluate({**opt,"independent_fair_value_lower_usd":"9"},now)["status"]=="BLOCK"
    assert evaluate({**opt,"ask_usd_per_contract":"8"},now)["status"]=="BLOCK"
    assert evaluate({**opt,"person_eligible_for_options_confirmed":False},now)["status"]=="BLOCK"
    assert evaluate({**opt,"rfq_observed_at_utc":"2026-11-02T12:59:00Z"},now)["status"]=="BLOCK"
    return {"selftest":"PASS","tests":16,"synthetic_positive_inputs_are_not_market_evidence":True}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=pathlib.Path)
    parser.add_argument("--selftest",action="store_true")
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.selftest:
        x=selftest()
        result_=dict(x,status="SIMULATED_TESTS_PASS",new_market_api_calls=0,real_trades=0)
    else:
        obj=json.loads(args.input.read_text()) if args.input else {}
        result_=dict(evaluate(obj),new_market_api_calls=0,real_trades=0)
    (OUT/"receipt.json").write_text(json.dumps(result_,sort_keys=True,indent=2)+"\n")
    print("ECONOMIC_EVIDENCE_GATE",json.dumps(result_,sort_keys=True),flush=True)
if __name__=="__main__":main()
