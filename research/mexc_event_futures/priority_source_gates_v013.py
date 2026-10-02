#!/usr/bin/env python3
"""Public source-only probes. No MEXC, accounts, outcomes or credentials."""
import argparse
import asyncio
import concurrent.futures
import hashlib
import json
import math
import pathlib
import time
import urllib.parse
import urllib.request

BASE = 'https://www.deribit.com/api/v2/public/'
ALLOWED = {'get_instruments', 'get_book_summary_by_currency', 'ticker'}

def now_ms():
    return time.time_ns() // 1_000_000

def positive(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x > 0

def fresh(ts, recv):
    return isinstance(ts, int) and not isinstance(ts, bool) and -1000 <= recv-ts <= 5000

class Evidence:
    def __init__(self, root):
        self.root = pathlib.Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.entries = []

    def save(self, name, body, **meta):
        raw = body if isinstance(body, bytes) else body.encode()
        sha = hashlib.sha256(raw).hexdigest()
        (self.root / name).write_bytes(raw)
        row = {'path': name, 'sha256': sha, 'bytes': len(raw), **meta}
        self.entries.append(row)
        return row

    def finish(self, receipt):
        receipt.update(research_outcomes_opened=0, active_families=0,
                       safety={'NO_AUTH': True, 'NO_PRIVATE': True, 'NO_ORDERS': True,
                               'NO_ACCOUNT_READS': True, 'NO_MEXC_OUTCOMES': True})
        receipt['evidence'] = sorted(self.entries, key=lambda r:r['path'])
        (self.root/'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
        print(json.dumps({k:v for k,v in receipt.items() if k != 'evidence'}, indent=2), flush=True)

def get(method, params, evidence, name):
    if method not in ALLOWED:
        raise ValueError('not a public allowlisted method')
    url = BASE+method+'?'+urllib.parse.urlencode(params)
    sent = now_ms()
    # No cookie handler, auth header or private session. GET, never POST.
    req = urllib.request.Request(url, headers={'Accept':'application/json'}, method='GET')
    with urllib.request.urlopen(req, timeout=20) as response:
        if response.geturl().split('?')[0] != BASE+method:
            raise ValueError('unexpected redirect')
        raw = response.read()
        recv = now_ms()
        ref = evidence.save(name, raw, source_url=url, received_at_ms=recv,
                            requested_at_ms=sent, http_status=response.status)
    obj = json.loads(raw)
    if 'error' in obj or 'result' not in obj:
        raise ValueError('JSON-RPC error or missing result')
    return obj['result'], recv, ref

def valid_ticker(t, meta, recv):
    try:
        if t['instrument_name'] != meta['instrument_name'] or t['state'] != 'open':
            return False
        if not fresh(t['timestamp'], recv):
            return False
        for k in ('mark_iv','bid_iv','ask_iv','index_price','underlying_price',
                  'best_bid_price','best_ask_price','best_bid_amount','best_ask_amount'):
            if not positive(t[k]):
                return False
        if t['best_ask_price'] < t['best_bid_price'] or t['ask_iv'] < t['bid_iv']:
            return False
        d = t['greeks']['delta']
        return (positive(d) and .15 <= d <= .35) if meta['option_type']=='call' else (
            isinstance(d,(int,float)) and math.isfinite(d) and -.35 <= d <= -.15)
    except (KeyError, TypeError):
        return False

def options_probe(evidence):
    rounds = []
    errors = []
    for round_id in range(3):
        accepted = {}
        for currency in ('BTC','ETH'):
            try:
                instruments, recv, meta_ref = get('get_instruments',
                    {'currency':currency,'kind':'option','expired':'false'}, evidence,
                    f'options-{round_id}-{currency}-instruments.json')
                eligible = [m for m in instruments if m.get('is_active') is True
                            and m.get('kind')=='option' and m.get('base_currency')==currency
                            and 7*86400000 <= m['expiration_timestamp']-recv <= 30*86400000]
                expiry = min(m['expiration_timestamp'] for m in eligible)
                eligible = [m for m in eligible if m['expiration_timestamp']==expiry]
                summary, _, sum_ref = get('get_book_summary_by_currency',
                    {'currency':currency,'kind':'option'}, evidence,
                    f'options-{round_id}-{currency}-summary.json')
                summaries = {r['instrument_name']:r for r in summary}
                choices = []
                for side in ('call','put'):
                    scored = []
                    for m in eligible:
                        if m['option_type'] != side:
                            continue
                        s = summaries.get(m['instrument_name'],{})
                        f = s.get('underlying_price'); iv = s.get('mark_iv')
                        if not positive(f) or not positive(iv):
                            continue
                        if (side=='call' and m['strike']<=f) or (side=='put' and m['strike']>=f):
                            continue
                        vol = iv/100; tau = (expiry-recv)/(365.25*86400000)
                        d1 = (math.log(f/m['strike']) + .5*vol*vol*tau)/(vol*math.sqrt(tau))
                        delta = .5*(1+math.erf(d1/math.sqrt(2))) - (side=='put')
                        scored.append((abs(abs(delta)-.25),m['instrument_name'],m))
                    choices.extend(x[2] for x in sorted(scored)[:2])
                candidates = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    futures = {pool.submit(get,'ticker',{'instrument_name':m['instrument_name']},
                                evidence,f'options-{round_id}-{m["instrument_name"]}-ticker.json'):m
                               for m in choices}
                    for fut,m in futures.items():
                        t, received, ref = fut.result()
                        candidates.append({'instrument':m['instrument_name'],'option_type':m['option_type'],
                            'valid':valid_ticker(t,m,received),'ticker':t,'received_at_ms':received,
                            'raw_sha256':ref['sha256'],'metadata_sha256':meta_ref['sha256'],
                            'selection_summary_sha256':sum_ref['sha256']})
                pair = []
                for side in ('call','put'):
                    valid = [r for r in candidates if r['valid'] and r['option_type']==side]
                    if valid:
                        pair.append(min(valid,key=lambda r:(abs(abs(r['ticker']['greeks']['delta'])-.25),r['instrument'])))
                ok = len(pair)==2 and abs(pair[0]['ticker']['timestamp']-pair[1]['ticker']['timestamp'])<=5000
                accepted[currency] = {'passed':ok,'expiry_ms':expiry,'candidates':candidates,
                                      'selected_pair':pair if ok else []}
            except Exception as exc:
                errors.append({'round':round_id,'currency':currency,'type':type(exc).__name__,'error':str(exc)})
                accepted[currency] = {'passed':False}
        rounds.append(accepted)
        if round_id < 2:
            time.sleep(10)
    counts = {c:sum(r[c]['passed'] for r in rounds) for c in ('BTC','ETH')}
    verdict = 'SOURCE_GATE_PASS' if all(n==3 for n in counts.values()) else (
        'PARTIAL_SOURCE' if any(counts.values()) else 'SOURCE_BLOCKED')
    evidence.finish({'family_id':'OPTIONS-VOL-FWD-001','verdict':verdict,
                     'valid_pairs_by_currency':counts,'rounds':rounds,'errors':errors})

def valid_liquidation(item, envelope, recv):
    try:
        return (envelope['topic']=='allLiquidation.'+item['s']
                and item['s'] in ('BTCUSDT','ETHUSDT') and item['S'] in ('Buy','Sell')
                and fresh(item['T'],recv) and isinstance(envelope['ts'],int)
                and fresh(envelope['ts'],recv) and item['T']-envelope['ts']<=1000
                and positive(float(item['v'])) and positive(float(item['p'])))
    except (KeyError,TypeError,ValueError):
        return False

async def liquidation_probe(evidence, seconds):
    import websockets
    counts = {'BTCUSDT':0,'ETHUSDT':0}
    records = []; errors = []; ack = False; seq = 0
    started = now_ms()
    try:
        async with websockets.connect('wss://stream.bybit.com/v5/public/linear',open_timeout=20) as ws:
            await ws.send(json.dumps({'op':'subscribe','args':['allLiquidation.BTCUSDT','allLiquidation.ETHUSDT']}))
            deadline = time.monotonic()+seconds
            last_ping = time.monotonic()
            while time.monotonic() < deadline:
                if time.monotonic()-last_ping >= 20:
                    await ws.send('{"op":"ping"}'); last_ping=time.monotonic()
                try:
                    raw = await asyncio.wait_for(ws.recv(),min(5,max(.001,deadline-time.monotonic())))
                except asyncio.TimeoutError:
                    continue
                received = now_ms(); seq += 1
                ref = evidence.save(f'liquidations-{seq:08d}.json',raw,received_at_ms=received,
                                     source_url='wss://stream.bybit.com/v5/public/linear')
                j = json.loads(raw)
                if j.get('op')=='subscribe':
                    ack = j.get('success') is True
                if j.get('topic') in ('allLiquidation.BTCUSDT','allLiquidation.ETHUSDT'):
                    for ordinal,item in enumerate(j.get('data',[])):
                        valid = valid_liquidation(item,j,received)
                        if valid:
                            counts[item['s']] += 1
                        records.append({'raw_sha256':ref['sha256'],'ordinal':ordinal,'valid':valid,
                                        'received_at_ms':received,'envelope_ts':j.get('ts'),'item':item})
    except Exception as exc:
        errors.append({'type':type(exc).__name__,'error':str(exc)})
    if errors or not ack:
        verdict = 'SOURCE_BLOCKED'
    elif all(counts.values()):
        verdict = 'SOURCE_GATE_PASS'
    elif any(counts.values()):
        verdict = 'PARTIAL_SOURCE'
    else:
        verdict = 'NO_EVENTS_OBSERVED'
    evidence.finish({'family_id':'LIQUIDATION-FLOW-FWD-001','verdict':verdict,
                     'subscription_ack':ack,'valid_events_by_symbol':counts,'events':records,
                     'started_at_ms':started,'finished_at_ms':now_ms(),'errors':errors})

def self_test():
    m={'instrument_name':'TEST','option_type':'call'}
    t={'instrument_name':'TEST','state':'open','timestamp':100000,'greeks':{'delta':.25},
       **{k:1. for k in ('mark_iv','bid_iv','ask_iv','index_price','underlying_price',
                         'best_bid_price','best_ask_price','best_bid_amount','best_ask_amount')}}
    assert valid_ticker(t,m,100001)
    assert not valid_ticker({**t,'mark_iv':float('nan')},m,100001)
    assert not valid_ticker({**t,'mark_iv':0},m,100001)
    assert not valid_ticker(t,m,106000)
    assert not valid_ticker(t,m,98000)
    assert not valid_ticker({**t,'greeks':{'delta':-.25}},m,100001)
    i={'s':'BTCUSDT','S':'Buy','T':100000,'v':'2','p':'100'}
    e={'topic':'allLiquidation.BTCUSDT','ts':100001}
    assert valid_liquidation(i,e,100002)
    assert not valid_liquidation({**i,'v':'NaN'},e,100002)
    assert not valid_liquidation(i,{**e,'topic':'allLiquidation.ETHUSDT'},100002)
    assert not valid_liquidation(i,e,106000)
    print('SOURCE_VALIDATOR_SELFTEST_PASS; SYNTHETIC_ONLY; RESEARCH_OUTCOMES_OPENED=0')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--family',choices=['options','liquidation'])
    ap.add_argument('--output',default='v013-source-evidence')
    ap.add_argument('--seconds',type=int,default=600)
    ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    if a.self_test:
        self_test()
    elif a.family=='options':
        options_probe(Evidence(a.output))
    elif a.family=='liquidation':
        asyncio.run(liquidation_probe(Evidence(a.output),a.seconds))
    else:
        ap.error('--family or --self-test required')
