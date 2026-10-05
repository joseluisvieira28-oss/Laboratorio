"""Public-only technical burn-in. No strategy runner or economic outcomes.

Python 3.11+, stdlib only. Persistent raw responses and receipt hash chain.
The setup runtime hard-stops before the protected event and cannot arm itself.
"""
import argparse
import concurrent.futures
import hashlib
import json
import math
import sqlite3
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SETUP_STOP = datetime(2026, 10, 23, tzinfo=timezone.utc).timestamp()
SOURCES = {
    'mexc_metadata': 'https://api.mexc.com/api/v1/contract/detail?symbol=EUR_USDT',
    'mexc_clock': 'https://api.mexc.com/api/v1/contract/ping',
    'mexc_depth': 'https://api.mexc.com/api/v1/contract/depth/EUR_USDT',
    'mexc_ticker': 'https://api.mexc.com/api/v1/contract/ticker?symbol=EUR_USDT',
    'mexc_trades': 'https://api.mexc.com/api/v1/contract/deals/EUR_USDT',
    'mexc_index': 'https://api.mexc.com/api/v1/contract/index_price/EUR_USDT',
    'mexc_fair': 'https://api.mexc.com/api/v1/contract/fair_price/EUR_USDT',
    'binance_metadata': 'https://data-api.binance.vision/api/v3/exchangeInfo?symbol=EURUSDT',
    'binance_clock': 'https://data-api.binance.vision/api/v3/time',
    'binance_depth': 'https://data-api.binance.vision/api/v3/depth?symbol=EURUSDT&limit=100',
    'binance_trades': 'https://data-api.binance.vision/api/v3/trades?symbol=EURUSDT&limit=100',
    'ecb_index': 'https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html',
    'ecb_calendar': 'https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html',
}


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(data):
    return hashlib.sha256(data).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PermissionError('REDIRECT_NOT_ALLOWED: ' + newurl)


def fetch(source):
    url = SOURCES[source]  # no configurable arbitrary URL/private endpoint
    started = time.time_ns() // 1_000_000
    mono = time.monotonic_ns()
    row = {'source': source, 'url': url, 'started_ms': started}
    raw = b''
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CryptoLab-FX-TechnicalBurnIn/0.2'})
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(req, timeout=12) as response:
            raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise ValueError('RESPONSE_TOO_LARGE')
            row.update(http_status=response.status, headers=dict(response.headers))
    except urllib.error.HTTPError as exc:
        raw = exc.read(4_000_000)
        row.update(http_status=exc.code, headers=dict(exc.headers), error='HTTP_ERROR')
    except Exception as exc:
        row['error'] = type(exc).__name__ + ': ' + str(exc)
    row.update(received_ms=time.time_ns() // 1_000_000,
               rtt_ms=(time.monotonic_ns() - mono) / 1_000_000,
               raw_sha256=digest(raw), raw_bytes=len(raw))
    return row, raw


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError('NONPOSITIVE_OR_NONFINITE')
    return number


def book(data):
    bids = data['bids']; asks = data['asks']
    if not bids or not asks:
        raise ValueError('EMPTY_BOOK')
    bp = [positive(x[0]) for x in bids]; ap = [positive(x[0]) for x in asks]
    for level in bids + asks:
        positive(level[1])
    if bp != sorted(bp, reverse=True) or ap != sorted(ap) or len(set(bp)) != len(bp) or len(set(ap)) != len(ap):
        raise ValueError('INVALID_BOOK_ORDER')
    if bp[0] >= ap[0]:
        raise ValueError('CROSSED_OR_LOCKED_BOOK')
    return {'bid_levels': len(bids), 'ask_levels': len(asks), 'bid': bp[0],
            'ask': ap[0], 'mid': (bp[0] + ap[0]) / 2}


def validate(row, raw):
    result = {'schema_valid': False, 'timing_valid': False, 'exchange_ms': None}
    try:
        if row.get('error') or row.get('http_status') != 200:
            raise ValueError(row.get('error', 'HTTP_NOT_200'))
        name = row['source']
        if name.startswith('ecb_'):
            text = raw.decode('utf-8')
            required = 'monetary policy' if name == 'ecb_index' else '29/10/2026'
            if required not in text or 'Site Unavailable' in text:
                raise ValueError('ECB_DOCUMENT_NOT_VALID')
            result.update(schema_valid=True, semantic_publication_detected=False,
                          note='Index/calendar capture only; generic HTML change is not a release.')
            return result
        obj = json.loads(raw)
        if name.startswith('mexc_'):
            if obj.get('success') is not True:
                raise ValueError('MEXC_SUCCESS_FALSE')
            data = obj['data']
        else:
            data = obj
        if name.endswith('_metadata'):
            if name.startswith('mexc'):
                contracts = data if isinstance(data, list) else [data]
                contract = next(c for c in contracts if c['symbol'] == 'EUR_USDT')
                if contract['baseCoin'] != 'EUR' or contract['quoteCoin'] != 'USDT' or contract['state'] != 0:
                    raise ValueError('CONTRACT_IDENTITY_INVALID')
                for key in ['contractSize', 'volUnit', 'minVol']:
                    positive(contract[key])
                result['identity'] = {k: contract[k] for k in ['symbol', 'contractSize', 'volUnit', 'minVol', 'indexOrigin']}
            else:
                symbol = next(x for x in data['symbols'] if x['symbol'] == 'EURUSDT')
                if (symbol['baseAsset'], symbol['quoteAsset'], symbol['status']) != ('EUR', 'USDT', 'TRADING'):
                    raise ValueError('SPOT_IDENTITY_INVALID')
                result['identity'] = {k: symbol[k] for k in ['symbol', 'baseAsset', 'quoteAsset', 'status']}
        elif name.endswith('_depth'):
            result.update(book(data))
            result['update_id'] = data.get('version', data.get('lastUpdateId'))
            result['exchange_ms'] = data.get('timestamp') if name.startswith('mexc') else None
            if result['exchange_ms'] is None:
                result['timing_reason'] = 'NO_EXCHANGE_TIMESTAMP: REST Binance depth is source-only.'
        elif name.endswith('_clock'):
            result['exchange_ms'] = data if name.startswith('mexc') else data['serverTime']
        elif name.endswith('_trades'):
            if not isinstance(data, list) or not data:
                raise ValueError('EMPTY_TRADES')
            result['records'] = len(data)
        elif name == 'mexc_ticker':
            if data['symbol'] != 'EUR_USDT':
                raise ValueError('SYMBOL_MISMATCH')
            for key in ['bid1', 'ask1', 'lastPrice']:
                positive(data[key])
            result['exchange_ms'] = data.get('timestamp')
        elif name in ['mexc_index', 'mexc_fair']:
            positive(data['indexPrice' if name.endswith('index') else 'fairPrice'])
            result['exchange_ms'] = data.get('timestamp')
            result['independent_venue'] = False
        result['schema_valid'] = True
        exchange_ms = result['exchange_ms']
        if exchange_ms is not None:
            if not isinstance(exchange_ms, int) or exchange_ms < 1_000_000_000_000:
                raise ValueError('INVALID_MILLISECOND_TIMESTAMP')
            result['clock_offset_estimate_ms'] = exchange_ms - (row['started_ms'] + row['received_ms']) / 2
            result['source_age_ms'] = row['received_ms'] - exchange_ms
            result['timing_valid'] = row['rtt_ms'] <= 500 and -250 <= result['source_age_ms'] <= 1000
    except (ValueError, KeyError, TypeError, StopIteration, UnicodeError) as exc:
        result.update(schema_valid=False, timing_valid=False, reason=str(exc))
    return result


class Store:
    def __init__(self, path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=10)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS raw(hash TEXT PRIMARY KEY, body BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS receipts(seq INTEGER PRIMARY KEY, token TEXT UNIQUE NOT NULL,
                payload TEXT NOT NULL, previous_hash TEXT NOT NULL, hash TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS messages(source TEXT, identity TEXT, raw_hash TEXT,
                PRIMARY KEY(source,identity));
            CREATE TABLE IF NOT EXISTS lock(id INTEGER PRIMARY KEY CHECK(id=1), owner TEXT, until_ms INTEGER);
        ''')
        self.db.commit()

    def acquire(self, owner, now_ms):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self.db.execute('SELECT owner,until_ms FROM lock WHERE id=1').fetchone()
            if row and row[1] > now_ms and row[0] != owner:
                raise RuntimeError('COLLECTOR_ALREADY_RUNNING')
            self.db.execute('INSERT OR REPLACE INTO lock VALUES(1,?,?)', (owner, now_ms + 60_000))

    def release(self, owner):
        with self.db:
            self.db.execute('DELETE FROM lock WHERE owner=?', (owner,))

    def append(self, token, row, raw):
        if digest(raw) != row['raw_sha256']:
            raise ValueError('RAW_HASH_MISMATCH')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            existing = self.db.execute('SELECT hash FROM receipts WHERE token=?', (token,)).fetchone()
            if existing:
                prior = json.loads(self.db.execute('SELECT payload FROM receipts WHERE token=?', (token,)).fetchone()[0])
                if prior['raw_sha256'] != row['raw_sha256']:
                    raise ValueError('IDEMPOTENCY_CONFLICT')
                return existing[0]
            row = dict(row)
            validation = row.get('validation', {})
            identity = validation.get('update_id')
            if identity is not None:
                old = self.db.execute('SELECT raw_hash FROM messages WHERE source=? AND identity=?', (row['source'], str(identity))).fetchone()
                row['duplicate_message'] = bool(old)
                if old and old[0] != row['raw_sha256']:
                    row['message_identity_conflict'] = True
                    row['validation'] = dict(validation, timing_valid=False, schema_valid=False)
                self.db.execute('INSERT OR IGNORE INTO messages VALUES(?,?,?)', (row['source'], str(identity), row['raw_sha256']))
            previous = self.db.execute('SELECT hash FROM receipts ORDER BY seq DESC LIMIT 1').fetchone()
            previous = previous[0] if previous else '0' * 64
            payload = canonical({'token': token, **row})
            sha = digest((previous + payload).encode())
            self.db.execute('INSERT OR IGNORE INTO raw VALUES(?,?)', (row['raw_sha256'], raw))
            self.db.execute('INSERT INTO receipts(token,payload,previous_hash,hash) VALUES(?,?,?,?)', (token, payload, previous, sha))
            return sha

    def verify(self):
        previous = '0' * 64; n = 0
        if self.db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLITE_INTEGRITY_FAILURE')
        for token, payload, prior, sha in self.db.execute('SELECT token,payload,previous_hash,hash FROM receipts ORDER BY seq'):
            if prior != previous or digest((prior + payload).encode()) != sha:
                raise ValueError('CHAIN_INVALID')
            obj = json.loads(payload)
            if obj['token'] != token:
                raise ValueError('TOKEN_INVALID')
            raw = self.db.execute('SELECT body FROM raw WHERE hash=?', (obj['raw_sha256'],)).fetchone()
            if raw is None or digest(raw[0]) != obj['raw_sha256']:
                raise ValueError('RAW_INVALID')
            previous = sha; n += 1
        return {'receipts': n, 'chain_head': previous, 'integrity': 'PASS'}

    def export(self, target):
        result = self.verify()
        target = Path(target); target.mkdir(parents=True, exist_ok=True)
        rows = [json.loads(r[0]) for r in self.db.execute('SELECT payload FROM receipts ORDER BY seq')]
        latencies = {}
        for source in SOURCES:
            samples = [r['rtt_ms'] for r in rows if r['source'] == source]
            if samples:
                latencies[source] = {'n': len(samples), 'median_ms': statistics.median(samples), 'max_ms': max(samples)}
        report = {**result, 'candidate_id': 'FOREX-ECB-EURUSDT-DISLOCATION-FWD-001',
                  'mode': 'TECHNICAL_BURN_IN_ONLY', 'verdict': 'OPERATIONALLY_BLOCKED',
                  'outcomes_opened': 0, 'signals_emitted': 0, 'latency_stats': latencies,
                  'rows': rows, 'activation': False,
                  'blockers': ['Qualified timestamped MEXC/Binance live pair not established',
                               'REST sampler is not a validated microstructure event runtime',
                               'Continuous persistent operator runtime not active',
                               'Semantic ECB target-release watcher not event-tested',
                               'Burn-in calibration minimums not met']}
        (target / 'SETUP_RECEIPT_V02.json').write_text(json.dumps(report, indent=2, allow_nan=False))
        rawdir = target / 'raw'; rawdir.mkdir(exist_ok=True)
        for sha, body in self.db.execute('SELECT hash,body FROM raw'):
            (rawdir / (sha + '.bin')).write_bytes(body)
        return {k: v for k, v in report.items() if k != 'rows'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', default=str(ROOT / 'state' / 'burnin.sqlite3'))
    parser.add_argument('--cycles', type=int, default=1)
    parser.add_argument('--interval', type=float, default=5)
    parser.add_argument('--export', default=str(ROOT / 'evidence'))
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.cycles <= 10000 or args.interval < 5:
        parser.error('cycles 1..10000 and interval >=5 seconds required; no event mode exists')
    store = Store(args.state)
    store.verify()  # detect corruption before accepting new observations
    if args.verify_only:
        print(canonical(store.export(args.export))); return
    owner = digest(str(time.time_ns()).encode())
    try:
        for cycle in range(args.cycles):
            if time.time() + 15 >= SETUP_STOP:
                raise RuntimeError('PROTECTED_EVENT_LOCK: setup stops on 2026-10-23 UTC')
            store.acquire(owner, time.time_ns() // 1_000_000)
            selected = list(SOURCES) if cycle == 0 else [s for s in SOURCES if s.endswith(('_depth', '_clock', '_trades', '_ticker'))]
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
                for row, raw in pool.map(fetch, selected):
                    row['validation'] = validate(row, raw)
                    store.append(owner + ':' + str(cycle) + ':' + row['source'], row, raw)
            if cycle < args.cycles - 1:
                time.sleep(args.interval)
    finally:
        store.release(owner)
        print(canonical(store.export(args.export)))
        store.db.close()


if __name__ == '__main__':
    main()
