"""Replay frozen rules only on post-activation bars; open marks are provisional."""
import itertools,json,sys
import pandas as pd,numpy as np
from sklearn.ensemble import RandomForestRegressor
from experiment import ROOT,OUT,ASSETS,F,features,candidates,independent,simulate
from shadow import FENCE
MODEL=ROOT/'forward_model.json'
def fit():
    data=pd.read_csv(OUT/'opportunities.csv.gz',parse_dates=['exit_utc'])
    tr=independent(data)
    grid=pd.DataFrame(itertools.product([False,True],repeat=5),columns=F)
    model={}
    for lane in ['cv','mr']:
        sub=tr[(tr.lane==lane)&(tr.exit_utc<pd.Timestamp('2025-12-25',tz='UTC'))]
        rf=RandomForestRegressor(n_estimators=100,max_depth=3,min_samples_leaf=15,random_state=107,n_jobs=1).fit(sub[F],sub.ret)
        model[lane]={''.join(str(int(v)) for v in state):float(p) for state,p in zip(grid.values,rf.predict(grid))}
    MODEL.write_text(json.dumps(model,sort_keys=True,indent=2))
def score():
    files=sorted((ROOT/'forward').glob('bars-*.json'))
    if not files:return print('COLD_START; no completed day since activation')
    raw=[json.loads(p.read_text()) for p in files]; dfs={}
    for a in ASSETS:
        rows=[r for day in raw for r in day[a+'USDT']]
        d=pd.DataFrame([r[:6] for r in rows],columns=['time','open','high','low','close','volume'])
        d.index=pd.to_datetime(d.pop('time'),unit='ms',utc=True)
        expect=pd.date_range(pd.to_datetime(FENCE,unit='ms',utc=True),d.index[-1],freq='h')
        if not d.index.equals(expect):raise RuntimeError('incomplete source coverage')
        dfs[a]=features(d.astype(float))
    m=json.loads(MODEL.read_text());report=[]
    for a,d in dfs.items():
        d['R05']=d.R02&dfs['BTC'].R02
        for year in sorted(set(d.index.year)-{2026}):
            y=d.loc[str(year),'close'];t=candidates(d,a,year,.0005,0)
            if len(t)==0:continue
            t['pred']=[m[r.lane][''.join(str(int(getattr(r,f))) for f in F)] for r in t.itertuples()]
            t=t.sort_values(['sig','pred','lane'],ascending=[True,False,True])
            for sysname in ['A','B','C','D','H07']:
                s,curve,fills,_=simulate(y.to_numpy(),t,sysname,10000,a,year,'base')
                complete=y.index[-1]==pd.Timestamp(f'{year}-12-31 23:00',tz='UTC')
                report.append(dict(year=year,asset=a,system=sysname,complete=complete,net_mark_less_exit_cost=s[12],
                                   closed=sum(1 for f in fills if complete or f[-1]!='year_end'),
                                   provisional_open=sum(1 for f in fills if not complete and f[-1]=='year_end')))
    print(json.dumps(report,indent=1) if report else 'WARMUP; first scored hour 2027-01-01 UTC')
if __name__=='__main__':
    if sys.argv[1:]==['--freeze-model']:fit()
    else:score()
