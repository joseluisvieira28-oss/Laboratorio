"""Fixed-quantity attribution on regenerated upstream ledgers."""
from experiment import ROOT,OUT,features,F
import pandas as pd
import numpy as np
def market(asset,tf):
    rows=[]
    for p in sorted((ROOT/'futures_cache').glob(f'{asset}USDT-5m-*.zip')):
        d=pd.read_csv(p,header=None,usecols=list(range(6)),names=['ts','open','high','low','close','volume'])
        d=d[pd.to_numeric(d.ts,errors='coerce').notna()].astype(float)
        d.index=pd.to_datetime(d.pop('ts').astype('int64'),unit='ms',utc=True);rows.append(d)
    d=pd.concat(rows).resample(tf,label='right',closed='left').agg(dict(open='first',high='max',low='min',close='last',volume='sum'))
    return features(d)
def main():
    rows=[];tables=[]
    for asset,tf,folder in [('BTC','1h','btc'),('SOL','1h','SOL'),('BNB','4h','BNB')]:
        d=market(asset,tf);d['R05']=d.R02&market('BTC',tf).R02
        p=OUT/'legacy'/folder/(tf+'_BASE_TRADES.csv')
        t=pd.read_csv(p)
        # Legacy orders fill 5 minutes after the confirmed strategy-timeframe close.
        t.index=pd.to_datetime(t.open_t,unit='ms',utc=True)-pd.Timedelta(minutes=5)
        t=t.join(d[F+['ready']])
        assert t.ready.notna().all()
        t['top3']=t.net_pnl.rank(ascending=False)<=3
        t['asset']=asset;t['tf']=tf
        tables.append(t)
        for gate in ['ALL',*F,'H07']:
            keep=t.ready.copy() if gate=='ALL' else t.ready&(t[F].sum(axis=1)>=3 if gate=='H07' else t[gate])
            for year in [0,*sorted(t.exit_year.unique())]:
                v=t[(t.exit_year==year) if year else np.ones(len(t),dtype=bool)]
                s=v[keep.reindex(v.index)]
                rows.append([asset,tf,year,gate,len(v),int((~v.ready).sum()),len(s),int((s.net_pnl<0).sum()),int(s.top3.sum()),s.net_pnl.sum(),v.net_pnl.sum()])
    pd.concat(tables).to_csv(OUT/'original_entries.csv')
    pd.DataFrame(rows,columns='asset tf year gate original_n insufficient_warmup retained losses top3_kept net_kept original_net'.split()).to_csv(OUT/'original_regimes.csv',index=False)
if __name__=='__main__':main()
