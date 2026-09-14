#!/usr/bin/env python3
"""Transport-only sequential Range probe across one protected Blockchair dump."""
import hashlib, json, re, time, urllib.request, urllib.error
from pathlib import Path
OUT=Path('artifacts/stablecoin_exchange_flow_blockchair_range_access_probe_v01')
URL='https://gz.blockchair.com/ethereum/erc-20/transactions/blockchair_erc-20_transactions_20221111.tsv.gz'
SIZE=62325135
RANGES=[('start',0,1023),('quarter',SIZE//4,SIZE//4+1023),('middle',SIZE//2,SIZE//2+1023),('three_quarter',3*SIZE//4,3*SIZE//4+1023),('end',SIZE-1024,SIZE-1)]
def fetch(name,a,b):
 req=urllib.request.Request(URL,headers={'Range':f'bytes={a}-{b}','User-Agent':'CryptoLab-SEF-range-access/0.1'})
 try:
  with urllib.request.urlopen(req,timeout=45) as r:
   raw=r.read(); return {'name':name,'requested':[a,b],'status':r.status,'bytes':len(raw),'content_range':r.headers.get('Content-Range'),'sha256':hashlib.sha256(raw).hexdigest()}
 except urllib.error.HTTPError as e:
  raw=e.read(); return {'name':name,'requested':[a,b],'status':e.code,'bytes':len(raw),'content_range':e.headers.get('Content-Range'),'text':raw.decode(errors='replace')[:500]}
 except Exception as e: return {'name':name,'requested':[a,b],'status':None,'error':f'{type(e).__name__}:{e}'}
def main():
 OUT.mkdir(parents=True,exist_ok=True); rows=[]
 for x in RANGES:
  rows.append(fetch(*x)); time.sleep(2)
 ok=all(r.get('status')==206 and r.get('bytes')==1024 for r in rows)
 rec={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':'RANGE_ACCESS_PASS' if ok else 'RANGE_ACCESS_FAILURE','url':URL,'known_total_bytes':SIZE,'rows':rows,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
 (OUT/'BLOCKCHAIR_RANGE_ACCESS_RECEIPT.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n'); print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=='__main__': main()
