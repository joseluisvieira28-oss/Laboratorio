#!/usr/bin/env python3
"""Crypto Lab V2 — deterministic PAPER-ONLY risk firewall with mock execution.

No HTTP, exchange SDK, API keys, order transport, or real trading modes.
This is a model for adversarial failure injection, NOT a production trading system.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from pathlib import Path
import hashlib
import json
import os
import threading
from functools import wraps


class Rejected(Exception):
    """A deterministic fail-closed risk rejection."""


def D(x) -> Decimal:
    try:
        y = Decimal(str(x))
    except (ValueError, TypeError, InvalidOperation):
        raise Rejected("INVALID_DECIMAL")
    if not y.is_finite():
        raise Rejected("NONFINITE_DECIMAL")
    return y


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise Rejected(reason)


def is_sha(s: str) -> bool:
    return isinstance(s, str) and len(s) == 64 and all(c in "0123456789abcdef" for c in s)


@dataclass(frozen=True)
class Policy:
    """Illustrative limits, not trader-authorized or live-deployable settings."""
    strategy_sha: str
    symbol: str = "BTC_USDT"
    per_trade_fraction: str = "0.0025"
    aggregate_fraction: str = "0.005"
    daily_fraction: str = "0.01"
    weekly_fraction: str = "0.03"
    entry_fee: str = "0.0008"
    exit_fee: str = "0.0008"
    adverse_slip_each_side: str = "0.0002"
    funding_reserve_fraction: str = "0.0001"
    max_source_age_ms: int = 1500
    max_session_ms: int = 7_200_000
    max_positions: int = 1

    def __post_init__(self) -> None:
        require(is_sha(self.strategy_sha), "INVALID_STRATEGY_SHA")
        require(self.symbol == "BTC_USDT", "SYMBOL_SCOPE_NOT_APPROVED")
        for field in ("per_trade_fraction", "aggregate_fraction", "daily_fraction",
                      "weekly_fraction", "entry_fee", "exit_fee",
                      "adverse_slip_each_side", "funding_reserve_fraction"):
            value = D(getattr(self, field))
            require(value >= 0, "NEGATIVE_POLICY_VALUE")
        require(D(self.per_trade_fraction) <= D(self.aggregate_fraction), "INVALID_LIMIT_ORDER")
        require(D(self.daily_fraction) <= D(self.weekly_fraction), "INVALID_LOSS_LIMIT_ORDER")
        require(0 < self.max_source_age_ms <= 1500, "UNSAFE_SOURCE_AGE_POLICY")
        require(0 < self.max_session_ms <= 7_200_000, "UNSAFE_SESSION_TTL")
        require(self.max_positions == 1, "MULTI_POSITION_NOT_CERTIFIED")

    @property
    def digest(self) -> str:
        obj = {k: getattr(self, k) for k in self.__dataclass_fields__}
        return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: str
    ask: str
    published_ms: int
    received_ms: int

    def verify(self, now_ms: int, max_age: int) -> tuple[Decimal, Decimal]:
        require(self.symbol == "BTC_USDT", "QUOTE_SYMBOL_MISMATCH")
        bid, ask = D(self.bid), D(self.ask)
        require(0 < bid < ask, "CROSSED_OR_INVALID_BOOK")
        require(type(now_ms) is int and type(self.received_ms) is int
                and type(self.published_ms) is int, "INVALID_QUOTE_CLOCK")
        require(-250 <= self.received_ms - self.published_ms <= max_age,
                "QUOTE_PUBLISHER_STALE")
        require(0 <= now_ms - self.received_ms <= max_age, "QUOTE_RECEIPT_STALE")
        return bid, ask


@dataclass(frozen=True)
class Account:
    """Synthetic test fixture only. NOT an authenticated account attestation."""
    equity: str
    available_margin: str
    open_positions: int
    unmatched_orders: int
    verified_asof_ms: int
    one_way_mode: bool = True
    synthetic_fixture: bool = True

    def verify(self, now_ms: int, max_age: int) -> tuple[Decimal, Decimal]:
        require(self.synthetic_fixture is True, "NON_MOCK_ACCOUNT_NOT_SUPPORTED")
        require(self.one_way_mode, "NETTING_MODE_UNCERTIFIED")
        require(self.open_positions == 0, "PREEXISTING_POSITION_BLOCK")
        require(self.unmatched_orders == 0, "UNRECONCILED_BROKER_ORDERS")
        require(type(self.verified_asof_ms) is int
                and 0 <= now_ms - self.verified_asof_ms <= max_age, "ACCOUNT_SNAPSHOT_STALE")
        equity, available = D(self.equity), D(self.available_margin)
        require(equity > 0 and available > 0 and available <= equity, "ACCOUNT_BALANCE_INVALID")
        return equity, available


@dataclass(frozen=True)
class Intent:
    client_id: str
    strategy_sha: str
    symbol: str
    side: str
    contracts: str
    contract_multiplier: str
    step: str
    minimum_contracts: str
    tick: str
    stop: str
    signal_received_ms: int


@dataclass(frozen=True)
class BrokerScenario:
    """Controlled injection only; no broker actions happen."""
    entry: str = "FILLED"  # FILLED, PARTIAL, REJECTED, TIMEOUT
    filled_contracts: str = "0.01"
    stop: str = "ACK"      # ACK, REJECTED, TIMEOUT, WRONG_QTY, WRONG_SIDE, WEAKER
    flatten: str = "ACK"   # ACK, TIMEOUT


class HashJournal:
    """fsync append-only chain; cannot prove tamper resistance against privileged writers."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.previous = "0" * 64
        if self.path.exists():
            records = self.verify(self.path)
            if records:
                self.previous = records[-1]["hash"]

    @staticmethod
    def verify(path: Path) -> list[dict]:
        previous = "0" * 64
        entries = []
        with Path(path).open("r", encoding="utf-8") as fh:
            for line in fh:
                record = json.loads(line)
                require(record.get("prev") == previous, "JOURNAL_CHAIN_BROKEN")
                payload = {k: record[k] for k in ("prev", "event", "data")}
                digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                                    separators=(",", ":")).encode()).hexdigest()
                require(record.get("hash") == digest, "JOURNAL_HASH_MISMATCH")
                previous = digest
                entries.append(record)
        return entries

    def record(self, event: str, data: dict) -> None:
        require(isinstance(event, str) and bool(event), "EMPTY_EVENT")
        existing = self.verify(self.path) if self.path.exists() and self.path.stat().st_size else []
        current = existing[-1]["hash"] if existing else "0" * 64
        require(current == self.previous, "JOURNAL_EXTERNAL_WRITE_DETECTED")
        payload = {"prev": self.previous, "event": event, "data": data}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                            separators=(",", ":")).encode()).hexdigest()
        payload["hash"] = digest
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(encoded)
            fh.flush()
            os.fsync(fh.fileno())
        self.previous = digest


def synchronized(method):
    """Serialise simulated account state changes and id reservations."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapper


class Firewall:
    """Paper-only state machine: no method can produce or submit a real order."""

    def __init__(self, policy: Policy, journal: HashJournal):
        self.policy = policy
        self.journal = journal
        self._lock = threading.RLock()
        self.state = "DISARMED"
        self.expires_ms = -1
        self.used_ids = set()
        self.daily_loss = Decimal(0)
        self.weekly_loss = Decimal(0)
        self.active = None
        self.last_event = None
        self.loss_locked = False
        # On recovery, journal is authoritative for dedup and loss locks.
        # A recovered session is NEVER automatically armed.
        if self.journal.path.exists() and self.journal.path.stat().st_size:
            records = HashJournal.verify(self.journal.path)
            for event in records:
                if event["event"] == "INTENT_RESERVED":
                    self.used_ids.add(event["data"]["client_id"])
                elif event["event"] == "LOSS_SNAPSHOT":
                    self.daily_loss = max(self.daily_loss, D(event["data"]["daily"]))
                    self.weekly_loss = max(self.weekly_loss, D(event["data"]["weekly"]))
                elif event["event"] == "LOSS_LIMIT":
                    self.loss_locked = True
            self.state = "FROZEN_RECONCILIATION_REQUIRED"

    def _write(self, event: str, data: dict) -> None:
        try:
            self.journal.record(event, data)
        except Exception:
            self.state = "FROZEN_JOURNAL_FAILURE"
            raise Rejected("JOURNAL_WRITE_FAILED")

    @synchronized
    def arm_paper(self, now_ms: int, requested_ttl_ms: int, policy_digest: str,
                  strategy_sha: str, human_approval: bool) -> None:
        require(self.state == "DISARMED", "NOT_DISARMED")
        require(not self.loss_locked, "LOSS_LOCK_PERSISTENT")
        require(human_approval is True, "HUMAN_APPROVAL_REQUIRED")
        require(policy_digest == self.policy.digest, "POLICY_HASH_MISMATCH")
        require(strategy_sha == self.policy.strategy_sha, "STRATEGY_HASH_MISMATCH")
        require(type(now_ms) is int and type(requested_ttl_ms) is int
                and 0 < requested_ttl_ms <= self.policy.max_session_ms,
                "TTL_INVALID")
        self._write("PAPER_ARM", {"policy": policy_digest, "until": now_ms + requested_ttl_ms})
        self.expires_ms = now_ms + requested_ttl_ms
        self.state = "PAPER_ARMED"

    @synchronized
    def disarm(self, reason: str) -> None:
        frozen = self.state.startswith("FROZEN")
        self._write("DISARM", {"reason": reason, "position_known": self.active is not None,
                                "already_frozen": frozen})
        # CRITICAL: an operator DISARM must never clear a loss/unknown-broker freeze.
        if not frozen:
            self.state = "DISARMED" if self.active is None else "FROZEN_POSITION_NEEDS_RECONCILIATION"

    @synchronized
    def loss_mark(self, daily_cash_loss, weekly_cash_loss, now_ms: int, equity) -> None:
        daily, weekly, eq = D(daily_cash_loss), D(weekly_cash_loss), D(equity)
        require(eq > 0 and daily >= 0 and weekly >= 0, "BAD_PNL_SNAPSHOT")
        require(type(now_ms) is int, "BAD_PNL_TIME")
        # No reset by reporting a smaller loss. An actual new risk epoch would
        # need a separate audited procedure; not implemented.
        self.daily_loss = max(self.daily_loss, daily)
        self.weekly_loss = max(self.weekly_loss, weekly)
        self._write("LOSS_SNAPSHOT", {"daily": str(self.daily_loss),
                                      "weekly": str(self.weekly_loss),
                                      "equity": str(eq), "at_ms": now_ms})
        if (self.daily_loss >= eq * D(self.policy.daily_fraction)
                or self.weekly_loss >= eq * D(self.policy.weekly_fraction)):
            self._write("LOSS_LIMIT", {"daily": str(self.daily_loss),
                                       "weekly": str(self.weekly_loss)})
            self.loss_locked = True
            self.state = "FROZEN_LOSS_LIMIT"

    def _preflight(self, intent: Intent, quote: Quote, account: Account,
                   now_ms: int) -> dict:
        require(self.state == "PAPER_ARMED", "NOT_PAPER_ARMED")
        require(now_ms < self.expires_ms, "SESSION_EXPIRED")
        require(not self.active, "EXISTING_PHYSICAL_POSITION")
        require(intent.client_id and len(intent.client_id) <= 100, "INVALID_INTENT_ID")
        require(intent.client_id not in self.used_ids, "DUPLICATE_INTENT")
        require(intent.strategy_sha == self.policy.strategy_sha, "FOREIGN_STRATEGY")
        require(intent.symbol == self.policy.symbol, "FOREIGN_SYMBOL")
        require(intent.side in ("LONG", "SHORT"), "INVALID_DIRECTION")
        require(type(intent.signal_received_ms) is int
                and 0 <= now_ms - intent.signal_received_ms <= self.policy.max_source_age_ms,
                "SIGNAL_STALE")
        equity, available = account.verify(now_ms, self.policy.max_source_age_ms)
        require(self.daily_loss < equity * D(self.policy.daily_fraction)
                and self.weekly_loss < equity * D(self.policy.weekly_fraction),
                "LOSS_CIRCUIT_OPEN")
        bid, ask = quote.verify(now_ms, self.policy.max_source_age_ms)
        qty, mult = D(intent.contracts), D(intent.contract_multiplier)
        step, minimum, tick, stop = map(D, (intent.step,intent.minimum_contracts,intent.tick,intent.stop))
        require(qty > 0 and mult > 0 and step > 0 and minimum > 0 and tick > 0,
                "INVALID_CONTRACT_SPEC")
        require(qty >= minimum and qty % step == 0, "MIN_CONTRACT_OR_STEP")
        require(stop > 0 and stop % tick == 0, "INVALID_STOP_TICK")
        entry = ask if intent.side == "LONG" else bid
        require((stop < bid if intent.side == "LONG" else stop > ask),
                "STOP_WRONG_SIDE_OR_CROSSED")
        notional = entry * qty * mult
        # Planned loss includes stop move, 2-sided taker fees, 2-sided impact and
        # funding reserve; it is not an upper bound on gap/slippage risk.
        stop_move = abs(entry-stop) * qty * mult
        costs = (entry*(D(self.policy.entry_fee)+D(self.policy.adverse_slip_each_side))
                 + stop*(D(self.policy.exit_fee)+D(self.policy.adverse_slip_each_side))
                 + entry*D(self.policy.funding_reserve_fraction)) * qty * mult
        modeled_risk = stop_move + costs
        require(modeled_risk <= equity * D(self.policy.per_trade_fraction),
                "PER_TRADE_RISK_TOO_LARGE")
        require(modeled_risk <= equity * D(self.policy.aggregate_fraction),
                "AGGREGATE_RISK_TOO_LARGE")
        # Intentionally overconservative: assume 1x initial margin until separately
        # verified actual isolated-margin and liquidation mechanics exist.
        require(notional <= available, "INSUFFICIENT_UNLEVERED_MARGIN")
        return {"client_id":intent.client_id, "side":intent.side, "contracts":str(qty),
                "entry_quote":str(entry), "stop":str(stop), "risk_cash":str(modeled_risk),
                "notional":str(notional), "policy_sha":self.policy.digest}

    @synchronized
    def simulate(self, intent: Intent, quote: Quote, account: Account,
                 scenario: BrokerScenario, now_ms: int) -> str:
        try:
            estimate = self._preflight(intent, quote, account, now_ms)
        except Rejected as e:
            # Do not erase a previously frozen state on rejection.
            self._write("PREFLIGHT_REJECT", {"id":intent.client_id,"reason":str(e)})
            return "REJECT:" + str(e)
        # Durable idempotency entry BEFORE any hypothetical broker activity.
        self._write("INTENT_RESERVED", estimate)
        self.used_ids.add(intent.client_id)
        self.state = "PAPER_ENTRY_PENDING"
        if scenario.entry == "REJECTED":
            self._write("ENTRY_REJECTED", {"id":intent.client_id})
            self.state = "PAPER_ARMED"
            return "ENTRY_REJECTED"
        if scenario.entry not in ("FILLED", "PARTIAL"):
            self._write("ENTRY_UNKNOWN", {"id":intent.client_id})
            self.state = "FROZEN_BROKER_UNKNOWN"
            return "FROZEN_ENTRY_UNKNOWN"
        qty = D(scenario.filled_contracts)
        planned = D(intent.contracts)
        if qty <= 0 or qty > planned or (scenario.entry=="FILLED" and qty!=planned) or (scenario.entry=="PARTIAL" and qty==planned):
            self._write("FILL_INCONSISTENT", {"id":intent.client_id,"qty":str(qty)})
            self.state = "FROZEN_BROKER_UNKNOWN"
            return "FROZEN_FILL_MISMATCH"
        self.active = {"id":intent.client_id, "side":intent.side,
                       "filled_contracts":str(qty), "stop":intent.stop,
                       "stop_ack":False}
        self._write("PAPER_FILL", dict(self.active))
        self.state = "PAPER_UNPROTECTED_GAP"
        if scenario.stop != "ACK":
            self._write("STOP_NOT_ACKNOWLEDGED", {"reason":scenario.stop,
                                                  "id":intent.client_id})
            if scenario.flatten == "ACK":
                self._write("EMERGENCY_FLATTEN_SIMULATED_ACK", {"id":intent.client_id})
                self.active = None
                self.state = "FROZEN_AFTER_EMERGENCY_FLATTEN"
                return "FROZEN_FLATTEN_ACK"
            self._write("EMERGENCY_FLATTEN_UNKNOWN", {"id":intent.client_id})
            self.state = "FROZEN_EXPOSURE_UNKNOWN"
            return "FROZEN_EXPOSURE_UNKNOWN"
        self.active["stop_ack"] = True
        self._write("PAPER_STOP_ACK", dict(self.active))
        self.state = "PAPER_PROTECTED"
        return "PAPER_PROTECTED"

    @synchronized
    def reconcile_flat(self, *, paper_broker_flat: bool, human_approval: bool) -> None:
        require(not self.loss_locked, "LOSS_LOCK_PERSISTENT")
        require(self.state.startswith("FROZEN") or self.state == "PAPER_PROTECTED",
                "RECONCILIATION_NOT_NEEDED")
        require(human_approval is True and paper_broker_flat is True,
                "RECONCILIATION_PROOF_MISSING")
        self._write("PAPER_RECONCILED_FLAT", {"verified_paper_only":True})
        self.active = None
        self.expires_ms = -1
        self.state = "DISARMED"


def live_enabled() -> bool:
    """Hard fail-closed compile-time guard, not a switch."""
    return False
