#!/usr/bin/env python3
"""Acquire protected daily USDT external flows for the frozen Binance public address basket.

FAIL-CLOSED: will not run unless SOURCE_PROVENANCE_DECISION_V0.1.md exists and contains
SOURCE_CROSSCHECK_EXACT_PASS. Source/data only. No BTC market data, returns, PnL, 2025 or 2026.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import random
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

LAB='STABLECOIN-EXCHANGE-FLOW-001'
MVE='SEF-BINANCE-PUBLIC-USDT-ETH-1D-001'
RPC='https://rpc.mevblocker.io'
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
BASKET=[
'0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']
BASKET_SET={x[2:].lower() for x in BASKET}
PADS=['0x'+'0'*24+x[2:].lower() for x in sorted(BASKET)]
START_DATE=dt.date(2022,11,11)
END_DATE=dt.date(2024,12,30)
START_TS=int(dt.datetime(2022,11,11,tzinfo=dt.timezone.utc).timestamp())
TERMINAL_TS=int(dt.datetime(2024,12,31,tzinfo=dt.timezone.utc).timestamp())
START_LO=15943000
START_HI=15943061
END_LO=21518000
END_HI=21519027
BASE_CHUNK=3200
MAX_WORKERS=4
MAX_RETRIES=7
OUT=Path('artifacts/stablecoin_exchange_flow_acquisition_v01')
DECISION=Path('labs/STABLECOIN_EXCHANGE_FLOW_001/SOURCE_PROVENANCE_DECISION_V0.1.md')
REQ_LOCK=Lock()
REQ_ID=1000

def sha256_bytes(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def git_head()->str:
    try: return subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    except Exception: return os.environ.get('GITHUB_SHA','UNKNOWN')

def next_id()->int:
    global REQ_ID
    with REQ_LOCK:
        REQ_ID+=1; return REQ_ID

def request_json(method:str,params:list,timeout:int=90)->dict:
    rid=next_id()
    body=json.dumps({'jsonrpc':'2.0','method':method,'params':params,'id':rid},separators=(',',':')).encode()
    last=None
    for attempt in range(MAX_RETRIES):
        req=urllib.request.Request(RPC,data=body,headers={
            'Content-Type':'application/json','Accept-Encoding':'gzip','User-Agent':'CryptoLab-SEF-acquisition/0.1'},method='POST')
        t0=time.monotonic()
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:
                wire=r.read(); enc=(r.headers.get('Content-Encoding') or '').lower()
                logical=gzip.decompress(wire) if enc=='gzip' else wire
                payload=json.loads(logical.decode())
                return {'ok':True,'payload':payload,'http_status':r.status,'content_encoding':enc or None,
                        'wire_bytes':len(wire),'logical_bytes':len(logical),'wire_sha256':sha256_bytes(wire),
                        'logical_sha256':sha256_bytes(logical),'elapsed_s':round(time.monotonic()-t0,4),'attempt':attempt+1}
        except urllib.error.HTTPError as e:
            raw=e.read(); last={'http_status':e.code,'text':raw.decode(errors='replace')[:1000]}
            if e.code not in (408,429,500,502,503,504): break
        except Exception as e:
            last={'error':f'{type(e).__name__}:{e}'}
        time.sleep(min(20.0,(2**attempt)+random.random()))
    return {'ok':False,'last_error':last,'attempts':MAX_RETRIES}

def get_block(n:int)->dict:
    q=request_json('eth_getBlockByNumber',[hex(n),False],60)
    if not q['ok']: raise RuntimeError(f'block request transport failure block={n}: {q}')
    p=q['payload']; r=p.get('result') if isinstance(p,dict) else None
    if not isinstance(r,dict) or not r.get('timestamp'): raise RuntimeError(f'block metadata unavailable block={n}: {p}')
    ts=int(r['timestamp'],16)
    if ts>=int(dt.datetime(2025,1,1,tzinfo=dt.timezone.utc).timestamp()):
        raise RuntimeError(f'PROTECTED_PERIOD_VIOLATION block={n} timestamp={ts}')
    return {'block':n,'timestamp':ts,'hash':r.get('hash'),'response':{k:q[k] for k in q if k not in ('payload',)}}

def first_block_at_or_after(target_ts:int,lo:int,hi:int)->tuple[int,list]:
    manifest=[]
    blo=get_block(lo); bhi=get_block(hi); manifest += [blo,bhi]
    if not (blo['timestamp'] < target_ts <= bhi['timestamp']):
        raise RuntimeError(f'boundary bracket invalid target={target_ts} lo={blo} hi={bhi}')
    while lo+1<hi:
        mid=(lo+hi)//2; bm=get_block(mid); manifest.append(bm)
        if bm['timestamp'] < target_ts: lo=mid
        else: hi=mid
    return hi,manifest

def filt(a:int,b:int,direction:str)->dict:
    topics=[TRANSFER,None,None]
    topics[2 if direction=='inbound' else 1]=PADS
    return {'fromBlock':hex(a),'toBlock':hex(b),'address':USDT,'topics':topics}

def is_split_error(payload)->bool:
    if not isinstance(payload,dict): return False
    e=payload.get('error')
    if not isinstance(e,dict): return False
    code=e.get('code'); msg=str(e.get('message','')).lower()
    return code in (-32005,-32602) or 'more than 10000' in msg or 'block range' in msg or 'range is too large' in msg or 'query returned more' in msg

def query_logs_adaptive(a:int,b:int,direction:str,depth:int=0)->tuple[list,list]:
    q=request_json('eth_getLogs',[filt(a,b,direction)],120)
    if q['ok']:
        p=q['payload']; result=p.get('result') if isinstance(p,dict) else None
        if isinstance(result,list):
            rec={'from_block':a,'to_block':b,'direction':direction,'result_count':len(result),'depth':depth,
                 **{k:q[k] for k in q if k not in ('payload','ok')}}
            return result,[rec]
        if is_split_error(p):
            pass
        else:
            raise RuntimeError(f'unexpected RPC payload {direction} {a}-{b}: {p}')
    else:
        # transport failure after retries: only split a range >1; single block is fatal
        if a>=b: raise RuntimeError(f'irreducible RPC transport failure {direction} block={a}: {q}')
    if a>=b or depth>=22: raise RuntimeError(f'irreducible log query {direction} {a}-{b}')
    mid=(a+b)//2
    l,ml=query_logs_adaptive(a,mid,direction,depth+1)
    r,mr=query_logs_adaptive(mid+1,b,direction,depth+1)
    return l+r,ml+mr

def topic_addr(x:str)->str:
    if not isinstance(x,str) or not x.startswith('0x') or len(x)<42: raise RuntimeError(f'bad indexed address topic {x!r}')
    return x[-40:].lower()

def parse_chunk(logs:list,direction:str,a:int,b:int)->tuple[dict,list]:
    seen={}; agg={}; diagnostics=[]
    for x in logs:
        if not isinstance(x,dict): raise RuntimeError('non-object log')
        if x.get('removed') is True: raise RuntimeError('removed historical log encountered')
        bn=int(x['blockNumber'],16)
        if not (a<=bn<=b): raise RuntimeError(f'log outside queried range block={bn} range={a}-{b}')
        key=(x.get('transactionHash'),x.get('logIndex'))
        canonical=(x.get('blockHash'),x.get('blockNumber'),tuple(x.get('topics') or []),x.get('data'),x.get('blockTimestamp'))
        if key in seen:
            if seen[key]!=canonical: raise RuntimeError(f'disagreeing duplicate log {key}')
            continue
        seen[key]=canonical
        topics=x.get('topics') or []
        if len(topics)<3 or topics[0].lower()!=TRANSFER: raise RuntimeError('malformed Transfer topics')
        sender=topic_addr(topics[1]); recipient=topic_addr(topics[2]); value=int(x.get('data','0x0'),16)
        ts_raw=x.get('blockTimestamp')
        if not isinstance(ts_raw,str) or not ts_raw.startswith('0x'): raise RuntimeError(f'missing/malformed blockTimestamp {ts_raw!r}')
        ts=int(ts_raw,16)
        if ts<START_TS or ts>=TERMINAL_TS: raise RuntimeError(f'log timestamp outside protected window ts={ts} block={bn}')
        date=dt.datetime.fromtimestamp(ts,tz=dt.timezone.utc).date()
        sb=sender in BASKET_SET; rb=recipient in BASKET_SET
        if direction=='inbound':
            if not rb: raise RuntimeError('inbound filter returned non-basket recipient')
            if sb: continue
            count_key='external_in_count'; raw_key='external_in_raw'
        else:
            if not sb: raise RuntimeError('outbound filter returned non-basket sender')
            if rb: continue
            count_key='external_out_count'; raw_key='external_out_raw'
        row=agg.setdefault(date,{'external_in_count':0,'external_out_count':0,'external_in_raw':0,'external_out_raw':0,'min_block':bn,'max_block':bn})
        row[count_key]+=1; row[raw_key]+=value; row['min_block']=min(row['min_block'],bn); row['max_block']=max(row['max_block'],bn)
    return agg,diagnostics

def merge_agg(dst:dict,src:dict):
    for d,r in src.items():
        x=dst.setdefault(d,{'external_in_count':0,'external_out_count':0,'external_in_raw':0,'external_out_raw':0,'min_block':r['min_block'],'max_block':r['max_block']})
        for k in ('external_in_count','external_out_count','external_in_raw','external_out_raw'): x[k]+=r[k]
        x['min_block']=min(x['min_block'],r['min_block']); x['max_block']=max(x['max_block'],r['max_block'])

def process_task(task):
    a,b,direction=task
    logs,manifest=query_logs_adaptive(a,b,direction)
    agg,_=parse_chunk(logs,direction,a,b)
    return agg,manifest

def daterange(a:dt.date,b:dt.date):
    d=a
    while d<=b:
        yield d; d+=dt.timedelta(days=1)

def file_sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def activation_gate():
    if not DECISION.exists(): raise RuntimeError('ACTIVATION_BLOCKED: SOURCE_PROVENANCE_DECISION_V0.1.md missing')
    text=DECISION.read_text(encoding='utf-8')
    if 'SOURCE_CROSSCHECK_EXACT_PASS' not in text or 'FULL_ACQUISITION_AUTHORIZED' not in text:
        raise RuntimeError('ACTIVATION_BLOCKED: exact crosscheck/full acquisition authorization not present')
    return hashlib.sha256(text.encode()).hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    activation_sha=activation_gate()
    start_block,mstart=first_block_at_or_after(START_TS,START_LO,START_HI)
    terminal_block,mend=first_block_at_or_after(TERMINAL_TS,END_LO,END_HI)
    if start_block>=terminal_block: raise RuntimeError('invalid global block bounds')
    # prove predecessor/successor boundary timestamps explicitly
    bprev=get_block(start_block-1); bstart=get_block(start_block); bendprev=get_block(terminal_block-1); bend=get_block(terminal_block)
    if not (bprev['timestamp']<START_TS<=bstart['timestamp']): raise RuntimeError('start boundary proof failed')
    if not (bendprev['timestamp']<TERMINAL_TS<=bend['timestamp']): raise RuntimeError('terminal boundary proof failed')

    chunks=[]; a=start_block
    while a<terminal_block:
        b=min(terminal_block-1,a+BASE_CHUNK-1); chunks.append((a,b)); a=b+1
    tasks=[(a,b,d) for a,b in chunks for d in ('inbound','outbound')]
    global_agg={}; query_manifest=[]
    # bounded concurrency; results merged only in main thread
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs={ex.submit(process_task,t):t for t in tasks}
        done=0
        for f in as_completed(futs):
            t=futs[f]
            try: agg,man=f.result()
            except Exception as e: raise RuntimeError(f'acquisition task failed {t}: {type(e).__name__}:{e}') from e
            merge_agg(global_agg,agg); query_manifest.extend(man); done+=1
            if done%100==0: print(json.dumps({'progress_tasks':done,'total_tasks':len(tasks)}),flush=True)

    expected_dates=list(daterange(START_DATE,END_DATE))
    rows=[]
    for d in expected_dates:
        r=global_agg.get(d,{'external_in_count':0,'external_out_count':0,'external_in_raw':0,'external_out_raw':0,'min_block':'','max_block':''})
        net=r['external_in_raw']-r['external_out_raw']
        rows.append({'date_utc':d.isoformat(),'external_in_count':r['external_in_count'],'external_out_count':r['external_out_count'],
                     'external_in_raw':r['external_in_raw'],'external_out_raw':r['external_out_raw'],'net_flow_raw':net,
                     'external_in_usdt':f"{r['external_in_raw']/1_000_000:.6f}",'external_out_usdt':f"{r['external_out_raw']/1_000_000:.6f}",
                     'net_flow_usdt':f"{net/1_000_000:.6f}",'first_block':r['min_block'],'last_block':r['max_block']})
    unexpected=sorted(d.isoformat() for d in global_agg if d<START_DATE or d>END_DATE)
    if unexpected: raise RuntimeError(f'unexpected aggregated dates {unexpected[:20]}')
    if len(rows)!=len(expected_dates): raise RuntimeError('calendar materialization row-count failure')

    csv_path=OUT/'daily_binance_public_usdt_flow_20221111_20241230.csv'
    fields=['date_utc','external_in_count','external_out_count','external_in_raw','external_out_raw','net_flow_raw','external_in_usdt','external_out_usdt','net_flow_usdt','first_block','last_block']
    with csv_path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    manifest={'lab_id':LAB,'mve_id':MVE,'source_endpoint':RPC,'git_head':git_head(),'activation_decision_sha256':activation_sha,
              'usdt_contract':USDT,'basket':BASKET,'protected_start':START_DATE.isoformat(),'protected_end':END_DATE.isoformat(),
              'global_bounds':{'start_block':start_block,'terminal_exclusive_block':terminal_block,'start_predecessor':bprev,'start_block_meta':bstart,'terminal_predecessor':bendprev,'terminal_block_meta':bend},
              'boundary_search_manifest':mstart+mend,'base_chunk_blocks':BASE_CHUNK,'max_workers':MAX_WORKERS,'query_manifest':sorted(query_manifest,key=lambda x:(x['from_block'],x['direction'],x['to_block'])),
              'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
    manifest_path=OUT/'extraction_manifest.json'; manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    receipt={'lab_id':LAB,'mve_id':MVE,'classification':'DATA_ACQUISITION_PASS','row_count':len(rows),'expected_row_count':len(expected_dates),
             'first_date':rows[0]['date_utc'],'last_date':rows[-1]['date_utc'],'start_block':start_block,'terminal_exclusive_block':terminal_block,
             'aggregate_external_in_count':sum(int(r['external_in_count']) for r in rows),'aggregate_external_out_count':sum(int(r['external_out_count']) for r in rows),
             'csv_sha256':file_sha(csv_path),'manifest_sha256':file_sha(manifest_path),'query_manifest_entries':len(query_manifest),
             'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
    (OUT/'DATA_ACQUISITION_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True),flush=True)

if __name__=='__main__': main()
