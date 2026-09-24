"""Deterministic venue-native order-book reconstruction for MRCR V0.1.

Offline/state-reconstruction only. No network access, no targets, no trading logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Sequence

from source_adapters import (
    CanonicalBookUpdate,
    binance_depth_sequence_ok,
    coinbase_sequence_transition,
)


class BookError(ValueError):
    pass


class BookNotInitialized(BookError):
    pass


class BookSequenceGap(BookError):
    pass


class CrossedBook(BookError):
    pass


@dataclass(frozen=True)
class DepthSpec:
    mode: str
    value: Decimal

    def __post_init__(self) -> None:
        if self.mode not in {"TOP_N", "BPS_BAND"}:
            raise ValueError("depth mode must be TOP_N or BPS_BAND")
        if self.value <= 0:
            raise ValueError("depth value must be > 0")
        if self.mode == "TOP_N" and self.value != self.value.to_integral_value():
            raise ValueError("TOP_N depth value must be an integer")


@dataclass(frozen=True)
class BookMetrics:
    best_bid: Decimal
    best_ask: Decimal
    mid: Decimal
    spread_abs: Decimal
    spread_bps: Decimal
    bid_depth_quote: Decimal
    ask_depth_quote: Decimal
    total_depth_quote: Decimal
    sequence_last: int


@dataclass(frozen=True)
class ApplyResult:
    status: str
    previous_sequence: int
    sequence_last: int
    update_count: int


class LocalOrderBook:
    def __init__(self, *, venue: str, native_symbol: str) -> None:
        self.venue = venue
        self.native_symbol = native_symbol
        self._bids: dict[Decimal, Decimal] = {}
        self._asks: dict[Decimal, Decimal] = {}
        self._sequence_last: int | None = None

    @property
    def initialized(self) -> bool:
        return self._sequence_last is not None

    @property
    def sequence_last(self) -> int:
        if self._sequence_last is None:
            raise BookNotInitialized("book is not initialized")
        return self._sequence_last

    def load_snapshot_levels(
        self,
        *,
        bids: Iterable[tuple[Decimal, Decimal]],
        asks: Iterable[tuple[Decimal, Decimal]],
        sequence_last: int,
    ) -> None:
        bid_map = self._normalize_levels(bids)
        ask_map = self._normalize_levels(asks)
        self._validate_book_maps(bid_map, ask_map)
        self._bids = bid_map
        self._asks = ask_map
        self._sequence_last = int(sequence_last)

    def initialize_from_snapshot_updates(
        self, updates: Sequence[CanonicalBookUpdate]
    ) -> None:
        if not updates:
            raise BookError("snapshot updates are empty")
        self._validate_batch_identity(updates)
        sequences = {(u.sequence_first, u.sequence_last) for u in updates}
        if len(sequences) != 1:
            raise BookError("snapshot update batch has mixed sequence identifiers")

        bids: dict[Decimal, Decimal] = {}
        asks: dict[Decimal, Decimal] = {}
        for update in updates:
            target = bids if update.side == "BID" else asks
            if update.absolute_quantity > 0:
                target[update.price_level] = update.absolute_quantity

        self._validate_book_maps(bids, asks)
        self._bids = bids
        self._asks = asks
        self._sequence_last = updates[0].sequence_last

    def apply_updates(self, updates: Sequence[CanonicalBookUpdate]) -> ApplyResult:
        if self._sequence_last is None:
            raise BookNotInitialized("load a snapshot before incremental updates")
        if not updates:
            return ApplyResult(
                status="EMPTY",
                previous_sequence=self._sequence_last,
                sequence_last=self._sequence_last,
                update_count=0,
            )

        self._validate_batch_identity(updates)
        sequences = {(u.sequence_first, u.sequence_last) for u in updates}
        if len(sequences) != 1:
            raise BookError("incremental update batch has mixed sequence identifiers")
        first, last = next(iter(sequences))
        previous = self._sequence_last

        if last <= previous:
            return ApplyResult(
                status="STALE_OR_DUPLICATE_IGNORED",
                previous_sequence=previous,
                sequence_last=previous,
                update_count=len(updates),
            )

        if self.venue == "BINANCE_SPOT":
            if not binance_depth_sequence_ok(previous, first, last):
                raise BookSequenceGap(
                    f"Binance sequence gap: previous={previous}, first={first}, last={last}"
                )
        elif self.venue == "COINBASE_ADVANCED_SPOT":
            transition = coinbase_sequence_transition(previous, last)
            if transition == "GAP":
                raise BookSequenceGap(
                    f"Coinbase sequence gap: previous={previous}, current={last}"
                )
            if transition == "OUT_OF_ORDER_OR_DUPLICATE":
                return ApplyResult(
                    status="STALE_OR_DUPLICATE_IGNORED",
                    previous_sequence=previous,
                    sequence_last=previous,
                    update_count=len(updates),
                )
        else:
            raise BookError(f"unsupported venue: {self.venue}")

        next_bids = dict(self._bids)
        next_asks = dict(self._asks)
        for update in updates:
            target = next_bids if update.side == "BID" else next_asks
            if update.absolute_quantity == 0:
                target.pop(update.price_level, None)
            else:
                target[update.price_level] = update.absolute_quantity

        self._validate_book_maps(next_bids, next_asks)
        self._bids = next_bids
        self._asks = next_asks
        self._sequence_last = last
        return ApplyResult(
            status="APPLIED",
            previous_sequence=previous,
            sequence_last=last,
            update_count=len(updates),
        )

    def metrics(self, depth_spec: DepthSpec) -> BookMetrics:
        if self._sequence_last is None:
            raise BookNotInitialized("book is not initialized")
        self._validate_book_maps(self._bids, self._asks)
        best_bid = max(self._bids)
        best_ask = min(self._asks)
        mid = (best_bid + best_ask) / Decimal("2")
        spread = best_ask - best_bid
        spread_bps = (spread / mid) * Decimal("10000")
        bid_depth, ask_depth = self._depth_quote(depth_spec, mid)
        return BookMetrics(
            best_bid=best_bid,
            best_ask=best_ask,
            mid=mid,
            spread_abs=spread,
            spread_bps=spread_bps,
            bid_depth_quote=bid_depth,
            ask_depth_quote=ask_depth,
            total_depth_quote=bid_depth + ask_depth,
            sequence_last=self._sequence_last,
        )

    def _depth_quote(
        self, depth_spec: DepthSpec, mid: Decimal
    ) -> tuple[Decimal, Decimal]:
        if depth_spec.mode == "TOP_N":
            n = int(depth_spec.value)
            bid_levels = sorted(self._bids.items(), reverse=True)[:n]
            ask_levels = sorted(self._asks.items())[:n]
        else:
            band = depth_spec.value / Decimal("10000")
            bid_floor = mid * (Decimal("1") - band)
            ask_ceiling = mid * (Decimal("1") + band)
            bid_levels = [
                (price, qty)
                for price, qty in self._bids.items()
                if price >= bid_floor
            ]
            ask_levels = [
                (price, qty)
                for price, qty in self._asks.items()
                if price <= ask_ceiling
            ]

        bid_quote = sum(
            (price * qty for price, qty in bid_levels),
            Decimal("0"),
        )
        ask_quote = sum(
            (price * qty for price, qty in ask_levels),
            Decimal("0"),
        )
        return bid_quote, ask_quote

    def _validate_batch_identity(
        self, updates: Sequence[CanonicalBookUpdate]
    ) -> None:
        for update in updates:
            if update.venue != self.venue:
                raise BookError(
                    f"venue mismatch: expected={self.venue}, got={update.venue}"
                )
            if update.native_symbol != self.native_symbol:
                raise BookError(
                    "symbol mismatch: "
                    f"expected={self.native_symbol}, got={update.native_symbol}"
                )
            if update.side not in {"BID", "ASK"}:
                raise BookError(f"invalid side: {update.side}")
            if update.price_level <= 0 or update.absolute_quantity < 0:
                raise BookError("invalid price/quantity")

    @staticmethod
    def _normalize_levels(
        levels: Iterable[tuple[Decimal, Decimal]]
    ) -> dict[Decimal, Decimal]:
        out: dict[Decimal, Decimal] = {}
        for price, qty in levels:
            price = Decimal(price)
            qty = Decimal(qty)
            if price <= 0 or qty < 0:
                raise BookError("snapshot prices must be > 0 and quantities >= 0")
            if qty > 0:
                out[price] = qty
        return out

    @staticmethod
    def _validate_book_maps(
        bids: dict[Decimal, Decimal], asks: dict[Decimal, Decimal]
    ) -> None:
        if not bids or not asks:
            raise BookError("book must have at least one bid and one ask")
        best_bid = max(bids)
        best_ask = min(asks)
        if best_bid >= best_ask:
            raise CrossedBook(
                f"crossed/locked book: best_bid={best_bid}, best_ask={best_ask}"
            )
