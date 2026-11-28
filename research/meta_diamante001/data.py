"""Fetch only frozen historical spot archives. Verify publisher SHA and hourly grid."""
import concurrent.futures as cf
import hashlib, io, subprocess, zipfile
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'cache'
CACHE.mkdir(exist_ok=True)
ASSETS=['BTC','SOL','BNB']
def month(args):
    asset,date=args
    name=f'{asset}USDT-1h-{date:%Y-%m}.zip'
    url=f'https://data.binance.vision/data/spot/monthly/klines/{asset}USDT/1h/{name}'
    path=CACHE/name
    for suffix in ['','.CHECKSUM']:
        dest=Path(str(path)+suffix)
        if not dest.exists():
            subprocess.run(['curl','-fsSL','--max-time','30','--retry','3',url+suffix,'-o',str(dest)+'.tmp'],check=True)
            Path(str(dest)+'.tmp').replace(dest)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==Path(str(path)+'.CHECKSUM').read_text().split()[0]
    with zipfile.ZipFile(path) as archive:
        frame=pd.read_csv(io.BytesIO(archive.read(archive.namelist()[0])),header=None,usecols=range(6),names=['time','open','high','low','close','volume'])
    frame.index=pd.to_datetime(frame.pop('time'),unit='us' if date.year==2025 else 'ms',utc=True)
    return asset,url,digest,frame
if __name__=='__main__':
    jobs=[(a,d) for a in ASSETS for d in pd.date_range('2021-01-01','2025-12-01',freq='MS')]
    with cf.ThreadPoolExecutor(12) as pool: results=list(pool.map(month,jobs))
    pd.DataFrame([(a,u,h,len(f)) for a,u,h,f in results],columns=['asset','url','sha256','rows']).to_csv(ROOT/'out/sources.csv',index=False)
    for a in ASSETS:
        df=pd.concat([f for asset,_,_,f in results if asset==a])
        expected=pd.date_range('2021-01-01','2026-01-01',inclusive='left',freq='h',tz='UTC')
        assert df.index.is_unique and df.index.is_monotonic_increasing
        print(a,len(df),'missing',len(expected.difference(df.index)),flush=True)
        df.to_pickle(CACHE/(a+'.pkl'))
