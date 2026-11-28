"""Offline hourly spot transfer. All timestamps are UTC bar OPEN labels."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from data import ASSETS, ROOT
OUT=ROOT/'out'
F=['R01','R02','R03','R04','R05']
def wilder(s,n):
    v=s.dropna().copy()
    if len(v)<n:return s*np.nan
    v.iloc[n-1]=v.iloc[:n].mean()
    return v.iloc[n-1:].ewm(alpha=1/n,adjust=False).mean().reindex(s.index)
def features(df):
    d=df.copy();c=d.close;h=d.high;l=d.low
    ma=c.rolling(20).mean();sd=c.rolling(20).std(ddof=0)
    u=c.diff();up=wilder(u.clip(lower=0),14);down=wilder((-u).clip(lower=0),14)
    rsi=100-100/(1+up/down); lower=c<ma-2*sd
    z=(c-ma)/sd
    d['cv']=(((rsi<30).astype(int)+(z< -2).astype(int)+lower.astype(int)+(d.volume>d.volume.rolling(20).mean()).astype(int))>=3)&(c>c.rolling(200).mean())
    d['mr']=(rsi<30)&lower;d['reclaim']=c>=ma
    du=h.diff();dd=-l.diff()
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    atr=wilder(tr,14)
    pos=wilder(du.where((du>dd)&(du>0),0),14)/atr
    neg=wilder(dd.where((dd>du)&(dd>0),0),14)/atr
    d['R01']=100*wilder((pos-neg).abs()/(pos+neg),14)>=25
    slow=c.rolling(200).mean()
    d['R02']=(c>slow)&(slow>slow.shift(24))
    rv=np.log(c).diff().rolling(24).std()
    d['R03']=rv<rv.shift().rolling(720).quantile(.8)
    d['R04']=c.diff(20).abs()/u.abs().rolling(20).sum()>=.30
    d['ready']=rv.shift().rolling(720).count().eq(720)&slow.shift(24).notna()
    return d
def candidates(df,asset,year,slip,delay):
    y=df.loc[str(year)]
    o,h,l,c,rec=[y[k].to_numpy() for k in ['open','high','low','close','reclaim']]
    n=len(y);rows=[]
    for lane in ['cv','mr']:
        for i in np.flatnonzero((y[lane]&y.ready).to_numpy()):
            j=i+1+delay
            if j>=n:continue
            entry=o[j]*(1+slip);stop=entry*.96;peak=entry
            reason='year_end';raw=c[-1];k=n-1
            for k in range(j,n):
                if lane=='mr' and k>j+delay and rec[k-1-delay]:
                    raw=o[k];reason='reclaim';break
                if l[k]<=stop:
                    raw=min(o[k],stop);reason='stop';break
                if lane=='cv':
                    peak=max(peak,h[k])
                    stop=max(entry*.96,peak*.88) if c[k]>=entry*1.05 else entry*.96
            sell=raw*(1-slip)
            ret=(sell-entry-.001*(entry+sell))/entry
            rows.append((asset,year,lane,i,j,k,o[j],raw,entry,sell,ret,reason))
    t=pd.DataFrame(rows,columns='asset year lane sig enter exit raw_buy raw_sell buy sell ret reason'.split())
    t=t.astype({k:"int64" for k in ["sig","enter","exit"]})
    for f in F:t[f]=y[f].to_numpy()[t.sig]
    t['score']=t[F].sum(axis=1)
    t['oldscore']=y[F].sum(axis=1).shift(168).to_numpy()[t.sig]
    t['oldadx']=y.R01.astype(float).shift(168).to_numpy()[t.sig]
    for key in ['sig','enter','exit']:t[key+'_utc']=y.index[t[key]]
    return t.sort_values(['sig','lane'])
def independent(t):
    parts=[]
    for _,group in t.groupby(['asset','year','lane']):
        end=-1
        for r in group.itertuples():
            if r.sig>=end:
                parts.append(r.Index);end=r.exit
    return t.loc[parts]
def select(t,sys):
    cv=t.lane.eq('cv');mr=~cv
    if sys in F:return cv&t[sys]
    if sys=='A':return cv
    if sys=='MR':return mr
    if sys=='SIDE':return mr&~t.R01
    if sys=='H07':return cv&(t.score>=3)
    if sys=='B':return (cv&(t.score>=3))|(mr&(t.score<3)&~t.R01)
    if sys=='STALE':return (cv&(t.oldscore>=3))|(mr&(t.oldscore<3)&t.oldadx.eq(0))
    if sys=='C':return t.pred.gt(0)
    return cv&False
def simulate(y,t,sys,capital,asset,year,case):
    initial=capital/3;cash=initial;end=-1;curve=np.full(len(y),initial)
    eligible=select(t,sys)
    trades=[];fills=[];decision=[];exposure=0;last=0
    opp=t if sys in ['B','C','D','STALE'] else t[t.lane.eq('mr' if sys in ['SIDE','MR'] else 'cv')]
    detailed=capital==10000 and case=='base'
    for r in (t if detailed else t.loc[eligible]).itertuples():
        why='accept'
        if not eligible.at[r.Index]:why='filter'
        elif r.sig<end:why='occupied'
        elif cash*.2<10:why='min_notional'
        if detailed:decision.append((sys,asset,r.sig_utc,r.lane,r.score,r.pred,why))
        if why!='accept':continue
        q=cash*.2/r.buy
        fee=q*(r.buy+r.sell)*.001;fric=q*(r.buy-r.raw_buy+r.raw_sell-r.sell)
        net=q*(r.sell-r.buy)-fee
        curve[last:r.enter]=cash
        curve[r.enter:r.exit]=cash+q*(y[r.enter:r.exit]-r.buy)-q*r.buy*.001
        exposure+=r.exit-r.enter+1
        trades.append((net,q*(r.raw_sell-r.raw_buy),fee,fric,q*(r.buy+r.sell),int(q*r.sell<10)))
        if detailed:fills.append((sys,asset,year,r.lane,r.sig_utc,r.enter_utc,r.exit_utc,r.buy,r.sell,q,fee,fric,net,r.score,r.reason))
        cash+=net;end=r.exit;last=end
    curve[last:]=cash
    a=np.array(trades).reshape(-1,6);win=a[:,0]>0;loss=a[:,0]<0
    summary=[case,capital,sys,asset,year,len(opp),len(a),len(opp)-len(a),win.sum(),a[win,0].sum(),a[loss,0].sum(),*a.sum(axis=0),exposure,len(y),np.max(1-curve/np.maximum.accumulate(np.r_[initial,curve])[1:])]
    return summary,curve,fills,decision
def run():
    dfs={a:features(pd.read_pickle(ROOT/'cache'/(a+'.pkl'))) for a in ASSETS}
    for a,d in dfs.items():
        d['R05']=d.R02&dfs['BTC'].R02.reindex(d.index).fillna(False)
        assert (d.index.year<=2025).all()
    systems=['A','MR','SIDE',*F,'H07','B','C','STALE','D']
    metrics=[];curves=[];trades=[];decisions=[];modelrows=[]
    for case,slip,delay in [('base',.0005,0),('stress',.0015,0),('manual',.0025,1)]:
        ts=pd.concat([candidates(d,a,year,slip,delay) for a,d in dfs.items() for year in range(2021,2026)],ignore_index=True)
        if case=='base':train=independent(ts)
        ts['pred']=np.nan
        for year in range(2023,2026):
            for lane in ['cv','mr']:
                tr=train[(train.lane==lane)&(train.exit_utc<pd.Timestamp(f'{year}-01-01',tz='UTC')-pd.Timedelta(hours=168))]
                te=(ts.year==year)&(ts.lane==lane)
                model=RandomForestRegressor(n_estimators=100,max_depth=3,min_samples_leaf=15,random_state=107,n_jobs=1).fit(tr[F],tr.ret)
                ts.loc[te,'pred']=model.predict(ts.loc[te,F])
                modelrows.append([case,year,lane,len(tr),tr.exit_utc.max()])
        if case=='base':ts.to_csv(OUT/'opportunities.csv.gz',index=False)
        for (a,year),t in ts[ts.year>=2023].groupby(['asset','year']):
            t=t.sort_values(['sig','pred','lane'],ascending=[True,False,True])
            y=dfs[a].loc[str(year),'close']
            for cap in [100,250,500,1000,5000,10000]:
                for sys in systems:
                    s,curve,log,dec=simulate(y.to_numpy(),t,sys,cap,a,year,case)
                    metrics.append(s);trades.extend(log);decisions.extend(dec)
                    if cap==10000:
                        daily=pd.Series(curve,index=y.index).resample('D').last()
                        curves.append(pd.DataFrame(dict(date=daily.index,asset=a,year=year,system=sys,case=case,equity=daily.values)))
    for name,rows,cols in [
        ('metrics.csv',metrics,'case capital system asset year opportunities trades rejected wins gain loss net gross fees friction turnover dust hours_active hours drawdown'),
        ('trades.csv',trades,'system asset year lane signal_utc entry_utc exit_bar_utc buy sell qty fee friction net regime_score reason'),
        ('decisions.csv.gz',decisions,'system asset signal_utc lane regime_score model_expected_net_fraction reason'),
        ('training.csv',modelrows,'case test_year lane n last_exit')]:
        pd.DataFrame(rows,columns=cols.split()).to_csv(OUT/name,index=False)
    pd.concat(curves).to_csv(OUT/'equity.csv.gz',index=False)
if __name__=='__main__':run()
