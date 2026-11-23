#!/usr/bin/env python3
"""Fail-closed Binance SPOT local-book reconstruction, independent of transport."""
from __future__ import annotations
import hashlib
import json
from decimal import Decimal as D, InvalidOperation

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
ZERO = D("0")

def positive(value, *, zero_allowed=False):
    try:
        d = D(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("UNPARSEABLE_DECIMAL") from exc
    if not d.is_finite() or d < ZERO or (not zero_allowed and d == ZERO):
        raise ValueError("INVALID_DECIMAL")
    return d

def levels(arr, *, side, allow_zero=False, sorted_check=False):
    if not isinstance(arr, list) or len(arr) > 5000:
        raise ValueError("INVALID_LEVELS")
    if sorted_check and not arr:
        raise ValueError("EMPTY_SNAPSHOT_SIDE")
    result = []
    prior = None
    for pair in arr:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("BAD_LEVEL_PAIR")
        p = positive(pair[0]); q = positive(pair[1], zero_allowed=allow_zero)
        if sorted_check and prior is not None:
            if side == "bid" and p >= prior: raise ValueError("BAD_BID_SORT")
            if side == "ask" and p <= prior: raise ValueError("BAD_ASK_SORT")
        prior = p
        result.append((p, q))
    return result

def must_int(x, name):
    if type(x) is not int or x < 0:
        raise ValueError("INVALID_INTEGER_" + name)
    return x

def valid_millis(x, name):
    n = must_int(x, name)
    if not 1_500_000_000_000 <= n < 2_000_000_000_000:
        raise ValueError("INVALID_MILLISECONDS_" + name)
    return n

def event_validation(event, symbol):
    if not isinstance(event, dict) or event.get("s") != symbol:
        raise ValueError("WRONG_EVENT_SYMBOL")
    kind = event.get("e")
    if kind == "depthUpdate":
        u_start = must_int(event.get("U"), "U")
        u_last = must_int(event.get("u"), "u")
        if not u_start or u_last < u_start:
            raise ValueError("INVALID_DEPTH_RANGE")
        valid_millis(event.get("E"), "E")
        return "depth", u_start, u_last, levels(event.get("b"),side="bid",allow_zero=True), levels(event.get("a"),side="ask",allow_zero=True)
    if kind == "aggTrade":
        valid_millis(event.get("E"), "E")
        valid_millis(event.get("T"), "T")
        tid = must_int(event.get("a"), "a")
        first = must_int(event.get("f"), "f")
        last = must_int(event.get("l"), "l")
        if first > last or type(event.get("m")) is not bool:
            raise ValueError("BAD_AGG_TRADE_ID_OR_SIDE")
        return "trade", tid, positive(event.get("p")), positive(event.get("q")), event["m"]
    raise ValueError("UNSUPPORTED_EVENT")

class LocalBook:
    def __init__(self, symbol):
        if symbol not in SYMBOLS: raise ValueError("UNAPPROVED_SYMBOL")
        self.symbol = symbol
        self.status = "BUFFERING"
        self.failure = None
        self.bids, self.asks = {}, {}
        self.buffer = []
        self.last_update_id = None
        self.depth_messages = 0
        self.depth_applied = 0
        self.stale_depth = 0
        self.aggtrades = 0
        self.aggressive_buys = 0
        self.aggressive_sells = 0
        self.last_agg_id = None
        self.level_removed = 0
        self.level_added = 0
        self.qty_increase = 0
        self.qty_decrease = 0

    def stop(self, reason):
        self.failure = reason
        self.status = "SOURCE_BLOCKED"
        self.buffer.clear()

    def ingest(self, event):
        if self.status == "SOURCE_BLOCKED": return
        try:
            parsed = event_validation(event, self.symbol)
            if parsed[0] == "trade":
                _, trade_id, price, qty, is_buyer_maker = parsed
                if self.last_agg_id is not None and trade_id <= self.last_agg_id:
                    raise ValueError("DUPLICATE_OR_REVERSED_AGGTRADE_ID")
                self.last_agg_id = trade_id
                self.aggtrades += 1
                if is_buyer_maker: self.aggressive_sells += 1
                else: self.aggressive_buys += 1
                return
            self.depth_messages += 1
            if self.status == "BUFFERING":
                if len(self.buffer) >= 500:
                    raise ValueError("PRE_SNAPSHOT_BUFFER_OVERFLOW")
                self.buffer.append(parsed)
                return
            self._apply(parsed)
        except (ValueError, TypeError) as exc:
            self.stop(str(exc))

    def snapshot(self, data):
        if self.status == "SOURCE_BLOCKED": return
        if self.status != "BUFFERING":
            self.stop("DUPLICATE_SNAPSHOT")
            return
        try:
            if not isinstance(data, dict):
                raise ValueError("BAD_SNAPSHOT")
            seq = must_int(data.get("lastUpdateId"), "snapshot")
            if seq == 0: raise ValueError("ZERO_SNAPSHOT_ID")
            bids = levels(data.get("bids"), side="bid", sorted_check=True)
            asks = levels(data.get("asks"), side="ask", sorted_check=True)
            if bids[0][0] >= asks[0][0]: raise ValueError("CROSSED_SNAPSHOT")
            self.bids, self.asks = dict(bids), dict(asks)
            self.last_update_id = seq
            buffered = list(self.buffer)
            self.buffer.clear()
            self.status = "SYNCED"
            for evt in buffered:
                self._apply(evt)
                if self.status != "SYNCED": break
        except (ValueError, TypeError) as exc:
            self.stop(str(exc))

    def _apply(self, parsed):
        _, first, last, bids, asks = parsed
        assert self.last_update_id is not None
        if last <= self.last_update_id:
            self.stale_depth += 1
            return
        if first > self.last_update_id + 1:
            self.stop("SEQUENCE_GAP_NO_RESTART")
            return
        for new_levels, side in ((bids, self.bids), (asks, self.asks)):
            for price, qty in new_levels:
                current = side.get(price)
                if qty == ZERO:
                    if current is not None:
                        del side[price]
                        self.level_removed += 1
                else:
                    if current is None: self.level_added += 1
                    elif qty > current: self.qty_increase += 1
                    elif qty < current: self.qty_decrease += 1
                    side[price] = qty
        self.last_update_id = last
        self.depth_applied += 1
        if not self.bids or not self.asks or max(self.bids) >= min(self.asks):
            self.stop("EMPTY_OR_CROSSED_RECONSTRUCTED_BOOK")

    def summary(self):
        return {
            "status": self.status,
            "failure": self.failure,
            "last_update_id": self.last_update_id,
            "depth_messages": self.depth_messages,
            "depth_applied": self.depth_applied,
            "stale_depth": self.stale_depth,
            "aggtrades": self.aggtrades,
            "aggressive_buy_aggregates": self.aggressive_buys,
            "aggressive_sell_aggregates": self.aggressive_sells,
            "levels_removed_from_visible_book": self.level_removed,
            "levels_added_to_visible_book": self.level_added,
            "visible_qty_increase_events": self.qty_increase,
            "visible_qty_decrease_events": self.qty_decrease,
            "buffered_depth_end": len(self.buffer),
            "best_bid": str(max(self.bids)) if self.bids else None,
            "best_ask": str(min(self.asks)) if self.asks else None,
            "book_depth_scope": "Snapshot <=1000 per side plus subsequent updates, NOT complete book",
            "removal_not_identical_to_cancellation": True,
            "predictive_test_performed": False
        }

class Journal:
    """Raw UTF-8 frame + arrival clocks + tamper-evident journal hash chain."""
    def __init__(self, path):
        self.path = path
        self.fp = open(path, "w", encoding="utf-8")
        self.prev = "0" * 64
        self.n = 0
        self.bytes_written = 0

    @staticmethod
    def digest(prev, seq, utc_ns, mono_ns, kind, symbol, raw_digest):
        return hashlib.sha256(
            f"{prev}|{seq}|{utc_ns}|{mono_ns}|{kind}|{symbol}|{raw_digest}".encode("utf-8")
        ).hexdigest()

    def append(self, *, kind, symbol, raw, utc_ns, mono_ns):
        if not isinstance(raw, str) or kind not in ("ws","snapshot"):
            raise ValueError("UNSUPPORTED_JOURNAL_ENTRY")
        seq = self.n + 1
        raw_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        chain = self.digest(self.prev, seq, utc_ns, mono_ns, kind, symbol, raw_hash)
        record = {
            "seq":seq,"kind":kind,"symbol":symbol,"utc_ns":utc_ns,"mono_ns":mono_ns,
            "sha256_raw":raw_hash,"prev_chain":self.prev,"chain_sha256":chain,"raw":raw
        }
        encoded = json.dumps(record, ensure_ascii=False, separators=(",",":"))+"\n"
        self.fp.write(encoded)
        self.bytes_written += len(encoded.encode("utf-8"))
        self.n = seq
        self.prev = chain

    def close(self):
        self.fp.flush()
        self.fp.close()

def replay(path):
    books = {s:LocalBook(s) for s in SYMBOLS}
    last = "0"*64
    count = 0
    with open(path,"r",encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            count += 1
            if record["seq"] != count or record["prev_chain"] != last:
                raise ValueError("BROKEN_JOURNAL_CHAIN")
            raw_sha=hashlib.sha256(record["raw"].encode("utf-8")).hexdigest()
            if raw_sha != record["sha256_raw"]:
                raise ValueError("TAMPERED_JOURNAL_RAW")
            calc = Journal.digest(last,count,record["utc_ns"],record["mono_ns"],
                                  record["kind"],record["symbol"],raw_sha)
            if calc != record["chain_sha256"]:
                raise ValueError("TAMPERED_JOURNAL_CHAIN")
            last=calc
            if record["kind"] == "snapshot":
                if record["symbol"] not in books: raise ValueError("UNKNOWN_SNAPSHOT_SYMBOL")
                books[record["symbol"]].snapshot(json.loads(record["raw"]))
            elif record["kind"] == "ws":
                msg = json.loads(record["raw"])
                if not isinstance(msg,dict) or not isinstance(msg.get("stream"),str):
                    raise ValueError("WRONG_COMBINED_STREAM_FRAME")
                stream = msg["stream"]
                symbol = stream.split("@")[0].upper()
                if symbol not in books or stream not in (
                  symbol.lower()+"@depth@100ms",symbol.lower()+"@aggTrade"
                ):
                    raise ValueError("UNAPPROVED_STREAM_FRAME")
                event = msg.get("data")
                if not isinstance(event,dict): raise ValueError("BAD_STREAM_PAYLOAD")
                if event.get("e") != ("depthUpdate" if stream.endswith("@100ms") else "aggTrade"):
                    raise ValueError("STREAM_KIND_MISMATCH")
                books[symbol].ingest(event)
            else: raise ValueError("UNAPPROVED_JOURNAL_KIND")
    return {
        "events": count, "last_chain_hash":last,
        "books": {s:b.summary() for s,b in books.items()}
    }
