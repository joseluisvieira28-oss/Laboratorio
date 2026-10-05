"""Continuous public source/burn-in runtime. Activation and outcomes remain locked.

Run on persistent operator disk. Stops strictly before setup cutoff. No orders,
credentials, event execution, signals or historical price downloads.
"""
import argparse
import asyncio
import json
import math
import signal
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import collector as c
from feeds import DepthBook, clock_quality
import ecb_watcher as ecb


WS = {'binance': 'wss://data-stream.binance.vision/ws/eurusdt@depth@100ms',
      'mexc': 'wss://contract.mexc.com/edge'}
SNAPSHOT_URL = {'binance': 'https://data-api.binance.vision/api/v3/depth?symbol=EURUSDT&limit=5000',
                'mexc': 'https://api.mexc.com/api/v1/contract/depth/EUR_USDT?limit=1000'}
FREEZE_HASH = c.digest((c.ROOT / 'PRE_OUTCOME_METHOD_FREEZE_V02.json').read_bytes())


def ms(): return time.time_ns() // 1_000_000


def setup_allowed(now): return now + 15 < c.SETUP_STOP


def fetch_allowed(url, source):
    if url not in SNAPSHOT_URL.values() and not ecb.allowed_release(url, '2026-10-29'):
        raise PermissionError('URL_NOT_ALLOWLISTED')
    row = {'source': source, 'url': url, 'started_ms': ms()}
    begin = time.monotonic_ns(); raw = b''
    try:
        opener = urllib.request.build_opener(c.NoRedirect())
        with opener.open(urllib.request.Request(url, headers={'User-Agent': 'CryptoLab-FX-BurnIn/0.2'}), timeout=12) as response:
            raw = response.read(4_000_001)
            if len(raw) > 4_000_000: raise ValueError('RESPONSE_TOO_LARGE')
            row.update(http_status=response.status, headers=dict(response.headers))
    except urllib.error.HTTPError as exc:
        raw = exc.read(4_000_000); row.update(http_status=exc.code, error='HTTP_ERROR')
    except Exception as exc:
        row['error'] = type(exc).__name__ + ': ' + str(exc)
    row.update(received_ms=ms(), rtt_ms=(time.monotonic_ns()-begin)/1_000_000,
               raw_sha256=c.digest(raw), raw_bytes=len(raw))
    return row, raw


class Runtime:
    def __init__(self, state):
        self.store = c.Store(state); self.store.verify()
        self.owner = c.digest(str(time.time_ns()).encode())
        self.store.acquire(self.owner, ms())
        self.counter = 0; self.books = {v: DepthBook(v) for v in WS}
        self.clock = {}; self.metadata = {}; self.stop = asyncio.Event()
        self.status = {}; self.last_negative = None
        self.last_wall = None; self.last_mono = None
        self.freeze_hash = FREEZE_HASH
        hashes = {p.name: c.digest(p.read_bytes()) for p in [c.ROOT/'runtime.py', c.ROOT/'feeds.py', c.ROOT/'ecb_watcher.py', c.ROOT/'collector.py']}
        self.record('runtime_start', {'code_hashes': hashes, 'previous_chain': self.store.verify()['chain_head'], 'outcomes_opened': 0})

    def record(self, source, payload, validation=None, raw=None, row=None):
        raw = raw if raw is not None else c.canonical(payload).encode()
        row = dict(row or {'source': source, 'started_ms': ms(), 'received_ms': ms(), 'rtt_ms': 0})
        row.update(source=source, raw_sha256=c.digest(raw), raw_bytes=len(raw),
                   freeze_sha256=self.freeze_hash, monotonic_receipt_ns=time.monotonic_ns(),
                   validation=validation or {})
        self.counter += 1
        self.store.append(self.owner+':'+str(self.counter), row, raw)

    async def status_error(self, venue, exc):
        self.books[venue].reset()
        reason = type(exc).__name__ + ': ' + str(exc)
        self.status[venue] = {'connected': False, 'reason': reason}
        self.record(venue+'_connection_failure', {'reason': reason, 'captured_ms': ms()})

    async def feed(self, venue):
        import websockets
        retry = 2
        while not self.stop.is_set() and setup_allowed(time.time()):
            self.books[venue].reset()
            try:
                # Fixed official market-data WS only. No manual proxy, auth or regional bypass.
                async with websockets.connect(WS[venue], open_timeout=10, close_timeout=2,
                                              ping_interval=20, ping_timeout=20, max_size=4_000_000, max_queue=256) as ws:
                    self.status[venue] = {'connected': True, 'ready': False}
                    if venue == 'mexc':
                        await ws.send(c.canonical({'method': 'sub.depth', 'param': {'symbol': 'EUR_USDT', 'compress': False}, 'gzip': False}))
                    bootstrap = asyncio.create_task(asyncio.to_thread(fetch_allowed, SNAPSHOT_URL[venue], venue+'_bootstrap'))
                    buffer = []
                    try:
                        # Receive and timestamp while REST bootstrap is pending.
                        while not bootstrap.done():
                            try:
                                raw = await asyncio.wait_for(ws.recv(), .2)
                                receipt = ms()
                                if isinstance(raw, bytes):
                                    raise ValueError('UNEXPECTED_BINARY_FRAME')
                                self.record(venue+'_wire', {}, raw=raw.encode(), row={'received_ms': receipt, 'started_ms': receipt, 'rtt_ms': 0})
                                obj = json.loads(raw)
                                is_depth = obj.get('e') == 'depthUpdate' if venue == 'binance' else obj.get('channel') == 'push.depth'
                                self.record(venue+'_ws', obj, raw=raw.encode(), row={'received_ms': receipt, 'started_ms': receipt, 'rtt_ms': 0})
                                if is_depth: buffer.append((obj, receipt))
                                if len(buffer) > 10000: raise ValueError('BOOTSTRAP_BUFFER_OVERFLOW')
                            except asyncio.TimeoutError:
                                pass
                        row, raw = await bootstrap
                        self.record(venue+'_bootstrap', {}, raw=raw, row=row)
                        if row.get('http_status') != 200 or row.get('error'):
                            raise ValueError('BOOTSTRAP_HTTP_INVALID')
                        self.books[venue].snapshot(json.loads(raw))
                        for obj, receipt in buffer: self.books[venue].delta(obj, receipt)
                        retry = 2
                        last_ping = time.monotonic()
                        while not self.stop.is_set() and setup_allowed(time.time()):
                            if venue == 'mexc' and time.monotonic()-last_ping > 15:
                                await ws.send('{"method":"ping"}'); last_ping=time.monotonic()
                            try: raw = await asyncio.wait_for(ws.recv(), 1)
                            except asyncio.TimeoutError: continue
                            receipt = ms()
                            if isinstance(raw, bytes): raise ValueError('UNEXPECTED_BINARY_FRAME')
                            self.record(venue+'_wire', {}, raw=raw.encode(), row={'received_ms': receipt, 'started_ms': receipt, 'rtt_ms': 0})
                            obj = json.loads(raw)
                            is_depth = obj.get('e') == 'depthUpdate' if venue == 'binance' else obj.get('channel') == 'push.depth'
                            validation = {'is_depth': is_depth}
                            if is_depth:
                                validation['applied'] = self.books[venue].delta(obj, receipt)
                                validation['exchange_ms'] = self.books[venue].exchange_ms
                                if self.books[venue].exchange_ms is not None:
                                    validation['source_age_ms'] = receipt-self.books[venue].exchange_ms
                                self.status[venue]['ready'] = self.books[venue].ready
                            self.record(venue+'_ws', obj, validation, raw.encode(), {'received_ms': receipt, 'started_ms': receipt, 'rtt_ms': 0})
                    finally:
                        if not bootstrap.done(): bootstrap.cancel()
            except asyncio.CancelledError:
                self.books[venue].reset(); raise
            except Exception as exc:
                await self.status_error(venue, exc)
                try: await asyncio.wait_for(self.stop.wait(), retry)
                except asyncio.TimeoutError: pass
                retry = min(30, retry*2)

    async def prerequisites(self):
        while not self.stop.is_set() and setup_allowed(time.time()):
            for venue in WS:
                for field in ['metadata', 'clock']:
                    source = venue+'_'+field
                    row, raw = await asyncio.to_thread(c.fetch, source)
                    validation = c.validate(row, raw)
                    self.record(source, {}, validation, raw, row)
                    if field == 'clock':
                        self.clock[venue] = {'valid': clock_quality(row, validation), 'received_ms': row['received_ms']}
                    else:
                        self.metadata[venue] = {'valid': validation['schema_valid'], 'received_ms': row['received_ms']}
            try: await asyncio.wait_for(self.stop.wait(), 60)
            except asyncio.TimeoutError: pass

    async def watcher(self):
        while not self.stop.is_set() and setup_allowed(time.time()):
            try:
                row, raw = await asyncio.to_thread(c.fetch, 'ecb_index')
                validated = c.validate(row, raw)
                self.record('ecb_index', {}, validated, raw, row)
                if not validated['schema_valid']: raise ValueError('INVALID_ECB_INDEX')
                urls = ecb.discover(raw, '2026-10-29')
                if not urls:
                    self.last_negative = row['received_ms']
                for url in urls:
                    release_row, body = await asyncio.to_thread(fetch_allowed, url, 'ecb_release')
                    if release_row.get('http_status') != 200 or release_row.get('error'):
                        raise ValueError('INVALID_ECB_RELEASE_HTTP')
                    parsed = ecb.publication(body, url, '2026-10-29')
                    prior = ecb.first_seen(self.store, parsed['event_id'])
                    parsed.update(first_seen_ms=prior if prior is not None else release_row['received_ms'],
                                  observation_interval_valid=ecb.timing_interval(self.last_negative, release_row['received_ms'], release_row['rtt_ms']))
                    self.record('ecb_release', {}, parsed, body, release_row)
            except asyncio.CancelledError: raise
            except Exception as exc: self.record('ecb_watcher_failure', {'reason': type(exc).__name__+': '+str(exc)})
            # Setup polling only. Event-window 1s mode is locked, not silently enabled.
            try: await asyncio.wait_for(self.stop.wait(), 60)
            except asyncio.TimeoutError: pass

    async def grids(self):
        while not self.stop.is_set() and setup_allowed(time.time()):
            due = (ms()//1000+1)*1000
            await asyncio.sleep(max(0, (due-ms())/1000))
            now = ms(); mono = time.monotonic_ns()/1_000_000
            clock_step = (self.last_wall is not None and abs((now-self.last_wall)-(mono-self.last_mono)) > 250)
            self.last_wall, self.last_mono = now, mono
            self.store.acquire(self.owner, now)
            observations = {venue: self.books[venue].observation(now) for venue in WS}
            valid = now-due <= 250 and not clock_step and all(x['valid'] for x in observations.values())
            valid = valid and all(self.clock.get(v, {}).get('valid', False) and now-self.clock[v]['received_ms'] <= 120000 for v in WS)
            valid = valid and all(self.metadata.get(v, {}).get('valid', False) and now-self.metadata[v]['received_ms'] <= 3600000 for v in WS)
            if all(x['valid'] for x in observations.values()):
                valid = valid and abs(observations['mexc']['exchange_ms']-observations['binance']['exchange_ms']) <= 500
            current = datetime.fromtimestamp(due/1000, timezone.utc)
            eligible = current.weekday()<5 and 10 <= current.hour < 16
            payload = {'grid_ms': due, 'captured_ms': now, 'grid_lateness_ms': now-due,
                       'clock_step': clock_step, 'source_valid': bool(valid), 'burnin_eligible': eligible,
                       'observations': observations, 'outcomes_opened': 0, 'signals_emitted': 0}
            if valid and eligible:
                mexc = observations['mexc']; binance=observations['binance']
                payload['basis_bps'] = 10000*math.log(mexc['mid']/binance['mid'])
                payload['mexc_spread_bps'] = 10000*(mexc['ask']-mexc['bid'])/mexc['mid']
            self.record('paired_grid', payload)

    async def run(self, seconds):
        self.store.acquire(self.owner, ms())
        tasks = [asyncio.create_task(x) for x in [self.feed('binance'), self.feed('mexc'), self.prerequisites(), self.watcher(), self.grids()]]
        failure = None
        try:
            deadline = asyncio.create_task(asyncio.sleep(seconds))
            stop_wait = asyncio.create_task(self.stop.wait())
            done, _ = await asyncio.wait(tasks+[deadline, stop_wait], return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                if task in tasks and not task.cancelled() and task.exception():
                    failure=task.exception(); raise failure
        finally:
            self.stop.set()
            for task in tasks: task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            for task in [deadline, stop_wait]: task.cancel()
            await asyncio.gather(deadline, stop_wait, return_exceptions=True)
            self.record('runtime_stop', {'outcomes_opened': 0, 'status': self.status, 'failure': str(failure) if failure else None})
            self.store.release(self.owner)


async def main_async(args):
    if not setup_allowed(time.time()): raise RuntimeError('PROTECTED_EVENT_LOCK')
    runtime = Runtime(args.state)
    loop = asyncio.get_running_loop()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        try: loop.add_signal_handler(sig, runtime.stop.set)
        except (NotImplementedError, RuntimeError): pass
    try:
        await runtime.run(args.seconds)
        integrity = runtime.store.verify()
        rows = [json.loads(x[0]) for x in runtime.store.db.execute('SELECT payload FROM receipts ORDER BY seq')]
        grids = [json.loads(runtime.store.db.execute('SELECT body FROM raw WHERE hash=?', (r['raw_sha256'],)).fetchone()[0]) for r in rows if r['source']=='paired_grid']
        ws_rows = [r for r in rows if r['source']=='binance_ws' and r.get('validation',{}).get('applied')]
        ages = [r['validation']['source_age_ms'] for r in ws_rows]
        import statistics
        report = {**integrity, 'candidate_id': 'FOREX-ECB-EURUSDT-DISLOCATION-FWD-001',
                  'status': runtime.status, 'verdict': 'OPERATIONALLY_BLOCKED', 'activation': False,
                  'outcomes_opened': 0, 'economic_events': 0, 'paired_grids': len(grids),
                  'valid_burnin_grids': sum(g['source_valid'] and g['burnin_eligible'] for g in grids),
                  'binance_applied_deltas': len(ws_rows),
                  'binance_age_ms': {'n': len(ages), 'median': statistics.median(ages) if ages else None, 'max': max(ages) if ages else None},
                  'freeze_sha256': FREEZE_HASH,
                  'blockers': ['Paired source/clock/burn-in gates must pass', 'Event capture remains locked; setup stops 23 Oct', 'No qualified continuous operator runtime receipt']}
        target=Path(args.report);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(report,indent=2));print(c.canonical(report))
    finally: runtime.store.db.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--state', default=str(c.ROOT/'state/continuous.sqlite3'))
    parser.add_argument('--seconds',type=int,default=60)
    parser.add_argument('--report',default=str(c.ROOT/'evidence/RUNTIME_RECEIPT_V02_1.json'))
    args=parser.parse_args()
    if not 1 <= args.seconds <= 86400: parser.error('seconds 1..86400; no event mode')
    asyncio.run(main_async(args))


if __name__=='__main__': main()
