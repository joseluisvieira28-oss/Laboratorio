"""Obtain token bars only across the observed MEXC future overlap.
No corporate-action normalization or index-dependency assumption is fabricated.
"""
import concurrent.futures,json,pathlib,time,urllib.request,hashlib
from analyze import ROOT,load
def main():
    last,_,_=load('last'); start=min(last); end=max(last)
    def fetch(t):
        url=f'https://api.mexc.com/api/v3/klines?symbol=NVDAONUSDT&interval=1m&startTime={t*1000}&endTime={min(t+29940,end)*1000}&limit=500'
        rec={'url':url,'start_ns':time.time_ns()}
        try:
            raw=urllib.request.urlopen(url,timeout=20).read(); rec['response']=json.loads(raw); rec['body_sha256']=hashlib.sha256(raw).hexdigest()
        except Exception as e: rec['error']=str(e)
        rec['end_ns']=time.time_ns(); (ROOT/'raw'/f'token_{t}.json').write_text(json.dumps(rec,separators=(',',':')))
        return rec
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: responses=list(pool.map(fetch,range(start,end+1,30000)))
    times={int(r[0])//1000 for rec in responses if isinstance(rec.get('response'),list) for r in rec['response']}
    receipt={'requested_start':start,'requested_end':end,'bars':len(times),'common_future_minutes':len(times&set(last)),'errors':sum('error' in r for r in responses),'gate':'History obtainable. H3 still BLOCKED: precise total-return/share normalization and dated MEXC index dependency/weights plus executable costs missing. Token not substituted for Index.'}
    (ROOT/'token_source_receipt.json').write_text(json.dumps(receipt,indent=2)); print(json.dumps(receipt,indent=2))
if __name__=='__main__': main()
