"""Deterministic L2 replay primitives for Microstructure Scalping Lab.

Research-only. This module computes contemporaneous book features only.
It does not generate trades or inspect future outcomes.
"""
from dataclasses import dataclass
from typing import Dict, Iterable, Optional


@dataclass(frozen=True)
class BookState:
    ts: int
    cts: Optional[int]
    update_id: Optional[int]
    seq: Optional[int]
    best_bid: float
    best_ask: float
    mid: float
    spread_bps: float
    microprice: float
    imbalance_l1: float
    imbalance_l5: float
    imbalance_l10: float


class L2Replay:
    def __init__(self):
        self.bids: Dict[float, float] = {}
        self.asks: Dict[float, float] = {}
        self.initialized = False
        self.last_ts: Optional[int] = None
        self.last_cts: Optional[int] = None
        self.last_u: Optional[int] = None
        self.last_seq: Optional[int] = None

    @staticmethod
    def _apply_side(book: Dict[float, float], rows: Iterable):
        for row in rows:
            price = float(row[0])
            qty = float(row[1])
            if qty < 0:
                raise ValueError("negative_quantity")
            if qty == 0:
                book.pop(price, None)
            else:
                book[price] = qty

    def apply(self, message: dict) -> BookState:
        typ = message.get("type")
        data = message.get("data") or {}
        ts = message.get("ts")
        cts = message.get("cts")
        u = data.get("u")
        seq = data.get("seq")
        if typ not in {"snapshot", "delta"}:
            raise ValueError("invalid_message_type")
        if ts is None:
            raise ValueError("missing_ts")
        if self.last_ts is not None and ts < self.last_ts:
            raise ValueError("nonmonotonic_ts")
        if cts is not None and self.last_cts is not None and cts < self.last_cts:
            raise ValueError("nonmonotonic_cts")
        if seq is not None and self.last_seq is not None and seq < self.last_seq:
            raise ValueError("nonmonotonic_seq")
        if u is not None and self.last_u is not None and typ == "delta" and u < self.last_u:
            raise ValueError("nonmonotonic_update_id")

        if typ == "snapshot":
            self.bids.clear()
            self.asks.clear()
            self._apply_side(self.bids, data.get("b", []))
            self._apply_side(self.asks, data.get("a", []))
            self.initialized = True
        else:
            if not self.initialized:
                raise ValueError("delta_before_snapshot")
            self._apply_side(self.bids, data.get("b", []))
            self._apply_side(self.asks, data.get("a", []))

        if not self.bids or not self.asks:
            raise ValueError("empty_book_side")
        bb = max(self.bids)
        ba = min(self.asks)
        if bb >= ba:
            raise ValueError("crossed_or_locked_book")

        self.last_ts, self.last_cts, self.last_u, self.last_seq = ts, cts, u, seq
        mid = (bb + ba) / 2.0
        bid_q = self.bids[bb]
        ask_q = self.asks[ba]
        denom = bid_q + ask_q
        micro = (ba * bid_q + bb * ask_q) / denom if denom else mid
        return BookState(
            ts=ts, cts=cts, update_id=u, seq=seq,
            best_bid=bb, best_ask=ba, mid=mid,
            spread_bps=(ba-bb)/mid*10_000.0,
            microprice=micro,
            imbalance_l1=self._imbalance(1),
            imbalance_l5=self._imbalance(5),
            imbalance_l10=self._imbalance(10),
        )

    def _imbalance(self, n: int) -> float:
        bids = sorted(self.bids.items(), reverse=True)[:n]
        asks = sorted(self.asks.items())[:n]
        bq = sum(q for _, q in bids)
        aq = sum(q for _, q in asks)
        total = bq + aq
        return (bq-aq)/total if total else 0.0
