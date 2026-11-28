"""Public spot reads only. Persist append-only quotes and completed post-freeze candles."""
import sys,time,json,hashlib,urllib.parse,urllib.request,datetime as dt
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent
FOLDER=ROOT/'forward'
ASSETS=['BTCUSDT','SOLUSDT','BNBUSDT']
UTC=dt.timezone.utc
FENCE=int(dt.datetime(2026,11,28,13,tzinfo=UTC).timestamp()*1000)
HOUR=3600000
def get(route,**params):
    url='https://data-api.binance.vision/api/v3/'+route+'?'+urllib.parse.urlencode(params)
    with urllib.request.urlopen(url,timeout=15) as f:return json.load(f)
def tick(day=None):
    now=int(time.time()*1000);server=get('time')['serverTime']
    if abs(server-now)>60000:raise RuntimeError('exchange clock out of tolerance')
    nowdt=dt.datetime.fromtimestamp(now/1000,UTC)
    if day is None:
        stamp=nowdt.strftime('%Y%m%dT%H%M%SZ')
        def quote(a):
            start=time.time_ns();q=get('depth',symbol=a,limit=5);end=time.time_ns()
            if end-start>10_000_000_000 or float(q['bids'][0][0])>=float(q['asks'][0][0]):raise ValueError('stale or crossed')
            return dict(symbol=a,request_ns=start,received_ns=end,depth=q)
        with ThreadPoolExecutor(3) as pool:quotes=list(pool.map(quote,ASSETS))
        data=dict(status='WARMUP_OR_QUOTE_WITNESS_ONLY',server_ms=server,receipts=quotes)
        path=FOLDER/('quote-'+stamp+'.json')
    else:
        start=int(dt.datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp()*1000)
        end=start+24*HOUR
        if start<FENCE-13*HOUR or end>server:raise ValueError('outside closed prospective window')
        start=max(start,FENCE)
        path=FOLDER/('bars-'+day+'.json')
        if path.exists():return
        data={}
        for a in ASSETS:
            rows=get('klines',symbol=a,interval='1h',startTime=start,endTime=end-1,limit=24)
            if [r[0] for r in rows]!=list(range(start,end,HOUR)) or any(r[6]!=r[0]+HOUR-1 for r in rows):
                raise ValueError('missing or mismatched hourly candle')
            data[a]=rows
    FOLDER.mkdir(exist_ok=True)
    with path.open('x') as f:json.dump(data,f,sort_keys=True)
    print(path.name,hashlib.sha256(path.read_bytes()).hexdigest())
if __name__=='__main__':tick(sys.argv[1] if len(sys.argv)>1 else None)
