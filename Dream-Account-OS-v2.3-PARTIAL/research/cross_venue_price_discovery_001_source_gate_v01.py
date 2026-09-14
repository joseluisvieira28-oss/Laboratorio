#!/usr/bin/env python3
from __future__ import annotations
import json, urllib.request, urllib.error, hashlib

DATES = [
    '2024-01-01','2024-01-07','2024-01-13','2024-01-19','2024-01-25',
    '2024-04-01','2024-04-07','2024-04-13','2024-04-19','2024-04-25',
    '2024-07-01','2024-07-07','2024-07-13','2024-07-19','2024-07-25',
    '2024-10-01','2024-10-07','2024-10-13','2024-10-19','2024-10-25'
]
BINANCE = 'https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-{date}.zip'
HL = 'https://hyperliquid-archive.s3.amazonaws.com/market_data/{yyyymmdd}/0/l2Book/BTC.lz4'


def head(url: str, headers=None):
    req = urllib.request.Request(url, method='HEAD', headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {'ok': 200 <= r.status < 400, 'status': r.status,
                    'etag': r.headers.get('ETag'), 'length': r.headers.get('Content-Length')}
    except urllib.error.HTTPError as e:
        return {'ok': False, 'status': e.code, 'error': str(e)}
    except Exception as e:
        return {'ok': False, 'status': None, 'error': type(e).__name__ + ': ' + str(e)}


def main():
    assert all(d.startswith('2024-') for d in DATES)
    binance=[]; hl=[]
    for d in DATES:
        b = head(BINANCE.format(date=d))
        binance.append({'date': d, **b})
        ymd=d.replace('-','')
        h = head(HL.format(yyyymmdd=ymd), headers={'x-amz-request-payer':'requester'})
        hl.append({'date': d, **h})
    b_ok=sum(x['ok'] for x in binance)
    h_ok=sum(x['ok'] for x in hl)
    quarters=len({int(d[5:7])//3 + (0 if int(d[5:7])%3 else -1) for d in DATES})
    if b_ok == 20 and h_ok == 20:
        classification='SOURCE_DATA_PASS'
    elif b_ok == 20 and h_ok == 0 and all(x.get('status') in (401,403,None) for x in hl):
        classification='SOURCE_ACQUISITION_TECHNICAL_FAILURE_HL_REQUESTER_PAYS_AUTH'
    elif b_ok < 20 or h_ok < 20:
        classification='INSUFFICIENT_SAMPLE_OR_SOURCE_AVAILABILITY'
    else:
        classification='PROVENANCE_FAILURE'
    receipt={
        'lab':'CROSS-VENUE-PRICE-DISCOVERY-001',
        'phase':'SOURCE_PROVENANCE_GATE_ONLY',
        'classification':classification,
        'frozen_dates':DATES,
        'binance_objects_ok':b_ok,
        'hyperliquid_objects_ok':h_ok,
        'quarter_count':4,
        'binance':binance,
        'hyperliquid':hl,
        'economic_values_downloaded':False,
        'returns_computed':False,
        'lead_lag_computed':False,
        'pnl_computed':False,
        '2025_accessed':False,
        '2026_accessed':False,
        'live_trading':False,
        'exchange_mutation':False,
    }
    blob=json.dumps(receipt,sort_keys=True,separators=(',',':')).encode()
    receipt['receipt_sha256']=hashlib.sha256(blob).hexdigest()
    print('CVPD001_SOURCE_GATE_JSON='+json.dumps(receipt,sort_keys=True))
    print('CVPD001_SOURCE_GATE='+classification)
    if classification != 'SOURCE_DATA_PASS':
        raise SystemExit(2)

if __name__ == '__main__':
    main()
