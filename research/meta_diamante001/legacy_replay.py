"""Run pinned upstream historical engines with a verified local transport cache.
Supply directory built with git archive $(cat out/legacy_sha.txt), as in README.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,sys,os,json
import pandas as pd
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(sys.argv[1]).resolve()))
from research.btc_convex_multifront_v01 import retrospective_diagnostic as src
from research.btc_convex_timeframe_matrix_20261013 import matrix
from research.convex_8alt_common_2023_25 import common_3yr as alt
dest=ROOT/'out/legacy';dest.mkdir(exist_ok=True)
cache=ROOT/'futures_cache';cache.mkdir(exist_ok=True)
def get(url,limit):
    p=cache/url.rsplit('/',1)[1]
    if not p.exists():
        subprocess.run(['curl','-fsSL','--retry','3','--max-time','45',url,'-o',str(p)+'.tmp'],check=True)
        Path(str(p)+'.tmp').replace(p)
    data=p.read_bytes()
    if len(data)>limit: raise ValueError('size')
    return data
def collect_asset(asset):
    start='2020-11' if asset=='BTC' else '2022-11'
    urls=[]
    for d in pd.period_range(start,'2025-12',freq='M'):
        for k in ['1h','5m','fundingRate']:
            if k=='fundingRate' and str(d)<('2021-01' if asset=='BTC' else '2023-01'):continue
            rel=f'fundingRate/{asset}USDT' if k=='fundingRate' else f'klines/{asset}USDT/{k}'
            u=f'{src.BASE}/{rel}/{asset}USDT-{k}-{d}.zip'
            urls.extend([u,u+'.CHECKSUM'])
    with ThreadPoolExecutor(20) as pool:list(pool.map(lambda u:get(u,25_000_000),urls))
src.fetch=get
for asset in sys.argv[2:]:
    collect_asset(asset)
    if asset=='BTC':
        src.OUT=dest/'scalp';src.main()
        matrix.OUT=dest/'btc';matrix.main()
    else:
        out=dest/asset;out.mkdir(exist_ok=True)
        sys.argv=['common','--symbol',asset+'USDT','--output-dir',str(out)]
        alt.main()
