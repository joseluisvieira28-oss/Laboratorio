#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import duckdb
from huggingface_hub import hf_hub_download

REPO_ID='Slinky21/Pumpfun_Memecoin_Corpus'
BASE_FIELDS=['buy_pressure','net_flow_sol','trade_count','unique_wallets','delta_curve_pct','price_return_pct','avg_trade_sol','median_trade_sol','largest_buy_sol','largest_sell_sol','buy_volume_sol','sell_volume_sol','curve_pct_depleted_eob','buy_count','sell_count']

def period_stats(g, feature):
    x=pd.to_numeric(g[feature],errors='coerce').replace([np.inf,-np.inf],np.nan); y=pd.to_numeric(g.net_return_5m,errors='coerce')
    z=pd.DataFrame({'x':x,'y':y}).dropna()
    if len(z)<50 or z.x.nunique()<5:return None
    rho=float(z.x.corr(z.y,method='spearman'))
    try:z['q']=pd.qcut(z.x,5,labels=False,duplicates='drop')
    except Exception:return None
    if z.q.nunique()<3:return None
    qs=[]
    for q,h in z.groupby('q'):
        v=h.y.to_numpy(float); s=np.sort(v); tr=s[1:-1] if len(s)>=5 else s
        qs.append({'q':int(q),'n':int(len(h)),'positive_rate':float((v>0).mean()),'mean_net':float(v.mean()),'median_net':float(np.median(v)),'trimmed_mean_net':float(tr.mean()),'pnl_1sol_each':float(v.sum()),'max_net':float(v.max()),'min_net':float(v.min())})
    qs=sorted(qs,key=lambda r:r['q']); lo,hi=qs[0],qs[-1]
    return {'n':int(len(z)),'spearman_net':rho,'low_quintile':lo,'high_quintile':hi,'high_minus_low_positive_rate':hi['positive_rate']-lo['positive_rate'],'high_minus_low_median_net':hi['median_net']-lo['median_net'],'high_minus_low_trimmed_mean_net':hi['trimmed_mean_net']-lo['trimmed_mean_net'],'quintiles':qs}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--outcomes',required=True); ap.add_argument('--data-dir',default='pmd_v011_data'); ap.add_argument('--out',default='pmd_v011_flow_feature_autopsy.json'); a=ap.parse_args()
    root=Path(a.data_dir);root.mkdir(parents=True,exist_ok=True)
    sp=hf_hub_download(repo_id=REPO_ID,repo_type='dataset',filename='snapshots.parquet',local_dir=str(root))
    o=pd.read_csv(a.outcomes); o['anchor_dt']=pd.to_datetime(o.anchor_ts,utc=True); o=o.sort_values(['anchor_dt','mint']).reset_index(drop=True)
    con=duckdb.connect(':memory:'); con.register('outcomes',o[['mint','anchor_dt']])
    spq=str(Path(sp).resolve()).replace("'","''")
    con.execute(f"CREATE VIEW s AS SELECT * FROM read_parquet('{spq}')")
    rows=[]
    for sec,cap in [(60,600),(300,1800)]:
        q=f'''SELECT * EXCLUDE(rn) FROM (
          SELECT o.mint,o.anchor_dt,s.bucket_start,s.bucket_seconds,{','.join('s.'+f for f in BASE_FIELDS)},
                 date_diff('second',s.bucket_start + s.bucket_seconds*INTERVAL 1 SECOND,o.anchor_dt) AS stale_seconds,
                 row_number() over(partition by o.mint order by s.bucket_start desc) rn
          FROM outcomes o JOIN s USING(mint)
          WHERE s.bucket_seconds={sec}
            AND s.bucket_start + s.bucket_seconds*INTERVAL 1 SECOND <= o.anchor_dt
            AND s.bucket_start + s.bucket_seconds*INTERVAL 1 SECOND >= o.anchor_dt - INTERVAL {cap} SECOND
        ) WHERE rn=1'''
        h=con.execute(q).fetchdf(); h['window']=sec; rows.append(h)
    snap=pd.concat(rows,ignore_index=True)
    wide=o.copy()
    for sec in [60,300]:
        h=snap[snap.window==sec].copy().set_index('mint')
        cols=BASE_FIELDS+['stale_seconds']
        h=h[cols].rename(columns={c:f'{c}_{sec}' for c in cols})
        wide=wide.merge(h,left_on='mint',right_index=True,how='left',validate='one_to_one')
    eps=1e-12
    for sec in [60,300]:
        if f'trade_count_{sec}' in wide:
            wide[f'wallet_per_trade_{sec}']=wide[f'unique_wallets_{sec}']/wide[f'trade_count_{sec}'].clip(lower=1)
            wide[f'count_balance_{sec}']=(wide[f'buy_count_{sec}']-wide[f'sell_count_{sec}'])/wide[f'trade_count_{sec}'].clip(lower=1)
            den=(wide[f'buy_volume_sol_{sec}']+wide[f'sell_volume_sol_{sec}']).abs()+eps
            wide[f'volume_balance_{sec}']=(wide[f'buy_volume_sol_{sec}']-wide[f'sell_volume_sol_{sec}'])/den
    pairs=['net_flow_sol','trade_count','unique_wallets','buy_volume_sol','sell_volume_sol','delta_curve_pct']
    for b in pairs:
        wide[f'{b}_accel_60_vs_300']=wide[f'{b}_60']-wide[f'{b}_300']/5.0
    n=len(wide); cuts=[0,n//3,(2*n)//3,n]; wide['third']=''; wide.loc[:cuts[1]-1,'third']='early'; wide.loc[cuts[1]:cuts[2]-1,'third']='middle'; wide.loc[cuts[2]:,'third']='late'
    features=[]
    for c in wide.columns:
        if c.endswith('_60') or c.endswith('_300') or c.endswith('_accel_60_vs_300'): features.append(c)
    features=[c for c in features if c not in {'stale_seconds_60','stale_seconds_300'}]
    out={'lab':'PMD-001','stage':'V011_FLOW_FEATURE_AUTOPSY','exploratory_only':True,'promotion_authority':False,'rows':int(n),
         'source_rule':'latest complete 60s bucket ending <=T0 and no older than 600s; latest complete 300s bucket ending <=T0 and no older than 1800s','coverage':{'bucket60':int(wide['buy_pressure_60'].notna().sum()),'bucket300':int(wide['buy_pressure_300'].notna().sum())},'features':{}}
    ranking=[]
    for f in features:
        allstat=period_stats(wide,f); periods={k:period_stats(g,f) for k,g in wide.groupby('third')}
        signs=[]
        for k in ['early','middle','late']:
            r=periods.get(k)
            if r is not None:
                x=r['high_minus_low_median_net']; signs.append(1 if x>0 else(-1 if x<0 else 0))
        same=bool(len(signs)==3 and abs(sum(signs))==3)
        out['features'][f]={'all':allstat,'thirds':periods,'median_delta_signs':signs,'same_sign_all_thirds':same}
        if allstat: ranking.append({'feature':f,'abs_spearman_net':abs(allstat['spearman_net']),'spearman_net':allstat['spearman_net'],'high_minus_low_median_net':allstat['high_minus_low_median_net'],'high_minus_low_positive_rate':allstat['high_minus_low_positive_rate'],'same_sign_all_thirds':same})
    out['diagnostic_ranking']=sorted(ranking,key=lambda x:(x['same_sign_all_thirds'],x['abs_spearman_net']),reverse=True)
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n')
    print(json.dumps({'stage':out['stage'],'coverage':out['coverage'],'top_diagnostics':out['diagnostic_ranking'][:15]},indent=2))
if __name__=='__main__':main()
