"""Three CONVEX V5 offline shadow engine — NEVER a real exchange executor.

Source original signal, 4% initial stop / conditional NONLATCHED 12% trailing.
A single physical LONG exposure per symbol, up to two symbols. Automated
symbol/timeframe signal evaluation, model costs, receipts, risk checks, gap
handling and crash-safe *output receipts*. No API keys or network/POST.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path

from engine.three_convex_v05.signals import (
    Bar, Halt, MS5, PERIODS, SYMBOLS, aggregate_complete,
    parent_signal_function,
)

RISK_TRADE = Decimal("0.50")
RISK_GLOBAL = Decimal("1.50")
RISK_SOL = Decimal("1.00")
LEVERAGE = Decimal("10")
FEE = Decimal("0.0008")
SLIP = Decimal("0.0002")
FUND_RESERVE = Decimal("0.0005")
STOP = Decimal("0.04")
TRAIL = Decimal("0.12")
ACTIVATE = Decimal("0.05")
CONTRACT_BASE_QTY = {"SOL_USDT": Decimal("0.1"), "BNB_USDT": Decimal("0.01")}
CAPITAL_DECLARED = Decimal("100")
MIN_REQUIRED_PARENT_TF_BARS = 250
PREREG_ID = "THREE_CONVEX_V05_SHADOW_PREOUTCOME_2026_10_14"


def dec(value):
    d = Decimal(str(value))
    if not d.is_finite():
        raise Halt("NONFINITE_MODEL_VALUE")
    return d


def raw_market_bars(rows):
    """Input rows MUST contain a declared historical/prospective source."""
    data = {"SOL_USDT": [], "BNB_USDT": []}
    for row in rows:
        symbol = row.get("symbol")
        if symbol not in data:
            raise Halt("INVALID_SYMBOL")
        if row.get("source") != "BINANCE_USDM_CANONICAL_5M":
            raise Halt("INVALID_CANONICAL_SOURCE_ID")
        try:
            bar = Bar(t=row["t"], open=row["open"], high=row["high"],
                      low=row["low"], close=row["close"], volume=row["volume"]).validate()
        except (KeyError, TypeError) as exc:
            raise Halt("BAD_BAR_SHAPE") from exc
        data[symbol].append(bar)
    if not data["SOL_USDT"] or not data["BNB_USDT"]:
        raise Halt("BOTH_SYMBOLS_REQUIRED")
    for sym, bars in data.items():
        if any(b.t != bars[0].t + i*MS5 for i,b in enumerate(bars)):
            raise Halt("GAP_REORDER_OR_DUPLICATE_" + sym)
    return data


def build_signal_schedule(data):
    """Compute exact pinned-parent V5 flags once per timeframe; never look ahead."""
    fn = parent_signal_function()
    events = {}
    evidence = []
    for lane,n in PERIODS.items():
        symbol = SYMBOLS[lane]
        bars = aggregate_complete(data[symbol], n)
        if len(bars) < MIN_REQUIRED_PARENT_TF_BARS:
            evidence.append({"lane":lane,"tf_bars":len(bars),"status":"INSUFFICIENT_SOURCE_WARMUP"})
            continue
        flags, detail = fn(bars)
        if len(flags)!=len(bars):
            raise Halt("PINNED_PARENT_SIGNAL_LENGTH")
        admitted = 0
        for i in range(MIN_REQUIRED_PARENT_TF_BARS-1,len(bars)):
            if not flags[i]:
                continue
            close_ms = bars[i]["t"] + n*MS5
            uid = f"{lane}:{close_ms}"
            events.setdefault(close_ms,[]).append(dict(lane=lane,symbol=symbol,
                signal_id=uid,signal_close_ms=close_ms,
                entry_open_ms=close_ms+MS5,score=detail[i]["score"]))
            admitted += 1
        evidence.append({"lane":lane,"tf_bars":len(bars),"status":"PARENT_SIGNAL_COMPUTED",
                         "signals":admitted,"first_admissible_tf_end":bars[MIN_REQUIRED_PARENT_TF_BARS-1]["t"]+n*MS5})
    return events,evidence


@dataclass
class PaperPosition:
    lane: str
    signal_id: str
    symbol: str
    contracts: int
    qty: Decimal
    entry_t: int
    entry: Decimal
    initial_stop: Decimal
    stop: Decimal
    peak: Decimal
    modeled_cash_risk: Decimal
    entry_fee: Decimal
    funding_reserve: Decimal


def model_one_contract(symbol, ask):
    """Illustrative one-minimum-contract LOSS-AT-STOP, NOT a loss cap."""
    if symbol not in CONTRACT_BASE_QTY:
        raise Halt("UNKNOWN_CONTRACT")
    a = dec(ask)
    if a <= 0:
        raise Halt("BAD_QUOTE")
    qty = CONTRACT_BASE_QTY[symbol]
    entry = a*(1+SLIP)
    stop = entry*(1-STOP)
    modeled_fill = stop*(1-SLIP)
    cash_risk = qty*((entry-modeled_fill)+entry*FEE+modeled_fill*FEE+entry*FUND_RESERVE)
    margin = qty*entry/LEVERAGE
    if cash_risk>RISK_TRADE or margin>CAPITAL_DECLARED:
        raise Halt("MIN_ONE_CONTRACT_RISK_OR_MARGIN_EXCEEDS_BUDGET")
    return dict(qty=qty, entry=entry, stop=stop, margin=margin, cash_risk=cash_risk,
                entry_fee=entry*qty*FEE, funding_reserve=qty*entry*FUND_RESERVE,
                modeled_exit_fee=modeled_fill*qty*FEE)


class ShadowMotor:
    """Research-only bar replay; no broker transport, credentials or order mutation."""
    def __init__(self, data):
        self.data = data
        self.schedule, self.signal_evidence = build_signal_schedule(data)
        self.positions = {}
        self.pending = {}
        self.ledger = []
        self.seq = 0
        self.prev_hash = "0"*64
        self.realized = Decimal("0")
        self.fees = Decimal("0")
        self.opened = 0
        self.closed = 0
        self.blocked = {}
        self.loosen_warnings = 0

    def receipt(self, event, **fields):
        payload = dict(seq=self.seq+1,event=event,**fields,previous_hash=self.prev_hash)
        blob=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)
        digest=hashlib.sha256(blob.encode("utf-8")).hexdigest()
        payload["receipt_sha256"] = digest
        self.seq += 1
        self.prev_hash = digest
        self.ledger.append(payload)

    def block(self, reason, *, signal=None):
        self.blocked[reason]=self.blocked.get(reason,0)+1
        if signal:
            self.receipt("BLOCKED_ENTRY",reason=reason,signal_id=signal["signal_id"])

    def _exit_if_hit(self, bar):
        p=self.positions.get(bar_symbol := self._active_symbol)
        if p is None:
            return
        stop=p.stop
        opening=dec(bar.open)
        low=dec(bar.low)
        if opening <= stop:
            raw=opening
            cause="GAP_AT_5M_OPEN"
        elif low <= stop:
            raw=stop
            cause="STOP_FIRST_MODEL_AT_5M_LOW"
        else:
            # Parent trailing uses highs from 5m bars while trade was open,
            # updates only when its own TF candle has just finished.
            p.peak=max(p.peak,dec(bar.high))
            n=PERIODS[p.lane]
            if (bar.t + MS5) % (n*MS5) == 0:
                candidate=max(p.initial_stop, p.peak*(1-TRAIL)) if (
                    (dec(bar.close)-p.entry)/p.entry >= ACTIVATE) else p.initial_stop
                if candidate < p.stop:
                    self.loosen_warnings += 1
                    self.receipt("ORIGINAL_V5_NONLATCHED_STOP_WEAKENS",
                                 symbol=p.symbol,signal_id=p.signal_id,old=p.stop,
                                 candidate=candidate,live_stop_amend_authorized=False)
                p.stop = candidate
            return
        exit_price=raw*(1-SLIP)
        exit_fee=p.qty*exit_price*FEE
        pnl=p.qty*(exit_price-p.entry)-p.entry_fee-exit_fee-p.funding_reserve
        self.realized += pnl
        self.fees += exit_fee
        self.closed += 1
        self.receipt("PAPER_EXIT_MODEL",symbol=p.symbol,signal_id=p.signal_id,
                     lane=p.lane,entry_t=p.entry_t,close_bar_t=bar.t,cause=cause,
                     original_v5_stop_unrounded=stop,exit_price_proxy=exit_price,
                     pnl_after_model_costs=pnl,exit_fee_model=exit_fee)
        del self.positions[p.symbol]

    def _enter_pending(self, symbol, bar):
        q=self.pending.get(symbol)
        if q is None:
            return
        if bar.t < q["entry_open_ms"]:
            return
        if bar.t != q["entry_open_ms"]:
            self.block("MISSED_STRICT_FIRST_ENTRY_OPEN",signal=q)
            self.pending.pop(symbol)
            return
        if symbol in self.positions:
            self.block("DUPLICATE_PHYSICAL_POSITION",signal=q)
            self.pending.pop(symbol)
            return
        # Binance next-open PROXY for costed offline shadow ONLY. This is
        # NOT an MEXC executable ask, real fill, or fee/stop acknowledgement.
        try:
            m=model_one_contract(symbol,bar.open)
        except Halt as exc:
            self.block(str(exc),signal=q)
            self.pending.pop(symbol)
            return
        total_risk=sum((p.modeled_cash_risk for p in self.positions.values()),Decimal("0"))+m["cash_risk"]
        sol_risk=sum((p.modeled_cash_risk for p in self.positions.values()
                      if p.symbol=="SOL_USDT"),Decimal("0"))+(m["cash_risk"] if symbol=="SOL_USDT" else 0)
        total_margin=sum((p.qty*p.entry/LEVERAGE for p in self.positions.values()),Decimal("0"))+m["margin"]
        if total_risk>RISK_GLOBAL or sol_risk>RISK_SOL or total_margin>CAPITAL_DECLARED:
            self.block("AGGREGATE_CASH_RISK_OR_MARGIN",signal=q)
            self.pending.pop(symbol)
            return
        self.positions[symbol]=PaperPosition(
            lane=q["lane"],signal_id=q["signal_id"],symbol=symbol,
            contracts=1,qty=m["qty"],entry_t=bar.t,entry=m["entry"],
            initial_stop=m["stop"],stop=m["stop"],peak=m["entry"],
            modeled_cash_risk=m["cash_risk"],entry_fee=m["entry_fee"],
            funding_reserve=m["funding_reserve"])
        self.fees+=m["entry_fee"]
        self.opened+=1
        self.receipt("PAPER_ENTRY_MODEL_NOT_ORDER",symbol=symbol,
                     signal_id=q["signal_id"],entry_bar_t=bar.t,contracts=1,
                     initial_stop_unrounded=m["stop"],entry_price_proxy=m["entry"],
                     projected_loss_if_stop_fill=m["cash_risk"],model_margin=m["margin"],
                     broker_stop_ack=False,exchange_mutation=False)
        self.pending.pop(symbol)

    def run(self):
        """Single deterministic chronological pass; completed candle decides future entry."""
        timeline=sorted((b.t, sym, b) for sym,bs in self.data.items() for b in bs)
        for t,sym,bar in timeline:
            self._active_symbol=sym
            self._enter_pending(sym,bar)
            self._exit_if_hit(bar)
            close_ms=bar.t+MS5
            decisions=[d for d in self.schedule.get(close_ms,[]) if d["symbol"]==sym]
            if not decisions:
                continue
            if len(decisions)>1:
                # Simultaneous LONG signals on same symbol are ambiguous.
                for s in decisions:
                    self.block("SAME_SYMBOL_SIMULTANEOUS_SIGNALS",signal=s)
                continue
            signal=decisions[0]
            if sym in self.positions or sym in self.pending:
                self.block("PHYSICAL_SYMBOL_ALREADY_RESERVED",signal=signal)
                continue
            self.pending[sym]=signal
            self.receipt("PARENT_V5_SIGNAL_SCHEDULED",signal_id=signal["signal_id"],
                         symbol=sym,signal_close_ms=close_ms,
                         first_eligible_bar_open_ms=signal["entry_open_ms"],
                         no_broker_order_authority=True)
        return {
            "status":"OFFLINE_SHADOW_ENGINE_COMPLETE_NO_LIVE_GO",
            "execution_authority":"NONE","broker_stop_ack":False,
            "trading_enabled":False,"live_outcomes_observed":False,
            "operator_equity_declared_usdt":"100","leverage_requested":"10x ISOLATED",
            "parent_pinned_blob": "19c8b8e2363f253458db42111b6701f3a3ef1f4b",
            "signal_provenance":self.signal_evidence,
            "opened_proxy_positions":self.opened,"closed_proxy_positions":self.closed,
            "realized_model_pnl_usdt":str(self.realized),
            "fees_model_usdt":str(self.fees),
            "modeled_active_positions":{sym:dict(lane=p.lane,contracts=p.contracts,
                                                 stop_unrounded=str(p.stop),
                                                 risk_model_usdt=str(p.modeled_cash_risk))
                                         for sym,p in self.positions.items()},
            "pending_signals":{s:x["signal_id"] for s,x in self.pending.items()},
            "blocked_counts":self.blocked,
            "original_nonlatched_stop_weakening_observed":self.loosen_warnings,
            "model_uses_binance_5m_open_proxy_not_mexc_ask":True,
            "min_contract_specs_user_reported_not_authenticated":True,
            "funding_fee_is_single_illustrative_debit_not_exact":True,
            "replay_receipts":len(self.ledger),
            "last_receipt_hash":self.prev_hash,
            "readiness":["UNVERIFIED_ACCOUNT_AND_EXCHANGE_STOPS",
                         "UNVERIFIED_REAL_TIME_FEED_VENUE_PARITY",
                         "NO_COSTED_PROSPECTIVE_FORWARD",
                         "NO_REAL_MEXC_ORDER_ADAPTER",
                         "ORIGINAL_NONLATCHED_TRAIL_BROKER_PROTECTION_UNRESOLVED"]
        }


class DisabledBroker:
    """A deliberately non-functional adapter; no accidental live order path."""
    def __getattr__(self,name):
        raise Halt("EXCHANGE_MUTATION_NOT_IMPLEMENTED_NO_LIVE_GO:"+str(name))
