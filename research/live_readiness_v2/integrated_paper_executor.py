#!/usr/bin/env python3
"""Integrated, PAPER-ONLY crash-boundary research executor.

Combines risk_firewall.py and single_writer_recovery.py with a *separate* SQLite
simulated exchange ledger. Never opens network connections or sends real orders.
This is deliberately NOT production-ready: there is no external broker fencing,
real position/stop acknowledgment, or cryptographic human authentication.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import os
import sqlite3

from risk_firewall import Account, Firewall, HashJournal, Intent, Policy, Quote, Rejected
from single_writer_recovery import GuardError, PaperFencedStore, Ticket


class PaperBroker:
    """Independent persistent mock broker representing side effects across crash."""

    def __init__(self, path: Path):
        self.path=Path(path)
        self.db=sqlite3.connect(str(self.path),timeout=5,isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("""CREATE TABLE IF NOT EXISTS paper_orders(
           client_id TEXT PRIMARY KEY, symbol TEXT NOT NULL, side TEXT NOT NULL,
           volume TEXT NOT NULL, stop_price TEXT NOT NULL, state TEXT NOT NULL,
           created_ms INTEGER NOT NULL, updated_ms INTEGER NOT NULL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS paper_receipts(
           seq INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL,
           client_id TEXT NOT NULL, at_ms INTEGER NOT NULL)""")

    def close(self):
        self.db.close()

    def _event(self, name, client_id, now_ms):
        self.db.execute("INSERT INTO paper_receipts(event,client_id,at_ms) VALUES(?,?,?)",
                        (name,client_id,now_ms))

    def accept_paper_entry(self, intent: Intent, now_ms: int) -> None:
        """Durable independent simulated fill; explicitly not a market fill."""
        if intent.symbol!="BTC_USDT" or intent.side not in ("LONG","SHORT"):
            raise GuardError("MOCK_BROKER_SYMBOL_OR_SIDE")
        if Decimal(intent.contracts)<=0:
            raise GuardError("MOCK_BROKER_INVALID_VOLUME")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if self.db.execute("SELECT 1 FROM paper_orders WHERE client_id=?",
                               (intent.client_id,)).fetchone():
                raise GuardError("MOCK_BROKER_DUPLICATE_CLIENT_ID")
            if self.db.execute("""SELECT 1 FROM paper_orders
                 WHERE state<>'FLAT' LIMIT 1""").fetchone():
                raise GuardError("MOCK_BROKER_EXISTING_POSITION")
            self.db.execute("""INSERT INTO paper_orders
               (client_id,symbol,side,volume,stop_price,state,created_ms,updated_ms)
               VALUES (?,?,?,?,?,'FILLED_NO_STOP',?,?)""",
               (intent.client_id,intent.symbol,intent.side,intent.contracts,
                intent.stop,now_ms,now_ms))
            self._event("SIMULATED_ENTRY_FILLED",intent.client_id,now_ms)
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        else:self.db.execute("COMMIT")

    def ack_paper_stop(self, client_id: str, qty: str, stop_price: str,
                       now_ms: int) -> None:
        """Mock broker validates matched stop; no real stop or guarantee."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("""SELECT volume,stop_price,state FROM paper_orders
                                    WHERE client_id=?""",(client_id,)).fetchone()
            if row is None or row[2]!="FILLED_NO_STOP":
                raise GuardError("MOCK_STOP_WRONG_STATE")
            if Decimal(str(qty))!=Decimal(row[0]) or Decimal(str(stop_price))!=Decimal(row[1]):
                raise GuardError("MOCK_STOP_QTY_OR_PRICE_MISMATCH")
            self.db.execute("""UPDATE paper_orders SET state='STOP_ACTIVE',
                               updated_ms=? WHERE client_id=?""",(now_ms,client_id))
            self._event("SIMULATED_SERVER_STOP_ACK",client_id,now_ms)
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        else:self.db.execute("COMMIT")

    def human_mock_flatten(self, client_id: str, now_ms: int,
                           *, human_approval: bool) -> None:
        if human_approval is not True:
            raise GuardError("MOCK_FLATTEN_REQUIRES_OPERATOR")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT state FROM paper_orders WHERE client_id=?",
                                (client_id,)).fetchone()
            if row is None or row[0]=="FLAT":
                raise GuardError("NO_OPEN_MOCK_POSITION")
            self.db.execute("""UPDATE paper_orders SET state='FLAT',updated_ms=?
                                WHERE client_id=?""",(now_ms,client_id))
            self._event("SIMULATED_OPERATOR_CLOSED",client_id,now_ms)
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        else:self.db.execute("COMMIT")

    def snapshot(self) -> dict:
        rows=self.db.execute("""SELECT client_id,symbol,side,volume,stop_price,state
                                FROM paper_orders ORDER BY client_id""").fetchall()
        receipts=self.db.execute("SELECT COUNT(*) FROM paper_receipts").fetchone()[0]
        return {
          "orders":[dict(zip(("id","symbol","side","volume","stop","state"),r)) for r in rows],
          "mock_receipts":receipts,
          "open_positions":sum(r[5]!="FLAT" for r in rows),
          "server_stops":sum(r[5]=="STOP_ACTIVE" for r in rows),
          "unprotected_positions":sum(r[5]=="FILLED_NO_STOP" for r in rows),
          "is_flat":all(r[5]=="FLAT" for r in rows),
          "source":"OFFLINE_SEPARATE_PERSISTENT_MOCK_ONLY"
        }


class PaperCoordinator:
    """Main controller. Local fenced store is authoritative for reservation.

    All external-order semantics are intentionally absent; this entire module
    is a research-only paper-model integration, not an exchange adapter.
    """

    def __init__(self, directory: str | Path, policy: Policy):
        self.directory=Path(directory)
        if not self.directory.is_dir():
            raise GuardError("PAPER_DIRECTORY_MISSING")
        self.policy=policy
        self.custody=PaperFencedStore(self.directory/"custody.sqlite")
        try:
            self.broker=PaperBroker(self.directory/"mock_broker.sqlite")
        except BaseException:
            self.custody.close()
            raise
        self.ticket: Ticket | None=None
        self.firewall: Firewall | None=None

    def close(self):
        self.broker.close()
        self.custody.close()

    def claim(self, now_ms: int) -> Ticket:
        self.ticket=self.custody.claim(now_ms)
        self.firewall=Firewall(self.policy,HashJournal(
             self.directory/f"paper_risk_epoch_{self.ticket.epoch}.ndjson"))
        return self.ticket

    def _ticket(self) -> Ticket:
        if self.ticket is None:
            raise GuardError("NO_CUSTODY_TICKET")
        return self.ticket

    def arm(self, now_ms: int, account: Account, *,
            human_approval: bool, ttl_ms: int=8000) -> None:
        ticket=self._ticket()
        if self.firewall is None:
            raise GuardError("NO_INDEPENDENT_RISK_FIREWALL")
        equity,_=account.verify(now_ms,self.policy.max_source_age_ms)
        # Durably compare against cumulative historical loss before allowing ARM.
        snapshot=self.custody.record_paper_loss(
             ticket,now_ms,daily_cash="0",weekly_cash="0",equity_cash=equity,
             daily_fraction=self.policy.daily_fraction,
             weekly_fraction=self.policy.weekly_fraction)
        if snapshot["locked"]:
            raise GuardError("PERSISTENT_LOSS_LOCK")
        self.firewall.arm_paper(now_ms,ttl_ms,self.policy.digest,
                                self.policy.strategy_sha,human_approval)
        self.firewall.loss_mark(snapshot["daily"],snapshot["weekly"],now_ms,equity)
        if self.firewall.state!="PAPER_ARMED":
            raise GuardError("INDEPENDENT_RISK_GATE_FROZEN")
        try:
            self.custody.arm_paper(ticket,now_ms,human_approval=human_approval,
                   policy_sha=self.policy.digest,
                   strategy_sha=self.policy.strategy_sha,ttl_ms=ttl_ms)
        except BaseException:
            self.firewall.disarm("CUSTODY_ARM_DENIED")
            raise

    def record_loss(self, now_ms: int, account: Account,
                    daily_cash, weekly_cash) -> dict:
        ticket=self._ticket()
        equity,_=account.verify(now_ms,self.policy.max_source_age_ms)
        result=self.custody.record_paper_loss(ticket,now_ms,
                 daily_cash=daily_cash,weekly_cash=weekly_cash,equity_cash=equity,
                 daily_fraction=self.policy.daily_fraction,
                 weekly_fraction=self.policy.weekly_fraction)
        if self.firewall is not None:
            self.firewall.loss_mark(result["daily"],result["weekly"],now_ms,equity)
        return result

    def enter(self, now_ms: int, intent: Intent, quote: Quote,
              account: Account, *, fault_at: str|None=None,
              stop_result: str="ACK") -> str:
        ticket=self._ticket()
        if self.firewall is None:
            raise GuardError("MISSING_RISK_GATE")
        # Preflight risk must pass BEFORE the durable paper reservation.
        try:
            self.firewall._preflight(intent,quote,account,now_ms)
        except Rejected as ex:
            return "REJECT_RISK:"+str(ex)
        equity,_=account.verify(now_ms,self.policy.max_source_age_ms)
        stored=self.custody.record_paper_loss(ticket,now_ms,
                 daily_cash=self.firewall.daily_loss,
                 weekly_cash=self.firewall.weekly_loss,equity_cash=equity,
                 daily_fraction=self.policy.daily_fraction,
                 weekly_fraction=self.policy.weekly_fraction)
        if stored["locked"]:
            return "FROZEN_PERSISTENT_LOSS"
        self.custody.reserve(ticket,now_ms,intent.client_id,intent.strategy_sha)
        if fault_at=="AFTER_RESERVATION":
            os._exit(41)  # hard process-exit fault injection; PAPER ONLY
        self.broker.accept_paper_entry(intent,now_ms)
        if fault_at=="AFTER_BROKER_FILL":
            os._exit(42)
        self.custody.change_mock_intent(ticket,now_ms,intent.client_id,
                                        "PENDING","FILLED_UNPROTECTED")
        if stop_result!="ACK":
            self.custody.disarm(ticket,now_ms)
            if self.firewall.state=="PAPER_ARMED":
                self.firewall.disarm("MOCK_STOP_NOT_CONFIRMED")
            return "FROZEN_MOCK_UNPROTECTED"
        self.broker.ack_paper_stop(intent.client_id,intent.contracts,intent.stop,now_ms)
        if fault_at=="AFTER_BROKER_STOP_ACK":
            os._exit(43)
        self.custody.change_mock_intent(ticket,now_ms,intent.client_id,
                                        "FILLED_UNPROTECTED","PROTECTED")
        return "PAPER_PROTECTED_MOCK_ONLY"

    def close_protected_paper(self, now_ms: int, client_id: str,
                              *, human_approval: bool) -> None:
        ticket=self._ticket()
        local=self.custody.inspect()
        if local["phase"]!="PAPER_ARMED" or not any(
             x["id"]==client_id and x["state"]=="PROTECTED" for x in local["intents"]):
            raise GuardError("CUSTODY_NOT_PROTECTED")
        self.broker.human_mock_flatten(client_id,now_ms,human_approval=human_approval)
        self.custody.change_mock_intent(ticket,now_ms,client_id,"PROTECTED","CLOSED")

    def reconcile_paper(self, now_ms: int, *, human_approval: bool) -> None:
        ticket=self._ticket()
        if human_approval is not True:
            raise GuardError("HUMAN_APPROVAL_REQUIRED")
        # Two separately persisted ledgers must be inspected every time.
        broker=self.broker.snapshot()
        local=self.custody.inspect()
        local_ids={x["id"] for x in local["intents"]}
        remote_ids={x["id"] for x in broker["orders"]}
        if remote_ids-local_ids:
            raise GuardError("MOCK_BROKER_ORPHAN_NOT_IN_CUSTODY")
        if not broker["is_flat"] or broker["open_positions"] or broker["server_stops"]:
            raise GuardError("MOCK_BROKER_NOT_FLAT_UNSAFE_RECONCILIATION")
        closed_ids=[x["id"] for x in broker["orders"] if x["state"]=="FLAT"]
        self.custody.reconcile_flat(ticket,now_ms,
               human_approval=True,mock_flat_confirmed=True,
               mock_confirmed_closed_ids=closed_ids)

    def status(self) -> dict:
        return {"custody":self.custody.inspect(),
                "mock_broker":self.broker.snapshot(),
                "live_enabled":False}


def live_enabled() -> bool:
    return False
