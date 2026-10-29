"""Source-only validation for immutable JOINT_SOURCE_GATE_V01; no outcome joins."""
import concurrent.futures, datetime, hashlib, json, urllib.request, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path('joint_sources'); ROOT.mkdir(exist_ok=True)
START=int(pd.Timestamp('2026-04-01',tz='UTC').timestamp()*1e6)
END=START+86400*1000000
KINDS=('trades','liquidations','book_snapshot_5')

def validate(pair):
    sym,kind=pair
    url=f'https://datasets.tardis.dev/v1/bybit/{kind}/2026/04/01/{sym}.csv.gz'
    path=ROOT/f'{sym}_{kind}.csv.gz'
    sha=hashlib.sha256(); md5=hashlib.md5(); total=0
    started=time.monotonic();expected_size=None
    with path.open('wb') as out:
        while expected_size is None or total<expected_size:
            if time.monotonic()-started>120: raise TimeoutError('120s per-file transfer cap')
            req=urllib.request.Request(url,headers={'Range':f'bytes={total}-{total+1048575}'})
            with urllib.request.urlopen(req,timeout=15) as r:
                headers=dict(r.headers)
                if r.status!=206: raise ValueError('Range transfer requires HTTP206')
                cr=headers['Content-Range'];expected_size=int(cr.split('/')[-1])
                if not cr.startswith(f'bytes {total}-'): raise ValueError('Incorrect Content-Range offset')
                if expected_size>250_000_000: raise ValueError('250MB per-file cap')
                block=r.read(1048576)
                if not block: raise ValueError('Empty range')
                total+=len(block);sha.update(block);md5.update(block);out.write(block)
    receipt={'symbol':sym,'kind':kind,'url':url,'bytes':total,'sha256':sha.hexdigest(),'md5':md5.hexdigest(),'headers':headers,'downloaded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    expected=headers.get('x-md5','').strip('"')
    receipt['publisher_md5_match']=bool(expected) and expected==md5.hexdigest()
    rows=0;invalid=0;regress=0;prev=None;minutes=set();lags=[];first=None;last=None;maxgap=0; event_minutes=set()
    for d in pd.read_csv(path,chunksize=100000):
        rows+=len(d)
        ts=d.timestamp.to_numpy(dtype='int64'); local=d.local_timestamp.to_numpy(dtype='int64')
        bad=(d.symbol!=sym)|(d.exchange!='bybit')|(ts<START)|(ts>=END)|(~np.isfinite(ts))
        regress+=int((np.diff(local)<0).sum())
        if prev is not None:
            regress+=int(local[0]<prev);maxgap=max(maxgap,int(local[0]-prev))
        if len(local)>1:maxgap=max(maxgap,int(np.diff(local).max()))
        prev=int(local[-1]);first=int(local[0]) if first is None else first;last=prev
        minutes.update(((local-START)//60_000_000).tolist());event_minutes.update(((ts-START)//60_000_000).tolist())
        lags.append(local-ts)
        if kind!='book_snapshot_5':
            bad=bad|(~d.side.isin(['buy','sell']))|(d.price<=0)|(d.amount<=0)|d.price.isna()|d.amount.isna()
        else:
            cols=[f'{side}[{i}].{field}' for i in range(5) for side in ('asks','bids') for field in ('price','amount')]
            vals=d[cols].to_numpy();bad=bad|(~np.isfinite(vals).all(axis=1))|(vals<=0).any(axis=1)
            ap=d[[f'asks[{i}].price' for i in range(5)]].to_numpy();bp=d[[f'bids[{i}].price' for i in range(5)]].to_numpy()
            bad=bad|(ap[:,0]<=bp[:,0])|(np.diff(ap,axis=1)<=0).any(axis=1)|(np.diff(bp,axis=1)>=0).any(axis=1)
        invalid+=int(bad.sum())
    lag=np.concatenate(lags)
    receipt.update(rows=rows,invalid_rows=invalid,local_regressions=regress,first_local_timestamp=first,last_local_timestamp=last,active_local_minutes=len(minutes & set(range(1440))),active_event_minutes=len(event_minutes & set(range(1440))),negative_lag_rows=int((lag<0).sum()),lag_us_p99=float(np.quantile(lag,.99)),lag_us_min=int(lag.min()),lag_us_max=int(lag.max()),max_interrow_local_gap_us=maxgap,gzip_parse_crc='PASS')
    receipt['mechanical_gate']=bool(receipt['publisher_md5_match'] and rows>0 and invalid==0 and regress==0 and 0<=receipt['lag_us_p99']<=5_000_000 and (kind=='liquidations' or receipt['active_local_minutes']/1440>=.99))
    (ROOT/f'{sym}_{kind}.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='headers'}),flush=True)
    return receipt

if __name__=='__main__':
    receipts=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(validate,(s,k)):(s,k) for s in ('BTCUSDT','ETHUSDT') for k in KINDS}
        for f in concurrent.futures.as_completed(futures):
            try:receipts.append(f.result())
            except Exception as e:errors.append({'pair':futures[f],'error':repr(e)})
    result={'freeze_commit':'e276595f47d905fab20a09b3dbb5a1722b9e370d','files':receipts,'errors':errors,'mechanical_gate':len(receipts)==6 and not errors and all(r['mechanical_gate'] for r in receipts),'liquidation_continuity':'NOT_ESTABLISHED: normalized CSV has no heartbeat/disconnect/sequence ledger; empty intervals cannot be certified healthy','verdict':'SOURCE_INCOMPLETE','outcomes_joined':0,'protected_holdout_requests':0}
    Path('joint_source_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='files'}),flush=True)
