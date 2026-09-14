#!/usr/bin/env python3
import json, urllib.request, hashlib
from pathlib import Path
OUT=Path('artifacts/stablecoin_exchange_flow_mevblocker_log_schema_v01'); RPC='https://rpc.mevblocker.io'
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'; TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'; A='0x'+'0'*24+'28c6c06298d514db089934071355e5743bf21d60'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 flt={'fromBlock':hex(15943061),'toBlock':hex(15943070),'address':USDT,'topics':[TRANSFER,None,A]}
 body=json.dumps({'jsonrpc':'2.0','method':'eth_getLogs','params':[flt],'id':1},separators=(',',':')).encode(); req=urllib.request.Request(RPC,data=body,headers={'Content-Type':'application/json','User-Agent':'CryptoLab-SEF-log-schema/0.1'},method='POST')
 with urllib.request.urlopen(req,timeout=30) as r: raw=r.read(); p=json.loads(raw.decode())
 logs=p.get('result') if isinstance(p,dict) else None; sample=logs[0] if isinstance(logs,list) and logs else {}
 rec={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','classification':'LOG_SCHEMA_PASS' if isinstance(logs,list) else 'LOG_SCHEMA_FAILURE','result_count':len(logs) if isinstance(logs,list) else None,'sample_keys':sorted(sample.keys()),'has_block_timestamp':('blockTimestamp' in sample),'sample_block_number':sample.get('blockNumber'),'response_sha256':hashlib.sha256(raw).hexdigest(),'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
 (OUT/'MEVBLOCKER_LOG_SCHEMA_RECEIPT.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n'); print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=='__main__': main()
