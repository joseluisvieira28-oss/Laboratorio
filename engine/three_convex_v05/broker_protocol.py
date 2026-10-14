"""Fail-closed MEXC Futures broker receipt INTERFACE — all evidence synthetic.

No authenticated transport, API client or methods to place orders. The
validators specify exactly what a future adapter must prove after a fill.
A passing simulated receipt is NOT real venue acceptance or trading authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import tempfile


class BrokerGateRejected(ValueError):
    pass


def D(value):
    try:
        d=Decimal(str(value))
    except Exception as exc:
        raise BrokerGateRejected("INVALID_NUMERIC_BROKER_FIELD") from exc
    if not d.is_finite():
        raise BrokerGateRejected("NONFINITE_BROKER_FIELD")
    return d


@dataclass(frozen=True)
class AccountView:
    """Future *authenticated* read-only snapshot. Synthetic in this module."""
    equity: str
    open_position_count: int
    open_order_count: int
    position_mode: str
    margin_mode: str
    leverage: int
    auto_margin_add: bool
    authenticated: bool
    observed_at_ms: int
    user_fee_taker_bps: str
    maintenance_margin_rate: str


def check_account(view: AccountView, now_ms: int):
    if not isinstance(view,AccountView) or view.authenticated is not True:
        raise BrokerGateRejected("NO_AUTHENTICATED_ACCOUNT_READ")
    if not isinstance(now_ms,int) or now_ms-view.observed_at_ms < 0 or now_ms-view.observed_at_ms > 5000:
        raise BrokerGateRejected("STALE_ACCOUNT_SNAPSHOT")
    if view.open_position_count != 0 or view.open_order_count != 0:
        raise BrokerGateRejected("EXISTING_ORDERS_OR_POSITIONS_NOT_RECONCILED")
    if (view.position_mode!="HEDGE" or view.margin_mode!="ISOLATED" or
        view.leverage!=10 or view.auto_margin_add is not False):
        raise BrokerGateRejected("MISMATCHED_HEDGE_ISOLATED_10X_ACCOUNT")
    if D(view.equity)<D("100"):
        raise BrokerGateRejected("EQUITY_BELOW_DECLARED_STARTING_BUDGET")
    if D(view.user_fee_taker_bps)<0 or D(view.maintenance_margin_rate)<=0:
        raise BrokerGateRejected("UNVERIFIED_FEE_OR_MARGIN_MODEL")
    return {"state":"ACCOUNT_READONLY_STRUCTURALLY_PASS",
            "do_not_place_orders":True,
            "this_does_not_authorize_trading":True}


@dataclass(frozen=True)
class PositionReceipt:
    symbol: str
    side: str
    position_id: str
    volume_contracts: int
    entry_price: str
    acknowledged_ms: int
    source: str


@dataclass(frozen=True)
class StopReceipt:
    symbol: str
    side: str
    position_id: str
    protected_volume_contracts: int
    stop_price: str
    trigger_type: str
    broker_order_id: str
    reduce_only: bool
    status: str
    acknowledged_ms: int
    source: str


def validate_filled_stop(position: PositionReceipt, stop: StopReceipt, now_ms: int):
    """Validate identity and quantity. Not proof that supplied receipts are real."""
    if not isinstance(position,PositionReceipt) or not isinstance(stop,StopReceipt):
        raise BrokerGateRejected("RECEIPTS_MISSING")
    if (position.source!="AUTHENTICATED_EXCHANGE_READ" or
        stop.source!="AUTHENTICATED_EXCHANGE_READ"):
        raise BrokerGateRejected("UNVERIFIED_BROKER_RECEIPT_PROVENANCE")
    if position.symbol not in ("SOL_USDT","BNB_USDT") or position.side!="LONG":
        raise BrokerGateRejected("UNFROZEN_SYMBOL_SIDE")
    if (stop.symbol!=position.symbol or stop.side!="LONG" or
        stop.position_id!=position.position_id or not stop.position_id or
        not stop.broker_order_id):
        raise BrokerGateRejected("BROKER_STOP_DOES_NOT_MATCH_POSITION")
    if (type(position.volume_contracts) is not int or position.volume_contracts<1 or
        type(stop.protected_volume_contracts) is not int or
        stop.protected_volume_contracts<position.volume_contracts):
        raise BrokerGateRejected("BROKER_STOP_DOES_NOT_COVER_FILL_VOLUME")
    if stop.trigger_type!="MARK_PRICE" or stop.reduce_only is not True or stop.status!="ACCEPTED":
        raise BrokerGateRejected("BROKER_STOP_NOT_ACCEPTED_PROTECTIVE")
    if (not isinstance(now_ms,int) or
        now_ms-position.acknowledged_ms not in range(0,5001) or
        now_ms-stop.acknowledged_ms not in range(0,5001)):
        raise BrokerGateRejected("STALE_POSITION_OR_STOP_ACK")
    ep=D(position.entry_price); sp=D(stop.stop_price)
    if ep<=0 or sp<=0 or sp>=ep:
        raise BrokerGateRejected("BAD_LONG_STOP_PRICE")
    # Original stop trigger is 4% below filled entry; price tick may require
    # downward rounding. This checks a safety ceiling, NOT tick validity.
    if sp > ep*D(".96"):
        raise BrokerGateRejected("UNFROZEN_OR_TOO_TIGHT_STOP")
    return {"state":"STRUCTURAL_STOP_RECEIPT_MATCH_ONLY",
            "source_assumed_not_independently_authenticated":True,
            "live_authority":"NONE"}


class DurableIntent:
    """Local first-write-wins reservation; never resends unknown requests."""
    def __init__(self, directory):
        self.directory=Path(directory)

    def reserve(self, signal_id, body):
        if not isinstance(signal_id,str) or not signal_id or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-:." for c in signal_id):
            raise BrokerGateRejected("INVALID_SIGNAL_ID")
        self.directory.mkdir(parents=True,exist_ok=True)
        fname=hashlib.sha256(signal_id.encode("utf-8")).hexdigest()+".json"
        path=self.directory/fname
        payload=dict(signal_id=signal_id,body=body,status="RESERVED_NO_ORDER",
                     no_exchange_transport=True)
        try:
            with path.open("x",encoding="utf-8") as f:
                f.write(json.dumps(payload,sort_keys=True,default=str)+"\n")
                f.flush()
                os.fsync(f.fileno())
        except FileExistsError as exc:
            raise BrokerGateRejected("INTENT_ALREADY_RESERVED_NO_BLIND_RESEND") from exc
        return path

    def recover(self, signal_id):
        fname=hashlib.sha256(signal_id.encode("utf-8")).hexdigest()+".json"
        path=self.directory/fname
        if not path.is_file():
            raise BrokerGateRejected("MISSING_INTENT_RECOVERY_HALT")
        p=json.loads(path.read_text(encoding="utf-8"))
        if p.get("signal_id")!=signal_id or p.get("status")!="RESERVED_NO_ORDER":
            raise BrokerGateRejected("UNRECONCILED_INTENT_RECOVERY_HALT")
        return {"state":"UNKNOWN_EXCHANGE_STATE_NO_RESEND",
                "live_authority":"NONE"}
