#!/usr/bin/env python3
"""BINANCE007 strict bounded historical Binance Spot price-level L2 replay.
Each Parquet row is ONE price-level change, NOT one WS event. No market orders.
"""
from __future__ import annotations
import math
from collections import Counter
from decimal import Decimal,InvalidOperation

MAX_LEVELS=1000

def decimal_positive(value, allow_zero=False):
    try: d=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError) as exc:raise ValueError("BAD_DECIMAL") from exc
    if not d.is_finite() or d<0 or (d==0 and not allow_zero):
        raise ValueError("NON_POSITIVE_OR_NONFINITE")
    return d

def integer(value,key):
    if isinstance(value,bool):raise ValueError("BAD_INTEGER_"+key)
    try:n=int(value)
    except (TypeError,ValueError) as exc:raise ValueError("BAD_INTEGER_"+key) from exc
    if n<0 or str(n)!=str(value):raise ValueError("BAD_INTEGER_"+key)
    return n

def timestamp(value):
    n=integer(value,"timestamp")
    if not 1750000000000<=n<=1800000000000:raise ValueError("NOT_2026_EPOCH_MILLIS")
    return n

class StrictBook:
    """Snapshot anchored, U/u gated, 1000-level bounded; does not infer L3."""
    def __init__(self,symbol="BTCUSDT"):
        if symbol not in ("BTCUSDT","ETHUSDT","SOLUSDT"):
            raise ValueError("BAD_ASSET")
        self.symbol=symbol
        self.bids={}
        self.asks={}
        self.snapshot_id=None
        self.snapshot_timestamp=None
        self.last_id=None
        self.events_seen=0
        self.events_applied=0
        self.stale_events=0
        self.changed_price_levels=0
        self.pruned_levels=0
        self.last_event_timestamp=None
        self.gaps=[]
        self.first_event_timestamp=None

    def seed(self,rows):
        if self.snapshot_id is not None:raise ValueError("DOUBLE_SNAPSHOT")
        if not rows:raise ValueError("NO_SNAPSHOT_ROWS")
        ids=set()
        stamps=set()
        bids={};asks={}
        for row in rows:
            if row.get("exchange")!="binance" or row.get("asset")!=self.symbol:
                raise ValueError("SNAPSHOT_WRONG_EXCHANGE_OR_ASSET")
            side=row.get("side")
            if side not in ("bid","ask"):raise ValueError("SNAPSHOT_BAD_SIDE")
            ids.add(integer(row.get("last_update_id"),"snapshot_update_id"))
            stamps.add(timestamp(row.get("timestamp_ms")))
            px=decimal_positive(row.get("price"))
            qty=decimal_positive(row.get("quantity"))
            book=bids if side=="bid" else asks
            if px in book:raise ValueError("SNAPSHOT_DUPLICATE_PRICE_LEVEL")
            book[px]=qty
        if len(ids)!=1 or len(stamps)!=1:
            raise ValueError("SNAPSHOT_MULTIPLE_ANCHORS")
        if not(100<=len(bids)<=MAX_LEVELS and 100<=len(asks)<=MAX_LEVELS):
            raise ValueError("SNAPSHOT_NOT_FULL_ENOUGH_OR_EXCEEDS_1000")
        if max(bids)>=min(asks):raise ValueError("SNAPSHOT_CROSSED_OR_LOCKED")
        self.snapshot_id=ids.pop()
        self.snapshot_timestamp=stamps.pop()
        if self.snapshot_id<=0:raise ValueError("SNAPSHOT_ZERO_ID")
        self.last_id=self.snapshot_id
        self.bids=bids;self.asks=asks

    def apply_event(self,rows):
        if self.last_id is None:raise ValueError("NO_INITIAL_SNAPSHOT")
        if not rows:raise ValueError("EMPTY_DIFF_EVENT")
        keys=set()
        levels=[]
        for r in rows:
            if r.get("asset")!=self.symbol or r.get("exchange")!="binance":
                raise ValueError("DIFF_WRONG_EXCHANGE_OR_ASSET")
            side=r.get("side")
            if side not in ("bid","ask"):raise ValueError("DIFF_BAD_SIDE")
            U=integer(r.get("first_update_id"),"first_update_id")
            u=integer(r.get("last_update_id"),"last_update_id")
            stamp=timestamp(r.get("timestamp_ms"))
            if U<=0 or u<U:raise ValueError("BAD_DIFF_U_u")
            keys.add((stamp,U,u))
            levels.append((side,decimal_positive(r.get("price")),
                           decimal_positive(r.get("quantity"),allow_zero=True)))
        if len(keys)!=1:raise ValueError("MIXED_DIFF_EVENT_ROWS")
        stamp,U,u=keys.pop()
        if self.last_event_timestamp is not None and stamp<self.last_event_timestamp:
            raise ValueError("DIFF_TIMESTAMP_REGRESSION")
        self.last_event_timestamp=stamp
        self.events_seen+=1
        if u<=self.last_id:
            self.stale_events+=1
            return False
        if U>self.last_id+1:
            self.gaps.append({"prev_last_id":self.last_id,"first_new_id":U,
                              "missing_update_count_lower_bound":U-self.last_id-1})
            raise ValueError("BINANCE_DIFF_SEQUENCE_GAP")
        if self.first_event_timestamp is None:
            self.first_event_timestamp=stamp
        for side,price,qty in levels:
            target=self.bids if side=="bid" else self.asks
            if qty==0:target.pop(price,None)
            else:target[price]=qty
        self.last_id=u
        self.events_applied+=1
        self.changed_price_levels+=len(levels)
        # CRITICAL: naive unlimited level cache accumulates ghost levels once
        # prices move beyond the initial top-1000 snapshot scope.
        for side,book in (("bid",self.bids),("ask",self.asks)):
            if len(book)>MAX_LEVELS:
                keys=sorted(book,reverse=(side=="bid"))
                for p in keys[MAX_LEVELS:]:del book[p];self.pruned_levels+=1
        if not self.bids or not self.asks or max(self.bids)>=min(self.asks):
            raise ValueError("REPLAY_CROSSED_OR_EMPTY_BOOK")
        return True

    def report(self):
        return {
            "asset":self.symbol,"snapshot_id":self.snapshot_id,
            "snapshot_timestamp_ms":self.snapshot_timestamp,
            "last_valid_update_id":self.last_id,
            "events_seen":self.events_seen,
            "events_applied":self.events_applied,
            "stale_events":self.stale_events,
            "changed_price_level_rows":self.changed_price_levels,
            "pruned_out_of_scope_levels":self.pruned_levels,
            "book_visible_max_per_side":MAX_LEVELS,
            "best_bid":str(max(self.bids)) if self.bids else None,
            "best_ask":str(min(self.asks)) if self.asks else None,
            "gap_count":len(self.gaps),"gaps":self.gaps[:5],
            "first_applied_event_ms":self.first_event_timestamp,
            "last_event_timestamp_ms":self.last_event_timestamp,
            "ghost_levels_possible_beyond_snapshot_visibility":True,
            "individual_order_cancellations_proven":False,
            "economic_returns_tested":False
        }
