"""Public-only shadow operator. No account, credential or order interface."""
from __future__ import annotations
import argparse
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import html
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'Dream-Account-OS-v2.3-PARTIAL' / 'src'))
from dream_account.mexc_client import MEXCClient
from dream_account.reliability import ReliableHTTP
from existing_signals import read_one
from existing_custody_gate import validate_quote_after_signal

ZERO_HASH = '0' * 64
LANES = {'SOL_CONVEX_1H': ('SOL_USDT', 3600000), 'BNB_CONVEX_4H': ('BNB_USDT', 14400000)}
PROTOCOL = {
    'mode': 'PAPER_SHADOW_ONLY', 'economic_verdict': 'NO_GO_EDGE_UNPROVEN',
    'convex_source_commit': 'f3e22ce065796bc073096892599669f7df13d141',
    'funding_source_commit': 'e83854059a0dd68701ac3c28dda3da79b7b23b62',
    'funding_rule': 'BTC OKX linear-minus-inverse last settled bps/hour; abs >= 0.5; 00:05 UTC; 24h; no threshold changes',
    'convex_lanes': LANES, 'notional_usdt': '100', 'fee_bps_per_execution': None,
    'slippage_reserve_bps': None, 'eur_per_usdt': None,
    'maximum_quote_age_ms': 2000, 'maximum_poll_gap_ms': 90000,
    'limits': 'No autonomous orders, no private API, no leverage, no historical 2026 reads. Local chain is not an independent signature.',
}

def now_ms(): return time.time_ns() // 1000000
def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
def sha(data): return hashlib.sha256(data).hexdigest()
def number(value):
    result = Decimal(str(value))
    if not result.is_finite(): raise ValueError('NONFINITE_NUMBER')
    return result

class Store:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        (self.folder / 'raw').mkdir(exist_ok=True)
        self.raw_bytes = sum(p.stat().st_size for p in (self.folder / 'raw').iterdir())
        self.db = sqlite3.connect(self.folder / 'receipts.sqlite3', timeout=10)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS receipts (seq INTEGER PRIMARY KEY, previous TEXT NOT NULL, digest TEXT UNIQUE NOT NULL, body TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY)')
        self.db.commit()
        freeze_path = self.folder / 'freeze.json'
        if not freeze_path.exists():
            frozen = {'started_ms': now_ms(), 'protocol': PROTOCOL,
                      'code_hashes': {p.name: sha(p.read_bytes()) for p in (HERE / 'shadow.py', HERE / 'existing_signals.py', HERE / 'existing_custody_gate.py')}}
            try:
                with freeze_path.open('x', encoding='utf-8') as f: f.write(canonical(frozen))
            except FileExistsError: pass
        self.freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
        if canonical(self.freeze['protocol']) != canonical(PROTOCOL): raise ValueError('PROTOCOL_CHANGED_USE_NEW_STATE_FOLDER')
        for name, digest in self.freeze['code_hashes'].items():
            if sha((HERE / name).read_bytes()) != digest: raise ValueError('CODE_CHANGED_USE_NEW_STATE_FOLDER')
        self.verify()
        self.freeze_digest = sha(canonical(self.freeze).encode())
        row = self.db.execute('SELECT body FROM receipts ORDER BY seq LIMIT 1').fetchone()
        if row and json.loads(row[0]).get('freeze_sha256') != self.freeze_digest:
            raise ValueError('FREEZE_TAMPERED')

    def add(self, kind, data, ident=None):
        body = canonical({'kind': kind, 'received_ms': now_ms(), 'freeze_sha256': self.freeze_digest, 'data': data})
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if ident is not None and not self.db.execute('INSERT OR IGNORE INTO seen VALUES(?)', (ident,)).rowcount:
                return None
            row = self.db.execute('SELECT digest FROM receipts ORDER BY seq DESC LIMIT 1').fetchone()
            previous = row[0] if row else ZERO_HASH
            digest = sha((previous + '\n' + body).encode())
            self.db.execute('INSERT INTO receipts(previous,digest,body) VALUES(?,?,?)', (previous, digest, body))
        return digest

    def verify(self):
        previous = ZERO_HASH
        for seq, prior, digest, body in self.db.execute('SELECT * FROM receipts ORDER BY seq'):
            if prior != previous or sha((prior + '\n' + body).encode()) != digest:
                raise ValueError(f'RECEIPT_CHAIN_BROKEN:{seq}')
            data = json.loads(body)
            if data['kind'] == 'HTTP':
                path = self.folder / 'raw' / (data['data']['sha256'] + '.json')
                if not path.is_file() or sha(path.read_bytes()) != data['data']['sha256']:
                    raise ValueError(f'RAW_RECEIPT_BROKEN:{seq}')
            previous = digest
        return previous

    def first_seen(self, ident):
        return self.db.execute('SELECT 1 FROM seen WHERE id=?', (ident,)).fetchone() is None

    def close(self): self.db.close()

class PublicTransport(ReliableHTTP):
    """Reuse existing retry/circuit code; hard restrict public URLs and archive bytes."""
    def __init__(self, store):
        super().__init__(connect_timeout=4, read_timeout=5, max_retries=0, response_observer=self.witness)
        self.store = store
        self.last = {}

    def get_json(self, bases, path, params=None, cache_ttl=0):
        allowed = {'/api/v1/contract/detail'}
        for symbol in ('SOL_USDT', 'BNB_USDT'):
            allowed.update(f'/api/v1/contract/{part}/{symbol}' for part in ('depth', 'funding_rate', 'index_price', 'fair_price'))
        okx = {'/api/v5/public/funding-rate', '/api/v5/public/instruments', '/api/v5/market/books'}
        if len(bases) != 1 or not ((bases[0] == 'https://api.mexc.com' and path in allowed) or
            (bases[0] == 'https://www.okx.com' and path in okx and (params or {}).get('instId') in ('BTC-USDT-SWAP', 'BTC-USD-SWAP'))):
            raise ValueError('NON_PUBLIC_OR_UNFROZEN_ENDPOINT_REJECTED')
        return super().get_json(bases, path, params, cache_ttl=0)

    def witness(self, url, status, raw, received_ms):
        digest = sha(raw)
        path = self.store.folder / 'raw' / (digest + '.json')
        if not path.exists():
            if self.store.raw_bytes + len(raw) > 512 * 1024 * 1024:
                raise OSError('RAW_ARCHIVE_512_MIB_LIMIT_STOP_AND_EXPORT_STATE')
            with path.open('xb') as f: f.write(raw)
            self.store.raw_bytes += len(raw)
        rec = {'url': url, 'http_status': status, 'sha256': digest, 'received_ms': received_ms}
        self.store.add('HTTP', rec)
        self.last[urlparse(url).path] = rec

def quote_view(payload, receipt, contract_size):
    data = payload['data']
    if payload.get('success') is not True: raise ValueError('DEPTH_SOURCE_REJECTED')
    ts = data.get('timestamp')
    if type(ts) is not int or not 0 <= receipt['received_ms'] - ts <= 2000: raise ValueError('STALE_OR_FUTURE_BOOK')
    bids, asks = data['bids'], data['asks']
    if not bids or not asks: raise ValueError('EMPTY_BOOK')
    for levels, reverse in ((bids, True), (asks, False)):
        prices = [number(x[0]) for x in levels]
        if prices != sorted(prices, reverse=reverse) or len(set(prices)) != len(prices): raise ValueError('UNSORTED_BOOK')
        if any(number(x[0]) <= 0 or number(x[1]) <= 0 for x in levels): raise ValueError('INVALID_DEPTH')
    bid, ask = number(bids[0][0]), number(asks[0][0])
    if ask <= bid: raise ValueError('CROSSED_OR_LOCKED_BOOK')
    size = number(contract_size)
    if size <= 0: raise ValueError('CONTRACT_SIZE_UNKNOWN')
    quantity = number(PROTOCOL['notional_usdt']) / ask
    def walk(levels):
        remaining, value = quantity, Decimal(0)
        for price, contracts, *_ in levels:
            take = min(remaining, number(contracts) * size)
            value += take * number(price)
            remaining -= take
            if remaining == 0: break
        if remaining > 0: raise ValueError('INSUFFICIENT_VISIBLE_DEPTH')
        return value / quantity
    buy, sell = walk(asks), walk(bids)
    return {'bid': str(bid), 'ask': str(ask), 'market_timestamp_ms': ts,
            'locally_received_ms': receipt['received_ms'], 'raw_response_sha256': receipt['sha256'],
            'visible_contract_qty': str(min(number(bids[0][1]), number(asks[0][1]))),
            'contract_size': str(size), 'quantity_base_scenario': str(quantity),
            'buy_ask_vwap_scenario': str(buy), 'sell_bid_vwap_scenario': str(sell),
            'static_crossing_loss_usdt': str((buy-sell)*quantity),
            'execution_status': 'PUBLIC_QUOTE_NOT_A_FILL', 'risk_initial_stop_4pct_usdt_scenario': '4',
            'fees_usdt': None, 'funding_realised_usdt': None, 'net_usdt': None, 'net_eur': None}

def collect_mexc(store, transport):
    client = MEXCClient(timeout=5, futures_base='https://api.mexc.com')
    client.transport = transport
    output = {}
    try:
        details = {r['symbol']: r for r in client.futures_detail()}
    except Exception as exc:
        return {'SOURCE': {'status': 'FAILED', 'reason': str(exc)}}
    for symbol in ('SOL_USDT', 'BNB_USDT'):
        row = {'status': 'FAILED', 'venue': 'MEXC_FUTURES_PUBLIC', 'symbol': symbol}
        try:
            detail = details[symbol]
            path = '/api/v1/contract/depth/' + symbol
            raw = client._get(client.futures_base, path)
            row.update(quote_view(raw, transport.last[path], detail['contractSize']))
            row['public_fee_fields_not_account_certified'] = {k: detail.get(k) for k in ('makerFeeRate', 'takerFeeRate', 'minVol', 'volUnit', 'priceUnit')}
            row['funding_prediction_not_cashflow'] = client.futures_funding(symbol)
            row['price_context'] = client.futures_price_context(symbol)
            row['status'] = 'PUBLIC_DATA_OK_COSTS_UNVERIFIED'
            row['reason'] = 'NO_GO: taxas da conta, slippage, sinal certificado e stop nativo por validar'
        except Exception as exc: row['reason'] = str(exc)
        output[symbol] = row
    return output

def collect_okx(transport):
    output = {}
    for instrument in ('BTC-USDT-SWAP', 'BTC-USD-SWAP'):
        row = {'status': 'FAILED', 'instrument': instrument}
        for key, path, params in (
            ('funding_prediction_not_cashflow', '/api/v5/public/funding-rate', {'instId': instrument}),
            ('contract', '/api/v5/public/instruments', {'instType': 'SWAP', 'instId': instrument}),
            ('book', '/api/v5/market/books', {'instId': instrument, 'sz': '20'})):
            try:
                data = transport.get_json(['https://www.okx.com'], path, params)
                if data.get('code') != '0' or not data.get('data'): raise ValueError('OKX_SOURCE_REJECTED')
                row[key] = data['data']
                if key == 'funding_prediction_not_cashflow': row['funding_receipt'] = transport.last[path]
            except Exception as exc:
                row['reason'] = str(exc)
                break
        else:
            row['status'] = 'SOURCE_ONLY_NO_SETTLED_CASHFLOW_PROOF'
            row['reason'] = 'V04: não extrapolar taxa prevista; faltam pares de settlements futuros testemunhados e FX/marks'
        output[instrument] = row
    return output

def funding_decisions(store, okx, current_ms):
    """Only settlements after installation; no historical requests or backfill."""
    utc = datetime.fromtimestamp(current_ms/1000, timezone.utc)
    due = utc.replace(hour=0, minute=5, second=0, microsecond=0)
    due_ms = int(due.timestamp()*1000)
    settled = {}
    for instrument, row in okx.items():
        try:
            funding = row['funding_prediction_not_cashflow'][0]
            t, ts = int(funding['prevFundingTime']), int(funding['ts'])
            interval = int(funding['fundingTime']) - t
            if funding['settState'] != 'settled' or not store.freeze['started_ms'] < t <= ts <= current_ms: continue
            if interval != 28800000 or current_ms-ts > 90000: continue
            rate = number(funding['settFundingRate'])
            if store.first_seen(f'SETTLED:{instrument}:{t}'):
                store.add('SETTLEMENT', {'instrument': instrument, 'funding_time_ms': t,
                    'rate': str(rate), 'interval_ms': interval, 'status': 'PUBLIC_SETTLED_RATE_NOT_ACCOUNT_CASHFLOW',
                    'raw_response_sha256': row['funding_receipt']['sha256']}, f'SETTLED:{instrument}:{t}')
        except (KeyError, IndexError, ValueError, InvalidOperation): continue
    for body, in store.db.execute('SELECT body FROM receipts ORDER BY seq'):
        event = json.loads(body)
        if event['kind'] == 'SETTLEMENT':
            data = event['data']
            if data['funding_time_ms'] < due_ms and event['received_ms'] <= due_ms:
                settled[data['instrument']] = data
    result = {'status': 'WAITING_FOR_FROZEN_0005_UTC', 'future_settlements_witnessed': len(settled), 'net_usdt': None, 'net_eur': None}
    if not 0 <= current_ms-due_ms <= 120000: return result
    ident = 'V04_DECISION:' + due.strftime('%Y-%m-%d')
    if not store.first_seen(ident): return {'status': 'DAILY_DECISION_ALREADY_RECORDED'}
    result['decision_time_ms'] = due_ms
    result['status'] = 'NO_GO_SETTLEMENT_PAIR_MISSING'
    if len(settled) == 2:
        linear, inverse = settled['BTC-USDT-SWAP'], settled['BTC-USD-SWAP']
        if linear['funding_time_ms'] == inverse['funding_time_ms'] and 0 < due_ms-linear['funding_time_ms'] <= 28800000:
            spread = (number(linear['rate'])-number(inverse['rate'])) * 10000 / 8
            result['lagged_spread_bps_per_hour'] = str(spread)
            result['signal'] = ('SHORT_LINEAR_LONG_INVERSE' if spread > 0 else 'SHORT_INVERSE_LONG_LINEAR') if abs(spread) >= Decimal('0.5') else 'FLAT'
            result['status'] = 'NO_TRADE_UNDER_FROZEN_RULE' if result['signal'] == 'FLAT' else 'SIGNAL_ONLY_NO_GO_COSTS_FX_EXITS_UNVERIFIED'
    store.add('FUNDING_DECISION', result, ident)
    return result

def observe_signals(store, localappdata, books):
    inventory = read_one(Path(localappdata), 'V07', 100)
    fresh = []
    for event in inventory.get('events', []):
        if event['lane'] not in LANES: continue
        close_ms = int(event['signal_id'].rsplit(':', 1)[1])
        if not store.freeze['started_ms'] <= close_ms <= now_ms(): continue
        if not store.first_seen(event['signal_id']): continue
        symbol, tf = LANES[event['lane']]
        witness = now_ms()
        # Existing outbox carries no raw-bar/proof hashes. Never invent them.
        signal = {'symbol': symbol.replace('_', ''), 'side': 'LONG', 'timeframe_ms': tf,
                  'bar_open_ms': close_ms-tf, 'witness_ms': witness}
        q = books.get(symbol, {})
        gate_quote = dict(q)
        for field in ('bid', 'ask', 'visible_contract_qty'):
            if field in gate_quote: gate_quote[field] = float(gate_quote[field])
        status = validate_quote_after_signal(signal, gate_quote)
        rec = {'signal_id': event['signal_id'], 'lane': event['lane'], 'signal_close_ms': close_ms,
               'observed_ms': witness, 'proof_gate': status, 'quote': q,
               'status': 'NO_GO_SIGNAL_PROOF_MISSING', 'net_usdt': None,
               'reason': 'Alerta real do outbox; sem prova bruta contemporânea do sinal. Zero crédito de edge.'}
        store.add('SIGNAL', rec, event['signal_id'])
        fresh.append(rec)
    return {'source_status': inventory['status'], 'new_alerts': fresh,
            'scope': 'Apenas V07 SOL1h / BNB4h; estratégias e observadores existentes intactos'}

def dashboard(store, latest):
    day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    records = [json.loads(row[0]) for row in store.db.execute('SELECT body FROM receipts ORDER BY seq')]
    today = [r for r in records if datetime.fromtimestamp(r['received_ms']/1000, timezone.utc).strftime('%Y-%m-%d') == day]
    signals = [r['data'] for r in today if r['kind'] == 'SIGNAL']
    failures = [r['data'] for r in today if r['kind'] == 'FAILURE']
    summary = {'day_utc': day, 'economic_verdict': 'NO_GO_EDGE_UNPROVEN', 'verified_net_opportunities': 0,
               'verified_net_usdt': None, 'verified_net_eur': None, 'realised_trading_pnl': None,
               'observed_alerts': len(signals), 'failures': len(failures), 'latest': latest,
               'signal_receipts': signals, 'failure_receipts': failures,
               'chain_head': store.verify(), 'freeze_sha256': store.freeze_digest}
    (store.folder / f'{day}.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    rows = []
    for symbol, row in latest.get('mexc', {}).items():
        rows.append('<tr>' + ''.join('<td>'+html.escape(str(v))+'</td>' for v in (symbol, row.get('bid', '—'), row.get('ask', '—'), row.get('static_crossing_loss_usdt', '—'), row.get('reason', '—'))) + '</tr>')
    page = '''<!doctype html><html lang="pt"><meta charset="utf-8"><meta http-equiv="refresh" content="30"><title>Crypto Lab — Shadow</title>
    <style>body{font:17px system-ui;background:#101820;color:#e5eef4;max-width:1100px;margin:40px auto;padding:20px}h1{color:#ffbf69}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid #456}pre{white-space:pre-wrap;overflow-wrap:anywhere}section{background:#192733;padding:20px;margin:20px 0}small{color:#b7c6d0}</style>
    <h1>NO-GO · vantagem líquida por provar</h1><p id="age"></p><p>Paper/shadow · sem ordens · dia UTC ''' + day + '''</p>
    <section><b>Oportunidades líquidas verificadas: 0</b><p>Líquido USDT: não apurado · EUR: não apurado · Lucro realizado: não existe neste operador.</p>
    <p>Não negociar: custos da conta e slippage não certificados, prova dos sinais incompleta, risco de gaps e stop nativo por validar.</p></section>
    <h2>Cotações públicas observadas</h2><table><tr><th>Instrumento</th><th>BID</th><th>ASK</th><th>Custo estático de cruzar o livro / 100 USDT</th><th>Decisão</th></tr>''' + ''.join(rows) + '''</table>
    <small>Cenário simultâneo de profundidade, sem preencher ordens. Não inclui taxas, funding futuro ou saída. Valores não constituem lucro ou preço garantido. Risco inicial de 4%: cenário de 4 USDT por 100 USDT, não perda máxima; gaps podem excedê-lo.</small>
    <h2>Funding Hunter V04</h2><p>Regra original preservada: 00:05 UTC, |spread de funding realizado anterior| ≥ 0,5 bps/h; 24h. Sem settlement certificado: nenhuma oportunidade verificada.</p>
    <h2>Recibos, falhas e cobertura</h2><pre>''' + html.escape(json.dumps(summary, indent=2, ensure_ascii=False)) + '''</pre>
    <p>Esta cadeia local deteta alterações sem recomputação; não é assinatura independente. Copiar diariamente JSON, base SQLite fechada e pasta raw para custódia separada.</p><script>
    const stamp=''' + str(latest.get('finished_ms', 0)) + ''';function age(){const s=Math.max(0,Math.floor((Date.now()-stamp)/1000));document.getElementById('age').textContent=(s>90?'RECOLHA PARADA OU ATRASADA · ':'Última recolha · ')+s+' segundos';}age();setInterval(age,1000);
    </script></html>'''
    tmp = store.folder / 'painel.tmp'
    tmp.write_text(page, encoding='utf-8')
    tmp.replace(store.folder / 'painel.html')
    return summary

def cycle(store, localappdata):
    transport = PublicTransport(store)
    previous = store.db.execute("SELECT body FROM receipts ORDER BY seq DESC LIMIT 1").fetchone()
    if previous and now_ms()-json.loads(previous[0])['received_ms'] > 90000:
        store.add('FAILURE', {'reason': 'POLL_GAP_OR_RESTART', 'gap_ms': now_ms()-json.loads(previous[0])['received_ms']})
    started = now_ms()
    books = collect_mexc(store, transport)
    okx = collect_okx(transport)
    signals = observe_signals(store, localappdata, books)
    funding = funding_decisions(store, okx, now_ms())
    latest = {'started_ms': started, 'finished_ms': now_ms(), 'mexc': books, 'okx': okx, 'signals': signals, 'funding_decision': funding}
    for venue, rows in (('MEXC', books), ('OKX', okx)):
        for symbol, row in rows.items():
            if row['status'] == 'FAILED': store.add('FAILURE', {'venue': venue, 'symbol': symbol, 'reason': row['reason']})
    if signals['source_status'] != 'READONLY_QUERY_OK': store.add('FAILURE', {'reason': signals['source_status'], 'source': 'V07_OUTBOX'})
    if latest['finished_ms']-started > 90000: store.add('FAILURE', {'reason': 'POLL_CYCLE_TOO_SLOW'})
    store.add('SNAPSHOT', latest)
    return dashboard(store, latest)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=Path('shadow-state'))
    parser.add_argument('--localappdata', type=Path, default=Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))))
    parser.add_argument('--once', action='store_true', help='Real public smoke; failures remain visible')
    parser.add_argument('--verify', action='store_true', help='Offline chain/raw verification; zero network')
    args = parser.parse_args(argv)
    args.state.mkdir(parents=True, exist_ok=True)
    lock = (args.state / 'operator.lock').open('a+b')
    lock.write(b'0'); lock.flush(); lock.seek(0)
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        raise SystemExit('OPERATOR_ALREADY_RUNNING_FOR_THIS_STATE')
    store = Store(args.state)
    try:
        if args.verify:
            print(canonical({'status': 'INTEGRITY_OK_NOT_PROFIT', 'chain_head': store.verify()}))
            return 0
        while True:
            summary = cycle(store, args.localappdata)
            print(canonical({'day': summary['day_utc'], 'verdict': summary['economic_verdict'], 'alerts': summary['observed_alerts'], 'failures': summary['failures'], 'panel': str((store.folder / 'painel.html').resolve())}), flush=True)
            if args.once: return 0 if any(r.get('status') == 'PUBLIC_DATA_OK_COSTS_UNVERIFIED' for r in summary['latest']['mexc'].values()) else 2
            time.sleep(30)
    except KeyboardInterrupt: return 0
    finally:
        store.close()
        lock.close()

if __name__ == '__main__': raise SystemExit(main())
