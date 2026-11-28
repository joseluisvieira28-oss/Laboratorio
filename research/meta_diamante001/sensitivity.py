"""Post-result adverse missing-bar and concentration checks; never used for selection."""
from experiment import *
def main():
    ds={a:features(pd.read_pickle(ROOT/'cache'/(a+'.pkl'))) for a in ASSETS}
    rows=[]
    for a,d in ds.items():
        d['R05']=d.R02&ds['BTC'].R02
        gap=d.index.to_series().diff()!=pd.Timedelta(hours=1)
        # Exclude new entries until 744 uninterrupted observations after any gap.
        d['ready'] &= (~gap).rolling(745).sum().eq(745)
        for year in [2023,2024,2025]:
            t=candidates(d,a,year,.0005,0);t['pred']=0.;y=d.loc[str(year),'close']
            for sys in ['A','H07','B']:
                s,_,logs,_=simulate(y.values,t,sys,10000,a,year,'base')
                crossed=sum(any((gap.index[gap]>f[5])&(gap.index[gap]<=f[6])) for f in logs)
                rows.append([a,year,sys,s[12],s[6],crossed])
    pd.DataFrame(rows,columns='asset year system net trades crosses_missing_hour'.split()).to_csv(OUT/'gap_sensitivity.csv',index=False)
    data=pd.read_csv(OUT/'equity.csv.gz').query('case=="base"').groupby(['date','year','system']).equity.sum().unstack('system')
    delta=data.groupby(level='year').diff().fillna(data-10000)
    rows=[]
    for block in [7,60,90]:
        n=len(delta);rng=np.random.default_rng(107)
        ids=(rng.integers(0,n,(2000,(n+block-1)//block,1))+np.arange(block))%n
        for s,r in [('H07','A'),('B','A'),('C','B')]:
            boot=(delta[s]-delta[r]).values[ids.reshape(2000,-1)[:,:n]].sum(axis=1)
            rows.append([block,s,r,*np.quantile(boot,[.025,.975])])
    pd.DataFrame(rows,columns='block_days system ref lo95 hi95'.split()).to_csv(OUT/'block_sensitivity.csv',index=False)
if __name__=='__main__':main()
