"""Microstructure Data Source & Provenance Gate V0.1 — offline core.

This module is intentionally OFFLINE. It implements deterministic validation,
normalization helpers, raw-message hashing, and synthetic L2 reconstruction only.
It MUST NOT fetch market data, access trading endpoints, place orders, mutate an
exchange, inspect target outcomes, or define a trading hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Iterable, Mapping, Sequence


ALLOWED_VENUES = ("BINANCE_SPOT", "COINBASE_SPOT", "COINBASE_ADVANCED_SPOT")
ALLOWED_STREAM_TYPES = ("L2_SNAPSHOT", "L2_DELTA", "BBO", "TRADE", "HEARTBEAT")
H02_STATUS = "NOT_AUTHORIZED"
STOP_CONDITION = (
    "STOP_AFTER_PROVENANCE_IMPLEMENTATION_AND_SYNTHETIC_VALIDATION_"
    "BEFORE_TARGET_OUTCOME_RESEARCH_OR_H02_FREEZE"
)


class ProvenanceViolation(ValueError):
    """Raised when provenance/integrity rules fail closed."""


def _finite_positive(value: float, *, field_name: str) -> float:
    x = float(value)
    if not math.isfinite(x) or x <= 0:
        raise ProvenanceViolation(f"{field_name} must be finite and > 0")
    return x


def _finite_nonnegative(value: float, *, field_name: str) -> float:
    x = float(value)
    if not math.isfinite(x) or x < 0:
        raise ProvenanceViolation(f"{field_name} must be finite and >= 0")
    return x


def canonical_json_bytes(payload: object) -> bytes:
    """Canonical UTF-8 JSON bytes for deterministic hashing of normalized fixtures."""
    try:
        text = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ProvenanceViolation("payload is not canonically JSON-serializable") from exc
    return text.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_payload_hash(payload: object) -> str:
    return sha256_hex(canonical_json_bytes(payload))


@dataclass(frozen=True)
class NormalizedRecord:
    venue: str
    market_type: str
    symbol: str
    stream_type: str
    exchange_ts_ns: int | None
    collector_ts_ns: int
    sequence_start: int | None
    sequence_end: int | None
    payload: object
    source_message_hash_sha256: str
    segment_id: str

    def validate(self) -> None:
        if self.venue not in ALLOWED_VENUES:
            raise ProvenanceViolation("venue is not allowed by V0.1 gate")
        if self.market_type != "SPOT":
            raise ProvenanceViolation("V0.1 gate permits SPOT only")
        if not self.symbol:
            raise ProvenanceViolation("symbol is required")
        if self.stream_type not in ALLOWED_STREAM_TYPES:
            raise ProvenanceViolation("unsupported stream_type")
        if self.exchange_ts_ns is not None and int(self.exchange_ts_ns) < 0:
            raise ProvenanceViolation("exchange_ts_ns must be non-negative or null")
        if int(self.collector_ts_ns) < 0:
            raise ProvenanceViolation("collector_ts_ns must be non-negative")
        if self.sequence_start is not None and int(self.sequence_start) < 0:
            raise ProvenanceViolation("sequence_start must be non-negative or null")
        if self.sequence_end is not None and int(self.sequence_end) < 0:
            raise ProvenanceViolation("sequence_end must be non-negative or null")
        if (
            self.sequence_start is not None
            and self.sequence_end is not None
            and int(self.sequence_start) > int(self.sequence_end)
        ):
            raise ProvenanceViolation("sequence_start cannot exceed sequence_end")
        if not self.segment_id:
            raise ProvenanceViolation("segment_id is required")
        expected = canonical_payload_hash(self.payload)
        if self.source_message_hash_sha256 != expected:
            raise ProvenanceViolation("source message hash mismatch")


@dataclass(frozen=True)
class BookLevelUpdate:
    side: str
    price: float
    quantity: float

    def validate(self) -> None:
        if self.side not in ("BID", "ASK"):
            raise ProvenanceViolation("side must be BID or ASK")
        _finite_positive(self.price, field_name="price")
        _finite_nonnegative(self.quantity, field_name="quantity")


@dataclass
class L2Book:
    """Synthetic deterministic L2 state for provenance validation.

    Quantities are interpreted as absolute quantities at a price level. Zero
    quantity deletes the level. The object fails closed after any continuity or
    book-state violation until an explicit resynchronization snapshot is loaded.
    """

    bids: dict[float, float] = field(default_factory=dict)
    asks: dict[float, float] = field(default_factory=dict)
    valid: bool = False
    last_sequence_end: int | None = None
    invalid_reason: str | None = None

    def _invalidate(self, reason: str) -> None:
        self.valid = False
        self.invalid_reason = reason

    def _assert_uncrossed(self) -> None:
        if not self.bids or not self.asks:
            self._invalidate("book side empty after update")
            raise ProvenanceViolation(self.invalid_reason)
        best_bid = max(self.bids)
        best_ask = min(self.asks)
        if best_bid >= best_ask:
            self._invalidate("crossed or locked synthetic book")
            raise ProvenanceViolation(self.invalid_reason)

    def load_snapshot(
        self,
        *,
        bids: Iterable[tuple[float, float]],
        asks: Iterable[tuple[float, float]],
        sequence_end: int | None,
    ) -> None:
        new_bids: dict[float, float] = {}
        new_asks: dict[float, float] = {}
        for side_name, levels, target in (
            ("BID", bids, new_bids),
            ("ASK", asks, new_asks),
        ):
            for price, quantity in levels:
                update = BookLevelUpdate(side_name, price, quantity)
                update.validate()
                if float(quantity) == 0:
                    continue
                target[float(price)] = float(quantity)
        if sequence_end is not None and int(sequence_end) < 0:
            raise ProvenanceViolation("snapshot sequence_end must be non-negative or null")
        self.bids = new_bids
        self.asks = new_asks
        self.last_sequence_end = None if sequence_end is None else int(sequence_end)
        self.valid = True
        self.invalid_reason = None
        self._assert_uncrossed()

    def apply_delta(
        self,
        updates: Sequence[BookLevelUpdate],
        *,
        sequence_start: int | None,
        sequence_end: int | None,
    ) -> None:
        if not self.valid:
            raise ProvenanceViolation("book is INVALID_UNTIL_RESYNC")
        if (sequence_start is None) != (sequence_end is None):
            self._invalidate("partial sequence metadata")
            raise ProvenanceViolation(self.invalid_reason)
        if sequence_start is not None:
            start = int(sequence_start)
            end = int(sequence_end)
            if start < 0 or end < start:
                self._invalidate("invalid sequence interval")
                raise ProvenanceViolation(self.invalid_reason)
            if self.last_sequence_end is not None and start != self.last_sequence_end + 1:
                self._invalidate("sequence gap or overlap detected")
                raise ProvenanceViolation(self.invalid_reason)
        for update in updates:
            update.validate()
            target = self.bids if update.side == "BID" else self.asks
            price = float(update.price)
            quantity = float(update.quantity)
            if quantity == 0:
                target.pop(price, None)
            else:
                target[price] = quantity
        if sequence_end is not None:
            self.last_sequence_end = int(sequence_end)
        self._assert_uncrossed()

    @property
    def best_bid(self) -> float:
        if not self.valid or not self.bids:
            raise ProvenanceViolation("book is not valid for metrics")
        return max(self.bids)

    @property
    def best_ask(self) -> float:
        if not self.valid or not self.asks:
            raise ProvenanceViolation("book is not valid for metrics")
        return min(self.asks)

    def spread_bps(self) -> float:
        bid = self.best_bid
        ask = self.best_ask
        mid = (bid + ask) / 2.0
        return (ask - bid) / mid * 10_000.0

    def depth_within_bps(self, bps: float) -> Mapping[str, float]:
        if not self.valid:
            raise ProvenanceViolation("book is not valid for metrics")
        width = _finite_positive(bps, field_name="bps") / 10_000.0
        bid = self.best_bid
        ask = self.best_ask
        mid = (bid + ask) / 2.0
        bid_floor = mid * (1.0 - width)
        ask_ceiling = mid * (1.0 + width)
        bid_depth = sum(q for p, q in self.bids.items() if p >= bid_floor)
        ask_depth = sum(q for p, q in self.asks.items() if p <= ask_ceiling)
        return {"bid_quantity": bid_depth, "ask_quantity": ask_depth}


def ordered_segment_digest(message_hashes: Iterable[str]) -> str:
    """Deterministic digest of ordered per-message SHA-256 hex digests."""
    hashes = tuple(message_hashes)
    if not hashes:
        raise ProvenanceViolation("at least one message hash is required")
    for h in hashes:
        if len(h) != 64:
            raise ProvenanceViolation("message hash must be 64 hex characters")
        try:
            bytes.fromhex(h)
        except ValueError as exc:
            raise ProvenanceViolation("message hash is not valid hex") from exc
    return sha256_hex("".join(hashes).encode("ascii"))


def provenance_governance_receipt() -> dict[str, object]:
    return {
        "status": "PROVENANCE_IMPLEMENTATION_ONLY",
        "h02_status": H02_STATUS,
        "target_outcomes_accessed_by_this_module": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "authenticated_trading_endpoints_required": False,
        "network_access_in_this_module": False,
        "mexc_2025_09_through_2025_12_accessed": False,
        "stop_condition": STOP_CONDITION,
    }
