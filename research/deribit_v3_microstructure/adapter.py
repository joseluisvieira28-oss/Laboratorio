"""Bounded public book adapter. No execution API; replay never counts as forward."""
import datetime as dt
import hashlib
import json
import math
import re
import urllib.parse
import urllib.request

BASE = 'https://www.deribit.com/api/v2/public/get_order_book?'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('REDIRECT_REFUSED')

def request_url(symbol):
    if not re.fullmatch(r'BTC_USDC-\d{1,2}[A-Z]{3}\d{2}-\d+(?:\.\d+)?-[CP]', symbol):
        raise ValueError('PRODUCT_IDENTITY')
    return BASE + urllib.parse.urlencode(dict(instrument_name=symbol, depth=5))

def decode(raw, symbol, received_ms, provenance='fixture'):
    request_url(symbol)
    if provenance not in {'fixture', 'historical', 'controlled_observation'}:
        raise ValueError('PROVENANCE')
    if not 0 < len(raw) <= 12000000:
        raise ValueError('RESPONSE_SIZE')
    j = json.loads(raw)
    if j.get('testnet') is not False or 'error' in j:
        raise ValueError('SOURCE_IDENTITY')
    b = j['result']
    if b['instrument_name'] != symbol or b['state'] != 'open':
        raise ValueError('BOOK_IDENTITY')
    def finite(x):
        if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
            raise ValueError('NONFINITE')
        return x
    timestamp = finite(b['timestamp'])
    age = finite(received_ms) - timestamp
    if not -3000 <= age <= 10000:
        raise ValueError('STALE_OR_FUTURE')
    sides = {}
    for key in ('bids', 'asks'):
        rows = b[key]
        if not rows or any(len(r) != 2 or any(finite(x) <= 0 for x in r) for r in rows):
            raise ValueError('BOOK_LEVELS')
        prices = [r[0] for r in rows]
        if len(set(prices)) != len(prices) or prices != sorted(prices, reverse=key=='bids'):
            raise ValueError('BOOK_ORDER')
        if rows[0][1] < .05:
            raise ValueError('DEPTH')
        sides[key] = rows
    if sides['bids'][0][0] >= sides['asks'][0][0] or finite(b['index_price']) <= 0:
        raise ValueError('PRICE')
    return dict(symbol=symbol, timestamp=timestamp, received_ms=received_ms, quote_age_ms=age,
                sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), provenance=provenance,
                prospective_v3=False, bid=sides['bids'][0], ask=sides['asks'][0],
                depth=sides, index=b['index_price'], net_pnl=None, delivery_fee_status='UNVERIFIED')

def synchronize(call, put, index_received_ms):
    if not call['symbol'].endswith('-C') or not put['symbol'].endswith('-P') or call['symbol'][:-1] != put['symbol'][:-1]:
        raise ValueError('PAIR_IDENTITY')
    skew = abs(call['timestamp'] - put['timestamp'])
    distances = [abs(b['timestamp'] - index_received_ms) for b in (call, put)]
    if skew > 1000 or max(distances) > 10000:
        raise ValueError('SYNCHRONIZATION')
    return dict(book_skew_ms=skew, per_book_index_distance_ms=distances)

def fetch(symbol):
    """One explicit controlled public request; no retry, auth, redirect or scheduler."""
    url = request_url(symbol)
    req = urllib.request.Request(url, headers={'Accept':'application/json'})
    started = dt.datetime.now(dt.timezone.utc).timestamp()*1000
    with urllib.request.build_opener(NoRedirect).open(req, timeout=15) as response:
        if response.status != 200:
            raise ValueError('HTTP_STATUS')
        raw = response.read(12000001)
    received = dt.datetime.now(dt.timezone.utc).timestamp()*1000
    return raw, dict(url=url, started_ms=started, **decode(raw, symbol, received, 'controlled_observation'))
