#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, io, json, math, zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

MVE_ID="MVE-SIMPLE4H-01"
START=pd.Timestamp("2025-01-01T00:00:00Z")
END=pd.Timestamp("2026-01-01T00:00:00Z")
WARMUP_START=pd.Timestamp("2024-12-01T00:00:00Z")
BOOT_REPS=3000
BOOT_BLOCK=5
SEED_TEXT="MVE_SIMPLE4H_01_2025_V02"
ARM_TOKEN="MVE_SIMPLE4H_01_2025_ONE_SHOT_V02"

FIXED=[
    ("ST-01_DONCHIAN_BREAKOUT","BNBUSDT"),
    ("ST-01_DONCHIAN_BREAKOUT","DOGEUSDT"),
    ("ST-01_DONCHIAN_BREAKOUT","SOLUSDT"),
    ("ST-01_DONCHIAN_BREAKOUT","XRPUSDT"),
    ("ST-02_EMA_PULLBACK","SOLUSDT"),
    ("ST-02_EMA_PULLBACK","DOGEUSDT"),
    ("ST-03_EXTREME_MEAN_REVERSION","DOGEUSDT"),
]
ASSETS=sorted(set(a for _,a in FIXED))
EXPECTED_MONTHS=["2024-12"]+[f"2025-{m:02d}" for m in range(1,13)]


def sha256_file(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest().lower()

def fail(msg):
    raise RuntimeError("FAIL_CLOSED: "+msg)

def parse_checksum(p:Path, expected_name:str):
    txt=p.read_text(encoding='utf-8-sig').strip().splitlines()
    matches=[]
    for line in txt:
        parts=line.strip().split()
        if len(parts)>=2 and parts[-1].lstrip('*')==expected_name:
            matches.append(parts[0].lower())
    if len(matches)!=1 or len(matches[0])!=64: fail(f"bad checksum sidecar {p}")
    return matches[0]

def source_files(root:Path,asset:str):
    found=[]
    for mo in EXPECTED_MONTHS:
        name=f"{asset}-1m-{mo}.zip"
        hits=list(root.rglob(name))
        if len(hits)!=1: fail(f"{asset} {mo}: expected exactly 1 {name}, got {len(hits)}")
        z=hits[0]
        if '2026' in str(z): fail('2026 path encountered')
        cs=Path(str(z)+'.CHECKSUM')
        if not cs.exists(): fail(f"missing checksum {cs}")
        expected=parse_checksum(cs,name)
        actual=sha256_file(z)
        if actual!=expected: fail(f"checksum mismatch {name}")
        found.append((mo,z,expected))
    return found

def source_manifest(root:Path):
    items=[]
    for asset in ASSETS:
        for mo,p,h in source_files(root,asset):
            items.append({'asset':asset,'month':mo,'filename':p.name,'sha256':h,'size':p.stat().st_size})
    payload={'mve_id':MVE_ID,'items':items,'2026_opened':False}
    b=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    payload['manifest_sha256']=hashlib.sha256(b).hexdigest()
    return payload

def verify_authorization(auth_path:Path, manifest_sha:str):
    a=json.loads(auth_path.read_text(encoding='utf-8-sig'))
    req={
        'mve_id':MVE_ID,
        'authorized':True,
        'period':'2025-01-01T00:00:00Z/2026-01-01T00:00:00Z',
        'source_manifest_sha256':manifest_sha,
        'arm_token':ARM_TOKEN,
        '2026_authorized':False,
        'live_trading_authorized':False,
    }
    for k,v in req.items():
        if a.get(k)!=v: fail(f"authorization mismatch {k}")
    if not str(a.get('branch_head','')).strip(): fail('missing frozen branch_head')
    return a

def read_zip_ohlc(path:Path):
    with zipfile.ZipFile(path,'r') as z:
        members=[n for n in z.namelist() if n.lower().endswith('.csv') and not n.endswith('/')]
        if len(members)!=1: fail(f"{path}: expected 1 CSV, got {len(members)}")
        with z.open(members[0],'r') as f:
            d=pd.read_csv(f,header=None,usecols=[0,1,2,3,4],names=['open_time','open','high','low','close'],dtype=str,low_memory=False)
    for c in ['open_time','open','high','low','close']:
        d[c]=pd.to_numeric(d[c],errors='coerce')
    d=d.dropna()
    if d.empty: fail(f"empty archive {path}")
    med=float(d['open_time'].median())
    unit='us' if med>1e14 else ('ms' if med>1e11 else 's')
    d['ts']=pd.to_datetime(d['open_time'].astype('int64'),unit=unit,utc=True)
    return d[['ts','open','high','low','close']]

def load_asset(root:Path,asset:str):
    frames=[]
    for _,p,_ in source_files(root,asset): frames.append(read_zip_ohlc(p))
    d=pd.concat(frames,ignore_index=True).sort_values('ts')
    d=d[(d.ts>=WARMUP_START)&(d.ts<END)].copy()
    if (d.ts>=END).any(): fail('2026 timestamp encountered')
    if d.ts.duplicated().any():
        dup=d[d.ts.duplicated(keep=False)]
        for ts,g in dup.groupby('ts'):
            if g[['open','high','low','close']].drop_duplicates().shape[0]>1: fail(f"{asset}: conflicting duplicate {ts}")
        d=d.drop_duplicates('ts',keep='first')
    return d.set_index('ts').sort_index()

def resample_complete(d):
    r=d.resample('240min',origin='epoch',closed='left',label='left')
    out=pd.DataFrame({'open':r.open.first(),'high':r.high.max(),'low':r.low.min(),'close':r.close.last(),'count':r.close.count()})
    return out[out['count']==240][['open','high','low','close']].copy()

def indicators(b):
    x=b.copy(); x['ema20']=x.close.ewm(span=20,adjust=False).mean(); x['ema50']=x.close.ewm(span=50,adjust=False).mean()
    prev=x.close.shift(1); tr=pd.concat([x.high-x.low,(x.high-prev).abs(),(x.low-prev).abs()],axis=1).max(axis=1)
    x['atr14']=tr.ewm(alpha=1/14,adjust=False).mean(); x['prev20_high']=x.high.shift(1).rolling(20,min_periods=20).max(); x['prev20_low']=x.low.shift(1).rolling(20,min_periods=20).min()
    return x

def signal(strategy,row):
    vals=[row.open,row.high,row.low,row.close,row.atr14,row.ema20,row.ema50]
    if not all(np.isfinite(v) for v in vals) or row.atr14<=0: return 0
    if strategy=='ST-01_DONCHIAN_BREAKOUT':
        if np.isfinite(row.prev20_high) and row.close>row.prev20_high:return 1
        if np.isfinite(row.prev20_low) and row.close<row.prev20_low:return -1
        return 0
    if strategy=='ST-02_EMA_PULLBACK':
        if row.ema20>row.ema50 and row.low<=row.ema20 and row.close>row.ema20 and row.close>row.open:return 1
        if row.ema20<row.ema50 and row.high>=row.ema20 and row.close<row.ema20 and row.close<row.open:return -1
        return 0
    if strategy=='ST-03_EXTREME_MEAN_REVERSION':
        if row.close<row.ema20-2*row.atr14:return 1
        if row.close>row.ema20+2*row.atr14:return -1
        return 0
    fail('unknown strategy')

def setup_trade(strategy,side,sig,entry):
    atr=float(sig.atr14)
    if strategy=='ST-01_DONCHIAN_BREAKOUT': risk=2*atr; target_r=4; max_hold=20; target=entry+side*target_r*risk
    elif strategy=='ST-02_EMA_PULLBACK': risk=1.5*atr; target_r=2; max_hold=10; target=entry+side*target_r*risk
    else:
        risk=1.5*atr; max_hold=8; target=float(sig.ema20)
        if (side==1 and entry>=target) or (side==-1 and entry<=target): return None
    stop=entry-side*risk
    if stop<=0 or target<=0 or risk<=0:return None
    return stop,target,risk,max_hold

def max_hold(strategy): return {'ST-01_DONCHIAN_BREAKOUT':20,'ST-02_EMA_PULLBACK':10,'ST-03_EXTREME_MEAN_REVERSION':8}[strategy]

def simulate_trade(b,signal_i,side,strategy):
    entry_i=signal_i+1; mh=max_hold(strategy); time_exit_i=entry_i+mh
    if time_exit_i>=len(b) or b.index[time_exit_i]>=END: return None
    entry=float(b.iloc[entry_i].open); sig=b.iloc[signal_i]; setup=setup_trade(strategy,side,sig,entry)
    if setup is None:return None
    stop,target,risk,mh=setup; exit_price=reason=exit_i=None; last_held=entry_i+mh-1
    for j in range(entry_i,last_held+1):
        bar=b.iloc[j]; op=float(bar.open); hi=float(bar.high); lo=float(bar.low)
        if side==1:
            if op<=stop: exit_price,reason,exit_i=op,'STOP_GAP',j;break
            if op>=target: exit_price,reason,exit_i=target,'TARGET',j;break
            if lo<=stop: exit_price,reason,exit_i=stop,'STOP',j;break
            if hi>=target: exit_price,reason,exit_i=target,'TARGET',j;break
        else:
            if op>=stop: exit_price,reason,exit_i=op,'STOP_GAP',j;break
            if op<=target: exit_price,reason,exit_i=target,'TARGET',j;break
            if hi>=stop: exit_price,reason,exit_i=stop,'STOP',j;break
            if lo<=target: exit_price,reason,exit_i=target,'TARGET',j;break
    if exit_price is None: exit_price=float(b.iloc[time_exit_i].open); exit_i=time_exit_i; reason='TIME'
    gross=float(side*np.log(exit_price/entry)*10000); rm=float(side*(exit_price-entry)/risk)
    return {'entry_i':entry_i,'exit_i':exit_i,'entry_time':b.index[entry_i],'exit_time':b.index[exit_i],'side':side,'entry_price':entry,'exit_price':exit_price,'stop_price':stop,'target_price':target,'gross_bps':gross,'net10_bps':gross-10,'net14_bps':gross-14,'r_multiple':rm,'exit_reason':reason}

def build_events(asset,strategy,b):
    rows=[]; i=max(50,int(np.searchsorted(b.index.values,START.to_datetime64(),side='left')))
    while i<len(b)-2 and b.index[i]<END:
        if b.index[i]<START: i+=1;continue
        mh=max_hold(strategy); entry_i=i+1; time_exit_i=entry_i+mh
        if time_exit_i>=len(b) or b.index[time_exit_i]>=END: i+=1;continue
        side=signal(strategy,b.iloc[i])
        if side==0: i+=1;continue
        tr=simulate_trade(b,i,side,strategy)
        if tr is None: i+=1;continue
        rows.append({'cell_id':f'{strategy}-{asset}-4H','asset':asset,'timeframe':'4H','strategy':strategy,**tr})
        i=max(i+1,tr['exit_i']+1)
    return pd.DataFrame(rows)

def bh_qvalues(pvals):
    p=np.asarray(pvals,float); q=np.full(len(p),np.nan); idx=np.where(np.isfinite(p))[0]
    if not len(idx):return q
    pf=p[idx]; order=np.argsort(pf); ranked=pf[order]; m=len(ranked); adj=ranked*m/np.arange(1,m+1); adj=np.minimum.accumulate(adj[::-1])[::-1]; adj=np.clip(adj,0,1); back=np.empty(m); back[order]=adj; q[idx]=back; return q

def bootstrap_lower95(x,cid):
    x=np.asarray(x,float); n=len(x)
    if n<2:return np.nan
    seed=int.from_bytes(hashlib.sha256((cid+'|'+SEED_TEXT).encode()).digest()[:8],'big')%(2**32-1)
    rng=np.random.default_rng(seed); k=math.ceil(n/BOOT_BLOCK); means=np.empty(BOOT_REPS)
    for r in range(BOOT_REPS):
        starts=rng.integers(0,n,size=k); vals=[]
        for s in starts: vals.extend(x[(s+np.arange(BOOT_BLOCK))%n].tolist())
        means[r]=np.mean(vals[:n])
    return float(np.quantile(means,.025))

def maxdd(x):
    if not len(x):return np.nan
    c=np.cumsum(np.asarray(x,float)/10000); peak=np.maximum.accumulate(c); return float((np.exp((c-peak).min())-1)*100)

def summarize(ev,cid,asset,strategy):
    x=ev.net10_bps.to_numpy(float) if len(ev) else np.array([]); n=len(x)
    r={'cell_id':cid,'asset':asset,'timeframe':'4H','strategy':strategy,'n':n}
    if n==0:return r
    mean=float(x.mean()); sd=float(np.std(x,ddof=1)) if n>1 else np.nan; se=sd/math.sqrt(n) if n>1 else np.nan
    if n>1 and se>0: t=mean/se; p=float(stats.t.sf(t,df=n-1)); crit=float(stats.t.ppf(.975,df=n-1)); lo=mean-crit*se; hi=mean+crit*se
    else:t=p=lo=hi=np.nan
    qs=[]
    for q in range(1,5):
        v=ev.loc[pd.to_datetime(ev.entry_time).dt.quarter==q,'net10_bps']; qs.append(float(v.mean()) if len(v) else np.nan)
    pos=x[x>0]; neg=x[x<0]; pos_sum=float(pos.sum()); neg_sum=float(-neg.sum())
    pf10=float(pos_sum/neg_sum) if neg_sum>0 else (float('inf') if pos_sum>0 else np.nan)
    top_trade_share=float(pos.max()/pos_sum) if len(pos) and pos_sum>0 else np.nan
    q_sums=[]
    for q in range(1,5):
        v=ev.loc[pd.to_datetime(ev.entry_time).dt.quarter==q,'net10_bps']; q_sums.append(float(v[v>0].sum()) if len(v) else 0.0)
    top_q_share=float(max(q_sums)/pos_sum) if pos_sum>0 else np.nan
    reasons=ev.exit_reason.astype(str)
    r.update({'gross_mean_bps':float(ev.gross_bps.mean()),'net10_mean_bps':mean,'net10_median_bps':float(ev.net10_bps.median()),'net14_mean_bps':float(ev.net14_bps.mean()),'profit_factor_net10':pf10,'win_rate_net10':float((ev.net10_bps>0).mean()),'sd_net10_bps':sd,'se_net10_bps':se,'ci95_low_net10_bps':lo,'ci95_high_net10_bps':hi,'t_stat_net10':t,'p_one_sided_net10':p,'max_drawdown_net10_pct':maxdd(x),'mean_r_multiple':float(ev.r_multiple.mean()),'stop_rate':float(reasons.str.startswith('STOP').mean()),'target_rate':float((reasons=='TARGET').mean()),'time_exit_rate':float((reasons=='TIME').mean()),'q1_net10_mean_bps':qs[0],'q2_net10_mean_bps':qs[1],'q3_net10_mean_bps':qs[2],'q4_net10_mean_bps':qs[3],'positive_quarters':int(sum(np.isfinite(v) and v>0 for v in qs)),'top_trade_positive_share':top_trade_share,'top_quarter_positive_share':top_q_share})
    return r

def classify(summary):
    adequate=summary.n>=50
    clean_positive=summary.cell_oos_positive & (~summary.concentration_red_flag)
    adequate_count=int(adequate.sum())
    high_n_count=int((summary.n>=100).sum())
    pos_count=int(clean_positive.sum())
    pos_strategy_count=int(summary.loc[clean_positive,'strategy'].nunique())
    strong_count=int(summary.cell_strong_evidence.sum())
    strong_strategy_count=int(summary.loc[summary.cell_strong_evidence,'strategy'].nunique())
    neg14_count=int((adequate & (summary.net14_mean_bps<=0)).sum())
    med14=float(summary.loc[adequate,'net14_mean_bps'].median()) if adequate.any() else np.nan

    if adequate_count>=5 and pos_count>=4 and pos_strategy_count>=2 and med14>0:
        decision='TIER_2_PROMOTED_CANDIDATE'
    elif adequate_count>=4 and med14>0 and ((pos_count>=2 and pos_strategy_count>=2) or pos_count>=3):
        decision='TIER_3_WATCHLIST'
    elif adequate_count>=5 and neg14_count>=5 and med14<=0:
        decision='REJECTED_STONE'
    elif adequate_count>=5:
        decision='NO_EDGE'
    else:
        decision='INSUFFICIENT_SAMPLE'

    quasi_review_eligible=bool(
        decision=='TIER_2_PROMOTED_CANDIDATE'
        and strong_count>=2
        and strong_strategy_count>=2
    )
    return decision,{
        'valid_n_ge_50_cells':adequate_count,
        'high_confidence_n_ge_100_cells':high_n_count,
        'clean_oos_positive_cells':pos_count,
        'clean_oos_positive_strategy_count':pos_strategy_count,
        'strong_evidence_cells':strong_count,
        'strong_evidence_strategy_count':strong_strategy_count,
        'negative_net14_cells':neg14_count,
        'median_net14_bps_adequate_cells':med14,
        'quasi_diamond_review_eligible':quasi_review_eligible
    }

def self_test():
    assert len(FIXED)==7 and len(ASSETS)==4
    assert max_hold('ST-01_DONCHIAN_BREAKOUT')==20 and max_hold('ST-02_EMA_PULLBACK')==10 and max_hold('ST-03_EXTREME_MEAN_REVERSION')==8
    x=np.array([.01,.02,.03,.04,.05,.06,.07]); q=bh_qvalues(x); assert np.all(np.isfinite(q)) and np.all((q>=0)&(q<=1))
    demo=pd.DataFrame({
        'n':[70,70,70,70,70,70,70],
        'net14_mean_bps':[5,4,3,2,-1,-2,-3],
        'strategy':['A','A','B','B','C','C','C'],
        'cell_oos_positive':[True,True,True,True,False,False,False],
        'concentration_red_flag':[False]*7,
        'cell_strong_evidence':[True,False,True,False,False,False,False],
    })
    dec,fm=classify(demo)
    assert dec=='TIER_2_PROMOTED_CANDIDATE' and fm['quasi_diamond_review_eligible'] is True
    print(json.dumps({'status':'SELF_TEST_PASS','promotion_gate_version':'V0.3','protected_market_data_read':False,'2026_opened':False,'live_trading_authorized':False},indent=2))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--source-root')
    ap.add_argument('--authorization-json')
    ap.add_argument('--out')
    a=ap.parse_args()
    if a.self_test:return self_test()
    if not (a.source_root and a.authorization_json and a.out): fail('armed run requires source-root, authorization-json, out')
    root=Path(a.source_root); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    manifest=source_manifest(root); auth=verify_authorization(Path(a.authorization_json),manifest['manifest_sha256'])
    (out/'MVE_SIMPLE4H_01_SOURCE_RECEIPT_V0.1.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    bars={a:indicators(resample_complete(load_asset(root,a))) for a in ASSETS}
    events=[]; rows=[]
    for strategy,asset in FIXED:
        ev=build_events(asset,strategy,bars[asset]); events.append(ev); rows.append(summarize(ev,f'{strategy}-{asset}-4H',asset,strategy))
    events=pd.concat(events,ignore_index=True) if events else pd.DataFrame(); summary=pd.DataFrame(rows)
    summary['q_bh_7']=bh_qvalues(summary.p_one_sided_net10.to_numpy(float))
    summary['bootstrap_lower95_net10_bps']=[bootstrap_lower95(events.loc[events.cell_id==r.cell_id,'net10_bps'].to_numpy(float),r.cell_id) if r.n>=50 else np.nan for _,r in summary.iterrows()]
    summary['concentration_red_flag']=(summary.top_trade_positive_share>0.25)|(summary.top_quarter_positive_share>0.60)
    summary['cell_oos_positive']=(summary.n>=50)&(summary.net10_mean_bps>0)&(summary.net14_mean_bps>0)&(summary.profit_factor_net10>1.0)&(summary.positive_quarters>=2)
    summary['cell_strong_evidence']=summary.cell_oos_positive&((summary.q_bh_7<0.05)|(summary.bootstrap_lower95_net10_bps>0))&(~summary.concentration_red_flag)
    decision,fm=classify(summary)
    events.to_csv(out/'MVE_SIMPLE4H_01_2025_EVENTS.csv.gz',index=False,compression='gzip'); summary.to_csv(out/'MVE_SIMPLE4H_01_2025_SUMMARY.csv',index=False)
    receipt={'mve_id':MVE_ID,'run_type':'ONE_SHOT_2025_CONFIRMATION_V0.3','branch_head':auth['branch_head'],'source_manifest_sha256':manifest['manifest_sha256'],'period':'2025-01-01T00:00:00Z/2026-01-01T00:00:00Z','family_metrics':fm,'decision':decision,'cells':summary.to_dict('records'),'2026_opened':False,'live_trading_authorized':False}
    (out/'MVE_SIMPLE4H_01_2025_DECISION_RECEIPT.json').write_text(json.dumps(receipt,indent=2,default=str),encoding='utf-8')
    print(json.dumps({'status':'ONE_SHOT_COMPLETE','promotion_gate_version':'V0.3','decision':decision,'family_metrics':fm,'2026_opened':False,'live_trading_authorized':False},indent=2))

if __name__=='__main__':
    main()
