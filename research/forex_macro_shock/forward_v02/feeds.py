"""Timestamped order book reconstruction; pure adapters, no execution."""
from decimal import Decimal
from collections import deque
import collector as c


class DepthBook:
    def __init__(self, venue):
        if venue not in ['binance', 'mexc']:
            raise ValueError('UNKNOWN_VENUE')
        self.venue = venue
        self.reset()

    def reset(self):
        self.bids = {}; self.asks = {}; self.last = None
        self.exchange_ms = None; self.received_ms = None
        self.ready = False; self.last_delta_hash = None
        self.history = deque()

    def snapshot(self, obj):
        data = obj['data'] if self.venue == 'mexc' else obj
        if self.venue == 'mexc' and obj.get('success') is not True:
            raise ValueError('SNAPSHOT_FAILED')
        self.reset()
        c.book(data)
        self.bids = {Decimal(str(p)): Decimal(str(q)) for p, q, *rest in data['bids']}
        self.asks = {Decimal(str(p)): Decimal(str(q)) for p, q, *rest in data['asks']}
        self.last = data['version' if self.venue == 'mexc' else 'lastUpdateId']
        if not isinstance(self.last, int) or self.last < 0:
            self.reset(); raise ValueError('INVALID_SNAPSHOT_SEQUENCE')
        # REST snapshot is only a bootstrap, not a timestamped live quote.

    def delta(self, obj, receipt_ms):
        if self.last is None:
            raise ValueError('NO_BOOTSTRAP')
        if self.venue == 'binance':
            if obj.get('e') != 'depthUpdate' or obj.get('s') != 'EURUSDT':
                raise ValueError('WRONG_SYMBOL_OR_CHANNEL')
            first, last, exchange_ms = obj['U'], obj['u'], obj['E']
            bids, asks = obj['b'], obj['a']
        else:
            if obj.get('channel') != 'push.depth' or obj.get('symbol') != 'EUR_USDT':
                raise ValueError('WRONG_SYMBOL_OR_CHANNEL')
            data = obj['data']; last = data['version']; first = last
            exchange_ms = data.get('cts')  # matching engine clock, never invented from ts
            bids, asks = data['bids'], data['asks']
        if not all(isinstance(x, int) and x >= 0 for x in [first, last]) or first > last:
            self.reset(); raise ValueError('INVALID_SEQUENCE')
        payload_hash = c.digest(c.canonical(obj).encode())
        if last < self.last:
            if self.ready:
                self.reset(); raise ValueError('OUT_OF_ORDER')
            return False  # old buffered delta during initial bootstrap
        if last == self.last:
            if self.ready and self.last_delta_hash != payload_hash:
                self.reset(); raise ValueError('DUPLICATE_ID_CONFLICT')
            return False
        if first > self.last + 1:
            self.reset(); raise ValueError('SEQUENCE_GAP')
        if not isinstance(exchange_ms, int) or exchange_ms < 1_000_000_000_000:
            self.reset(); raise ValueError('MISSING_EXCHANGE_CLOCK')
        if self.exchange_ms is not None and exchange_ms < self.exchange_ms:
            self.reset(); raise ValueError('EXCHANGE_CLOCK_REVERSED')
        for target, levels in [(self.bids, bids), (self.asks, asks)]:
            for level in levels:
                price, quantity = Decimal(str(level[0])), Decimal(str(level[1]))
                if not price.is_finite() or price <= 0 or not quantity.is_finite() or quantity < 0:
                    self.reset(); raise ValueError('INVALID_LEVEL')
                if quantity == 0:
                    target.pop(price, None)
                else:
                    target[price] = quantity
        if len(self.bids) > 10000 or len(self.asks) > 10000:
            self.reset(); raise ValueError('BOOK_MEMORY_LIMIT')
        try:
            result = self.levels()
            c.book(result)
        except Exception:
            self.reset(); raise
        self.last = last; self.exchange_ms = exchange_ms; self.received_ms = receipt_ms
        self.last_delta_hash = payload_hash; self.ready = True
        self.history.append({'exchange_ms': exchange_ms, 'received_ms': receipt_ms,
                             'sequence': last, **c.book(result)})
        # Keep bounded recent state, including the predecessor of the retention edge.
        while len(self.history) > 1 and self.history[1]['received_ms'] < receipt_ms-3000:
            self.history.popleft()
        return True

    def levels(self):
        return {'bids': [[str(p), str(q)] for p, q in sorted(self.bids.items(), reverse=True)],
                'asks': [[str(p), str(q)] for p, q in sorted(self.asks.items())]}

    def observation(self, now_ms):
        # The decision timestamp is a cutoff, never the delayed loop wake-up time.
        selected = next((x for x in reversed(self.history) if x['received_ms'] <= now_ms), None)
        if not self.ready or selected is None:
            return {'valid': False, 'reason': 'NO_BOOK_RECEIVED_BY_GRID'}
        age = now_ms - selected['exchange_ms']
        receipt_age = now_ms - selected['received_ms']
        valid = -250 <= age <= 1000 and 0 <= receipt_age <= 1000
        return {**selected, 'valid': valid, 'source_age_ms': age,
                'receipt_age_ms': receipt_age}


def clock_quality(row, validation):
    if not validation.get('schema_valid') or validation.get('exchange_ms') is None:
        return False
    offset = validation['exchange_ms'] - (row['started_ms'] + row['received_ms']) / 2
    return row['rtt_ms'] <= 500 and abs(offset) + row['rtt_ms'] / 2 <= 250
