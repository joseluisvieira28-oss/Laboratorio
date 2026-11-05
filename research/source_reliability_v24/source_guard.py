#!/usr/bin/env python3
"""No-network PAPER-only L50 fail-closed state machine for fault injection.

This module cannot trade or reconnect to any service itself. It returns an
explicit source-resubscription intent to a future operator/collector. Never
infer missing deltas from price changes; require a genuine NEW snapshot.
"""
from decimal import Decimal, InvalidOperation

class Blocked(Exception):
    pass

def num(x, zero=False):
    try:v=Decimal(str(x))
    except (ValueError,InvalidOperation,TypeError):raise Blocked("INVALID_DECIMAL")
    if not v.is_finite() or v<0 or (v==0 and not zero):raise Blocked("INVALID_QUANTITY_OR_PRICE")
    return v

class SafeL50:
    def __init__(self, quarantine_ms=30000, freshness_ms=1000):
        if quarantine_ms<30000 or freshness_ms>1000 or freshness_ms<=0:
            raise Blocked("UNSAFE_SOURCE_POLICY")
        self.quarantine_ms=quarantine_ms
        self.freshness_ms=freshness_ms
        self.state="AWAIT_SNAPSHOT"
        self.ready_after_ms=0
        self.bids={};self.asks={}
        self.u=None;self.seq=None
        self.last_ms=None
        self.incidents=[]
        self.resubscribe_required=True
    def _freeze(self,now_ms,reason):
        self.incidents.append({"at_ms":now_ms,"reason":reason})
        self.state="AWAIT_SNAPSHOT"
        self.resubscribe_required=True
        self.ready_after_ms=now_ms+self.quarantine_ms
        self.bids.clear();self.asks.clear()
        self.u=None;self.seq=None;self.last_ms=None
        return "RECONNECT_AND_RESUBSCRIBE_REQUIRED"
    def _levels(self,rows,side,allow_zero):
        if not isinstance(rows,list):raise Blocked("LEVEL_SHAPE")
        ordered=[]
        for item in rows:
            if not isinstance(item,list) or len(item)!=2:raise Blocked("LEVEL_SHAPE")
            ordered.append((num(item[0]),num(item[1],allow_zero)))
        ps=[p for p,q in ordered]
        if len(set(ps))!=len(ps) or ps!=sorted(ps,reverse=side=="bids"):
            raise Blocked("DUPLICATE_OR_UNSORTED")
        return ordered
    @staticmethod
    def _good(bids,asks):
        if not bids or not asks or max(bids)>=min(asks):
            raise Blocked("CROSSED_OR_EMPTY")
    def event(self,m,now_ms):
        try:
            if type(now_ms) is not int or now_ms<=0:raise Blocked("INVALID_RECEIVE_CLOCK")
            if m.get("topic")!="orderbook.50.BTCUSDT" or m.get("data",{}).get("s")!="BTCUSDT":
                raise Blocked("FOREIGN_SYMBOL")
            age=now_ms-int(m["ts"])
            if not -250<=age<=1500:raise Blocked("STALE_OR_FUTURE_PUBLISHER")
            d=m["data"];u=int(d["u"]);seq=int(d["seq"])
            if m.get("type")=="snapshot":
                bids=self._levels(d["b"],"bids",False)
                asks=self._levels(d["a"],"asks",False)
                b=dict(bids);a=dict(asks);self._good(b,a)
                # Receiving snapshot cannot circumvent pre-existing quarantine.
                self.bids=b;self.asks=a;self.u=u;self.seq=seq
                self.last_ms=now_ms
                self.resubscribe_required=False
                self.state="QUARANTINED" if now_ms<self.ready_after_ms else "SOURCE_READY"
                return self.state
            if m.get("type")!="delta":raise Blocked("INVALID_FRAME_TYPE")
            if u==1:
                return self._freeze(now_ms,"SERVICE_RESTART_U1")
            if self.state=="AWAIT_SNAPSHOT":
                return "IGNORE_DELTA_UNTIL_NEW_SNAPSHOT"
            if seq<=self.seq:raise Blocked("SEQ_REGRESSION")
            if u!=self.u+1:raise Blocked("MISSING_L50_UPDATE_ID")
            bids=self._levels(d["b"],"bids",True)
            asks=self._levels(d["a"],"asks",True)
            b=self.bids.copy();a=self.asks.copy()
            for dest,entries in ((b,bids),(a,asks)):
                for p,q in entries:
                    if q==0:dest.pop(p,None)
                    else:dest[p]=q
            self._good(b,a)
            self.bids=b;self.asks=a;self.u=u;self.seq=seq;self.last_ms=now_ms
            self.state="QUARANTINED" if now_ms<self.ready_after_ms else "SOURCE_READY"
            return self.state
        except (Blocked,ValueError,KeyError,TypeError) as exc:
            return self._freeze(now_ms if type(now_ms) is int else 0,str(exc))
    def quote(self,now_ms):
        if self.state!="SOURCE_READY" or self.resubscribe_required:
            raise Blocked("SOURCE_NOT_READY")
        if type(now_ms) is not int or self.last_ms is None or not 0<=now_ms-self.last_ms<=self.freshness_ms:
            self._freeze(now_ms if type(now_ms) is int else 0,"QUOTE_TOO_OLD")
            raise Blocked("STALE_BOOK_QUARANTINED")
        self._good(self.bids,self.asks)
        return {"bid":str(max(self.bids)),"ask":str(min(self.asks)),
                "u":self.u,"seq":self.seq,"asof_receive_ms":self.last_ms}

def live_enabled():
    return False
