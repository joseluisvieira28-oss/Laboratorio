"""Executable *simulation* of V08 position+native-stop lifecycle.

This runner uses a strictly synthetic broker. A transport with real MEXC POST
methods cannot be injected: the test client MUST expose _v08_synthetic=True.
Any uncertainty hard-halts the ledger; never resend a possibly accepted order.
The same invariants are prerequisites for a future reviewed real adapter.
"""
from __future__ import annotations
from decimal import Decimal,ROUND_FLOOR
import time

from engine.three_convex_v08.order_ledger import DurableLedger,SignalIntent,LedgerHalt
from engine.three_convex_v06.protection_gate import reconcile_native_stop,ProtectHalt


class SimHalt(ValueError):pass


def simulate_protected_open(*,broker,ledger:DurableLedger,signal:SignalIntent,
                            tick_size="0.01",now_ms=None):
    if getattr(broker,"_v08_synthetic",False) is not True:
        raise SimHalt("REAL_BROKER_ADAPTER_NOT_AUTHORIZED")
    if now_ms is None:now_ms=signal.observed_ms
    oid=ledger.reserve(signal)
    try:
        # Write before *any* simulated mutation; crash => unknown, not retry.
        ledger.advance(oid,"ENTRY_SUBMIT_UNKNOWN",now_ms)
        ack=broker.simulate_entry(symbol=signal.symbol,oid=oid)
        if not isinstance(ack,dict) or not str(ack.get("orderId","")).isdigit():
            raise SimHalt("ENTRY_ACK_MISSING_BROKER_ID")
        order_id=str(ack["orderId"])
        ledger.advance(oid,"ENTRY_ACK",now_ms+1,order_id=order_id)
        order=broker.simulate_get_order(order_id)
        if (order.get("externalOid")!=oid or order.get("state")!=3 or
            order.get("positionMode")!=1 or order.get("openType")!=1 or
            order.get("leverage")!=10 or order.get("dealVol")!=1):
            raise SimHalt("FILLED_ENTRY_READBACK_NOT_PROVEN")
        pos=str(order.get("positionId",""))
        if not pos.isdigit() or int(pos)<=0:raise SimHalt("FILL_POSITION_ID_INVALID")
        ledger.advance(oid,"FILLED_UNPROTECTED",now_ms+2,position_id=pos)
        price=Decimal(str(order["dealAvgPrice"]))
        tick=Decimal(tick_size)
        if price<=0 or tick<=0:raise SimHalt("BAD_STOP_GEOMETRY")
        stop=(price*Decimal(".96")/tick).to_integral_value(rounding=ROUND_FLOOR)*tick
        ledger.advance(oid,"STOP_SUBMIT_UNKNOWN",now_ms+3)
        stop_ack=broker.simulate_stop(symbol=signal.symbol,position_id=pos,
                                       volume=1,stop_price=stop)
        if not isinstance(stop_ack,dict) or not str(stop_ack.get("id","")).isdigit():
            raise SimHalt("STOP_ACK_MISSING_BROKER_ID")
        sid=str(stop_ack["id"])
        ledger.advance(oid,"STOP_ACK",now_ms+4,stop_id=sid)
        # Synchronously re-read position and stop AFTER stop POST/ACK,
        # rejecting quantity-lag and wrong/missing native stop.
        positions=broker.simulate_get_positions()
        stops=broker.simulate_get_stops()
        if len(positions)!=1 or len(stops)!=1:raise SimHalt("BROKER_SCOPE_AMBIGUOUS")
        proof=reconcile_native_stop(
            order=order,positions=positions,stops=stops,
            symbol=signal.symbol,external_oid=oid,tick_size=tick_size,
            mark_price=broker.simulate_mark(),
            now_ms=now_ms+8,order_read_ms=now_ms+5,
            position_read_ms=now_ms+6,stop_read_ms=now_ms+8,
            stop_submit_ack_ms=now_ms+4,stop_order_id=sid)
        ledger.advance(oid,"PROTECTED",now_ms+9,evidence=proof)
        return {"status":"SYNTHETIC_NATIVE_STOP_RECONCILIATION_PASS",
                "symbol":signal.symbol,"ledger_state":"PROTECTED",
                "synthetic_only":True,"live_orders":False}
    except Exception as exc:
        try:
            ledger.advance(oid,"HALTED",now_ms+20,
                           evidence={"reason_type":type(exc).__name__,
                                     "stop_state_unknown":True})
        except LedgerHalt:
            pass
        return {"status":"SYNTHETIC_FLOW_HARD_HALT",
                "reason_type":type(exc).__name__,
                "synthetic_only":True,"live_orders":False,
                "blind_resend":False}


class FakeMEXC:
    """Completely fake broker for protocol-test fixtures, no sockets."""
    _v08_synthetic=True
    def __init__(self,*,fail_at=None,quantity_lag=False):
        self.fail_at=fail_at;self.quantity_lag=quantity_lag
        self.orders=[];self.stops=[]
        self.pos=[]
        self._symbol=None
    def _fail(self,event):
        if self.fail_at==event:raise TimeoutError("SYNTHETIC_UNKNOWN_RESULT")
    def simulate_entry(self,*,symbol,oid):
        self._fail("entry")
        self._symbol=symbol
        order={"orderId":9001,"symbol":symbol,"externalOid":oid,
               "positionId":1234,"state":3,"side":1,
               "openType":1,"leverage":10,"positionMode":1,
               "dealVol":1,"dealAvgPrice":"102.74" if symbol=="SOL_USDT" else "720.9"}
        self.orders=[order]
        self.pos=[{"positionId":1234,"symbol":symbol,"positionType":1,
                  "openType":1,"leverage":10,"state":1,"autoAddIm":False,
                  "holdVol":1,"holdAvgPrice":order["dealAvgPrice"],
                  "liquidatePrice":"90" if symbol=="SOL_USDT" else "600"}]
        return {"orderId":9001}
    def simulate_get_order(self,order_id):
        self._fail("read_entry")
        return self.orders[0]
    def simulate_stop(self,*,symbol,position_id,volume,stop_price):
        self._fail("stop")
        self.stops=[{"id":7777,"positionId":1234,"symbol":symbol,
                     "positionType":1,"state":1,"isFinished":0,
                     "lossTrend":2,
                     "vol":0 if self.quantity_lag else volume,
                     "stopLossPrice":str(stop_price),"takeProfitPrice":0}]
        return {"id":7777}
    def simulate_get_positions(self):
        self._fail("read_positions")
        return self.pos
    def simulate_get_stops(self):
        self._fail("read_stops")
        return self.stops
    def simulate_mark(self):
        return "102.75" if self._symbol=="SOL_USDT" else "721"
