"""Offline Coinbase Advanced Trade public-market-data parser/state machine.

No network, credentials, account access, trading, exchange mutation, or target-outcome
logic exists here. This module implements Amendment 01 of the prospective collector.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from microstructure_provenance_v01 import (
    BookLevelUpdate,
    L2Book,
    ProvenanceViolation,
    canonical_payload_hash,
)

VENUE = "COINBASE_ADVANCED_SPOT"
PRODUCTS = {"BTC-USD", "ETH-USD"}
PUBLIC_CHANNELS = {"l2_data", "market_trades", "heartbeats"}


def _map(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProvenanceViolation(f"{name} must be a mapping")
    return value


def _seq(value: object, name: str) -> int:
    if isinstance(value, bool):
        raise ProvenanceViolation(f"{name} must be an integer")
    try:
        out = int(value)
    except (TypeError, ValueError) as exc:
        raise ProvenanceViolation(f"{name} must be an integer") from exc
    if out < 0:
        raise ProvenanceViolation(f"{name} must be non-negative")
    return out


def _utc_ns(value: object, name: str) -> int:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ProvenanceViolation(f"{name} must be UTC RFC3339")
    body = value[:-1]
    main, dot, frac = body.partition(".")
    if dot:
        if not frac.isdigit() or len(frac) > 9:
            raise ProvenanceViolation(f"{name} invalid fractional seconds")
        frac_ns = int(frac.ljust(9, "0"))
    else:
        frac_ns = 0
    try:
        base = datetime.strptime(main, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ProvenanceViolation(f"{name} invalid RFC3339") from exc
    return int(base.timestamp()) * 1_000_000_000 + frac_ns


@dataclass(frozen=True)
class AdvancedEnvelope:
    venue: str
    channel: str
    stream_type: str
    exchange_ts_ns: int
    sequence_num: int
    product_ids: tuple[str, ...]
    payload: Mapping[str, Any]
    source_message_hash_sha256: str


def parse_envelope(message: Mapping[str, Any]) -> AdvancedEnvelope:
    msg = _map(message, "message")
    channel = msg.get("channel")
    if channel not in PUBLIC_CHANNELS:
        raise ProvenanceViolation("channel outside frozen public Advanced Trade contract")
    if msg.get("client_id") not in (None, ""):
        raise ProvenanceViolation("non-empty client_id is not permitted in public collector")
    ts = _utc_ns(msg.get("timestamp"), "timestamp")
    seq = _seq(msg.get("sequence_num"), "sequence_num")
    events = msg.get("events")
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes, bytearray)) or not events:
        raise ProvenanceViolation("events must be a non-empty sequence")
    products: list[str] = []
    for raw_event in events:
        event = _map(raw_event, "event")
        product = event.get("product_id")
        if product is not None:
            if product not in PRODUCTS:
                raise ProvenanceViolation("product outside frozen contract")
            products.append(product)
        if channel == "market_trades":
            trades = event.get("trades")
            if not isinstance(trades, Sequence) or isinstance(trades, (str, bytes, bytearray)):
                raise ProvenanceViolation("market_trades event missing trades")
            for trade_raw in trades:
                trade = _map(trade_raw, "trade")
                p = trade.get("product_id")
                if p not in PRODUCTS:
                    raise ProvenanceViolation("trade product outside frozen contract")
                products.append(p)
                try:
                    price = float(trade.get("price"))
                    size = float(trade.get("size"))
                except (TypeError, ValueError) as exc:
                    raise ProvenanceViolation("trade price/size invalid") from exc
                if price <= 0 or size <= 0:
                    raise ProvenanceViolation("trade price/size must be positive")
                _utc_ns(trade.get("time"), "trade.time")
        elif channel == "l2_data":
            if event.get("type") not in {"snapshot", "update"}:
                raise ProvenanceViolation("unsupported l2 event type")
            updates = event.get("updates")
            if not isinstance(updates, Sequence) or isinstance(updates, (str, bytes, bytearray)) or not updates:
                raise ProvenanceViolation("l2 event requires updates")
            for upd_raw in updates:
                upd = _map(upd_raw, "l2 update")
                side_raw = str(upd.get("side", "")).lower()
                side = "BID" if side_raw in {"bid", "buy"} else "ASK" if side_raw in {"ask", "sell", "offer"} else None
                if side is None:
                    raise ProvenanceViolation("invalid l2 side")
                try:
                    level = BookLevelUpdate(side, float(upd.get("price_level")), float(upd.get("new_quantity")))
                except (TypeError, ValueError) as exc:
                    raise ProvenanceViolation("invalid l2 numeric value") from exc
                level.validate()
                _utc_ns(upd.get("event_time"), "event_time")
        elif channel == "heartbeats":
            if "heartbeat_counter" not in event:
                raise ProvenanceViolation("heartbeat_counter missing")
            _seq(event.get("heartbeat_counter"), "heartbeat_counter")
    stream = {"l2_data": "L2_DELTA", "market_trades": "TRADE", "heartbeats": "HEARTBEAT"}[channel]
    if channel == "l2_data" and any(_map(e, "event").get("type") == "snapshot" for e in events):
        stream = "L2_SNAPSHOT"
    return AdvancedEnvelope(
        venue=VENUE,
        channel=channel,
        stream_type=stream,
        exchange_ts_ns=ts,
        sequence_num=seq,
        product_ids=tuple(sorted(set(products))),
        payload=msg,
        source_message_hash_sha256=canonical_payload_hash(msg),
    )


def l2_updates(event: Mapping[str, Any]) -> list[BookLevelUpdate]:
    event = _map(event, "event")
    out: list[BookLevelUpdate] = []
    for raw in event.get("updates", []):
        upd = _map(raw, "l2 update")
        side_raw = str(upd.get("side", "")).lower()
        side = "BID" if side_raw in {"bid", "buy"} else "ASK" if side_raw in {"ask", "sell", "offer"} else None
        if side is None:
            raise ProvenanceViolation("invalid l2 side")
        item = BookLevelUpdate(side, float(upd["price_level"]), float(upd["new_quantity"]))
        item.validate()
        out.append(item)
    return out


class AdvancedTradeBook:
    """Per-product Level2 state; fails closed on sequence ambiguity/gap."""

    def __init__(self, product_id: str) -> None:
        if product_id not in PRODUCTS:
            raise ProvenanceViolation("product outside frozen contract")
        self.product_id = product_id
        self.book = L2Book()
        self.last_sequence_num: int | None = None
        self.synchronized = False

    def apply_message(self, message: Mapping[str, Any]) -> None:
        env = parse_envelope(message)
        if env.channel != "l2_data":
            raise ProvenanceViolation("l2_data message required")
        if self.last_sequence_num is not None and env.sequence_num != self.last_sequence_num + 1:
            self.book._invalidate("Advanced Trade sequence gap detected")
            self.synchronized = False
            raise ProvenanceViolation("Advanced Trade sequence gap detected")
        matching = [e for e in env.payload["events"] if e.get("product_id") == self.product_id]
        if not matching:
            raise ProvenanceViolation("message contains no event for configured product")
        for event in matching:
            updates = l2_updates(event)
            if event.get("type") == "snapshot":
                bids = [(u.price, u.quantity) for u in updates if u.side == "BID"]
                asks = [(u.price, u.quantity) for u in updates if u.side == "ASK"]
                self.book.load_snapshot(bids=bids, asks=asks, sequence_end=None)
                self.synchronized = True
            elif event.get("type") == "update":
                if not self.synchronized:
                    raise ProvenanceViolation("snapshot required before update")
                self.book.apply_delta(updates, sequence_start=None, sequence_end=None)
        self.last_sequence_num = env.sequence_num
