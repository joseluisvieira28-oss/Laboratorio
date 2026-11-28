from experiment import OUT,ROOT,ASSETS,F
import numpy as np
import pandas as pd
def evaluate():
    m=pd.read_csv(OUT/'metrics.csv')
    base=m.query('capital == 10000 and case == "base"')
    t=pd.read_csv(OUT/'trades.csv')
    eq=pd.read_csv(OUT/'equity.csv.gz')
    eq=eq.groupby(['case','date','year','system']).equity.sum().unstack('system')
    daily=eq.groupby(level=['case','year']).diff().fillna(eq-10000)
    # 1096 paired daily observations, same bootstrap indices for all systems
    n=len(daily.loc['base']);rng=np.random.default_rng(107)
    idx=(rng.integers(0,n,(2000,(n+29)//30,1))+np.arange(30))%n
    idx=idx.reshape(2000,-1)[:,:n]
    ci=[]
    for sys,ref in [(s,'A') for s in F+['H07','B']]+[('SIDE','MR'),('C','B'),('A','D'),('H07','D'),('B','D'),('C','D')]:
        delta=(daily.loc['base',sys]-daily.loc['base',ref]).values
        vals=delta[idx].sum(axis=1)
        ci.append([sys,ref,delta.sum(),*np.quantile(vals,[.05/9,.025,.975]),np.mean(vals<=0)])
    pd.DataFrame(ci,columns=['system','ref','delta','lower_adjusted','lo95','hi95','bootstrap_fraction_nonpositive']).to_csv(OUT/'uncertainty.csv',index=False)
    g=m.groupby(['case','capital','system'])
    summ=g[['opportunities','trades','rejected','wins','gain','loss','net','gross','fees','friction','turnover','dust','hours_active','hours']].sum()
    summ['win_pct']=100*summ.wins/summ.trades
    summ['avg_win']=summ.gain/summ.wins
    summ['avg_loss']=summ.loss/(summ.trades-summ.wins)
    summ['expectancy']=summ.net/summ.trades
    summ['pf']=-summ.gain/summ.loss
    summ['mean_annual_pct']=100*summ.net/summ.index.get_level_values('capital')/3
    summ['exposure_pct']=100*summ.hours_active/summ.hours
    summ['turnover_per_capital']=summ.turnover/summ.index.get_level_values('capital')
    summ['net_after_36_USDT_overhead']=summ.net-36
    summ.to_csv(OUT/'comparator.csv')
    risk=[]
    for (case,sys),s in daily.stack().groupby(level=['case','system']):
        v=s.values; path=10000+np.cumsum(v);pmax=np.maximum.accumulate(np.r_[10000,path])[1:]
        risk.append([case,sys,(1-path/pmax).max(),np.sqrt(365)*v.mean()/v.std() if v.std() else None,np.sqrt(365)*v.mean()/np.sqrt(np.mean(np.minimum(0,v)**2)) if min(v)<0 else None])
    pd.DataFrame(risk,columns=['case','system','daily_additive_dd','annualized_sharpe_fixed_budget','annualized_sortino_fixed_budget']).to_csv(OUT/'risk.csv',index=False)
    annual=base.pivot_table(index='system',columns='year',values='net',aggfunc='sum')
    annual.to_csv(OUT/'annual.csv')
    base.pivot_table(index='system',columns='asset',values='net',aggfunc='sum').to_csv(OUT/'by_asset.csv')
    t.groupby(['system','regime_score']).net.agg(['count','sum','mean']).to_csv(OUT/'by_regime.csv')
    rows=[]
    for sys,v in t.groupby('system'):
        top=v.net.nlargest(3).sum()
        rows.append([sys,top,top/v.net.sum(),v.net.sum()-top])
    pd.DataFrame(rows,columns=['system','top3','top3_over_net','net_after_removing_top3']).to_csv(OUT/'concentration.csv',index=False)
    # Same risk-budget passive price exposure, refreshed annually; cash residual.
    rows=[]
    for a in ASSETS:
        d=pd.read_pickle(ROOT/'cache'/(a+'.pkl'))
        for yr in [2023,2024,2025]:
            y=d.loc[str(yr)]
            qty=(10000/3*.20)/(y.open.iloc[0]*1.0005)
            buy=y.open.iloc[0]*1.0005;sell=y.close.iloc[-1]*.9995
            rows.append([a,yr,qty*(sell-buy-.001*(buy+sell))])
    pd.DataFrame(rows,columns=['asset','year','passive_net']).to_csv(OUT/'passive.csv',index=False)
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,4))
    for sys in ['A','B','C','D','H07']:
        s=daily.loc['base',sys].droplevel('year')
        ax.plot(pd.to_datetime(s.index),10000+s.cumsum(),label=sys,linewidth=1.4)
    ax.legend(ncol=5);ax.set_ylabel('USDT');ax.set_title('Saldo inicial 10 000 · PnL diário somado · orçamento reposto em janeiro')
    fig.tight_layout();fig.savefig(OUT/'equity.png',dpi=135);plt.close(fig)
if __name__=='__main__':evaluate()
