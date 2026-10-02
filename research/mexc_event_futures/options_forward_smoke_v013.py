#!/usr/bin/env python3
"""First bounded V0.13 shadow smoke, under immutable activation freeze."""
import argparse
import asyncio
import hashlib
import json
import math
import os
import pathlib
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from priority_source_gates_v013 import Evidence, now_ms, positive, fresh
from options_pair_source_v013 import options_round
from shadow_event_evaluator_v013 import resolve, break_even, validate_event

ROOT=pathlib.Path(__file__).parent
RULE=json.loads((ROOT/'OPTIONS_VOL_RULE_V013_V01.json').read_text())
RULE_HASH=hashlib.sha256(json.dumps(RULE,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert RULE_HASH==(ROOT/'OPTIONS_VOL_RULE_V013_V01.sha256').read_text().strip()
REGISTRY=json.loads((ROOT/'V013_FAMILY_REGISTRY_V0.2.json').read_text())
FAMILY=next(f for f in REGISTRY['families'] if f['family_id']==RULE['family_id'])
assert FAMILY['status']=='ACTIVE' and FAMILY['family_version']==RULE['family_version']
assert FAMILY['rule_hash']==RULE_HASH and FAMILY['min_n']==RULE['min_n']
DETAIL='/api/platform/futures/api/v1/event_contract/detail'
ENTRY='https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT'

class ShadowEvidence(Evidence):
    def finish(self,receipt):
        receipt['research_outcomes_opened']=receipt['outcomes_opened']
        receipt['active_families']=1 if receipt['preflight_pass'] else 0
        receipt['safety']={'NO_AUTH':True,'NO_PRIVATE':True,'NO_ORDERS':True,'NO_ACCOUNT_READS':True}
        receipt['evidence']=sorted(self.entries,key=lambda r:r['path'])
        (self.root/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
        print(json.dumps({k:v for k,v in receipt.items() if k!='evidence'},indent=2),flush=True)

def utc(ts):
    return datetime.fromtimestamp(ts/1000,timezone.utc).isoformat().replace('+00:00','Z')

def journal(evidence, name, row):
    with (evidence.root/name).open('a',encoding='utf-8') as f:
        f.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
        f.flush();os.fsync(f.fileno())

def condition(currency, pair, boundary):
    if not pair.get('passed'):
        return None
    byside={r['option_type']:r for r in pair['selected_pair']}
    c=byside['call'];p=byside['put']
    source_ts=max(c['ticker']['timestamp'],p['ticker']['timestamp'])
    if min(c['ticker']['timestamp'],p['ticker']['timestamp'])<=boundary:
        return None
    skew=p['ticker']['mark_iv']-c['ticker']['mark_iv']
    if abs(skew)<RULE['skew_threshold_pp']:
        return None
    symbol=currency+'_USDT'
    direction='DOWN' if skew>=RULE['skew_threshold_pp'] else 'UP'
    payload={'call':c,'put':p,'skew_pp':skew,'expiry_ms':pair['expiry_ms']}
    payload_hash=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    identity='|'.join([RULE['family_version'],symbol,c['raw_sha256'],p['raw_sha256'],RULE_HASH])
    return {'family_id':RULE['family_id'],'family_version':RULE['family_version'],
        'signal_id':hashlib.sha256(identity.encode()).hexdigest(),
        'signal_source':'DERIBIT_PUBLIC_MATCHED_OPTIONS_TICKER',
        'signal_source_ts_ms':source_ts,'signal_received_at_ms':max(c['received_at_ms'],p['received_at_ms']),
        'signal_source_ts_utc':utc(source_ts),
        'signal_received_at_utc':utc(max(c['received_at_ms'],p['received_at_ms'])),
        'symbol':symbol,'direction':direction,'direction_policy':RULE['direction_policy'],
        'horizon_minutes':RULE['horizon_minutes'],'condition_payload_hash':payload_hash,
        'rule_hash':RULE_HASH,'payload':payload}

class IndexStream:
    def __init__(self,evidence):
        self.evidence=evidence;self.ticks={s:[] for s in RULE['symbols']}
        self.error=None;self.seq=0

    async def run(self):
        import websockets
        try:
            async with websockets.connect('wss://futures.mexc.com/edge',origin='https://www.mexc.com',
                    open_timeout=20,ping_interval=15,ping_timeout=10,max_size=4*1024*1024) as ws:
                for symbol in RULE['symbols']:
                    await ws.send(json.dumps({'method':'sub.index.price','param':{'symbol':symbol}}))
                while True:
                    raw=await ws.recv();received=now_ms();self.seq+=1
                    ref=self.evidence.save(f'index-{self.seq:08d}.json',raw,
                        received_at_ms=received,source_url='wss://futures.mexc.com/edge')
                    j=json.loads(raw)
                    if j.get('channel')!='push.index.price':
                        continue
                    data=j.get('data') or {};symbol=j.get('symbol') or data.get('symbol')
                    price=float(data.get('price',0));ts=j.get('ts')
                    if symbol not in self.ticks or not positive(price) or not fresh(ts,received):
                        journal(self.evidence,'index_rejections.jsonl',{'raw_sha256':ref['sha256'],'reason':'INVALID_OR_STALE_INDEX'})
                        continue
                    ticks=self.ticks[symbol]
                    if ticks and ts<ticks[-1]['ts']:
                        journal(self.evidence,'index_rejections.jsonl',{'raw_sha256':ref['sha256'],'reason':'OUT_OF_ORDER_INDEX'})
                        continue
                    ticks.append({'ts':ts,'price':price,'received_at_ms':received,'raw_sha256':ref['sha256']})
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.error=type(exc).__name__+': '+str(exc)

    async def first(self,symbol,target,local_after,timeout):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            if self.error:
                raise ValueError('INDEX_STREAM_FAILED: '+self.error)
            for tick in self.ticks[symbol]:
                if tick['ts']>=target and tick['received_at_ms']>=local_after:
                    return tick
            await asyncio.sleep(.025)
        raise ValueError('INDEX_TICK_TIMEOUT')

class ProductCapture:
    def __init__(self,evidence):
        self.evidence=evidence;self.future=None;self.seq=0
        self.blocked_non_get=0;self.blocked_sensitive=0;self.auth_blocked=0

    async def start(self):
        from playwright.async_api import async_playwright
        self.pw=await async_playwright().start()
        self.browser=await self.pw.chromium.launch(headless=True)
        self.ctx=await self.browser.new_context(locale='en-GB',timezone_id='UTC',service_workers='block')
        await self.ctx.clear_cookies()
        async def route(r):
            req=r.request;path=urlparse(req.url).path.lower()
            if req.method!='GET':
                self.blocked_non_get+=1;await r.abort();return
            if any(term in path for term in ('/private/','/account','/balance','/wallet','/position','/order','/user/','/api_key','/apikey')):
                self.blocked_sensitive+=1;await r.abort();return
            if 'authorization' in {k.lower() for k in req.headers}:
                self.auth_blocked+=1;await r.abort();return
            await r.continue_()
        await self.ctx.route('**/*',route)
        # Do not let normal page websocket traffic create any unreviewed subscriptions.
        await self.ctx.route_web_socket('**/*',lambda ws:ws.close())
        self.page=await self.ctx.new_page()
        self.page.on('response',self.response)

    async def response(self,response):
        if urlparse(response.url).path!=DETAIL or self.future is None or self.future.done():
            return
        try:
            raw=await response.body();received=now_ms()
            if len(raw)>4*1024*1024:
                return
            j=json.loads(raw)
            if response.status!=200 or j.get('success') is not True or not isinstance(j.get('data'),list) or not j['data']:
                return
            if self.future is None or self.future.done():
                return
            self.seq+=1
            ref=self.evidence.save(f'payout-{self.seq:06d}.json',raw,
                    source_url=response.url,received_at_ms=received,http_status=response.status)
            self.future.set_result({'data':j['data'],'received_at_ms':received,'raw_sha256':ref['sha256']})
        except Exception:
            return

    async def capture(self,initial=False):
        self.future=asyncio.get_running_loop().create_future()
        if initial:
            await self.page.goto(ENTRY,wait_until='domcontentloaded',timeout=75000)
        else:
            await self.page.reload(wait_until='commit',timeout=15000)
        return await asyncio.wait_for(self.future,35 if initial else 8)

    async def close(self):
        await self.browser.close();await self.pw.stop()

def payout(snapshot,symbol,direction):
    product=next((p for p in snapshot['data'] if p.get('symbol')==symbol),None)
    if not product or product.get('state')!='ONLINE':
        raise ValueError('BLOCKED_PRODUCT_NOT_ONLINE')
    cfg=next((c for c in product.get('cycleConfigMap',{}).get('MINUTE',[]) if c.get('val')==10),None)
    if not cfg:
        raise ValueError('BLOCKED_MISSING_FROZEN_CYCLE')
    q=float(cfg['downPayRate' if direction=='DOWN' else 'upPayRate'])
    if not positive(q):
        raise ValueError('BLOCKED_INVALID_PAYOUT')
    return q

async def main(boundary,evidence):
    if (evidence.root/'session_receipt.json').exists():
        raise ValueError('INITIAL_SMOKE_ALREADY_EXISTS: continuity receipt required')
    stream=IndexStream(evidence);capture=ProductCapture(evidence)
    task=asyncio.create_task(stream.run());pending={};resolved=[];seen=set();attempts=[]
    started=now_ms();preflight=False;error=None
    async def settle(opened):
        target=opened['expiry_target_ts_ms']
        try:
            tick=await stream.first(opened['symbol'],target,0,max(0,(target-now_ms())/1000)+5)
            if tick['ts']-target>5000:
                raise ValueError('BLOCKED_MISSING_EXPIRY_INDEX')
            outcome,ret=resolve(opened['direction'],opened['decision_index'],tick['price'],opened['payout'])
            row={**opened,'expiry_ts_ms':tick['ts'],'expiry_index':tick['price'],
                'expiry_index_raw_sha256':tick['raw_sha256'],'outcome':outcome,'unit_return':ret,
                'status':'RESOLVED','source_integrity_ok':True}
            validate_event(row);journal(evidence,'resolved_events.jsonl',row);resolved.append(row)
        except Exception as exc:
            journal(evidence,'blocked_events.jsonl',{**opened,'status':'BLOCKED','reason':str(exc)})

    try:
        await capture.start()
        snap=await capture.capture(initial=True)
        for symbol in RULE['symbols']:
            tick=await stream.first(symbol,snap['received_at_ms'],snap['received_at_ms'],5)
            if not 0<=tick['received_at_ms']-snap['received_at_ms']<=5000:
                raise ValueError('PREFLIGHT_STALE_JOIN')
            # Check ONLINE exact 10min payout source only, both directions; no outcome.
            for direction in ('UP','DOWN'):
                payout(snap,symbol,direction)
        preflight=True
        journal(evidence,'runtime_preflight.jsonl',{'status':'RUNTIME_PREFLIGHT_PASS',
                'observed_at_ms':now_ms(),'payout_source_sha256':snap['raw_sha256'],'outcomes_opened':0})
        deadline=time.monotonic()+RULE['initial_accept_seconds']
        last_minute=None;round_id=0
        while time.monotonic()<deadline:
            minute=now_ms()//60000
            if minute==last_minute:
                await asyncio.sleep(.1);continue
            last_minute=minute;round_id+=1
            pairs,errors=await asyncio.to_thread(options_round,evidence,f'smoke-{round_id}')
            journal(evidence,'source_rounds.jsonl',{'minute':minute,'pairs':pairs,'errors':errors})
            for currency,pair in pairs.items():
                signal=condition(currency,pair,boundary)
                if signal is None:
                    attempts.append({'currency':currency,'minute':minute,'status':'NO_SIGNAL_OR_INVALID_SOURCE'})
                    continue
                symbol=signal['symbol']
                if signal['signal_id'] in seen:
                    attempts.append({'signal_id':signal['signal_id'],'status':'SKIPPED_DUPLICATE'});continue
                seen.add(signal['signal_id']);journal(evidence,'condition_receipts.jsonl',signal)
                if symbol in pending and not pending[symbol].done():
                    attempts.append({'signal_id':signal['signal_id'],'status':'SKIPPED_OVERLAP'});continue
                try:
                    if not fresh(signal['signal_source_ts_ms'],now_ms()):
                        raise ValueError('BLOCKED_STALE_SIGNAL')
                    snapshot=await capture.capture()
                    q=payout(snapshot,symbol,signal['direction'])
                    tick=await stream.first(symbol,snapshot['received_at_ms'],snapshot['received_at_ms'],5)
                    if tick['received_at_ms']-snapshot['received_at_ms']>5000:
                        raise ValueError('BLOCKED_STALE_DECISION_JOIN')
                    if not fresh(signal['signal_source_ts_ms'],tick['ts']):
                        raise ValueError('BLOCKED_STALE_SIGNAL_AT_DECISION')
                    opened={k:signal[k] for k in ('family_id','family_version','signal_id','symbol','direction',
                            'direction_policy','horizon_minutes','condition_payload_hash','rule_hash')}
                    opened.update(decision_ts_ms=tick['ts'],decision_index=tick['price'],payout=q,
                        break_even_probability=break_even(q),expiry_target_ts_ms=tick['ts']+600000,
                        payout_source_sha256=snapshot['raw_sha256'],decision_index_raw_sha256=tick['raw_sha256'],
                        signal_source_ts_ms=signal['signal_source_ts_ms'],signal_received_at_ms=signal['signal_received_at_ms'],
                        payout_received_at_ms=snapshot['received_at_ms'],decision_received_at_ms=tick['received_at_ms'],status='OPEN')
                    journal(evidence,'opened_events.jsonl',opened)
                    pending[symbol]=asyncio.create_task(settle(opened))
                    attempts.append({'signal_id':signal['signal_id'],'status':'OPEN'})
                except Exception as exc:
                    attempts.append({'signal_id':signal['signal_id'],'status':'BLOCKED','reason':str(exc)})
        if pending:
            await asyncio.wait_for(asyncio.gather(*pending.values()),RULE['expiry_drain_seconds'])
    except Exception as exc:
        error=type(exc).__name__+': '+str(exc)
    finally:
        task.cancel()
        await asyncio.gather(task,return_exceptions=True)
        if hasattr(capture,'browser'):
            await capture.close()
    status='INSUFFICIENT_N' if preflight else 'FROZEN_RUNTIME_BLOCKED'
    receipt={'family_id':RULE['family_id'],'family_version':RULE['family_version'],'rule_hash':RULE_HASH,
        'status':status,'preflight_pass':preflight,'started_at_ms':started,'finished_at_ms':now_ms(),
        'forward_boundary_ms':boundary,'resolved_n':len(resolved),
        'outcomes_opened':sum(r['status']=='OPEN' for r in attempts),'attempts':attempts,'error':error,
        'min_n_per_symbol':100,'statistics_run':False,'continuous_collector':False,
        'blocked_non_get_requests':capture.blocked_non_get,'blocked_sensitive_gets':capture.blocked_sensitive,
        'blocked_authenticated_requests':capture.auth_blocked}
    journal(evidence,'session_receipt.json',receipt)
    # Hash finalized ledgers as well as raw source bytes.
    for p in sorted(evidence.root.glob('*.jsonl')):
        evidence.entries.append({'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    evidence.finish(receipt)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--boundary-ms',type=int,required=True)
    ap.add_argument('--output',default='v013-options-forward-smoke');a=ap.parse_args()
    if a.boundary_ms>=now_ms():
        raise SystemExit('forward boundary must precede run')
    asyncio.run(main(a.boundary_ms,ShadowEvidence(a.output)))
