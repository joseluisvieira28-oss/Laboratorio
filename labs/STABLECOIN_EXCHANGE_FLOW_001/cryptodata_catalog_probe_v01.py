#!/usr/bin/env python3
"""Probe protected Blockchair mirror/catalog metadata for exact monthly ERC-20 dump URLs.
No 2025/2026 datasets, no market outcomes.
"""
from __future__ import annotations
import json, urllib.parse, urllib.request, urllib.error
from pathlib import Path

OUT = Path('artifacts/stablecoin_exchange_flow_catalog_probe_v01')
DATASETS = ['bcd_erc-20_transactions_2022_11','bcd_erc-20_transactions_2024_11']
BASE = 'https://cryptodata.center/api/3/action/package_show'

def fetch(dataset: str) -> dict:
    url = BASE + '?' + urllib.parse.urlencode({'id': dataset})
    req = urllib.request.Request(url, headers={'User-Agent':'CryptoLab-SEF-catalog-probe/0.1'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            payload = json.loads(raw.decode('utf-8'))
            result = payload.get('result') or {}
            resources = []
            for x in result.get('resources') or []:
                resources.append({k:x.get(k) for k in ['id','name','format','url','url_type','size','hash','created','last_modified']})
            return {'dataset':dataset,'status':r.status,'title':result.get('title'),'resources':resources}
    except urllib.error.HTTPError as e:
        return {'dataset':dataset,'status':e.code,'error':e.read().decode('utf-8',errors='replace')[:1000]}
    except Exception as e:
        return {'dataset':dataset,'status':None,'error':f'{type(e).__name__}:{e}'}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    probes=[fetch(x) for x in DATASETS]
    urls=[r.get('url') for p in probes for r in p.get('resources',[]) if r.get('url')]
    classification='CATALOG_ROUTE_PASS' if urls else 'CATALOG_ROUTE_NOT_FOUND'
    receipt={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':classification,'datasets':DATASETS,'resource_urls':urls,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,'probes':probes}
    (OUT/'CATALOG_PROBE_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
