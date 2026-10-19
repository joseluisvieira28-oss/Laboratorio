"""Chronological offline 400-level L2 orderbook + taker sweep *research model*.

Source admission is external; synthetic demonstration IS NOT executable proof.
No API, no account, no orders, no gap guarantees or futures profit claim.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from decimal import Decimal,InvalidOperation

class SourceRejected(ValueError):pass

def d(value,positive=True):
    if isinstance(value,bool):raise SourceRejected("BOOLEAN_DECIMAL")
    try: x=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError) as exc:raise SourceRejected("BAD_DECIMAL") from exc
    if not x.is_finite() or (x<=0 if positive else x<0):
        raise SourceRejected("NONPOSITIVE_OR_NONFINITE")
    return x

@dataclass
class Book:
    symbol:str
    asks:dict=field(default_factory=dict)
    bids:dict=field(default_factory=dict)
    ts:int|None=None
    seq:int|None=None
    initialized:bool=False
    sequence_mode:bool|None=None
    count:int=0

def update(book,event):
    if event.get("instId")!=book.symbol or book.symbol not in ("SOL-USDT-SWAP","BNB-USDT-SWAP"):
        raise SourceRejected("WRONG_OR_UNVERIFIED_INSTRUMENT")
    ts=event.get("ts")
    if type(ts)!=int or ts<0 or (book.ts is not None and ts<book.ts):
        raise SourceRejected("NONMONOTONIC_OR_INVALID_EVENT_TIME")
    action=event.get("action")
    if action not in ("snapshot","update"):
        raise SourceRejected("UNKNOWN_BOOK_ACTION")
    if action=="update" and not book.initialized:
        raise SourceRejected("MISSING_FULL_SNAPSHOT")
    seq=event.get("seqId")
    prev=event.get("prevSeqId")
    hasseq=(type(seq) is int and type(prev) is int)
    if (seq is None)!=(prev is None) or (seq is not None and not hasseq):
        raise SourceRejected("INVALID_SEQUENCE_METADATA")
    if book.sequence_mode is not None and book.sequence_mode!=hasseq:
        raise SourceRejected("CHANGING_SEQUENCE_PROOF_MODE")
    if action=="update" and hasseq and prev!=book.seq:
        raise SourceRejected("BROKEN_SEQ_CONTINUITY")
    if hasseq and action=="update" and seq<prev:
        raise SourceRejected("DECREASING_SEQ")
    if action=="snapshot":
        book.asks={}
        book.bids={}
    for name,prices in (("asks",book.asks),("bids",book.bids)):
        raw=event.get(name)
        if not isinstance(raw,list):raise SourceRejected("MISSING_LEVEL_ARRAY")
        seen=set()
        for level in raw:
            if not isinstance(level,(tuple,list)) or len(level)<2:
                raise SourceRejected("BAD_LEVEL_SHAPE")
            price,qty=d(level[0]),d(level[1],positive=False)
            if price in seen:raise SourceRejected("DUPLICATE_PRICE_LEVEL_IN_UPDATE")
            seen.add(price)
            if qty==0:
                prices.pop(price,None)
            else:
                prices[price]=qty
        if len(prices)>400:raise SourceRejected("EXCEEDS_400_LEVEL_BOOK")
    if not book.asks or not book.bids:
        raise SourceRejected("EMPTY_BOOK_SIDE")
    if max(book.bids)>=min(book.asks):
        raise SourceRejected("CROSSED_BOOK")
    book.ts=ts
    book.seq=seq if hasseq else None
    book.sequence_mode=hasseq
    book.initialized=True
    book.count+=1
    return book

def reconstruct_at(events,symbol,t0_ms,max_age_ms=2000):
    if type(t0_ms) is not int or t0_ms<=0:
        raise SourceRejected("INVALID_FROZEN_SIGNAL_TIME")
    b=Book(symbol=symbol)
    for row in events:
        if type(row.get("ts")) is not int:
            raise SourceRejected("INVALID_EVENT_TIMESTAMP")
        if row["ts"]>t0_ms:
            # Can never use a future book to fill a past trade.
            break
        update(b,row)
    if not b.initialized:raise SourceRejected("NO_CAUSAL_SNAPSHOT")
    age=t0_ms-b.ts
    if age<0 or age>max_age_ms:
        raise SourceRejected("STALE_OR_FUTURE_BOOK")
    return b,age

def sweep(book, side, original_base_qty, historic_ct_val, historic_lot_sz,
          historic_contract_metadata_verified=False):
    """Taker BUY walks ASK, SELL walks BID. Qty in base coins -> contracts.

    Instrument ctVal currency/base and lot size MUST be historically verified,
    not inferred from current specs. No actual order/exchange broker fill.
    """
    if not historic_contract_metadata_verified:
        raise SourceRejected("HISTORICAL_CONTRACT_METADATA_UNVERIFIED")
    qty_base=d(original_base_qty)
    ctval=d(historic_ct_val)
    lotsz=d(historic_lot_sz)
    contracts=qty_base/ctval
    if contracts/lotsz != (contracts/lotsz).to_integral_value():
        raise SourceRejected("MODEL_SIZE_OFF_HISTORICAL_CONTRACT_LOT")
    if side=="BUY_LONG_ENTRY":
        levels=sorted(book.asks.items())
    elif side=="SELL_LONG_EXIT":
        levels=sorted(book.bids.items(),reverse=True)
    else:raise SourceRejected("SIDE_NOT_FROZEN")
    if not levels:raise SourceRejected("NO_VALID_SIDE")
    best=levels[0][0]
    remaining=contracts
    used=[]
    cost=Decimal(0)
    for price,qty in levels:
        if remaining<=0:break
        fill=min(remaining,qty)
        remaining-=fill
        cost+=fill*price
        used.append((str(price),str(fill)))
    filled=contracts-remaining
    full=remaining==0
    vwap=cost/filled if filled else None
    direction=Decimal(1) if side=="BUY_LONG_ENTRY" else Decimal(-1)
    impact=(vwap/best-1)*Decimal(10000)*direction if vwap is not None else None
    return {
        "status":"HYPOTHETICAL_L2_LEVEL_SWEEP_NOT_FILL" if full else "INSUFFICIENT_400_LEVEL_DEPTH",
        "base_quantity":str(qty_base),
        "contract_value_base":str(ctval),
        "contracts_required":str(contracts),
        "contracts_swept":str(filled),
        "contracts_missing":str(remaining),
        "best_px":str(best),
        "hypothetical_vwap_px":str(vwap) if vwap else None,
        "hypothetical_impact_bps":str(impact) if impact is not None else None,
        "levels_used":len(used),
        "source_books_prove_broker_fill":False,
        "funding_fee_slippage_stop_ack_verification":False,
        "live_go":False
    }
