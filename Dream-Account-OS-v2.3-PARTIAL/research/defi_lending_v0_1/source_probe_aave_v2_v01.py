#!/usr/bin/env python3
import json, urllib.request, urllib.error
from pathlib import Path

OUT=Path('aave_source_probe_output'); OUT.mkdir(exist_ok=True)
ENDPOINT='https://api.thegraph.com/subgraphs/name/aave/protocol-v2'

def gql(query):
    body=json.dumps({'query':query}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'DEFI-LENDING-002-source-probe/0.1'})
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            raw=r.read(); code=r.status
        return code,json.loads(raw),raw
    except urllib.error.HTTPError as e:
        raw=e.read(); return e.code,{'http_error':e.code,'body':raw.decode('utf-8','replace')},raw

q1='''{ reserves(where:{symbol:"USDC"}) { id symbol underlyingAsset lastUpdateTimestamp variableBorrowRate } }'''
code1,obj1,raw1=gql(q1)
(OUT/'AAVE_V2_USDC_RESERVE_PROBE.json').write_bytes(raw1)
reserve_id=None
if code1==200 and not obj1.get('errors'):
    rs=(obj1.get('data') or {}).get('reserves') or []
    if rs: reserve_id=rs[0]['id']

hist=None; code2=None; raw2=b''
if reserve_id:
    q2='''{ reserveParamsHistoryItems(first:5, orderBy:timestamp, orderDirection:asc, where:{reserve:"%s", timestamp_gte:1609459200}) { id timestamp variableBorrowRate utilizationRate } }''' % reserve_id
    code2,hist,raw2=gql(q2)
    (OUT/'AAVE_V2_USDC_HISTORY_PROBE.json').write_bytes(raw2)

classification='SOURCE_PROBE_PASS' if reserve_id and code2==200 and hist and not hist.get('errors') and ((hist.get('data') or {}).get('reserveParamsHistoryItems') or []) else 'SOURCE_AUTH_OR_ENDPOINT_BLOCKED'
report={
 'lab':'DEFI-LENDING-002','mve_id':'DL-AAVEV2-USDC-BORROW-001','mode':'SOURCE_PROBE_ONLY',
 'endpoint':ENDPOINT,'reserve_query_http':code1,'reserve_id':reserve_id,'history_query_http':code2,
 'classification':classification,
 'signal_computed':False,'btc_price_values_evaluated':False,'btc_returns_computed':False,'pnl_computed':False,
 'holdout_2025_accessed':False,'year_2026_accessed':False,
}
(OUT/'AAVE_V2_SOURCE_PROBE_RECEIPT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
print('SOURCE PROBE ONLY / NO SIGNAL / NO BTC / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
raise SystemExit(0 if classification=='SOURCE_PROBE_PASS' else 2)
