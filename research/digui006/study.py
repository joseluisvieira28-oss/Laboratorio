#!/usr/bin/env python3
"""DIGUI-006 independent predictive screening: no trading, signing or keys."""
import hashlib, io, json, sys, urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

COMMIT="7070d00e1e4492f8604d988549d91785cc5f43f7"
URL=f"https://raw.githubusercontent.com/ian05012/solana-memecoin-dataset/{COMMIT}/data/tokens.parquet"
BASE=['time_since_launch_sec','market_cap_usd','liquidity_usd','volume_h24',
 'price_change_1h','price_change_6h','unique_buyers','unique_sellers',
 'active_wallets','buy_usd_1h','sell_usd_1h','net_flow_usd','trade_buy_sell_ratio']
STRUCT=['holder_count','top10_holder_pct','dev_remaining_pct','rat_position_pct',
 'cluster_count','cluster_max_pct','cluster_top3_pct','bundler_pct_holders',
 'fresh_wallet_pct','insider_pct_holders','sniper_pct_holders',
 'insider_cluster_size','insider_holding_ratio','bundler_ratio']
SMART_UNAUDITED=['smart_money_count','smart_money_pct','smart_concurrent_15m',
 'smart_entry_rec','crew_cohesion','known_smart_count','known_insider_count',
 'smart_buy_1h','early_smart_ratio']
FORBIDDEN=['max_return_1h','max_return_6h','max_return_24h','max_return_3d',
 'reaches_2x','runner_peak_x','staged_exit_return','scalp_exit_return',
 'close_return_1h','mdd_from_peak','time_to_peak_sec']

def load(source=None):
    if source is None:
        with urllib.request.urlopen(URL,timeout=120) as response:
            raw=response.read()
    else:
        raw=Path(source).read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    df=pd.read_parquet(io.BytesIO(raw))
    must={'token_address','captured_at','reaches_2x'}
    if not must<=set(df): raise ValueError(f'Missing: {sorted(must-set(df))}')
    original=len(df)
    df['captured_at']=pd.to_datetime(df.captured_at,utc=True,errors='coerce')
    df=df.dropna(subset=['token_address','captured_at']).copy()
    df=df.sort_values(['captured_at','token_address']).drop_duplicates('token_address',keep='first')
    target=df.reaches_2x.astype(str).str.lower().map({'true':1,'false':0,'1':1,'0':0,'1.0':1,'0.0':0})
    df=df.loc[target.notna()].copy()
    df['target']=target.loc[target.notna()].astype(int)
    if len(df)<300:raise ValueError('Too few unique labelled tokens')
    return df.reset_index(drop=True),{'sha256':digest,'original_snapshots':int(original),
      'unique_labelled_tokens':int(len(df)),'start':str(df.captured_at.min()),
      'end':str(df.captured_at.max()),'base_rate':float(df.target.mean())}

def split(df):
    df=df.sort_values('captured_at').reset_index(drop=True)
    cut1=df.captured_at.iloc[int(len(df)*.6)]
    cut2=df.captured_at.iloc[int(len(df)*.8)]
    embargo=pd.Timedelta(hours=24)
    tr=df[df.captured_at<cut1-embargo].copy()
    va=df[(df.captured_at>=cut1)&(df.captured_at<cut2-embargo)].copy()
    te=df[df.captured_at>=cut2].copy()
    if min(len(tr),len(va),len(te))<100:raise ValueError('Tiny fold')
    assert tr.captured_at.max()+embargo<va.captured_at.min()
    assert va.captured_at.max()+embargo<te.captured_at.min()
    return (tr,va,te),{'training_cut':str(cut1),'testing_cut':str(cut2),'embargo_hours':24}

def choose(train,names):
    assert set(names).isdisjoint(FORBIDDEN)
    return [n for n in names if n in train and pd.to_numeric(train[n],errors='coerce').notna().sum()>=100]

def scores(train,ev,cols):
    def x(df):return df[cols].apply(pd.to_numeric,errors='coerce').replace([np.inf,-np.inf],np.nan)
    m=make_pipeline(SimpleImputer(strategy='median',keep_empty_features=True),
      RobustScaler(),LogisticRegression(max_iter=800,random_state=17))
    m.fit(x(train),train.target)
    return m.predict_proba(x(ev))[:,1]

def measures(y,p):
    y=np.asarray(y,dtype=int);p=np.asarray(p,dtype=float)
    top=max(1,int(np.ceil(len(y)*.1)))
    return {'n':len(y),'positive':int(y.sum()),'prevalence':float(y.mean()),
      'ap':float(average_precision_score(y,p)),
      'top10_precision':float(y[np.argsort(-p,kind='stable')[:top]].mean()),
      'brier':float(brier_score_loss(y,p)),
      'auc':float(roc_auc_score(y,p)) if y.min()!=y.max() else None}

def day_bootstrap(y,full,base,dates,n=500):
    y=np.asarray(y,dtype=int);full=np.asarray(full);base=np.asarray(base)
    dates=np.asarray(pd.Series(dates).astype(str))
    days=np.unique(dates)
    if len(days)<3:return {'days':len(days),'ci95':None}
    rng=np.random.default_rng(17)
    diffs=[]
    for _ in range(n):
        picks=rng.choice(days,size=len(days),replace=True)
        inds=np.concatenate([np.flatnonzero(dates==v) for v in picks])
        if len(np.unique(y[inds]))<2:continue
        diffs.append(average_precision_score(y[inds],full[inds])-average_precision_score(y[inds],base[inds]))
    return {'days':len(days),'ci95':[float(v) for v in np.quantile(diffs,[.025,.975])],
       'warning':'NOT INDEPENDENT REPLICATION: less than 30 calendar days' if len(days)<30 else None}

def main(out='digui006-result.json'):
    df,quality=load()
    (tr,va,te),times=split(df)
    b=choose(tr,BASE);st=choose(tr,STRUCT);sm=choose(tr,SMART_UNAUDITED)
    if len(b)<5 or len(st)<4:raise ValueError('Insufficient predeclared features')
    folds={}
    for label,fold in [('validation',va),('test',te)]:
        y=fold.target.to_numpy()
        pb=scores(tr,fold,b);ps=scores(tr,fold,b+st)
        mb=measures(y,pb);ms=measures(y,ps)
        o={'base':mb,'plus_structure':ms,'delta_ap':float(ms['ap']-mb['ap']),
           'delta_top10_precision':float(ms['top10_precision']-mb['top10_precision']),
           'day_block_bootstrap':day_bootstrap(y,ps,pb,fold.captured_at.dt.strftime('%Y-%m-%d'))}
        if sm:
            pu=scores(tr,fold,b+st+sm)
            o['smart_labels_UNAUDITED']={'metrics':measures(y,pu),
                'delta_ap_vs_structure':float(average_precision_score(y,pu)-ms['ap'])}
        folds[label]=o
    result={'study':'DIGUI-006','source':URL,'data':quality,'splits':times,
       'fold_sizes':{'train':len(tr),'validation':len(va),'test':len(te)},
       'features':{'market':b,'structure':st,'unaudited_smart_labels':sm},
       'results':folds,'interpretation':{
          'economic':'NO-GO: label is maximum future price, not tradable PnL',
          'asof':'SOURCE DATA TIMESTAMPS UNVERIFIED; no live GO',
          'selection':'Only GMGN detected tokens; no full launch universe',
          'replication':'20-day single regime, too short for broad inference'},
       'orders_sent':0}
    Path(out).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else 'digui006-result.json')
