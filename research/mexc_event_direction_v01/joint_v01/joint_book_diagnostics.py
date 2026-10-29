"""Classify source defects only; no future returns or outcome selection."""
import json,sys
from pathlib import Path
import pandas as pd
import numpy as np
counts={k:0 for k in ('nonfinite','nonpositive','crossed_or_locked','ask_not_strict','bid_not_strict','exchange_time_outside_day','wrong_identity')};badrows=[]
sym=sys.argv[1] if len(sys.argv)>1 else 'BTCUSDT'
assert sym in ('BTCUSDT','ETHUSDT')
start=int(pd.Timestamp('2026-04-01',tz='UTC').timestamp()*1e6);end=start+86400000000
for d in pd.read_csv(f'joint_sources/{sym}_book_snapshot_5.csv.gz',chunksize=100000):
    cols=[f'{s}[{i}].{f}' for i in range(5) for s in ('asks','bids') for f in ('price','amount')]
    vals=d[cols].to_numpy();ap=d[[f'asks[{i}].price' for i in range(5)]].to_numpy();bp=d[[f'bids[{i}].price' for i in range(5)]].to_numpy()
    masks={'nonfinite':~np.isfinite(vals).all(axis=1),'nonpositive':(vals<=0).any(axis=1),'crossed_or_locked':ap[:,0]<=bp[:,0],'ask_not_strict':(np.diff(ap,axis=1)<=0).any(axis=1),'bid_not_strict':(np.diff(bp,axis=1)>=0).any(axis=1),'exchange_time_outside_day':((d.timestamp<start)|(d.timestamp>=end)).to_numpy(),'wrong_identity':((d.exchange!='bybit')|(d.symbol!=sym)).to_numpy()}
    anybad=np.zeros(len(d),dtype=bool)
    for k,m in masks.items():counts[k]+=int(m.sum());anybad|=m
    for pos in np.flatnonzero(anybad):
        badrows.append({'csv_data_row_1based':int(d.index[pos])+1,'timestamp':int(d.iloc[pos].timestamp),'local_timestamp':int(d.iloc[pos].local_timestamp),'reasons':[k for k,m in masks.items() if m[pos]]})
r={'source':f'{sym}_book_snapshot_5.csv.gz','counts':counts,'badrows':badrows,'action':'REJECT_UNCHANGED_SOURCE_GATE; no drops, repairs, threshold relaxation or outcomes'}
Path(f'joint_book_defects_{sym}.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps(r))
