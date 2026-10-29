"""Bounded public source availability probe; never requests protected dates or outcomes."""
import concurrent.futures, datetime, hashlib, json, urllib.request, urllib.error
from pathlib import Path

DAY = '2026/04/01'
URLS = [f'https://datasets.tardis.dev/v1/bybit/{kind}/{DAY}/{sym}.csv.gz'
        for sym in ('BTCUSDT', 'ETHUSDT')
        for kind in ('trades', 'liquidations', 'book_snapshot_5')]
URLS += [f'https://data.binance.vision/data/futures/um/daily/liquidationSnapshot/{sym}/{sym}-liquidationSnapshot-2026-04-01.zip' for sym in ('BTCUSDT','ETHUSDT')]

def probe(url):
    row = {'url': url, 'method': 'GET', 'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'Range':'bytes=0-8191'}), timeout=30) as r:
            body=r.read(8192)
            row.update(status=r.status, headers=dict(r.headers), prefix_bytes=len(body), prefix_sha256=hashlib.sha256(body).hexdigest())
    except urllib.error.HTTPError as e:
        body=e.read(8192)
        row.update(status=e.code, headers=dict(e.headers), error_body=body.decode('utf8','replace'), error_body_sha256=hashlib.sha256(body).hexdigest())
    except Exception as e:
        row.update(status=None, error=str(e))
    return row

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(probe, URLS))
    result = {'scope':'2026-04-01 only, already-open Discovery', 'stage':'availability only; HTTP 200 is NOT full source PASS', 'probes':rows, 'outcomes_opened':0, 'protected_holdout_requests':0}
    Path('joint_source_get_availability.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))
