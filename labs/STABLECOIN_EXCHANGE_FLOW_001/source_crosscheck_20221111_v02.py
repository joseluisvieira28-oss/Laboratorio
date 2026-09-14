#!/usr/bin/env python3
"""Exact 2022-11-11 MEV Blocker vs Blockchair dump cross-check, parallel-range transport.

Same scientific semantics as V0.1. The Blockchair gzip file is fetched byte-for-byte via
HTTP Range in parallel, reassembled in canonical byte order, hashed, then decompressed.
No BTC data, returns, PnL, 2025 or 2026.
"""
from __future__ import annotations
import csv, gzip, hashlib, io, json, re, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

OUT=Path('artifacts/stablecoin_exchange_flow_source_crosscheck_20221111_v02')
RPC='https://rpc.mevblocker.io'
DUMP='https://gz.blockchair.com/ethereum/erc-20/transactions/blockchair_erc-20_transactions_20221111.tsv.gz'
USDT='dac17f958d2ee523a2206206994597c13d831ec7'; USDT0='0x'+USDT
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
BASKET={x.lower().removeprefix('0x') for x in [
'0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']}
PADS=['0x'+'0'*24+x for x in sorted(BASKET)]
START_BLOCK=15943061
TARGET_END_TS=1668211200
PARTS=8

def rpc(method,params,rid,timeout=90):
    body=json.dumps({'jsonrpc':'2.0','method':method,'params':params,'id':rid},separators=(',',':')).encode()
    req=urllib.request.Request(RPC,data=body,headers={'Content-Type':'application/json','User-Agent':'CryptoLab-SEF-crosscheck-v02/0.1'},method='POST')
    try:
      with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read(); return json.loads(raw.decode()), hashlib.sha256(raw).hexdigest(), len(raw)
    except Exception as e: return {'error_local':f'{type(e).__name__}:{e}'},None,None

def block_ts(n,rid):
    p,_,_=rpc('eth_getBlockByNumber',[hex(n),False],rid)
    r=p.get('result') if isinstance(p,dict) else None
    return int(r['timestamp'],16) if isinstance(r,dict) and r.get('timestamp') else None

def find_last_block_before_target():
    lo=START_BLOCK; hi=START_BLOCK+9000; rid=100
    while True:
      ts=block_ts(hi,rid); rid+=1
      if ts is None: raise RuntimeError('block timestamp unavailable during upper bound search')
      if ts>=TARGET_END_TS: break
      hi+=4000
    while lo+1<hi:
      mid=(lo+hi)//2; ts=block_ts(mid,rid); rid+=1
      if ts is None: raise RuntimeError('block timestamp unavailable during binary search')
      if ts<TARGET_END_TS: lo=mid
      else: hi=mid
    return lo

def log_filter(a,b,direction):
    t=[TRANSFER,None,None]; t[2 if direction=='inbound' else 1]=PADS
    return {'fromBlock':hex(a),'toBlock':hex(b),'address':USDT0,'topics':t}

def get_logs_adaptive(a,b,direction,ridbox,depth=0):
    ridbox[0]+=1; p,h,n=rpc('eth_getLogs',[log_filter(a,b,direction)],ridbox[0])
    if isinstance(p,dict) and isinstance(p.get('result'),list):
      return p['result'],[{'from':a,'to':b,'direction':direction,'count':len(p['result']),'sha256':h,'bytes':n}]
    if a>=b or depth>=18: raise RuntimeError(f'RPC log query failed irreducibly {direction} {a}-{b}: {p}')
    mid=(a+b)//2
    left,ml=get_logs_adaptive(a,mid,direction,ridbox,depth+1); right,mr=get_logs_adaptive(mid+1,b,direction,ridbox,depth+1)
    return left+right,ml+mr

def topic_addr(t): return t[-40:].lower()
def parse_rpc(logs,direction):
    seen={}; count=0; total=0
    for x in logs:
      key=(x.get('transactionHash'),x.get('logIndex'))
      canonical=(x.get('blockNumber'),tuple(x.get('topics') or []),x.get('data'))
      if key in seen:
        if seen[key]!=canonical: raise RuntimeError(f'disagreeing duplicate RPC log {key}')
        continue
      seen[key]=canonical
      topics=x.get('topics') or []
      if len(topics)<3: raise RuntimeError('undecodable RPC log topics')
      sender=topic_addr(topics[1]); recipient=topic_addr(topics[2]); val=int(x.get('data','0x0'),16)
      if direction=='inbound' and recipient in BASKET and sender not in BASKET: count+=1; total+=val
      elif direction=='outbound' and sender in BASKET and recipient not in BASKET: count+=1; total+=val
    return {'count':count,'raw_value':total}

def probe_total_size():
    req=urllib.request.Request(DUMP,headers={'Range':'bytes=0-0','User-Agent':'CryptoLab-SEF-crosscheck-v02/0.1'})
    with urllib.request.urlopen(req,timeout=60) as r:
      raw=r.read(); cr=r.headers.get('Content-Range','')
      m=re.search(r'/([0-9]+)$',cr)
      if r.status!=206 or not m: raise RuntimeError(f'Range size probe failed status={r.status} content-range={cr!r}')
      return int(m.group(1)),hashlib.sha256(raw).hexdigest()

def fetch_part(idx,start,end):
    req=urllib.request.Request(DUMP,headers={'Range':f'bytes={start}-{end}','User-Agent':'CryptoLab-SEF-crosscheck-v02/0.1'})
    with urllib.request.urlopen(req,timeout=180) as r:
      raw=r.read(); cr=r.headers.get('Content-Range','')
      if r.status!=206: raise RuntimeError(f'part {idx}: expected 206 got {r.status}')
      if len(raw)!=(end-start+1): raise RuntimeError(f'part {idx}: byte length mismatch {len(raw)} vs {end-start+1}')
      return idx,start,end,raw,cr,hashlib.sha256(raw).hexdigest()

def download_parallel():
    total,probe_sha=probe_total_size(); step=(total+PARTS-1)//PARTS; ranges=[]
    for i in range(PARTS):
      a=i*step
      if a>=total: break
      b=min(total-1,(i+1)*step-1); ranges.append((i,a,b))
    out=[None]*len(ranges); manifest=[]
    with ThreadPoolExecutor(max_workers=len(ranges)) as ex:
      futs={ex.submit(fetch_part,*r):r[0] for r in ranges}
      for f in as_completed(futs):
        idx,a,b,raw,cr,sha=f.result(); out[idx]=raw; manifest.append({'part':idx,'start':a,'end':b,'bytes':len(raw),'content_range':cr,'sha256':sha})
    blob=b''.join(out)
    if len(blob)!=total: raise RuntimeError(f'reassembled dump length mismatch {len(blob)} vs {total}')
    return blob,sorted(manifest,key=lambda x:x['part']),probe_sha

def parse_dump(rawgz):
    result={'inbound':{'count':0,'raw_value':0},'outbound':{'count':0,'raw_value':0},'internal':{'count':0,'raw_value':0}}
    with gzip.GzipFile(fileobj=io.BytesIO(rawgz),mode='rb') as gz:
      text=io.TextIOWrapper(gz,encoding='utf-8',newline=''); rd=csv.DictReader(text,delimiter='\t')
      for row in rd:
        if (row.get('token_address') or '').lower()!=USDT: continue
        s=(row.get('sender') or '').lower().removeprefix('0x'); r=(row.get('recipient') or '').lower().removeprefix('0x')
        sb=s in BASKET; rb=r in BASKET
        if not (sb or rb): continue
        v=int(row['value'])
        if sb and rb: result['internal']['count']+=1; result['internal']['raw_value']+=v
        elif rb: result['inbound']['count']+=1; result['inbound']['raw_value']+=v
        elif sb: result['outbound']['count']+=1; result['outbound']['raw_value']+=v
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True); end_block=find_last_block_before_target(); rid=[1000]
    inlogs,mi=get_logs_adaptive(START_BLOCK,end_block,'inbound',rid); outlogs,mo=get_logs_adaptive(START_BLOCK,end_block,'outbound',rid)
    rpc_tot={'inbound':parse_rpc(inlogs,'inbound'),'outbound':parse_rpc(outlogs,'outbound')}
    raw,parts,probe_sha=download_parallel(); dump_sha=hashlib.sha256(raw).hexdigest(); dump_tot=parse_dump(raw)
    exact=(rpc_tot['inbound']==dump_tot['inbound'] and rpc_tot['outbound']==dump_tot['outbound'])
    receipt={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':'SOURCE_CROSSCHECK_EXACT_PASS' if exact else 'SOURCE_CROSSCHECK_MISMATCH','transport_version':'parallel-range-v02','date':'2022-11-11','start_block':START_BLOCK,'end_block':end_block,'rpc':RPC,'rpc_totals':rpc_tot,'blockchair_dump':DUMP,'dump_sha256':dump_sha,'dump_bytes':len(raw),'dump_parts':parts,'range_probe_first_byte_sha256':probe_sha,'dump_totals':dump_tot,'rpc_chunk_manifest':mi+mo,'exact_external_flow_match':exact,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
    (OUT/'SOURCE_CROSSCHECK_20221111_V02_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,indent=2,sort_keys=True))
if __name__=='__main__': main()
