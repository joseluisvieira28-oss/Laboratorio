"""V08 crash-durable MEXC Futures trade-intent ledger. Never sends orders.

SOL5m/SOL1h share ONE SOL physical position; BNB4h uses one BNB.
Pre-record intent, unknown POST state, and native stop readback separately.
A restart NEVER implicitly retries a broker mutation.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import re
import sqlite3
from pathlib import Path

LANES={"SOL_CONVEX_NATIVE_5M":"SOL_USDT","SOL_CONVEX_1H":"SOL_USDT",
       "BNB_CONVEX_4H":"BNB_USDT"}
PATH={
    "RESERVED":"ENTRY_SUBMIT_UNKNOWN",
    "ENTRY_SUBMIT_UNKNOWN":"ENTRY_ACK",
    "ENTRY_ACK":"FILLED_UNPROTECTED",
    "FILLED_UNPROTECTED":"STOP_SUBMIT_UNKNOWN",
    "STOP_SUBMIT_UNKNOWN":"STOP_ACK",
    "STOP_ACK":"PROTECTED",
    "PROTECTED":"EXIT_SUBMIT_UNKNOWN",
    "EXIT_SUBMIT_UNKNOWN":"EXIT_ACK",
    "EXIT_ACK":"CLOSED",
}

class LedgerHalt(ValueError):pass

@dataclass(frozen=True)
class SignalIntent:
    lane:str
    signal_id:str
    close_ms:int
    observed_ms:int
    direction:str="LONG"
    def __post_init__(self):
        if self.lane not in LANES or self.direction!="LONG":
            raise LedgerHalt("LANE_DIRECTION_UNAUTHORIZED")
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{6,150}",self.signal_id or ""):
            raise LedgerHalt("BAD_SIGNAL_ID")
        if not self.signal_id.startswith(self.lane+":"):
            raise LedgerHalt("SOURCE_ID_LANE_MISMATCH")
        if type(self.close_ms)!=int or type(self.observed_ms)!=int or not 0<=self.observed_ms-self.close_ms<=120000:
            raise LedgerHalt("SIGNAL_STALE_OR_FUTURE")
    @property
    def symbol(self):return LANES[self.lane]
    @property
    def oid(self):
        return "CL8"+hashlib.sha256((self.signal_id+"|"+self.direction).encode()).hexdigest()[:28]

class DurableLedger:
    def __init__(self,data_dir):
        root=Path(data_dir);root.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(root/"V08_ORDER_LEDGER.sqlite3",timeout=3,isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA busy_timeout=3000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS intents(
          oid TEXT PRIMARY KEY, signal_id TEXT NOT NULL UNIQUE, lane TEXT NOT NULL,
          symbol TEXT NOT NULL, created_ms INTEGER NOT NULL,
          state TEXT NOT NULL, order_id TEXT, position_id TEXT,stop_id TEXT);
        CREATE TABLE IF NOT EXISTS receipts(
          id INTEGER PRIMARY KEY AUTOINCREMENT, oid TEXT NOT NULL,
          before_state TEXT,after_state TEXT NOT NULL,utc_ms INTEGER NOT NULL,
          evidence_hash TEXT NOT NULL);
        """)
    def _receipt(self,oid,before,after,utc,evidence):
        h=hashlib.sha256(json.dumps(evidence or {},sort_keys=True,
                  separators=(",",":")).encode()).hexdigest()
        self.db.execute("INSERT INTO receipts(oid,before_state,after_state,utc_ms,evidence_hash) VALUES(?,?,?,?,?)",
                        (oid,before,after,utc,h))
    def reserve(self,signal):
        if not isinstance(signal,SignalIntent):raise LedgerHalt("SIGNAL_TYPE_INVALID")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if self.db.execute("SELECT 1 FROM intents WHERE signal_id=?",
                               (signal.signal_id,)).fetchone():
                raise LedgerHalt("DUPLICATE_SIGNAL_NO_RESEND")
            active=self.db.execute("SELECT symbol,state FROM intents WHERE state!='CLOSED'").fetchall()
            if any(state=="HALTED" for symbol,state in active):
                raise LedgerHalt("HALTED_ACCOUNT_REQUIRES_RECONCILIATION")
            if any(sym==signal.symbol for sym,state in active):
                raise LedgerHalt("PHYSICAL_SYMBOL_ALREADY_RESERVED")
            if len(active)>=2:raise LedgerHalt("MAX_TWO_PHYSICAL_SYMBOLS")
            self.db.execute("INSERT INTO intents(oid,signal_id,lane,symbol,created_ms,state) VALUES(?,?,?,?,?,?)",
                            (signal.oid,signal.signal_id,signal.lane,
                             signal.symbol,signal.observed_ms,"RESERVED"))
            self._receipt(signal.oid,None,"RESERVED",signal.observed_ms,
                          {"source":"PINNED_V5_SIGNAL"})
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK");raise
        return signal.oid
    def advance(self,oid,new_state,utc_ms,*,evidence=None,order_id=None,
                position_id=None,stop_id=None):
        if not re.fullmatch(r"CL8[0-9a-f]{28}",oid or "") or type(utc_ms)!=int or utc_ms<=0:
            raise LedgerHalt("IDENTITY_OR_TIME_INVALID")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT state,created_ms,order_id,position_id,stop_id FROM intents WHERE oid=?",
                                (oid,)).fetchone()
            if not row:raise LedgerHalt("INTENT_ABSENT")
            before,created,stored_order,stored_pos,stored_stop=row
            allowed=PATH.get(before)
            if new_state!="HALTED" and new_state!=allowed:
                raise LedgerHalt("ILLEGAL_TRANSITION")
            if new_state=="HALTED" and before=="CLOSED":
                raise LedgerHalt("CANNOT_HALT_CLOSED")
            if utc_ms<created:raise LedgerHalt("TIME_BEFORE_SOURCE")
            order_id=order_id or stored_order
            position_id=position_id or stored_pos
            stop_id=stop_id or stored_stop
            if new_state=="ENTRY_ACK" and not order_id:raise LedgerHalt("ORDER_ACK_ID_MISSING")
            if new_state=="FILLED_UNPROTECTED" and not position_id:raise LedgerHalt("POSITION_ID_MISSING")
            if new_state=="STOP_ACK" and not stop_id:raise LedgerHalt("STOP_ACK_ID_MISSING")
            if new_state=="PROTECTED":
                if (not isinstance(evidence,dict) or
                    evidence.get("state")!="STRUCTURALLY_MATCHED_ACTIVE_NATIVE_STOP_AFTER_FILL" or
                    evidence.get("stop_readback_after_post_ack") is not True or
                    str(evidence.get("order_id"))!=str(order_id) or
                    str(evidence.get("position_id"))!=str(position_id) or
                    str(evidence.get("stop_id"))!=str(stop_id)):
                    raise LedgerHalt("NATIVE_STOP_READBACK_NOT_PROVEN")
            if new_state=="CLOSED":
                if not isinstance(evidence,dict) or evidence.get("independent_broker_flat_reads")!=2:
                    raise LedgerHalt("TWO_BROKER_FLAT_READS_REQUIRED")
            self.db.execute("UPDATE intents SET state=?,order_id=?,position_id=?,stop_id=? WHERE oid=?",
                            (new_state,order_id,position_id,stop_id,oid))
            self._receipt(oid,before,new_state,utc_ms,evidence)
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK");raise
    def summary(self):
        active=self.db.execute("SELECT lane,symbol,state FROM intents WHERE state!='CLOSED' ORDER BY created_ms").fetchall()
        return {"active":[{"lane":lane,"symbol":sym,"state":state} for lane,sym,state in active],
                "restart_requires_broker_reconciliation":bool(active),
                "unknown_post_never_retried":True,"real_order_authority":"NONE"}
    def close(self):self.db.close()
