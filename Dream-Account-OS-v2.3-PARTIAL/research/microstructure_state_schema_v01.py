"""Deterministic pre-data schema/alignment core for Microstructure State Lab V0.1.

Offline only. No network, credentials, exchange mutation, target outcomes, labels,
strategy logic, or hypothesis testing are permitted here.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


H02_STATUS = "NOT_AUTHORIZED"
STOP_CONDITION = "STOP_BEFORE_TARGET_OUTCOMES_OR_H02_FREEZE"


class SchemaViolation(ValueError):
    """Fail-closed validation error for the pre-data measurement layer."""


def _finite_positive(value: float, name: str) -> float:
    x = float(value)
    if not math.isfinite(x) or x <= 0:
        raise SchemaViolation(f"{name} must be finite and > 0")
    return x


def _nonnegative_int(value: int, name: str) -> int:
    if isinstance(value, bool):
        raise SchemaViolation(f"{name} must be a non-negative integer")
    try:
        x = int(value)
    except (TypeError, ValueError) as exc:
        raise SchemaViolation(f"{name} must be a non-negative integer") from exc
    if x < 0:
        raise SchemaViolation(f"{name} must be a non-negative integer")
    return x


@dataclass(frozen=True)
class MarketIdentity:
    venue: str
    market_type: str
    symbol: str
    canonical_asset: str
    quote_asset: str

    def validate(self) -> None:
        if self.venue not in {"BINANCE_SPOT", "COINBASE_ADVANCED_SPOT"}:
            raise SchemaViolation("venue outside frozen provenance scope")
        if self.market_type != "SPOT":
            raise SchemaViolation("market_type must be SPOT")
        allowed = {
            ("BINANCE_SPOT", "BTCUSDT", "BTC", "USDT"),
            ("BINANCE_SPOT", "ETHUSDT", "ETH", "USDT"),
            ("COINBASE_ADVANCED_SPOT", "BTC-USD", "BTC", "USD"),
            ("COINBASE_ADVANCED_SPOT", "ETH-USD", "ETH", "USD"),
        }
        key = (self.venue, self.symbol, self.canonical_asset, self.quote_asset)
        if key not in allowed:
            raise SchemaViolation("identity mapping outside frozen schema")


@dataclass(frozen=True)
class ProvenanceClock:
    exchange_ts_ns: int | None
    collector_wall_ns: int
    collector_monotonic_ns: int
    source_order: int
    source_hash_sha256: str

    def validate(self) -> None:
        if self.exchange_ts_ns is not None:
            _nonnegative_int(self.exchange_ts_ns, "exchange_ts_ns")
        _nonnegative_int(self.collector_wall_ns, "collector_wall_ns")
        _nonnegative_int(self.collector_monotonic_ns, "collector_monotonic_ns")
        _nonnegative_int(self.source_order, "source_order")
        if len(self.source_hash_sha256) != 64:
            raise SchemaViolation("source_hash_sha256 must be 64 hex characters")
        try:
            bytes.fromhex(self.source_hash_sha256)
        except ValueError as exc:
            raise SchemaViolation("source_hash_sha256 must be hexadecimal") from exc


@dataclass(frozen=True)
class BBOObservation:
    identity: MarketIdentity
    clock: ProvenanceClock
    best_bid_price: float
    best_bid_quantity: float
    best_ask_price: float
    best_ask_quantity: float

    def validate(self) -> None:
        self.identity.validate()
        self.clock.validate()
        bid = _finite_positive(self.best_bid_price, "best_bid_price")
        ask = _finite_positive(self.best_ask_price, "best_ask_price")
        _finite_positive(self.best_bid_quantity, "best_bid_quantity")
        _finite_positive(self.best_ask_quantity, "best_ask_quantity")
        if bid >= ask:
            raise SchemaViolation("BBO must be strictly uncrossed")

    @property
    def mid(self) -> float:
        self.validate()
        return (float(self.best_bid_price) + float(self.best_ask_price)) / 2.0

    @property
    def spread(self) -> float:
        self.validate()
        return float(self.best_ask_price) - float(self.best_bid_price)

    @property
    def spread_bps(self) -> float:
        return self.spread / self.mid * 10_000.0


@dataclass(frozen=True)
class TradeObservation:
    identity: MarketIdentity
    clock: ProvenanceClock
    price: float
    quantity: float
    trade_id: int | None = None
    aggressor_side: str | None = None

    def validate(self) -> None:
        self.identity.validate()
        self.clock.validate()
        if self.clock.exchange_ts_ns is None:
            raise SchemaViolation("trade exchange timestamp is required")
        _finite_positive(self.price, "price")
        _finite_positive(self.quantity, "quantity")
        if self.trade_id is not None:
            _nonnegative_int(self.trade_id, "trade_id")
        if self.aggressor_side not in {None, "BUY", "SELL"}:
            raise SchemaViolation("aggressor_side must be BUY, SELL, or null")


@dataclass(frozen=True)
class AlignedPair:
    anchor: BBOObservation
    other: BBOObservation | None
    skew_ns: int | None


def backward_asof_align(
    anchor: BBOObservation,
    candidates: Sequence[BBOObservation],
    *,
    max_skew_ns: int,
) -> AlignedPair:
    """Return latest candidate at or before anchor exchange time.

    No interpolation and no use of future observations. Missingness is explicit.
    """
    anchor.validate()
    max_skew = _nonnegative_int(max_skew_ns, "max_skew_ns")
    if anchor.clock.exchange_ts_ns is None:
        raise SchemaViolation("anchor exchange timestamp is required for alignment")
    t = int(anchor.clock.exchange_ts_ns)

    eligible: list[BBOObservation] = []
    for candidate in candidates:
        candidate.validate()
        if candidate.identity.canonical_asset != anchor.identity.canonical_asset:
            continue
        if candidate.identity.venue == anchor.identity.venue:
            continue
        cts = candidate.clock.exchange_ts_ns
        if cts is None:
            continue
        if int(cts) <= t:
            eligible.append(candidate)

    if not eligible:
        return AlignedPair(anchor=anchor, other=None, skew_ns=None)

    chosen = max(
        eligible,
        key=lambda x: (int(x.clock.exchange_ts_ns), int(x.clock.source_order)),
    )
    skew = t - int(chosen.clock.exchange_ts_ns)
    if skew > max_skew:
        return AlignedPair(anchor=anchor, other=None, skew_ns=None)
    return AlignedPair(anchor=anchor, other=chosen, skew_ns=skew)


def dedupe_identical_hashes(records: Iterable[BBOObservation]) -> tuple[BBOObservation, ...]:
    """Stable de-duplication by provenance hash.

    Identical hash repeats are removed. A conflicting reuse of a source-order key
    with a different hash fails closed.
    """
    out: list[BBOObservation] = []
    seen_hashes: set[str] = set()
    seen_order_keys: dict[tuple[str, str, int], str] = {}
    for record in records:
        record.validate()
        key = (record.identity.venue, record.identity.symbol, record.clock.source_order)
        prior = seen_order_keys.get(key)
        if prior is not None and prior != record.clock.source_hash_sha256:
            raise SchemaViolation("conflicting payload at identical source order")
        seen_order_keys[key] = record.clock.source_hash_sha256
        if record.clock.source_hash_sha256 in seen_hashes:
            continue
        seen_hashes.add(record.clock.source_hash_sha256)
        out.append(record)
    return tuple(out)
