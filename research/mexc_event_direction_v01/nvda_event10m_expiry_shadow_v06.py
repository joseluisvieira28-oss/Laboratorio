#!/usr/bin/env python3
"""Strict offline NVIDIA Event10m public-index SHADOW settlement mechanics.
Requires pre-outcome custody proof; an unverified anchor cannot certify EV.
No network calls, exchange writes, account reads or orders.
"""
import hashlib,json,math,re
SHA=re.compile("^[0-9a-f]{64}$")
def digest(obj):
    return hashlib.sha256((json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
def check(x,msg):
    if not x:raise ValueError(msg)
def valid_sha(x):
    return isinstance(x,str) and SHA.fullmatch(x) is not None
def settle(decision,anchor,expiry_tick):
    check(isinstance(decision,dict) and isinstance(anchor,dict) and isinstance(expiry_tick,dict),
          "INVALID_RECEIPT_STRUCTURE")
    check(decision.get("study")=="NVIDIA_EVENT10M_INTEGRATED_V05","WRONG_STUDY")
    check(decision.get("status")=="PAPER_FORECAST_UNANCHORED_NOT_EVENT_FUTURES_EXECUTION",
          "DECISION_NOT_FROZEN_PAPER")
    model=decision.get("forecast") or {}
    check(model.get("study")=="NVIDIA_EVENT10M_CASH_REF_V01","WRONG_FROZEN_MODEL")
    side=model.get("candidate")
    check(side in ("UP","DOWN"),"ABSTAIN_OR_BAD_SIDE_CANNOT_SETTLE")
    d=int(model["decision_ts_ms"]);target=int(model["expiry_target_ms"])
    check(target==d+600000 and target>d,"HORIZON_NOT_10M")
    check(model.get("asset")=="NVIDIA_USDT" and model.get("horizon_min")==10,"WRONG_ASSET_OR_HORIZON")
    check(anchor.get("decision_canonical_sha256")==digest(decision),
          "ANCHOR_DECISION_HASH_MISMATCH")
    check(type(anchor.get("published_ms")) is int and d<=anchor["published_ms"]<target,
          "NO_PRE_OUTCOME_PUBLISH_TIME")
    check(type(anchor.get("github_artifact_id")) is int and anchor["github_artifact_id"]>0,
          "ANCHOR_ID_MISSING")
    check(valid_sha(anchor.get("github_artifact_digest_sha256")),"HOST_DIGEST_MISSING")
    check(expiry_tick.get("symbol")=="NVIDIA_USDT" and
          valid_sha(expiry_tick.get("raw_sha256")),"INVALID_PUBLIC_EXPIRY_SOURCE")
    server=expiry_tick.get("server_ts_ms");received=expiry_tick.get("received_ms")
    check(type(server) is int and type(received) is int,"NO_EXPIRY_CLOCKS")
    check(target<=server<=target+5000 and server<=received<=server+5000,
          "EXPIRY_QUOTE_OUT_OF_BOUNDS")
    price=float(expiry_tick.get("index_price"))
    entry=float(decision.get("decision_public_index"))
    check(all(math.isfinite(x) and x>0 for x in (entry,price)),"INVALID_INDEX_PRICE")
    payout=float(model["payout_up"] if side=="UP" else model["payout_down"])
    check(math.isfinite(payout) and payout>0,"INVALID_SOURCE_PAYOUT")
    change=price-entry
    if change==0:out,ret="TIE",0.0
    elif change*(1 if side=="UP" else -1)>0:out,ret="WIN",payout
    else:out,ret="LOSS",-1.0
    return {"study":"NVIDIA_EVENT10M_INDEX_SHADOW_V06",
      "signal_id":model["decision_ts_ms"],"asset":"NVIDIA_USDT",
      "direction":side,"decision_ts_ms":d,
      "expiry_target_ms":target,"observed_expiry_server_ms":server,
      "observed_expiry_receive_ms":received,
      "index_shadow_outcome":out,"index_shadow_unit_return":ret,
      "decision_index":entry,"expiry_index":price,
      "payout_at_decision":payout,
      "decision_receipt_sha256":digest(decision),
      "expiry_raw_sha256":expiry_tick["raw_sha256"],
      "external_anchor_id_claim":anchor["github_artifact_id"],
      "external_anchor_published_ms_claim":anchor["published_ms"],
      "custody_independently_authenticated":False,
      "actual_event_futures_fill_parity_proven":False,
      "verdict":"INDEX_SHADOW_MECHANICS_ONLY__NOT_ECONOMIC_EDGE"}
