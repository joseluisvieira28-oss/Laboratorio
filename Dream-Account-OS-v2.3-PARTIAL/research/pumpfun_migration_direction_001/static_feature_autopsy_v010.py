#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download

REPO_ID='Slinky21/Pumpfun_Memecoin_Corpus'
STATIC_FEATURES=[
    'seconds_to_graduation','initial_buy_sol','initial_market_cap_sol',
    'dev_buy_pct_corrected','initial_holder_count','initial_top1_pct_corrected',
    'initial_top5_pct_corrected','initial_top10_pct_corrected','initial_gini',
    'creator_past_tokens','creator_past_rugs','launch_snipe_delta_sol'
]
CONCENTRATION={'initial_top1_pct_corrected','initial_top5_pct_corrected','initial_top10_pct_corrected','initial_gini'}

def finite(s):
    return pd.to_numeric(s,errors='coerce').replace([np.inf,-np.inf],np.nan)

def period_stats(g, feature):
    x=finite(g[feature]); y=finite(g['net_return_5m']); m=x.notna() & y.notna()
    z=g.loc[m,[feature,'net_return_5m']].copy()
    if len(z)<40 or z[feature].nunique()<5: return None
    z['positive']=(z.net_return_5m>0).astype(int)
    rho=float(z[feature].corr(z.net_return_5m,method='spearman'))
    try: z['q']=pd.qcut(z[feature],5,labels=False,duplicates='drop')
    except Exception: return None
    if z.q.nunique()<3: return None
    qs=[]
    for q,h in z.groupby('q'):
        v=h.net_return_5m.to_numpy(float)
        s=np.sort(v)
        trimmed=s[1:-1] if len(s)>=5 else s
        qs.append({'q':int(q),'n':int(len(h)),'feature_min':float(h[feature].min()),'feature_max':float(h[feature].max()),
                   'positive_rate':float((v>0).mean()),'mean_net':float(v.mean()),'median_net':float(np.median(v)),
                   'trimmed_mean_net':float(trimmed.mean()),'pnl_1sol_each':float(v.sum()),'max_net':float(v.max()),'min_net':float(v.min())})
    qs=sorted(qs,key=lambda r:r['q'])
    lo,hi=qs[0],qs[-1]
    return {'n':int(len(z)),'spearman_net':rho,'low_quintile':lo,'high_quintile':hi,
            'high_minus_low_positive_rate':hi['positive_rate']-lo['positive_rate'],
            'high_minus_low_median_net':hi['median_net']-lo['median_net'],
            'high_minus_low_trimmed_mean_net':hi['trimmed_mean_net']-lo['trimmed_mean_net'],
            'quintiles':qs}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--outcomes',required=True); ap.add_argument('--data-dir',default='pmd_v010_data'); ap.add_argument('--out',default='pmd_v010_static_feature_autopsy.json'); a=ap.parse_args()
    root=Path(a.data_dir); root.mkdir(parents=True,exist_ok=True)
    tokp=hf_hub_download(repo_id=REPO_ID,repo_type='dataset',filename='tokens.parquet',local_dir=str(root))
    migp=hf_hub_download(repo_id=REPO_ID,repo_type='dataset',filename='migrations.parquet',local_dir=str(root))
    o=pd.read_csv(a.outcomes); t=pd.read_parquet(tokp); m=pd.read_parquet(migp)[['mint','seconds_to_graduation']]
    d=o.merge(t,on='mint',how='left',validate='one_to_one').merge(m,on='mint',how='left',validate='one_to_one',suffixes=('','_mig'))
    if 'seconds_to_graduation_mig' in d.columns: d['seconds_to_graduation']=d['seconds_to_graduation_mig'].combine_first(d.get('seconds_to_graduation'))
    d['anchor_dt']=pd.to_datetime(d['anchor_ts'],utc=True)
    d=d.sort_values(['anchor_dt','mint']).reset_index(drop=True)
    n=len(d); cuts=[0,n//3,(2*n)//3,n]
    d['third']=''; d.loc[cuts[0]:cuts[1]-1,'third']='early'; d.loc[cuts[1]:cuts[2]-1,'third']='middle'; d.loc[cuts[2]:cuts[3]-1,'third']='late'
    out={'lab':'PMD-001','stage':'V010_STATIC_FEATURE_AUTOPSY','exploratory_only':True,'promotion_authority':False,'rows':int(n),
         'feature_policy':'launch/static fields plus seconds_to_graduation only; no post-migration or peak/full-life fields',
         'features':{}}
    for f in STATIC_FEATURES:
        if f not in d.columns: continue
        base=d.copy()
        if f in CONCENTRATION and 'top10_pct_suspect' in base.columns:
            base.loc[base['top10_pct_suspect'].fillna(False),f]=np.nan
        allstat=period_stats(base,f)
        periods={k:period_stats(g,f) for k,g in base.groupby('third')}
        signs=[]
        for k in ['early','middle','late']:
            r=periods.get(k)
            if r is not None:
                x=r['high_minus_low_median_net']; signs.append(1 if x>0 else (-1 if x<0 else 0))
        out['features'][f]={'all':allstat,'thirds':periods,'median_delta_signs':signs,
                            'same_sign_all_thirds':bool(len(signs)==3 and abs(sum(signs))==3)}
    # fixed diagnostic ordering, not a promotion score
    ranking=[]
    for f,r in out['features'].items():
        a0=r.get('all')
        if not a0: continue
        ranking.append({'feature':f,'abs_spearman_net':abs(a0['spearman_net']),
                        'high_minus_low_median_net':a0['high_minus_low_median_net'],
                        'high_minus_low_positive_rate':a0['high_minus_low_positive_rate'],
                        'same_sign_all_thirds':r['same_sign_all_thirds']})
    out['diagnostic_ranking']=sorted(ranking,key=lambda x:(x['same_sign_all_thirds'],x['abs_spearman_net']),reverse=True)
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n')
    print(json.dumps({'stage':out['stage'],'rows':n,'top_diagnostics':out['diagnostic_ranking'][:12]},indent=2))
if __name__=='__main__': main()
