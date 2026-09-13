"""Offline venue parsers for Microstructure Prospective Collector V0.1.

No sockets, HTTP clients, credentials, exchange mutation, trading logic, or target
outcome analysis are permitted in this module. It converts synthetic/raw JSON
objects into the provenance core's normalized primitives and venue state inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Iterable, Mapping, Sequence

from microstructure_provenance_v01 import (
    BookLevelUpdate,
    L2Book,
    ProvenanceViolation,
    canonical_payload_hash,
)


BINANCE_SYMBOLS = {"BTCUSDT", "ETHUSDT"}
COINBASE_PRODUCTS = {"BTC-USD", "ETH-USD"}


@dataclass(frozen=True)
class ParsedEnvelope:
    venue: str
    symbol: str
    stream_type: str
    exchange_ts_ns: int | None
    sequence_start: int | None
    sequence_end: int | None
    payload: Mapping[str, Any]
    source_message_hash_sha256: str


def _require_mapping(value: object, name: str = "message") -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProvenanceViolation(f"{name} must be a mapping")
    return value


def _require_str(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProvenanceViolation(f"{name} must be a non-empty string")
    return value


def _require_int(value: object, name: str) -> int:
    if isinstance(value, bool):
        raise ProvenanceViolation(f"{name} must be an integer")
    try:
        out = int(value)
    except (TypeError, ValueError) as exc:
        raise ProvenanceViolation(f"{name} must be an integer") from exc
    if out < 0:
        raise ProvenanceViolation(f"{name} must be non-negative")
    return out


def _ms_to_ns(value: object, name: str) -> int:
    return _require_int(value, name) * 1_000_000


def _iso_to_ns(value: object, name: str) -> int:
    text = _require_str(value, name)
    # Coinbase emits RFC3339 timestamps, often with up to nanosecond precision.
    # Python datetime only retains microseconds, so preserve sub-microsecond digits
    # deterministically by parsing the fractional component manually.
    if not text.endswith("Z"):
        raise ProvenanceViolation(f"{name} must be UTC RFC3339 ending in Z")
    body = text[:-1]
    if "." in body:
        main, frac = body.split(".", 1)
        if not frac.isdigit() or len(frac) > 9:
            raise ProvenanceViolation(f"{name} has invalid fractional seconds")
        frac_ns = int(frac.ljust(9, "0"))
    else:
        main = body
        frac_ns = 0
    try:
        base = datetime.strptime(main, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ProvenanceViolation(f"{name} is not valid RFC3339 UTC") from exc
    return int(base.timestamp()) * 1_000_000_000 + frac_ns


def _levels(raw: object, side: str) -> list[BookLevelUpdate]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise ProvenanceViolation(f"{side} levels must be a sequence")
    out: list[BookLevelUpdate] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, Sequence) or isinstance(item, (str, bytes, bytearray)) or len(item) < 2:
            raise ProvenanceViolation(f"{side}[{idx}] must contain price and quantity")
        try:
            price = float(item[0])
            quantity = float(item[1])
        except (TypeError, ValueError) as exc:
            raise ProvenanceViolation(f"{side}[{idx}] has invalid numeric value") from exc
        update = BookLevelUpdate(side, price, quantity)
        update.validate()
        out.append(update)
    return out


def parse_binance_diff_depth(message: Mapping[str, Any]) -> ParsedEnvelope:
    msg = _require_mapping(message)
    if msg.get("e") != "depthUpdate":
        raise ProvenanceViolation("not a Binance diff-depth event")
    symbol = _require_str(msg.get("s"), "s")
    if symbol not in BINANCE_SYMBOLS:
        raise ProvenanceViolation("Binance symbol outside frozen contract")
    first = _require_int(msg.get("U"), "U")
    last = _require_int(msg.get("u"), "u")
    if first > last:
        raise ProvenanceViolation("Binance U cannot exceed u")
    _levels(msg.get("b"), "BID")
    _levels(msg.get("a"), "ASK")
    return ParsedEnvelope(
        venue="BINANCE_SPOT",
        symbol=symbol,
        stream_type="L2_DELTA",
        exchange_ts_ns=_ms_to_ns(msg.get("E"), "E"),
        sequence_start=first,
        sequence_end=last,
        payload=msg,
        source_message_hash_sha256=canonical_payload_hash(msg),
    )


def parse_binance_book_ticker(message: Mapping[str, Any]) -> ParsedEnvelope:
    msg = _require_mapping(message)
    symbol = _require_str(msg.get("s"), "s")
    if symbol not in BINANCE_SYMBOLS:
        raise ProvenanceViolation("Binance symbol outside frozen contract")
    for field in ("b", "B", "a", "A"):
        try:
            value = float(msg.get(field))
        except (TypeError, ValueError) as exc:
            raise ProvenanceViolation(f"invalid Binance bookTicker field {field}") from exc
        if value < 0 or (field in ("b", "a") and value <= 0):
            raise ProvenanceViolation(f"invalid Binance bookTicker field {field}")
    update_id = _require_int(msg.get("u"), "u")
    return ParsedEnvelope(
        venue="BINANCE_SPOT",
        symbol=symbol,
        stream_type="BBO",
        exchange_ts_ns=None,
        sequence_start=update_id,
        sequence_end=update_id,
        payload=msg,
        source_message_hash_sha256=canonical_payload_hash(msg),
    )


def parse_binance_trade(message: Mapping[str, Any]) -> ParsedEnvelope:
    msg = _require_mapping(message)
    if msg.get("e") != "trade":
        raise ProvenanceViolation("not a Binance trade event")
    symbol = _require_str(msg.get("s"), "s")
    if symbol not in BINANCE_SYMBOLS:
        raise ProvenanceViolation("Binance symbol outside frozen contract")
    _require_int(msg.get("t"), "t")
    for field in ("p", "q"):
        try:
            value = float(msg.get(field))
        except (TypeError, ValueError) as exc:
            raise ProvenanceViolation(f"invalid Binance trade field {field}") from exc
        if value <= 0:
            raise ProvenanceViolation(f"invalid Binance trade field {field}")
    return ParsedEnvelope(
        venue="BINANCE_SPOT",
        symbol=symbol,
        stream_type="TRADE",
        exchange_ts_ns=_ms_to_ns(msg.get("T"), "T"),
        sequence_start=_require_int(msg.get("t"), "t"),
        sequence_end=_require_int(msg.get("t"), "t"),
        payload=msg,
        source_message_hash_sha256=canonical_payload_hash(msg),
    )


def parse_binance_depth_snapshot(message: Mapping[str, Any], symbol: str) -> tuple[int, list[BookLevelUpdate], list[BookLevelUpdate]]:
    msg = _require_mapping(message)
    if symbol not in BINANCE_SYMBOLS:
        raise ProvenanceViolation("Binance symbol outside frozen contract")
    last_update_id = _require_int(msg.get("lastUpdateId"), "lastUpdateId")
    bids = _levels(msg.get("bids"), "BID")
    asks = _levels(msg.get("asks"), "ASK")
    if not bids or not asks:
        raise ProvenanceViolation("Binance snapshot must contain both sides")
    return last_update_id, bids, asks


class BinanceSnapshotBridge:
    """Offline implementation of the frozen Binance snapshot + diff bridge."""

    def __init__(self) -> None:
        self.book = L2Book()
        self.snapshot_update_id: int | None = None
        self.synchronized = False

    def load_snapshot(self, snapshot: Mapping[str, Any], symbol: str) -> None:
        last_id, bids, asks = parse_binance_depth_snapshot(snapshot, symbol)
        self.book.load_snapshot(
            bids=[(u.price, u.quantity) for u in bids],
            asks=[(u.price, u.quantity) for u in asks],
            sequence_end=last_id,
        )
        self.snapshot_update_id = last_id
        self.synchronized = False

    def apply_first_buffered(self, message: Mapping[str, Any]) -> bool:
        if self.snapshot_update_id is None or not self.book.valid:
            raise ProvenanceViolation("snapshot required before Binance bridge")
        env = parse_binance_diff_depth(message)
        if env.sequence_end <= self.snapshot_update_id:
            return False
        # Official bridge requirement: snapshot update ID + 1 must fall inside [U,u].
        target = self.snapshot_update_id + 1
        if not (env.sequence_start <= target <= env.sequence_end):
            self.book._invalidate("invalid Binance snapshot bridge")
            raise ProvenanceViolation("invalid Binance snapshot bridge")
        updates = _levels(env.payload["b"], "BID") + _levels(env.payload["a"], "ASK")
        # The generic book continuity check is stricter than the first Binance bridge,
        # so apply the documented bridge event against the snapshot then advance ID.
        for update in updates:
            target_side = self.book.bids if update.side == "BID" else self.book.asks
            if update.quantity == 0:
                target_side.pop(update.price, None)
            else:
                target_side[update.price] = update.quantity
        self.book.last_sequence_end = env.sequence_end
        self.book._assert_uncrossed()
        self.synchronized = True
        return True

    def apply_next(self, message: Mapping[str, Any]) -> None:
        if not self.synchronized:
            raise ProvenanceViolation("Binance bridge is not synchronized")
        env = parse_binance_diff_depth(message)
        updates = _levels(env.payload["b"], "BID") + _levels(env.payload["a"], "ASK")
        if env.sequence_end < (self.book.last_sequence_end or 0):
            return
        if env.sequence_start > (self.book.last_sequence_end or 0) + 1:
            self.book._invalidate("Binance sequence gap detected")
            self.synchronized = False
            raise ProvenanceViolation("Binance sequence gap detected")
        # Overlap is allowed when the current local update ID falls within [U,u].
        for update in updates:
            target_side = self.book.bids if update.side == "BID" else self.book.asks
            if update.quantity == 0:
                target_side.pop(update.price, None)
            else:
                target_side[update.price] = update.quantity
        self.book.last_sequence_end = env.sequence_end
        self.book._assert_uncrossed()


def parse_coinbase_level2(message: Mapping[str, Any]) -> ParsedEnvelope:
    msg = _require_mapping(message)
    mtype = _require_str(msg.get("type"), "type")
    if mtype not in {"snapshot", "l2update"}:
        raise ProvenanceViolation("not a Coinbase Exchange level2 message")
    product = _require_str(msg.get("product_id"), "product_id")
    if product not in COINBASE_PRODUCTS:
        raise ProvenanceViolation("Coinbase product outside frozen contract")
    exchange_ts = _iso_to_ns(msg["time"], "time") if msg.get("time") is not None else None
    sequence = _require_int(msg["sequence"], "sequence") if msg.get("sequence") is not None else None
    if mtype == "snapshot":
        bids = _levels(msg.get("bids"), "BID")
        asks = _levels(msg.get("asks"), "ASK")
        if not bids or not asks:
            raise ProvenanceViolation("Coinbase snapshot must contain both sides")
        stream_type = "L2_SNAPSHOT"
    else:
        changes = msg.get("changes")
        if not isinstance(changes, Sequence) or isinstance(changes, (str, bytes, bytearray)):
            raise ProvenanceViolation("Coinbase changes must be a sequence")
        for idx, change in enumerate(changes):
            if not isinstance(change, Sequence) or isinstance(change, (str, bytes, bytearray)) or len(change) < 3:
                raise ProvenanceViolation(f"Coinbase changes[{idx}] malformed")
            side_raw = _require_str(change[0], "side").lower()
            side = "BID" if side_raw == "buy" else "ASK" if side_raw == "sell" else None
            if side is None:
                raise ProvenanceViolation("Coinbase side must be buy or sell")
            BookLevelUpdate(side, float(change[1]), float(change[2])).validate()
        stream_type = "L2_DELTA"
    return ParsedEnvelope(
        venue="COINBASE_SPOT",
        symbol=product,
        stream_type=stream_type,
        exchange_ts_ns=exchange_ts,
        sequence_start=sequence,
        sequence_end=sequence,
        payload=msg,
        source_message_hash_sha256=canonical_payload_hash(msg),
    )


def coinbase_snapshot_levels(message: Mapping[str, Any]) -> tuple[list[BookLevelUpdate], list[BookLevelUpdate]]:
    env = parse_coinbase_level2(message)
    if env.stream_type != "L2_SNAPSHOT":
        raise ProvenanceViolation("Coinbase snapshot required")
    return _levels(env.payload["bids"], "BID"), _levels(env.payload["asks"], "ASK")


def coinbase_delta_updates(message: Mapping[str, Any]) -> list[BookLevelUpdate]:
    env = parse_coinbase_level2(message)
    if env.stream_type != "L2_DELTA":
        raise ProvenanceViolation("Coinbase l2update required")
    out: list[BookLevelUpdate] = []
    for side_raw, price, quantity, *_ in env.payload["changes"]:
        side = "BID" if str(side_raw).lower() == "buy" else "ASK"
        update = BookLevelUpdate(side, float(price), float(quantity))
        update.validate()
        out.append(update)
    return out


def parse_coinbase_heartbeat(message: Mapping[str, Any]) -> ParsedEnvelope:
    msg = _require_mapping(message)
    if msg.get("type") != "heartbeat":
        raise ProvenanceViolation("not a Coinbase heartbeat")
    product = _require_str(msg.get("product_id"), "product_id")
    if product not in COINBASE_PRODUCTS:
        raise ProvenanceViolation("Coinbase product outside frozen contract")
    sequence = _require_int(msg.get("sequence"), "sequence")
    _require_int(msg.get("last_trade_id"), "last_trade_id")
    return ParsedEnvelope(
        venue="COINBASE_SPOT",
        symbol=product,
        stream_type="BBO",  # audit/control envelope only; not used as a BBO metric source
        exchange_ts_ns=_iso_to_ns(msg.get("time"), "time"),
        sequence_start=sequence,
        sequence_end=sequence,
        payload=msg,
        source_message_hash_sha256=canonical_payload_hash(msg),
    )


def parse_json_text(raw_text: str) -> Mapping[str, Any]:
    try:
        obj = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ProvenanceViolation("invalid JSON source message") from exc
    return _require_mapping(obj)
