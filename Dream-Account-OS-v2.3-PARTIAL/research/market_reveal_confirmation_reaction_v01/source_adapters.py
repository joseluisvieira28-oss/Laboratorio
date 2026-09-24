"""Deterministic public-feed semantic adapters for MRCR V0.1.

Synthetic/offline use only. No network client or target acquisition is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Tuple


@dataclass(frozen=True)
class CanonicalTrade:
    venue: str
    native_symbol: str
    trade_id: str
    trade_time: str
    source_event_time: str | None
    price: Decimal
    base_quantity: Decimal
    quote_notional: Decimal
    aggressor_side: str


@dataclass(frozen=True)
class CanonicalBookUpdate:
    venue: str
    native_symbol: str
    source_event_time: str
    sequence_first: int
    sequence_last: int
    side: str
    price_level: Decimal
    absolute_quantity: Decimal


def _decimal(name: str, value: Any, *, positive: bool = False) -> Decimal:
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{name} must be decimal-compatible") from exc
    if not out.is_finite():
        raise ValueError(f"{name} must be finite")
    if positive and out <= 0:
        raise ValueError(f"{name} must be > 0")
    if not positive and out < 0:
        raise ValueError(f"{name} must be >= 0")
    return out


def parse_binance_aggtrade(payload: Mapping[str, Any]) -> CanonicalTrade:
    if payload.get("e") != "aggTrade":
        raise ValueError("not a Binance aggTrade payload")
    symbol = str(payload["s"])
    price = _decimal("p", payload["p"], positive=True)
    qty = _decimal("q", payload["q"], positive=True)
    buyer_is_maker = payload.get("m")
    if not isinstance(buyer_is_maker, bool):
        raise ValueError("m must be boolean")
    aggressor = "SELL" if buyer_is_maker else "BUY"
    return CanonicalTrade(
        venue="BINANCE_SPOT",
        native_symbol=symbol,
        trade_id=str(payload["a"]),
        trade_time=str(payload["T"]),
        source_event_time=str(payload["E"]),
        price=price,
        base_quantity=qty,
        quote_notional=price * qty,
        aggressor_side=aggressor,
    )


def parse_coinbase_market_trade(
    trade: Mapping[str, Any], *, envelope_timestamp: str | None = None
) -> CanonicalTrade:
    maker_side = str(trade["side"]).upper()
    if maker_side not in {"BUY", "SELL"}:
        raise ValueError("Coinbase maker side must be BUY or SELL")
    aggressor = "SELL" if maker_side == "BUY" else "BUY"
    price = _decimal("price", trade["price"], positive=True)
    qty = _decimal("size", trade["size"], positive=True)
    return CanonicalTrade(
        venue="COINBASE_ADVANCED_SPOT",
        native_symbol=str(trade["product_id"]),
        trade_id=str(trade["trade_id"]),
        trade_time=str(trade["time"]),
        source_event_time=envelope_timestamp,
        price=price,
        base_quantity=qty,
        quote_notional=price * qty,
        aggressor_side=aggressor,
    )


def parse_binance_depth_update(
    payload: Mapping[str, Any],
) -> Tuple[CanonicalBookUpdate, ...]:
    if payload.get("e") != "depthUpdate":
        raise ValueError("not a Binance depthUpdate payload")
    symbol = str(payload["s"])
    first = int(payload["U"])
    last = int(payload["u"])
    if first > last:
        raise ValueError("invalid Binance update ID interval")

    rows = []
    for side_name, key in (("BID", "b"), ("ASK", "a")):
        for level in payload.get(key, []):
            if len(level) != 2:
                raise ValueError("depth level must contain price and quantity")
            rows.append(
                CanonicalBookUpdate(
                    venue="BINANCE_SPOT",
                    native_symbol=symbol,
                    source_event_time=str(payload["E"]),
                    sequence_first=first,
                    sequence_last=last,
                    side=side_name,
                    price_level=_decimal("price_level", level[0], positive=True),
                    absolute_quantity=_decimal("quantity", level[1]),
                )
            )
    return tuple(rows)


def parse_coinbase_level2_update(
    *,
    product_id: str,
    sequence_num: int,
    update: Mapping[str, Any],
    source_event_time_override: str | None = None,
) -> CanonicalBookUpdate:
    raw_side = str(update["side"]).lower()
    if raw_side not in {"bid", "ask"}:
        raise ValueError("Coinbase level2 side must be bid or ask")
    source_time = (
        str(source_event_time_override)
        if source_event_time_override is not None
        else str(update["event_time"])
    )
    return CanonicalBookUpdate(
        venue="COINBASE_ADVANCED_SPOT",
        native_symbol=product_id,
        source_event_time=source_time,
        sequence_first=int(sequence_num),
        sequence_last=int(sequence_num),
        side=raw_side.upper(),
        price_level=_decimal("price_level", update["price_level"], positive=True),
        absolute_quantity=_decimal("new_quantity", update["new_quantity"]),
    )


def parse_coinbase_level2_event(
    *,
    event: Mapping[str, Any],
    sequence_num: int,
    envelope_timestamp: str,
) -> tuple[str, Tuple[CanonicalBookUpdate, ...]]:
    event_type = str(event.get("type", "")).lower()
    if event_type not in {"snapshot", "update"}:
        raise ValueError("Coinbase level2 event type must be snapshot or update")
    product_id = str(event["product_id"])
    updates = event.get("updates", [])
    if not isinstance(updates, list):
        raise ValueError("Coinbase level2 updates must be a list")

    rows = []
    for update in updates:
        rows.append(
            parse_coinbase_level2_update(
                product_id=product_id,
                sequence_num=sequence_num,
                update=update,
                source_event_time_override=(
                    envelope_timestamp if event_type == "snapshot" else None
                ),
            )
        )
    return event_type, tuple(rows)


def binance_snapshot_bridge_status(
    snapshot_last_update_id: int,
    current_first: int,
    current_last: int,
) -> str:
    snapshot_last = int(snapshot_last_update_id)
    first = int(current_first)
    last = int(current_last)

    if first > last:
        return "INVALID_INTERVAL"
    if last <= snapshot_last:
        return "STALE"
    if first <= snapshot_last + 1 <= last:
        return "BRIDGES"
    if first > snapshot_last + 1:
        return "GAP"
    return "INVALID_INTERVAL"


def binance_depth_sequence_ok(previous_last: int, current_first: int, current_last: int) -> bool:
    status = binance_snapshot_bridge_status(previous_last, current_first, current_last)
    return status in {"STALE", "BRIDGES"}


def coinbase_sequence_transition(previous: int, current: int) -> str:
    if current == previous + 1:
        return "OK"
    if current <= previous:
        return "OUT_OF_ORDER_OR_DUPLICATE"
    return "GAP"
