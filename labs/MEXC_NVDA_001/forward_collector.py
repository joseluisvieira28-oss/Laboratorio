"""Bounded public REST collector; partial observed tape, never synthetic ticks.
Run --seconds 2592000 for the frozen 30-day collection in a persistent host.
No automatic scheduling, credentials or orders. --seconds 60 is a smoke run.
"""
import argparse, hashlib, json, pathlib, time, urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
ROUTES=['depth/NVIDIA_USDT','deals/NVIDIA_USDT?limit=100','index_price/NVIDIA_USDT','fair_price/NVIDIA_USDT','funding_rate/NVIDIA_USDT','ticker?symbol=NVIDIA_USDT','https://api.mexc.com/api/v3/depth?symbol=NVDAONUSDT&limit=100','https://api.mexc.com/api/v3/trades?symbol=NVDAONUSDT&limit=100']
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--seconds',type=int,default=60); ap.add_argument('--interval',type=float,default=2); args=ap.parse_args()
    assert args.seconds>0 and args.interval>=2
    dest=ROOT/'forward'; dest.mkdir(exist_ok=True)
    start=time.monotonic(); seen=set(); cycles=0; errors=0
    file=dest/f'public_{time.time_ns()}.jsonl'
    with file.open('x') as f:
        while time.monotonic()-start<args.seconds:
            cycle_start=time.monotonic()
            for route in ROUTES:
                if time.monotonic()-start>=args.seconds: break
                rec={'url':route if route.startswith('https://api.mexc.com/api/v3/') else 'https://contract.mexc.com/api/v1/contract/'+route,'start_utc_ns':time.time_ns(),'start_monotonic_ns':time.monotonic_ns()}
                try:
                    with urllib.request.urlopen(rec['url'],timeout=min(15,max(1,args.seconds-(time.monotonic()-start)))) as r:
                        body=r.read(); rec['raw_utf8']=body.decode(); rec['sha256']=hashlib.sha256(body).hexdigest(); rec['http_status']=r.status
                    response=json.loads(body)
                    if not route.startswith('https://') and not response.get('success'): raise ValueError('unsuccessful public response')
                    data=response if route.startswith('https://') else response.get('data')
                    if route.startswith('deals/'):
                        keys=[(x.get('t'),x.get('p'),x.get('v'),x.get('T'),x.get('O'),x.get('M')) for x in data]
                        rec['new_trade_keys']=[k for k in keys if k not in seen]
                        rec['trade_key_warning']='No unique exchange trade ID; identical timestamp/price/size keys can collide. Full raw batch retained.'
                        seen.update(keys)
                    if route.startswith('depth/'):
                        rec['book_version']=data.get('version'); bids=data.get('bids',[]); asks=data.get('asks',[])
                        rec['crossed_or_empty']=not bids or not asks or bids[0][0]>=asks[0][0]
                except Exception as e: rec['error']=str(e); errors+=1
                rec['end_utc_ns']=time.time_ns(); rec['end_monotonic_ns']=time.monotonic_ns()
                rec['request_latency_ms']=(rec['end_monotonic_ns']-rec['start_monotonic_ns'])/1e6
                f.write(json.dumps(rec,separators=(',',':'))+'\n'); f.flush()
            cycles+=1
            time.sleep(max(0,min(args.interval-(time.monotonic()-cycle_start),args.seconds-(time.monotonic()-start))))
    receipt={'file':str(file.relative_to(ROOT)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'seconds':time.monotonic()-start,'cycles':cycles,'errors':errors,'scope':'public MEXC future and NVDAON partial REST observations; Nasdaq rail absent; not lossless L2 or a validated execution simulator','analysis_gate':'30 days and separately verified rail timestamps/corporate actions required'}
    (dest/'smoke_receipt.json').write_text(json.dumps(receipt,indent=2)); print(json.dumps(receipt,indent=2))
if __name__=='__main__': main()
