"""Public MEXC Radar component. Durable receipts are authoritative; Telegram only reports."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import requests
from .mexc_universe_trade_scanner import scan

VERSION = 'MEXC_UNIVERSE_V01'

def utc():
    return datetime.now(timezone.utc).isoformat()

def signal_id(candidate):
    identity = [VERSION, candidate['symbol'], candidate['side'], candidate['signal_family'],
                int(candidate['signal_candle_open'])]
    return hashlib.sha256(json.dumps(identity, separators=(',', ':')).encode()).hexdigest()

def write_json(path, value, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')

def load_ledger(root):
    path = root / 'notifications.json'
    if not path.exists():
        # Existing receipt history without its ledger is unsafe to notify.
        if (root / 'runs').exists() and any((root / 'runs').iterdir()):
            raise ValueError('missing notification ledger')
        return {}
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('invalid notification ledger')
    return value

def payload(candidate):
    c = dict(candidate)
    c['signal_id'] = signal_id(c)
    c['signal_timestamp_utc'] = datetime.fromtimestamp(c['signal_candle_open']+900, timezone.utc).isoformat()
    c['expiry_utc'] = datetime.fromtimestamp(c['expires_at_epoch'], timezone.utc).isoformat()
    c['validation_size'] = {'contracts': c['contracts'], 'notional_usdt': c['notional_usdt'],
                            'margin_usdt': c['notional_usdt']/c['leverage']}
    c['fees'] = {'taker_bps_per_fill': c['fee_roundtrip_bps']/2,
                 'roundtrip_usdt': c['notional_usdt']*c['fee_roundtrip_bps']/10000,
                 'authority': 'inherited V0.1 fee assumption; no private fee lookup'}
    c['slippage'] = 'visible book impact only; future slippage and fills unverified'
    c['net_rr_scope'] = 'inherited V0.1 fees/spread/visible impact; future funding excluded'
    return c

def format_message(c):
    return '\n'.join([
        f"TRADEABLE_CANDIDATE â€” {c['symbol']} {c['side']}",
        f"Setup: {c['signal_family']}",
        f"Entry: {c['entry']} | Stop: {c['stop']}",
        f"TP1: {c['tp1']} | TP2: {c['tp2']}",
        f"{c['leverage']}x {c['margin_mode']} | Validation: {c['contracts']} contracts / {c['notional_usdt']:.2f} USDT notional / {c['validation_size']['margin_usdt']:.2f} USDT margin",
        f"Fees assumption: {c['fee_roundtrip_bps']} bps roundtrip / {c['fees']['roundtrip_usdt']:.4f} USDT",
        f"Funding: {c['funding_rate']} / {c['funding_cycle_hours']}h",
        f"Depth impact: {c['entry_impact_bps']:.4f} bps | {c['slippage']}",
        f"Net RR TP1/TP2: {c['net_rr_tp1']:.3f}/{c['net_rr_tp2']:.3f} (future funding excluded)",
        f"Signal: {c['signal_timestamp_utc']} | Expiry: {c['expiry_utc']}",
        f"Invalidation: {c['invalidation']}",
        f"signal_id: {c['signal_id']}",
        'Read-only advisory. No order executed.'
    ])

def prepare(root, run_id, scanner=scan, environ=None):
    env = os.environ if environ is None else environ
    ledger = load_ledger(root)
    run_path = root / 'runs' / f'{run_id}.json'
    if run_path.exists():
        raise ValueError('run receipt already exists')
    result = None
    try:
        result = scanner()
        if result.get('source_health') != 'OK':
            raise ValueError('source blocked')
        candidates = [payload(c) for c in result['candidates']]
        now = time.time()
        if any(c['expires_at_epoch'] <= now or c['source_book_timestamp'] > now+5 or
               c['signal_candle_open'] != (int(now)//900)*900-900 or
               c['confirmation_candle_open'] != (int(now)//3600)*3600-3600 for c in candidates):
            raise ValueError('stale source or signal')
        result['candidates'] = candidates
        result['verdict'] = 'TRADE' if candidates else 'NO_TRADE'
        result['classification'] = 'TRADEABLE_CANDIDATE' if candidates else 'RADAR_EMPTY'
    except Exception:
        previous = result or {}
        result = {'verdict': 'NO_TRADE', 'classification': 'RADAR_EMPTY', 'source_health': 'BLOCKED',
                  'universe_eligible_count': previous.get('universe_eligible_count', 0),
                  'reject_counts': {**previous.get('reject_counts', {}), 'SOURCE_OR_STALE': 1},
                  'source_error_counts': previous.get('source_error_counts', {}), 'candidates': []}
    enabled = bool(env.get('TELEGRAM_BOT_TOKEN') and env.get('TELEGRAM_CHAT_ID'))
    pending = []
    if enabled and result['verdict'] == 'TRADE':
        for c in result['candidates']:
            sid = c['signal_id']
            if sid not in ledger:
                ledger[sid] = {'status': 'RESERVED', 'run_id': run_id, 'reserved_at_utc': utc()}
                pending.append(sid)
    result.update({'run_id': run_id, 'timestamp_utc': utc(), 'component': VERSION,
                   'notifier': 'READY' if enabled else 'DISABLED_MISSING_SECRETS', 'pending_signal_ids': pending,
                   'code_sha': env.get('RADAR_CODE_SHA', 'local'), 'orders_created': False,
                   'account_reads': False, 'exchange_mutation': False})
    write_json(run_path, result, exclusive=True)
    write_json(root / 'notifications.json', ledger)
    write_json(root / 'status.json', result)
    return result

def notify(root, run_id, environ=None, post=requests.post):
    env = os.environ if environ is None else environ
    receipt = json.loads((root / 'runs' / f'{run_id}.json').read_text(encoding='utf-8'))
    ledger = load_ledger(root)
    event_path = root / 'events' / f'{run_id}.json'
    if event_path.exists():
        return json.loads(event_path.read_text(encoding='utf-8'))
    token, chat = env.get('TELEGRAM_BOT_TOKEN'), env.get('TELEGRAM_CHAT_ID')
    results = {}
    for c in receipt['candidates'] if receipt['verdict'] == 'TRADE' else []:
        sid = c['signal_id']
        reservation = ledger.get(sid, {})
        if sid not in receipt['pending_signal_ids'] or reservation.get('run_id') != run_id or reservation.get('status') != 'RESERVED':
            continue
        if not token or not chat:
            status = 'DISABLED_MISSING_SECRETS'
        elif time.time() >= c['expires_at_epoch']:
            status = 'EXPIRED'
        else:
            # Persist locally before POST; the workflow has already committed RESERVED remotely.
            # An interrupted/ambiguous POST is not retried, preferring no duplicate over guaranteed delivery.
            ledger[sid]['status'] = 'ATTEMPTED'
            write_json(root / 'notifications.json', ledger)
            try:
                response = post(f'https://api.telegram.org/bot{token}/sendMessage',
                                json={'chat_id': chat, 'text': format_message(c), 'disable_web_page_preview': True},
                                timeout=10, allow_redirects=False)
                status = 'SENT' if response.status_code == 200 and response.json().get('ok') is True else 'FAILED_NO_RETRY'
            except Exception:
                status = 'UNKNOWN_NO_RETRY'
        ledger[sid].update({'status': status, 'finished_at_utc': utc()})
        results[sid] = status
    event = {'run_id': run_id, 'timestamp_utc': utc(), 'notifier':
             'READY' if token and chat else 'DISABLED_MISSING_SECRETS', 'results': results}
    write_json(root / 'notifications.json', ledger)
    write_json(event_path, event, exclusive=True)
    return event

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('scan', 'notify', 'status'))
    parser.add_argument('--state-dir', default='runtime/mexc_universe')
    parser.add_argument('--run-id', default=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    args = parser.parse_args(argv)
    root = Path(args.state_dir)
    if args.phase == 'status':
        value = json.loads((root / 'status.json').read_text(encoding='utf-8'))
        if any(c['expires_at_epoch'] <= time.time() for c in value['candidates']):
            value.update(verdict='NO_TRADE', classification='RADAR_EMPTY', candidates=[], source_health='STALE')
    elif args.phase == 'scan':
        value = prepare(root, args.run_id)
    else:
        value = notify(root, args.run_id)
    print(json.dumps({'run_id': value.get('run_id'), 'state': value.get('classification'),
                      'source_health': value.get('source_health'), 'notifier': value.get('notifier')}, sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
