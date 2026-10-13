"""Prospective eligibility and proof-custody gate; cannot create forward proof.

Use only after 2026-10-15T00:00Z and only with independently observed
contemporaneous immutable bar/quote/funding witnesses. No network or orders.
"""
from __future__ import annotations
import hashlib
import json
import math

BOUNDARY_MS=1792022400000
TF_MS={"SOLUSDT":3_600_000,"BNBUSDT":14_400_000}
MAX_SIGNAL_WITNESS_LAG_MS=120_000
MAX_QUOTE_AGE_MS=2_000
MIN_INDEPENDENT_SIGNALS=60
MIN_SEPARATE_UTC_WEEKS=12

def valid_hex_sha(x):
    return isinstance(x,str) and len(x)==64 and all(ch in "0123456789abcdef" for ch in x)

def validate_future_signal(rec):
    if not isinstance(rec,dict):return "WITNESS_MALFORMED"
    symbol=rec.get("symbol")
    if symbol not in TF_MS:return "OUT_OF_SCOPE_ASSET"
    tf=TF_MS[symbol]
    start=rec.get("bar_open_ms")
    witnessed=rec.get("witness_ms")
    if not isinstance(start,int) or start<BOUNDARY_MS or start%tf:
        return "PREBOUNDARY_OR_UNALIGNED_BAR"
    if not isinstance(witnessed,int) or not(start+tf<=witnessed<=start+tf+MAX_SIGNAL_WITNESS_LAG_MS):
        return "NOT_CONTEMPORANEOUS_TO_COMPLETED_BAR"
    if rec.get("timeframe_ms")!=tf or rec.get("side")!="LONG":
        return "WRONG_FROZEN_V5_STRATEGY"
    if not valid_hex_sha(rec.get("source_raw_sha256")) or not valid_hex_sha(rec.get("signal_proof_sha256")):
        return "UNPROVEN_SOURCE_CUSTODY"
    if rec.get("warmup_completed_bar_count",0)<200:
        return "INSUFFICIENT_CONTEMPORANEOUS_WARMUP"
    if rec.get("source_observed_before_outcome") is not True:
        return "HINDSIGHT_OR_UNSEALED_EVENT"
    if rec.get("signed_or_append_only_receipt") is not True:
        return "NO_IMMUTABLE_WITNESS"
    return "FUTURE_SOURCE_DECISION_WITNESS_ELIGIBLE_NO_ALPHA_CREDIT"

def validate_quote_after_signal(signal,quote):
    s=validate_future_signal(signal)
    if s!="FUTURE_SOURCE_DECISION_WITNESS_ELIGIBLE_NO_ALPHA_CREDIT":
        return s
    if not isinstance(quote,dict):return "QUOTE_MISSING"
    t=quote.get("market_timestamp_ms")
    obs=quote.get("locally_received_ms")
    if not isinstance(t,int) or not isinstance(obs,int) or obs<t or obs-t>MAX_QUOTE_AGE_MS:
        return "PUBLIC_QUOTE_STALE_OR_MISSING_TIME"
    if t<signal["witness_ms"]:
        return "QUOTE_PRECEDES_SIGNAL_DECISION"
    if quote.get("venue") not in ("MEXC_FUTURES_PUBLIC","BINANCE_UM_PUBLIC"):
        return "UNFROZEN_VENUE_OR_PRIVATE_SOURCE"
    bid=quote.get("bid");ask=quote.get("ask");visible_qty=quote.get("visible_contract_qty")
    if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (bid,ask,visible_qty)):
        return "QUOTE_INVALID_NUMERIC"
    if bid<=0 or ask<=bid or visible_qty<=0:
        return "CROSSED_OR_DEPTH_UNKNOWN"
    if not valid_hex_sha(quote.get("raw_response_sha256")):
        return "QUOTE_RAW_SOURCE_HASH_MISSING"
    return "SOURCE_ONLY_ELIGIBLE_NOT_AN_EXECUTABLE_FILL"

def checkpoint(evidenced_events):
    """Count independently sealed signal clusters; don't fake sample size."""
    accepted=[]
    last_event_by_pair={}
    for item in sorted(evidenced_events,key=lambda x:x.get("bar_open_ms",0)):
        k=validate_future_signal(item)
        if k!="FUTURE_SOURCE_DECISION_WITNESS_ELIGIBLE_NO_ALPHA_CREDIT":
            continue
        sym=item["symbol"]
        t=item["bar_open_ms"]
        prev=last_event_by_pair.get(sym)
        if prev is not None and t-prev<TF_MS[sym]:
            continue
        last_event_by_pair[sym]=t
        accepted.append(item)
    # Per-pair UTC weekly counts: never pool both as if identical independent markets.
    by_pair={}
    for pair in TF_MS:
        valid=[x for x in accepted if x["symbol"]==pair]
        weeks={(x["bar_open_ms"]//604800000) for x in valid}
        by_pair[pair]={"valid_sealed_signals":len(valid),"distinct_utc_weeks":len(weeks),
                       "minimum_source_volume_met":len(valid)>=MIN_INDEPENDENT_SIGNALS and len(weeks)>=MIN_SEPARATE_UTC_WEEKS}
    return {"status":"FORWARD_SOURCE_WITNESSES_ONLY_NOT_ECONOMIC_GO",
            "pair_gate":by_pair,"economic_profitability_proven":False,
            "real_exchange_execution_proven":False,"trading_authority":"NONE"}
