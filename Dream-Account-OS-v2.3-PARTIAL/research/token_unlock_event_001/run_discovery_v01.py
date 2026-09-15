import csv, hashlib, io, json, math, random, statistics, sys, time, urllib.request, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROTOCOL=HERE/'FINAL_PRE_DISCOVERY_PROTOCOL_V01.json'
CAL=HERE/'signal_evidence/TUE_UNLOCK_PRESSURE_CALIBRATION_V01.json'
THR=HERE/'signal_evidence/TUE_UNLOCK_PRESSURE_THRESHOLD_FREEZE_V01.json'
OUTDIR=HERE/'discovery_evidence'
PREFLIGHT=OUTDIR/'TUE_DISCOVERY_AVAILABILITY_PREFLIGHT_V01.json'
OUT=OUTDIR/'TUE_DISCOVERY_RESULT_V01.json'
BASE='https://data.binance.vision/data/spot/daily/klines'
BASE_COST=.0030; STRESS_COST=.0060; BOOT=5000; SEED=230915


def load(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(b): return hashlib.sha256(b).hexdigest()
def req(url, attempts=4):
    last=None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'TOKEN-UNLOCK-EVENT-001-discovery/1.0'}),timeout=30) as r:return r.read()
        except Exception as e:last=e; time.sleep(.4*(2**i))
    raise last

def urls(sym,d):
    pair=f'{sym}USDT'; ds=d.isoformat(); root=f'{BASE}/{pair}/1d/{pair}-1d-{ds}.zip'; return root,root+'.CHECKSUM'
def checksum_meta(sym,d):
    _,u=urls(sym,d)
    try:
        body=req(u).decode('utf-8','replace').strip().split(); dg=body[0] if body else ''
        return {'ok':len(dg)==64 and all(c in '0123456789abcdefABCDEF' for c in dg),'sha256':dg.lower() if len(dg)==64 else None,'status':200}
    except Exception as e:return {'ok':False,'sha256':None,'status':f'ERROR:{type(e).__name__}'}
def daily_open(sym,d, expected_sha):
    u,_=urls(sym,d); raw=req(u)
    if sha(raw)!=expected_sha: raise RuntimeError(f'checksum mismatch {sym} {d}')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist();
        if len(names)!=1: raise RuntimeError('bad zip members')
        rows=list(csv.reader(io.StringIO(z.read(names[0]).decode('utf-8'))))
    if len(rows)!=1 or len(rows[0])<2: raise RuntimeError(f'bad daily row {sym} {d}')
    row=rows[0]; ts=int(row[0]); rd=datetime.fromtimestamp(ts/1000,tz=timezone.utc).date()
    if rd!=d: raise RuntimeError(f'date mismatch {sym} {d} {rd}')
    op=float(row[1]);
    if not math.isfinite(op) or op<=0: raise RuntimeError(f'bad open {sym} {d}')
    return op

def percentile(xs,p):
    s=sorted(xs); k=(len(s)-1)*p; lo=math.floor(k); hi=math.ceil(k)
    return s[lo] if lo==hi else s[lo]+(s[hi]-s[lo])*(k-lo)
def mean(xs): return sum(xs)/len(xs) if xs else float('nan')
def rankdata(xs):
    idx=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0.0]*len(xs); j=0
    while j<len(idx):
        k=j
        while k+1<len(idx) and xs[idx[k+1]]==xs[idx[j]]: k+=1
        rr=(j+k+2)/2.0
        for q in range(j,k+1): r[idx[q]]=rr
        j=k+1
    return r
def corr(a,b):
    ma=mean(a); mb=mean(b); da=[x-ma for x in a]; db=[y-mb for y in b]
    den=math.sqrt(sum(x*x for x in da)*sum(y*y for y in db)); return sum(x*y for x,y in zip(da,db))/den if den else float('nan')
def ols_cluster(x,y,clusters):
    n=len(x); sx=sum(x); sy=sum(y); sxx=sum(v*v for v in x); sxy=sum(a*b for a,b in zip(x,y)); det=n*sxx-sx*sx
    if det<=0: raise RuntimeError('singular regression')
    b0=(sxx*sy-sx*sxy)/det; b1=(n*sxy-sx*sy)/det
    resid=[yy-b0-b1*xx for xx,yy in zip(x,y)]
    inv=[[sxx/det,-sx/det],[-sx/det,n/det]]
    score=defaultdict(lambda:[0.0,0.0])
    for xx,u,g in zip(x,resid,clusters): score[g][0]+=u; score[g][1]+=xx*u
    meat=[[0.0,0.0],[0.0,0.0]]
    for v in score.values():
        for i in range(2):
            for j in range(2): meat[i][j]+=v[i]*v[j]
    tmp=[[sum(inv[i][k]*meat[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    cov=[[sum(tmp[i][k]*inv[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    G=len(score); corrfac=(G/(G-1))*((n-1)/(n-2)) if G>1 and n>2 else 1.0
    se=math.sqrt(max(0.0,cov[1][1]*corrfac)); return {'intercept':b0,'beta':b1,'cluster_se':se,'ci95_low':b1-1.96*se,'ci95_high':b1+1.96*se,'n':n,'clusters':G}
def cluster_bootstrap(rows,value_key,reps=BOOT,seed=SEED):
    by=defaultdict(list)
    for r in rows: by[r['symbol']].append(float(r[value_key]))
    toks=sorted(by); rng=random.Random(seed); vals=[]
    for _ in range(reps):
        sample=[]
        for _ in toks: sample.extend(by[rng.choice(toks)])
        vals.append(mean(sample))
    return {'lower95':percentile(vals,.025),'upper95':percentile(vals,.975),'replications':reps,'seed':seed}
def merge_episodes(high):
    by=defaultdict(list)
    for e in high: by[e['symbol']].append(e)
    eps=[]
    for sym,arr in by.items():
        arr=sorted(arr,key=lambda e:e['entry_date'])
        cur=None
        for e in arr:
            a=date.fromisoformat(e['entry_date']); b=date.fromisoformat(e['exit_date'])
            if cur is None or a>date.fromisoformat(cur['exit_date']):
                if cur: eps.append(cur)
                cur={'symbol':sym,'entry_date':a.isoformat(),'exit_date':b.isoformat(),'event_count':1,'event_dates':[e['event_date']]}
            else:
                if b>date.fromisoformat(cur['exit_date']): cur['exit_date']=b.isoformat()
                cur['event_count']+=1; cur['event_dates'].append(e['event_date'])
        if cur: eps.append(cur)
    return eps

def main():
    protocol=load(PROTOCOL); cal=load(CAL); thr=load(THR)
    assert protocol['status']=='FROZEN_PRE_DISCOVERY_OUTCOME_BLIND'
    cr=cal['receipt']; assert cr['classification']=='SIGNAL_CALIBRATION_PASS'
    if sha(CAL.read_bytes())!=thr['calibration_file_sha256']: raise RuntimeError('calibration SHA mismatch')
    threshold=float(thr['threshold'])
    if abs(threshold-float(cr['frozen_high_pressure_threshold_unlock_pressure_days']))>1e-15: raise RuntimeError('threshold mismatch')
    candidates=[]; protected=[]
    for s in cal['signals']:
        ed=date.fromisoformat(s['event_date']); en=date.fromisoformat(s['entry_day']); ex=ed+timedelta(days=8)
        if ex.year>=2025:
            protected.append({**s,'reason':'EXIT_REQUIRES_2025_PROTECTED_DATA'}); continue
        candidates.append({**s,'entry_date':en.isoformat(),'exit_date':ex.isoformat(),'high_pressure':float(s['unlock_pressure_days'])>=threshold})
    # metadata-only availability gate before any market value is downloaded
    needed=set()
    for e in candidates:
        en=date.fromisoformat(e['entry_date']); ex=date.fromisoformat(e['exit_date'])
        needed|={(e['symbol'],en),(e['symbol'],ex),('BTC',en),('BTC',ex)}
    meta={k:checksum_meta(*k) for k in sorted(needed,key=lambda z:(z[0],z[1]))}
    avail=[]; excluded=[]
    for e in candidates:
        en=date.fromisoformat(e['entry_date']); ex=date.fromisoformat(e['exit_date']); ks=[(e['symbol'],en),(e['symbol'],ex),('BTC',en),('BTC',ex)]
        if all(meta[k]['ok'] for k in ks): avail.append(e)
        else: excluded.append({**e,'reason':'DISCOVERY_ENTRY_EXIT_ARCHIVE_ROUTE_INCOMPLETE','statuses':[meta[k]['status'] for k in ks]})
    toks=sorted({e['symbol'] for e in avail}); yrs=sorted({int(e['event_date'][:4]) for e in avail}); high=[e for e in avail if e['high_pressure']]; ht=sorted({e['symbol'] for e in high})
    pre={'lab_id':'TOKEN-UNLOCK-EVENT-001','mode':'DISCOVERY_AVAILABILITY_PREFLIGHT_ONLY','candidate_after_2025_firewall':len(candidates),'protected_exclusions':len(protected),'availability_resolved_events':len(avail),'availability_resolved_tokens':len(toks),'years':yrs,'high_pressure_events':len(high),'high_pressure_tokens':len(ht),'archive_metadata_queries':len(meta),'threshold':threshold,'guards':{'market_price_values_opened':False,'returns_computed':False,'pnl_computed':False,'year_2025_opened':False,'year_2026_opened':False}}
    OUTDIR.mkdir(parents=True,exist_ok=True); PREFLIGHT.write_text(json.dumps({'receipt':pre,'excluded':excluded,'protected':protected},indent=2,sort_keys=True)+'\n')
    if len(avail)<100 or len(toks)<15 or len(yrs)<2 or len(high)<40 or len(ht)<10:
        result={'classification':'INSUFFICIENT_SAMPLE','preflight':pre}; OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2)); return 5
    # Only now open the frozen entry/exit price values.
    opens={}
    for k in sorted(needed,key=lambda z:(z[0],z[1])):
        if meta[k]['ok']: opens[k]=daily_open(k[0],k[1],meta[k]['sha256'])
    event_rows=[]
    for e in avail:
        en=date.fromisoformat(e['entry_date']); ex=date.fromisoformat(e['exit_date']); a=opens[(e['symbol'],en)]; b=opens[(e['symbol'],ex)]; ba=opens[('BTC',en)]; bb=opens[('BTC',ex)]
        tr=b/a-1; lr=math.log(b/a); blr=math.log(bb/ba); adj=lr-blr
        event_rows.append({**e,'entry_open':a,'exit_open':b,'token_simple_return':tr,'gross_avoidance_return':1-b/a,'base_net_avoidance_return':1-b/a-BASE_COST,'stress_net_avoidance_return':1-b/a-STRESS_COST,'btc_adjusted_log_return':adj})
    high_rows=[e for e in event_rows if e['high_pressure']]
    episodes=merge_episodes(high_rows); episode_rows=[]
    for ep in episodes:
        en=date.fromisoformat(ep['entry_date']); ex=date.fromisoformat(ep['exit_date']); a=opens[(ep['symbol'],en)]; b=opens[(ep['symbol'],ex)]
        ep={**ep,'gross_avoidance_return':1-b/a,'base_net_avoidance_return':1-b/a-BASE_COST,'stress_net_avoidance_return':1-b/a-STRESS_COST,'year':en.year}; episode_rows.append(ep)
    reg=ols_cluster([float(e['log1p_unlock_pressure']) for e in event_rows],[float(e['btc_adjusted_log_return']) for e in event_rows],[e['symbol'] for e in event_rows])
    spearman=corr(rankdata([e['unlock_pressure_days'] for e in event_rows]),rankdata([e['btc_adjusted_log_return'] for e in event_rows]))
    stress_boot=cluster_bootstrap(episode_rows,'stress_net_avoidance_return')
    adj_boot=cluster_bootstrap(high_rows,'btc_adjusted_log_return')
    annual={str(y):mean([e['base_net_avoidance_return'] for e in episode_rows if e['year']==y]) for y in (2023,2024)}
    counts=Counter(e['symbol'] for e in high_rows); concentration=max(counts.values())/len(high_rows) if high_rows else 1.0
    metrics={'mechanism_regression':reg,'spearman_pressure_vs_btc_adjusted':spearman,'high_pressure_event_count':len(high_rows),'high_pressure_token_count':len(set(e['symbol'] for e in high_rows)),'avoidance_episode_count':len(episode_rows),'episode_base_mean_net_avoidance':mean([e['base_net_avoidance_return'] for e in episode_rows]),'episode_stress_mean_net_avoidance':mean([e['stress_net_avoidance_return'] for e in episode_rows]),'stress_episode_cluster_bootstrap':stress_boot,'high_pressure_mean_btc_adjusted_log_return':mean([e['btc_adjusted_log_return'] for e in high_rows]),'high_pressure_btc_adjusted_cluster_bootstrap':adj_boot,'annual_base_mean_net_avoidance':annual,'largest_token_share_high_pressure_events':concentration}
    gates={
      'sample_minimums':len(event_rows)>=100 and len(set(e['symbol'] for e in event_rows))>=15 and len({e['event_date'][:4] for e in event_rows})>=2 and len(high_rows)>=40 and len(set(e['symbol'] for e in high_rows))>=10,
      'mechanism_beta_negative_ci':reg['beta']<0 and reg['ci95_high']<0,
      'base_mean_positive':metrics['episode_base_mean_net_avoidance']>0,
      'stress_mean_positive':metrics['episode_stress_mean_net_avoidance']>0,
      'stress_bootstrap_lower_positive':stress_boot['lower95']>0,
      'btc_adjusted_mean_negative':metrics['high_pressure_mean_btc_adjusted_log_return']<0,
      'btc_adjusted_bootstrap_upper_negative':adj_boot['upper95']<0,
      'year_2023_base_nonnegative':annual['2023']>=0,
      'year_2024_base_nonnegative':annual['2024']>=0,
      'token_concentration_ok':concentration<=.35
    }
    classification='SURVIVES_DISCOVERY' if all(gates.values()) else 'NO_EDGE'
    receipt={'lab_id':'TOKEN-UNLOCK-EVENT-001','mve_id':'TUE-CLIFF-ADV30-001','classification':classification,'resolved_event_count':len(event_rows),'resolved_tokens':len(set(e['symbol'] for e in event_rows)),'resolved_years':sorted({int(e['event_date'][:4]) for e in event_rows}),'threshold':threshold,'metrics':metrics,'promotion_gates':gates,'guards':{'threshold_changed_after_outcomes':False,'alternative_horizon_opened':False,'year_2025_opened':False,'year_2026_opened':False,'live_trading':False,'exchange_mutation':False}}
    OUT.write_text(json.dumps({'receipt':receipt,'availability_preflight':pre,'event_rows':event_rows,'avoidance_episodes':episode_rows},indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,indent=2,sort_keys=True)); print('DISCOVERY ONLY / 2025 LOCKED / 2026 LOCKED / NO LIVE TRADING')
    return 0
if __name__=='__main__':sys.exit(main())
