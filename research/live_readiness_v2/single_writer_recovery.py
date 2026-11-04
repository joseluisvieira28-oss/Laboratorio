#!/usr/bin/env python3
"""SQLite-fenced PAPER-ONLY single-writer and crash-recovery research prototype.

No exchange adapters, external networking, API keys, real orders or live arm path.
SQLite locking is local to one correctly shared database; this does not establish
a distributed lease or fence any broker-side in-flight order.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import uuid


class GuardError(Exception):
    pass


@dataclass(frozen=True)
class Ticket:
    owner: str
    epoch: int
    process_id: int


@dataclass(frozen=True)
class Denied:
    reason: str


class PaperFencedStore:
    """One SQLite writer at a time using BEGIN IMMEDIATE and epoch fencing.

    A lease is never authority to trade: only a paper session can be armed.
    Expired owners never get automatic recovery, even when no intent is pending.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if str(self.path) == ":memory:":
            raise GuardError("PERSISTENT_FILE_REQUIRED")
        if not self.path.parent.is_dir():
            raise GuardError("JOURNAL_DIRECTORY_MISSING")
        self.db = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("""CREATE TABLE IF NOT EXISTS owner_state (
             id INTEGER PRIMARY KEY CHECK(id=1),
             owner TEXT, epoch INTEGER NOT NULL, lease_until_ms INTEGER NOT NULL,
             last_ms INTEGER NOT NULL, phase TEXT NOT NULL,
             session_until_ms INTEGER NOT NULL, policy_sha TEXT, strategy_sha TEXT,
             hard_lock INTEGER NOT NULL CHECK(hard_lock IN (0,1)),
             last_digest TEXT NOT NULL)""")
        self.db.execute("""INSERT OR IGNORE INTO owner_state
             (id,owner,epoch,lease_until_ms,last_ms,phase,session_until_ms,
              policy_sha,strategy_sha,hard_lock,last_digest)
             VALUES (1,NULL,0,0,0,'DISARMED',0,NULL,NULL,0,?)""", ("0"*64,))
        self.db.execute("""CREATE TABLE IF NOT EXISTS paper_intents (
             client_id TEXT PRIMARY KEY, epoch INTEGER NOT NULL,
             state TEXT NOT NULL, created_ms INTEGER NOT NULL, updated_ms INTEGER NOT NULL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS audit (
             seq INTEGER PRIMARY KEY AUTOINCREMENT, at_ms INTEGER NOT NULL,
             epoch INTEGER NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL,
             previous_digest TEXT NOT NULL, digest TEXT NOT NULL)""")
        # Refuse to boot if evidence is corrupt, and close the database even
        # when startup verification raises (Windows holds open files locked).
        try:
            self.verify_audit()
        except BaseException:
            self.db.close()
            raise

    def close(self) -> None:
        self.db.close()

    @contextmanager
    def _tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")

    def _meta(self) -> dict:
        cur = self.db.execute("""SELECT owner,epoch,lease_until_ms,last_ms,phase,
            session_until_ms,policy_sha,strategy_sha,hard_lock,last_digest
            FROM owner_state WHERE id=1""")
        fields = ("owner","epoch","lease_until_ms","last_ms","phase","session_until_ms",
                  "policy_sha","strategy_sha","hard_lock","last_digest")
        return dict(zip(fields,cur.fetchone()))

    def _event(self, epoch: int, at_ms: int, event: str, detail: dict) -> None:
        prev = self._meta()["last_digest"]
        payload = json.dumps({"at_ms":at_ms,"epoch":epoch,"event":event,
                              "detail":detail,"prev":prev},
                             sort_keys=True,separators=(",",":"))
        digest=hashlib.sha256(payload.encode()).hexdigest()
        self.db.execute("""INSERT INTO audit(at_ms,epoch,event,detail,previous_digest,digest)
                          VALUES(?,?,?,?,?,?)""",
                        (at_ms,epoch,event,json.dumps(detail,sort_keys=True),prev,digest))
        self.db.execute("UPDATE owner_state SET last_digest=? WHERE id=1",(digest,))

    @staticmethod
    def _time(now_ms: int) -> None:
        if type(now_ms) is not int or now_ms<=0:
            raise GuardError("INVALID_TIME")

    @staticmethod
    def _sha(s: str) -> bool:
        return isinstance(s,str) and len(s)==64 and all(x in "0123456789abcdef" for x in s)

    def _guard(self, m: dict, ticket: Ticket, now_ms: int):
        self._time(now_ms)
        if ticket.process_id != os.getpid():
            return Denied("TICKET_PROCESS_MISMATCH")
        if now_ms < m["last_ms"]:
            # Persisted circuit breaker, not rolled back by raising.
            self.db.execute("UPDATE owner_state SET hard_lock=1,phase='FROZEN_CLOCK' WHERE id=1")
            self._event(m["epoch"],now_ms,"CLOCK_ROLLBACK",{})
            return Denied("CLOCK_ROLLBACK_HARD_LOCK")
        if m["hard_lock"]:
            return Denied("PERSISTENT_HARD_LOCK")
        if m["owner"]!=ticket.owner or m["epoch"]!=ticket.epoch:
            return Denied("STALE_FENCING_TOKEN")
        if now_ms>=m["lease_until_ms"]:
            return Denied("LEASE_EXPIRED")
        self.db.execute("UPDATE owner_state SET last_ms=? WHERE id=1",(now_ms,))
        return None

    def _run(self, ticket: Ticket, now_ms: int, callback):
        denial=None;result=None
        with self._tx():
            m=self._meta()
            denial=self._guard(m,ticket,now_ms)
            if denial is None:
                result=callback(m)
        if denial is not None:
            raise GuardError(denial.reason)
        return result

    def claim(self, now_ms: int, lease_ms: int=30000) -> Ticket:
        self._time(now_ms)
        if type(lease_ms) is not int or not 1000<=lease_ms<=60000:
            raise GuardError("LEASE_TTL_INVALID")
        denial=None
        ticket=None
        with self._tx():
            m=self._meta()
            if now_ms<m["last_ms"]:
                self.db.execute("UPDATE owner_state SET hard_lock=1,phase='FROZEN_CLOCK' WHERE id=1")
                self._event(m["epoch"],now_ms,"CLOCK_ROLLBACK",{})
                denial="CLOCK_ROLLBACK_HARD_LOCK"
            elif m["owner"] is not None and now_ms<m["lease_until_ms"]:
                denial="LEASE_HELD_BY_OTHER"
            elif m["hard_lock"]:
                denial="PERSISTENT_HARD_LOCK"
            else:
                owner=uuid.uuid4().hex
                epoch=m["epoch"]+1
                # Never resume automatically after any previously held lease.
                phase="DISARMED" if m["epoch"]==0 else "FROZEN_RECOVERY_REQUIRED"
                self.db.execute("""UPDATE owner_state SET owner=?,epoch=?,lease_until_ms=?,
                     last_ms=?,phase=?,session_until_ms=0,policy_sha=NULL,strategy_sha=NULL
                     WHERE id=1""",(owner,epoch,now_ms+lease_ms,now_ms,phase))
                self._event(epoch,now_ms,"FENCE_CLAIM",{"recovery_required":epoch>1})
                ticket=Ticket(owner,epoch,os.getpid())
        if denial:raise GuardError(denial)
        return ticket

    def renew(self, ticket: Ticket, now_ms: int, lease_ms: int=30000) -> None:
        if type(lease_ms) is not int or not 1000<=lease_ms<=60000:
            raise GuardError("LEASE_TTL_INVALID")
        def action(m):
            self.db.execute("UPDATE owner_state SET lease_until_ms=? WHERE id=1",
                            (now_ms+lease_ms,))
            self._event(m["epoch"],now_ms,"FENCE_RENEW",{})
        self._run(ticket,now_ms,action)

    def arm_paper(self, ticket: Ticket, now_ms: int, *, human_approval: bool,
                  policy_sha: str, strategy_sha: str, ttl_ms: int=10000) -> None:
        if human_approval is not True:
            raise GuardError("HUMAN_PAPER_APPROVAL_REQUIRED")
        if not self._sha(policy_sha) or not self._sha(strategy_sha):
            raise GuardError("INVALID_STRATEGY_OR_POLICY_SHA")
        if type(ttl_ms) is not int or not 1000<=ttl_ms<=10000:
            raise GuardError("SESSION_TTL_INVALID")
        def action(m):
            if m["phase"]!="DISARMED":raise GuardError("RECOVERY_OR_FREEZE_BLOCK")
            if now_ms+ttl_ms>m["lease_until_ms"]:
                raise GuardError("SESSION_OUTLASTS_FENCE")
            unresolved=self.db.execute("""SELECT COUNT(*) FROM paper_intents
                WHERE state NOT IN ('CLOSED','CANCELLED')""").fetchone()[0]
            if unresolved:raise GuardError("UNRESOLVED_PAPER_INTENTS")
            self.db.execute("""UPDATE owner_state SET phase='PAPER_ARMED',
               session_until_ms=?, policy_sha=?,strategy_sha=? WHERE id=1""",
                            (now_ms+ttl_ms,policy_sha,strategy_sha))
            self._event(m["epoch"],now_ms,"PAPER_ARM",{"until":now_ms+ttl_ms})
        self._run(ticket,now_ms,action)

    def reserve(self, ticket: Ticket, now_ms: int, client_id: str,
                strategy_sha: str, *, crash_before_commit: bool=False) -> None:
        if not isinstance(client_id,str) or not 1<=len(client_id)<=100:
            raise GuardError("INVALID_CLIENT_ID")
        def action(m):
            if m["phase"]!="PAPER_ARMED" or now_ms>=m["session_until_ms"]:
                raise GuardError("NOT_PAPER_ARMED")
            if strategy_sha!=m["strategy_sha"]:
                raise GuardError("WRONG_STRATEGY")
            if self.db.execute("SELECT 1 FROM paper_intents WHERE client_id=?",
                               (client_id,)).fetchone():
                raise GuardError("DUPLICATE_INTENT_PERSISTENT")
            if self.db.execute("""SELECT 1 FROM paper_intents
                 WHERE state NOT IN ('CLOSED','CANCELLED') LIMIT 1""").fetchone():
                raise GuardError("ANOTHER_POSITION_OR_ORDER_PENDING")
            self.db.execute("""INSERT INTO paper_intents
                 (client_id,epoch,state,created_ms,updated_ms) VALUES(?,?,'PENDING',?,?)""",
                            (client_id,m["epoch"],now_ms,now_ms))
            self._event(m["epoch"],now_ms,"PAPER_INTENT_RESERVED",{"id":client_id})
            if crash_before_commit:
                raise RuntimeError("INJECTED_POWER_LOSS_BEFORE_COMMIT")
        self._run(ticket,now_ms,action)

    def change_mock_intent(self, ticket: Ticket, now_ms: int, client_id: str,
                           expected: str, to_state: str) -> None:
        if (expected,to_state) not in (
            ("PENDING","FILLED_UNPROTECTED"),
            ("FILLED_UNPROTECTED","PROTECTED"),
            ("PENDING","CANCELLED"),
            ("PROTECTED","CLOSED"),
        ):
            raise GuardError("INVALID_MOCK_TRANSITION")
        def action(m):
            if m["phase"]!="PAPER_ARMED" or now_ms>=m["session_until_ms"]:
                raise GuardError("NOT_PAPER_ARMED")
            row=self.db.execute("SELECT state FROM paper_intents WHERE client_id=?",
                                (client_id,)).fetchone()
            if row is None or row[0]!=expected:raise GuardError("UNKNOWN_OR_INCONSISTENT_INTENT")
            self.db.execute("UPDATE paper_intents SET state=?,updated_ms=? WHERE client_id=?",
                            (to_state,now_ms,client_id))
            self._event(m["epoch"],now_ms,"MOCK_"+to_state,{"id":client_id})
        self._run(ticket,now_ms,action)

    def disarm(self, ticket: Ticket, now_ms: int) -> None:
        def action(m):
            if m["phase"]!="PAPER_ARMED":
                raise GuardError("NO_ACTIVE_PAPER_SESSION")
            unresolved=self.db.execute("""SELECT COUNT(*) FROM paper_intents
                WHERE state NOT IN ('CLOSED','CANCELLED')""").fetchone()[0]
            new="FROZEN_RECOVERY_REQUIRED" if unresolved else "DISARMED"
            self.db.execute("UPDATE owner_state SET phase=?,session_until_ms=0 WHERE id=1",
                            (new,))
            self._event(m["epoch"],now_ms,"DISARM_PAPER",{"unresolved":unresolved})
        self._run(ticket,now_ms,action)

    def reconcile_flat(self, ticket: Ticket, now_ms: int, *,
                       human_approval: bool, mock_flat_confirmed: bool) -> None:
        if human_approval is not True or mock_flat_confirmed is not True:
            raise GuardError("MOCK_RECOVERY_PROOF_REQUIRED")
        def action(m):
            if m["phase"]!="FROZEN_RECOVERY_REQUIRED":
                raise GuardError("RECOVERY_NOT_REQUIRED")
            self.db.execute("""UPDATE paper_intents SET state='CANCELLED',updated_ms=?
                 WHERE state NOT IN ('CLOSED','CANCELLED')""",(now_ms,))
            self.db.execute("""UPDATE owner_state SET phase='DISARMED',
                 session_until_ms=0 WHERE id=1""")
            self._event(m["epoch"],now_ms,"PAPER_RECONCILED_FLAT",{"mock_only":True})
        self._run(ticket,now_ms,action)

    def inspect(self) -> dict:
        m=self._meta()
        intents=self.db.execute("SELECT client_id,state,epoch FROM paper_intents ORDER BY client_id").fetchall()
        return {"epoch":m["epoch"],"phase":m["phase"],"owner":m["owner"],
                "lease_until_ms":m["lease_until_ms"],"hard_lock":bool(m["hard_lock"]),
                "session_until_ms":m["session_until_ms"],
                "intents":[{"id":a,"state":b,"epoch":c} for a,b,c in intents]}

    def verify_audit(self) -> int:
        prev="0"*64;count=0
        for at_ms,epoch,event,detail,previous,digest in self.db.execute(
           "SELECT at_ms,epoch,event,detail,previous_digest,digest FROM audit ORDER BY seq"):
            if previous!=prev:raise GuardError("AUDIT_CHAIN_BROKEN")
            payload=json.dumps({"at_ms":at_ms,"epoch":epoch,"event":event,
                                "detail":json.loads(detail),"prev":previous},
                               sort_keys=True,separators=(",",":"))
            expected=hashlib.sha256(payload.encode()).hexdigest()
            if digest!=expected:raise GuardError("AUDIT_DIGEST_MISMATCH")
            prev=digest;count+=1
        if prev!=self._meta()["last_digest"]:
            raise GuardError("AUDIT_HEAD_MISMATCH")
        return count


def live_enabled() -> bool:
    return False
