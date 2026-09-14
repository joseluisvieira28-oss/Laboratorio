#!/usr/bin/env python3
"""Late protected full-day source equivalence cross-check: 2024-11-11.

MEV Blocker historical USDT Transfer logs vs canonical Blockchair ERC-20 daily dump.
Source/data only. No BTC price, returns, PnL, 2025 or 2026.
"""
from __future__ import annotations
import csv,gzip,hashlib,io,json,urllib.request
from pathlib import Path
OUT=Path('artifacts/stablecoin_exchange_flow_source_crosscheck_20241111_v01')
RPC='https://rpc.mevblocker.io'
DUMP='https://gz.blockchair.com/ethereum/erc-20/transactions/blockchair_erc-20_transactions_20241111.tsv.gz'
USDT='dac17f958d2ee523a2206206994597c13d831ec7'; USDT0='0x'+USDT
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
BASKET={x.lower().removeprefix('0x') for x in ['0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']}
PADS=['0x'+'0'*24+x for x in sorted(BASKET)]
DAY_START_TS=1731283200  # 2024-11-11 00:00 UTC
DAY_END_TS=1731369600    # 2024-11-12 00:00 UTC
LO=21000000; HI=21300000

def rpc(method,params,rid,timeout=120):
 body=json.dumps({'jsonrpc':'2.0','method':method,'params':params,'id':rid},separators=(',',':')).encode(); req=urllib.request.Request(RPC,data=body,headers={'Content-Type':'application/json','Accept-Encoding':'gzip','User-Agent':'CryptoLab-SEF-2024-crosscheck/0.1'},method='POST')
 with urllib.request.urlopen(req,timeout=timeout) as r:
  wire=r.read(); enc=(r.headers.get('Content-Encoding') or '').lower(); logical=gzip.decompress(wire) if enc=='gzip' else wire; return json.loads(logical.decode()),hashlib.sha256(logical).hexdigest(),len(logical)
def block_ts(n,rid):
 p,_,_=rpc('eth_getBlockByNumber',[hex(n),False],rid,60); r=p.get('result') if isinstance(p,dict) else None
 return int(r['timestamp'],16) if isinstance(r,dict) and r.get('timestamp') else None
def first_at(target,rid0):
 lo,hi=LO,HI; rid=rid0; tl=block_ts(lo,rid); rid+=1; th=block_ts(hi,rid); rid+=1
 if tl is None or th is None or not (tl<target<=th): raise RuntimeError(f'bad protected bracket target={target} lo_ts={tl} hi_ts={th}')
 while lo+1<hi:
  mid=(lo+hi)//2; t=block_ts(mid,rid); rid+=1
  if t is None: raise RuntimeError('missing block timestamp')
  if t<target: lo=mid
  else: hi=mid
 return hi,rid
def filt(a,b,d):
 t=[TRANSFER,None,None]; t[2 if d=='inbound' else 1]=PADS
 return {'fromBlock':hex(a),'toBlock':hex(b),'address':USDT0,'topics':t}
def logs(a,b,d,ridbox,depth=0):
 ridbox[0]+=1
 try: p,h,n=rpc('eth_getLogs',[filt(a,b,d)],ridbox[0])
 except Exception as e: p={'error_local':f'{type(e).__name__}:{e}'}; h=None; n=None
 if isinstance(p,dict) and isinstance(p.get('result'),list): return p['result'],[{'from':a,'to':b,'direction':d,'count':len(p['result']),'logical_sha256':h,'logical_bytes':n}]
 if a>=b or depth>=20: raise RuntimeError(f'irreducible log query {d} {a}-{b}: {p}')
 m=(a+b)//2; l,ml=logs(a,m,d,ridbox,depth+1); r,mr=logs(m+1,b,d,ridbox,depth+1); return l+r,ml+mr
def addr(t): return t[-40:].lower()
def parse_rpc(xs,d):
 seen={}; c=0; total=0
 for x in xs:
  k=(x.get('transactionHash'),x.get('logIndex')); canon=(x.get('blockNumber'),tuple(x.get('topics') or []),x.get('data'))
  if k in seen:
   if seen[k]!=canon: raise RuntimeError(f'disagreeing duplicate {k}')
   continue
  seen[k]=canon; tt=x.get('topics') or []; s=addr(tt[1]); r=addr(tt[2]); v=int(x.get('data','0x0'),16)
  if d=='inbound' and r in BASKET and s not in BASKET: c+=1; total+=v
  elif d=='outbound' and s in BASKET and r not in BASKET: c+=1; total+=v
 return {'count':c,'raw_value':total}
def parse_dump(raw):
 out={'inbound':{'count':0,'raw_value':0},'outbound':{'count':0,'raw_value':0},'internal':{'count':0,'raw_value':0}}
 with gzip.GzipFile(fileobj=io.BytesIO(raw),mode='rb') as g:
  rd=csv.DictReader(io.TextIOWrapper(g,encoding='utf-8',newline=''),delimiter='\t')
  for row in rd:
   if (row.get('token_address') or '').lower()!=USDT: continue
   s=(row.get('sender') or '').lower().removeprefix('0x'); r=(row.get('recipient') or '').lower().removeprefix('0x'); sb=s in BASKET; rb=r in BASKET
   if not(sb or rb): continue
   v=int(row['value'])
   if sb and rb: out['internal']['count']+=1; out['internal']['raw_value']+=v
   elif rb: out['inbound']['count']+=1; out['inbound']['raw_value']+=v
   elif sb: out['outbound']['count']+=1; out['outbound']['raw_value']+=v
 return out
def main():
 OUT.mkdir(parents=True,exist_ok=True); start,rid=first_at(DAY_START_TS,1); terminal,rid=first_at(DAY_END_TS,rid+10); end=terminal-1; box=[rid+100]
 il,mi=logs(start,end,'inbound',box); ol,mo=logs(start,end,'outbound',box); rt={'inbound':parse_rpc(il,'inbound'),'outbound':parse_rpc(ol,'outbound')}
 req=urllib.request.Request(DUMP,headers={'User-Agent':'CryptoLab-SEF-2024-crosscheck/0.1'}); 
 with urllib.request.urlopen(req,timeout=1200) as r: raw=r.read()
 dtot=parse_dump(raw); exact=(rt['inbound']==dtot['inbound'] and rt['outbound']==dtot['outbound'])
 rec={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':'SOURCE_CROSSCHECK_EXACT_PASS' if exact else 'SOURCE_CROSSCHECK_MISMATCH','date':'2024-11-11','start_block':start,'end_block':end,'terminal_exclusive_block':terminal,'rpc_totals':rt,'dump_totals':dtot,'blockchair_dump':DUMP,'dump_bytes':len(raw),'dump_sha256':hashlib.sha256(raw).hexdigest(),'rpc_chunk_manifest':mi+mo,'exact_external_flow_match':exact,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
 (OUT/'SOURCE_CROSSCHECK_20241111_RECEIPT.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n'); print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=='__main__': main()
