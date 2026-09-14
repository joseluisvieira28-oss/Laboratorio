#!/usr/bin/env python3
"""Transport-only protected Blockchair Range size profile."""
import hashlib,json,time,urllib.request,urllib.error
from pathlib import Path
OUT=Path('artifacts/stablecoin_exchange_flow_blockchair_range_size_profile_v01')
URL='https://gz.blockchair.com/ethereum/erc-20/transactions/blockchair_erc-20_transactions_20221111.tsv.gz'
TOTAL=62325135
SIZES=[1<<20,2<<20,4<<20,8<<20]
START=20<<20

def fetch(n):
 a=START; b=min(TOTAL-1,a+n-1); req=urllib.request.Request(URL,headers={'Range':f'bytes={a}-{b}','User-Agent':'CryptoLab-SEF-range-size/0.1'})
 t=time.monotonic()
 try:
  with urllib.request.urlopen(req,timeout=120) as r:
   raw=r.read(); return {'requested_bytes':b-a+1,'status':r.status,'bytes':len(raw),'elapsed_s':round(time.monotonic()-t,3),'content_range':r.headers.get('Content-Range'),'sha256':hashlib.sha256(raw).hexdigest()}
 except urllib.error.HTTPError as e:
  raw=e.read(); return {'requested_bytes':b-a+1,'status':e.code,'bytes':len(raw),'elapsed_s':round(time.monotonic()-t,3),'text':raw.decode(errors='replace')[:500]}
 except Exception as e: return {'requested_bytes':b-a+1,'status':None,'elapsed_s':round(time.monotonic()-t,3),'error':f'{type(e).__name__}:{e}'}
def main():
 OUT.mkdir(parents=True,exist_ok=True); rows=[]
 for n in SIZES:
  rows.append(fetch(n)); time.sleep(3)
 safe=[r['requested_bytes'] for r in rows if r.get('status')==206 and r.get('bytes')==r.get('requested_bytes')]
 rec={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':'RANGE_SIZE_PROFILE_PASS' if safe else 'RANGE_SIZE_PROFILE_FAILURE','max_observed_safe_bytes':max(safe) if safe else 0,'rows':rows,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
 (OUT/'BLOCKCHAIR_RANGE_SIZE_PROFILE_RECEIPT.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n'); print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=='__main__': main()
