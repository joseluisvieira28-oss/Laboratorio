"""Pure, offline broker-stop *ACK-contract model*; NEVER sends an order.

Distinguishes calculated monotonic stop proposals from confirmed exchange state.
None of the synthetic arguments is evidence of an actual exchange ACK.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation

class StopHalt(ValueError):
    pass

def D(s):
    try:
        v=Decimal(str(s))
        if not v.is_finite() or v<=0:raise StopHalt("INVALID_POSITIVE_DECIMAL")
        return v
    except (InvalidOperation, TypeError, ValueError) as exc:
        if isinstance(exc,StopHalt):raise
        raise StopHalt("INVALID_DECIMAL") from exc

@dataclass(frozen=True)
class StopProof:
    position_id: str
    broker_stop_id: str
    side: str
    contracts: Decimal
    ack_stop: Decimal
    tick: Decimal
    state: str = "ACK_VERIFIED"
    next_price: Decimal|None = None
    intent_id: str|None = None

def initial(position_id,stop_id,side,qty,stop,tick,active_broker_receipt):
    if not position_id or not stop_id or side not in ("LONG","SHORT"):
        raise StopHalt("BAD_OR_MISSING_IDENTITY")
    q, s, t=D(qty),D(stop),D(tick)
    if s%t:raise StopHalt("BROKER_STOP_NOT_ON_TICK")
    if not isinstance(active_broker_receipt,dict) or not active_broker_receipt.get("verified"):
        raise StopHalt("NO_BROKER_ACK")
    if (active_broker_receipt.get("position_id")!=position_id
        or active_broker_receipt.get("stop_id")!=stop_id
        or active_broker_receipt.get("side")!=side
        or D(active_broker_receipt.get("contracts"))!=q
        or D(active_broker_receipt.get("stop"))!=s
        or active_broker_receipt.get("active") is not True):
        raise StopHalt("BROKER_STATE_MISMATCH")
    return StopProof(position_id,stop_id,side,q,s,t)

def prepare(state:StopProof,desired,executable_quote,quote_age_ms,intent_id):
    if state.state!="ACK_VERIFIED":
        raise StopHalt("STOP_NOT_VERIFIED_OR_PENDING")
    if not intent_id or state.intent_id or state.next_price is not None:
        raise StopHalt("DUPLICATE_OR_INVALID_INTENT")
    if not isinstance(quote_age_ms,int) or isinstance(quote_age_ms,bool) or quote_age_ms<0 or quote_age_ms>2000:
        raise StopHalt("STALE_OR_INVALID_QUOTE")
    d,q=D(desired),D(executable_quote)
    if d%state.tick:raise StopHalt("OFF_TICK")
    if state.side=="LONG":
        if d<state.ack_stop:raise StopHalt("LONG_PROTECTION_WEAKENED")
        if d>=q:raise StopHalt("STOP_ALREADY_CROSSED_LONG")
    else:
        if d>state.ack_stop:raise StopHalt("SHORT_PROTECTION_WEAKENED")
        if d<=q:raise StopHalt("STOP_ALREADY_CROSSED_SHORT")
    if d==state.ack_stop:return state
    return replace(state,state="PENDING_UNACKNOWLEDGED",next_price=d,intent_id=intent_id)

def confirm_readback(state:StopProof,broker_receipt:dict):
    if state.state!="PENDING_UNACKNOWLEDGED" or state.next_price is None:
        raise StopHalt("NO_PENDING_INTENT")
    if not isinstance(broker_receipt,dict) or broker_receipt.get("verified") is not True:
        raise StopHalt("MISSING_READBACK")
    if (broker_receipt.get("position_id")!=state.position_id
        or broker_receipt.get("stop_id")!=state.broker_stop_id
        or broker_receipt.get("side")!=state.side
        or broker_receipt.get("intent_id")!=state.intent_id
        or broker_receipt.get("active") is not True
        or D(broker_receipt.get("contracts"))!=state.contracts
        or D(broker_receipt.get("stop"))!=state.next_price):
        raise StopHalt("READBACK_NOT_EXACT_PENDING_STOP")
    if state.side=="LONG" and state.next_price<state.ack_stop:
        raise StopHalt("IMPOSSIBLE_LONG_LOOSEN")
    if state.side=="SHORT" and state.next_price>state.ack_stop:
        raise StopHalt("IMPOSSIBLE_SHORT_LOOSEN")
    return replace(state,ack_stop=state.next_price,next_price=None,
                   intent_id=None,state="ACK_VERIFIED")

def uncertain_timeout(state:StopProof):
    if state.state!="PENDING_UNACKNOWLEDGED":
        raise StopHalt("TIMEOUT_WITHOUT_PENDING")
    # Never infer broker mutation succeeded or failed. No re-sends.
    return replace(state,state="UNKNOWN_NEEDS_RECONCILIATION")

def recover(state:StopProof,receipt:dict):
    if state.state!="UNKNOWN_NEEDS_RECONCILIATION":
        raise StopHalt("RECOVER_ONLY_UNCERTAIN")
    # Only exact readback can prove success; no fresh write.
    return confirm_readback(replace(state,state="PENDING_UNACKNOWLEDGED"),receipt)
