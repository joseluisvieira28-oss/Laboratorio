import json, urllib.request, urllib.error, datetime, pathlib
ROOT = pathlib.Path(__file__).parent
def probe(url, method='GET'):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method=method), timeout=20) as r:
            body = r.read(200000) if method == 'GET' else b''
            result = {'url':url,'observed_at':started,'http_status':r.status}
            try:
                data=json.loads(body)
                allowed=['health','status','mode','checked_at_utc','runtime_identity','deployment_drift','ced1d_render_shadow','runtime_gap_history','runtime_liveness','persistence_watchdog','evidence_identity','live_capital_enabled','orders_created','authenticated_exchange_api_used','database_target_mode']
                result['operational_fields']={k:data[k] for k in allowed if k in data}
            except Exception:
                result['body_json']=False
            return result
    except urllib.error.HTTPError as e:
        result={'url':url,'observed_at':started,'http_status':e.code}
        try:
            data=json.loads(e.read(200000))
            result['operational_fields']={k:data[k] for k in ['health','checked_at_utc','runtime_identity','deployment_drift','ced1d_render_shadow','runtime_gap_history','runtime_liveness','persistence_watchdog','evidence_identity'] if k in data}
        except Exception: pass
        return result
    except Exception as e:
        return {'url':url,'observed_at':started,'error_class':type(e).__name__}
urls=[
 'https://crypto-edge-radar-v05-canary.onrender.com/health',
 'https://crypto-edge-radar-v05-canary.onrender.com/api/state',
 'https://laboratorio-080u.onrender.com/health',
 'https://ema6h-source-equivalence-canary.onrender.com/health',
 'https://tv-footprint-calibration-ingest-v01.onrender.com/health',
 'https://crypto-edge-radar-v09-forward-preflight.onrender.com/health',
 'https://crypto-edge-radar-v07-control-room-canary.onrender.com/health',
 'https://crypto-edge-radar-v06-etf-cme-canary.onrender.com/health',
 'https://crypto-edge-radar-canary-v04.onrender.com/health']
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as pool:
    results=list(pool.map(probe,urls))
base='https://data.binance.vision/data/futures/um/daily/bookDepth/AVAXUSDT/AVAXUSDT-bookDepth-2026-10-08.zip'
results += [probe(base,'HEAD'),probe(base+'.CHECKSUM')]
(ROOT/'http-probes.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
for r in results: print(r['url'],r.get('http_status',r.get('error_class')),r.get('operational_fields',{}).get('health'))
