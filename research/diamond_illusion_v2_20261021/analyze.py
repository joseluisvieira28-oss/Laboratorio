"""Offline adversarial analysis. Reads only pinned 2024/2025 market archives."""
from pathlib import Path
import csv,json,zipfile,io,datetime as dt,hashlib,math,statistics
import numpy as np
P=Path(__file__).parent;D=P/'data';R=P/'results';R.mkdir(exist_ok=True)
CHECK=[]
# Fail closed on source-byte changes before computing outcomes.
for source in json.loads((P/'source_manifest.json').read_text()):
 f=P/source.get('path','source_archives/'+source['file']);assert hashlib.sha256(f.read_bytes()).hexdigest()==source['sha256']
for source in json.loads((P/'input_manifest.json').read_text()):
 f=P/source['path'];assert hashlib.sha256(f.read_bytes()).hexdigest()==source['sha256']

def dump(name,obj):(R/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def rows(f):return list(csv.DictReader(f.open(encoding='utf-8-sig')))
def csvout(name,rr):
 if not rr:return
 keys=list(dict.fromkeys(k for r in rr for k in r))
 with (R/name).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rr)
def ck(name,a,b,tol=1e-8):
 ok=bool(abs(a-b)<=tol);CHECK.append(dict(check=name,passed=ok,actual=a,expected=b));assert ok,name

def stats(v):
 a=np.array(v,dtype=float);n=len(a)
 if n==0:return {'n':0}
 w=a[a>0];l=-a[a<0];aw=float(w.mean()) if len(w) else None;al=float(l.mean()) if len(l) else None
 st=mx=0
 for x in a:st=st+1 if x<0 else 0;mx=max(mx,st)
 c=np.cumsum(a);dd=float(np.min(c-np.maximum.accumulate(np.r_[0,c])[1:]));ph=len(w)/n;z=1.959963984540054;den=1+z*z/n;mid=(ph+z*z/(2*n))/den;hh=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
 return dict(n=n,wins=len(w),losses=len(l),zeros=n-len(w)-len(l),mean=float(a.mean()),sd=float(a.std(ddof=1)) if n>1 else 0,win_rate=ph,wilson95=[mid-hh,mid+hh],avg_win=aw,avg_loss_abs=al,payoff=aw/al if aw is not None and al else None,profit_factor=float(w.sum()/l.sum()) if len(l) else None,total=float(a.sum()),additive_dd=dd,worst=float(a.min()),best=float(a.max()),max_losing_streak=mx,median=float(np.median(a)),q05=float(np.quantile(a,.05)),q95=float(np.quantile(a,.95)),tail_mean05=float(a[a<=np.quantile(a,.05)].mean()))
def equity_metrics(v):
 a=np.array(v)/10000;eq=np.cumprod(1+a);peaks=np.maximum.accumulate(np.r_[1,eq])[1:];return {'simple_cash_equity_return':float(eq[-1]-1),'simple_cash_equity_dd':float(np.min(eq/peaks-1))}
def bootstrap(v,block):
 a=np.array(v);n=len(a);rng=np.random.default_rng(20261021);nb=(n+block-1)//block;start=rng.integers(0,n,size=(20000,nb));ix=(start[:,:,None]+np.arange(block))%n;sample=a[ix.reshape(20000,-1)[:,:n]];means=sample.mean(axis=1)
 return {'block':block,'replications':20000,'mean_percentile95':np.quantile(means,[.025,.975]).tolist(),'resample_fraction_mean_le_zero':float(np.mean(means<=0)),'not_probability_of_true_edge':True}
def run_probability(n,q,k):
 a=np.zeros(k);a[0]=1
 for _ in range(n):
  b=np.zeros(k);b[0]=a.sum()*(1-q);b[1:]=a[:-1]*q;a=b
 return float(1-a.sum())
def datestr(ms):return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).date().isoformat()
observed=json.loads((D/'observed_costs.json').read_text())
assert observed['summary']['actual_taker_bps_per_side']==8.0
assert observed['financial_reconciliation_pass'] is True
# Daily context. 2025 prices are the original archived source-gate bytes.
DAILY={}
source_paths=list((P/'source_archives').glob('BTCUSDT-1d-2024-*.zip'))+list((P/'etf_source_2025').glob('BTCUSDT-1d-2025-*.zip'))
for f in source_paths:
 with zipfile.ZipFile(f) as z:
  for a in csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())):
   ts=int(a[0]);ms=ts//1000 if ts>10**14 else ts;date=datestr(ms);assert date[:4] in ['2024','2025'];DAILY[date]={'open':float(a[1]),'high':float(a[2]),'low':float(a[3]),'close':float(a[4])}
assert len(DAILY)==731
keys=sorted(DAILY);cl=np.array([DAILY[k]['close'] for k in keys]);rets=np.diff(np.log(cl));rv={}
for i in range(21,len(keys)):rv[keys[i-1]]=float(np.std(rets[i-21:i-1],ddof=1))
def context(date):
 i=keys.index(date);assert i>=200;prev=cl[i-1];sma=float(cl[i-200:i].mean());last=keys[i-1];hist=[x for k,x in rv.items() if k<=last];r=rv[last];return {'trend':'ABOVE_SMA200' if prev>sma else 'BELOW_SMA200','volatility':'HIGH_RV20' if r>statistics.median(hist) else 'LOW_RV20','regime_asof':last,'prior_close':prev,'sma200':sma,'rv20':r}
# Full minute opens/high/low/close for 2025; microsecond timestamp normalization.
minute=np.full((365*1440,4),np.nan);start_ms=int(dt.datetime(2025,1,1,tzinfo=dt.timezone.utc).timestamp()*1000)
for f in sorted((P/'source_archives').glob('BTCUSDT-1m-2025-*.zip')):
 with zipfile.ZipFile(f) as z:
  for a in csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())):
   ts=int(a[0]);ms=ts//1000 if ts>10**14 else ts;ix=(ms-start_ms)//60000;assert 0<=ix<len(minute);assert ms==start_ms+ix*60000;assert np.isnan(minute[ix,0]);minute[ix]=[float(a[j]) for j in range(1,5)]
assert not np.isnan(minute).any();ck('minute_count',len(minute),525600)
def idx(date,delay=0):return (dt.date.fromisoformat(date)-dt.date(2025,1,1)).days*1440+delay
TR=[]
for i,r in enumerate(rows(D/'etf_oos_2025.csv')):
 if not int(float(r['position'])):continue
 t={'family':'ETF','id':'ETF-'+str(i+1),'symbol':'BTCUSDT','signal_date':r['as_of'],'entry_date':r['entry'],'exit_date':r['exit'],'side':int(float(r['position'])),'weight':1.,'hold_days':7,'gross_canonical_bps':float(r['gross'])*10000,'canonical_base_bps':float(r['base_net'])*10000};t.update(context(t['entry_date']));TR.append(t)
for i,r in enumerate(rows(D/'options_v21_oos_2025.csv')):
 signal=dt.date.fromisoformat(r['signal_date']);t={'family':'OPTIONS','id':'OPTIONS-'+str(i+1),'symbol':'BTCUSDT','signal_date':str(signal),'entry_date':str(signal+dt.timedelta(days=1)),'exit_date':str(signal+dt.timedelta(days=2)),'side':int(r['position']),'weight':float(r['weight']),'hold_days':1,'gross_canonical_bps':float(r['unscaled_gross_bps'])*float(r['weight']),'canonical_base_bps':float(r['weight'])*(float(r['unscaled_gross_bps'])-10)};t.update(context(t['entry_date']));TR.append(t)
for t in TR:
 en=minute[idx(t['entry_date']),0];ex=minute[idx(t['exit_date']),0];ck('daily_minute_entry_'+t['id'],en,DAILY[t['entry_date']]['open']);ck('daily_minute_exit_'+t['id'],ex,DAILY[t['exit_date']]['open']);t['entry_px']=en;t['exit_px']=ex;t['gross_simple_bps']=t['weight']*t['side']*(ex/en-1)*10000
 if t['family']=='ETF':ck('ETF_gross_'+t['id'],t['gross_simple_bps'],t['gross_canonical_bps'])
 else:ck('OPTIONS_log_gross_'+t['id'],t['weight']*t['side']*math.log(ex/en)*10000,t['gross_canonical_bps'])

def net_canonical(t,cost,extra=0):return t['gross_canonical_bps']-t['weight']*(cost+extra)
def net_cash(t,fe,fx,extra=0):return t['gross_simple_bps']-t['weight']*(fe+fx*t['exit_px']/t['entry_px']+extra)
MET=[];COST=[];CONC=[];GROUP=[];BOOT=[];RUN=[];CAP=[];MTM=[];DELAY=[];POWER=[]
for family in ['ETF','OPTIONS']:
 tt=[t for t in TR if t['family']==family];n=len(tt);wmean=float(np.mean([t['weight'] for t in tt]));gross=float(np.mean([t['gross_canonical_bps'] for t in tt]));cashgross=float(np.mean([t['gross_simple_bps'] for t in tt]));cashden=float(np.mean([t['weight']*(1+t['exit_px']/t['entry_px'])/2 for t in tt]))
 for name,cost in [('FROZEN_BASE10',10),('OBSERVED_TAKER16_TRANSFER',16),('FROZEN_STRESS20',20)]:
  a=[net_canonical(t,cost) for t in tt];m={'family':family,'scenario':name,'convention':'frozen_simple_bps' if family=='ETF' else 'frozen_weighted_log_bps',**stats(a),'break_even_all_cost_full_notional_bps':gross/wmean,'break_even_equal_fee_cash_roundtrip_bps':cashgross/cashden};MET.append(m)
  for block in [1,4,8]:BOOT.append({'family':family,'scenario':name,**bootstrap(a,block)})
  q=m['losses']/n
  for k in [3,5,7,10,20]:RUN.append({'family':family,'scenario':name,'horizon_trades':n,'k':k,'empirical_loss_rate':q,'iid_probability_at_least_one_run':run_probability(n,q,k),'assumption':'IID stationary Bernoulli with plug-in observed loss probability; not forecast'})
  for k in [1,3,5]:
   ordered=sorted(a,reverse=True);top=sum(ordered[:k]);CONC.append({'family':family,'scenario':name,'top_k':k,'top_k_net_sum_bps':top,'share_of_positive_net_pnl':top/sum(x for x in a if x>0),'share_of_total_net_pnl':top/sum(a) if sum(a) else None,'remaining_n':n-k,'remaining_expectancy_bps':sum(ordered[k:])/(n-k),'remaining_pf':stats(ordered[k:])['profit_factor'],'not_new_trading_filter':True})
 for cost in [0,4,8,10,12,14,16,18,20,24,32]:
  for extra in [0,1,2,5,10]:
   v=[net_canonical(t,cost,extra) for t in tt];c=[net_cash(t,cost/2,cost/2,extra) for t in tt];COST.append({'family':family,'roundtrip_fee_assumption_bps':cost,'spread_slippage_financing_expense_bps':extra,'canonical_mean_bps':float(np.mean(v)),'canonical_pf':stats(v)['profit_factor'],'cash_simple_mean_bps':float(np.mean(c)),'cash_simple_pf':stats(c)['profit_factor'],'evidence':'16 bps taker rate transfer from 2026; all others are scenarios, not actual 2025 all-cost'})
 for label,fe,fx in [('MAKER_MAKER_QUOTED_NOT_GUARANTEED',6,6),('MAKER_TAKER_QUOTED_NOT_GUARANTEED',6,8),('TAKER_TAKER_OBSERVED_RATE_TRANSFER',8,8),('PUBLIC_DEFAULT_UNVERIFIED_FOR_ACCOUNT',0,2)]:
  for extra in [0,2,5]:
   v=[net_cash(t,fe,fx,extra) for t in tt];MET.append({'family':family,'scenario':label+'_EXTRA'+str(extra),'convention':'cash_simple_return_bps_not_historical_parent',**stats(v),**equity_metrics(v)})
 # All diagnostic groupings; no subset selected for trading.
 for scenario,cost in [('BASE10',10),('TAKER16',16)]:
  for group in ['symbol','side','trend','volatility','quarter','side_trend_volatility']:
   dd={}
   for t in tt:
    key=str(t[group]) if group in ['symbol','side','trend','volatility'] else (t['entry_date'] if family=='ETF' else t['signal_date'])[:4]+'Q'+str((int((t['entry_date'] if family=='ETF' else t['signal_date'])[5:7])-1)//3+1) if group=='quarter' else str(t['side'])+'_'+t['trend']+'_'+t['volatility']
    dd.setdefault(key,[]).append(net_canonical(t,cost))
   for key,v in sorted(dd.items()):GROUP.append({'family':family,'scenario':scenario,'group':group,'value':key,**stats(v),'diagnostic_only':True})
 # Minute delay perturbations: same sign/weight, never rerun strategy or choose best.
 for delay in [0,1,5,15,60]:
  for mode in ['entry_only','exit_only','both']:
   cv=[];sv=[]
   for t in tt:
    en=minute[idx(t['entry_date'],delay if mode in ['entry_only','both'] else 0),0];ex=minute[idx(t['exit_date'],delay if mode in ['exit_only','both'] else 0),0];ret=ex/en-1;g=t['weight']*t['side']*(math.log(ex/en) if family=='OPTIONS' else ret)*10000;cv.append(g-16*t['weight']);sv.append(t['weight']*(t['side']*ret*10000-8-8*ex/en))
   DELAY.append({'family':family,'delay_minutes':delay,'mode':mode,'cost_bps':16,'n':n,'canonical_mean_bps':float(np.mean(cv)),'canonical_pf':stats(cv)['profit_factor'],'cash_simple_mean_bps':float(np.mean(sv)),'cash_simple_pf':stats(sv)['profit_factor'],'source':'Binance spot minute-open proxy, not native MEXC execution or BBO','signal_and_weight_unchanged':True})
 # Model cash NAV and intratrade mark risk, no funding or additional slippage fabricated.
 for cost in [10,16,20]:
  eq=peak=1.;ddclose=ddadverse=0.;sample=[]
  for t in tt:
   a=idx(t['entry_date']);b=idx(t['exit_date']);w=t['weight'];side=t['side'];en=t['entry_px'];fe=fx=cost/2
   marks=eq*(1+w*side*(minute[a:b,3]/en-1)-w*fe/10000);adverse_px=minute[a:b,2] if side>0 else minute[a:b,1];adverse=eq*(1+w*side*(adverse_px/en-1)-w*fe/10000);peaks=np.maximum.accumulate(np.r_[peak,marks])[1:];ddclose=min(ddclose,float(np.min(marks/peaks-1)));ddadverse=min(ddadverse,float(np.min(adverse/peaks-1)));peak=max(peak,float(marks.max()));sample.extend([{'family':family,'fee_roundtrip_bps':cost,'utc':dt.datetime.fromtimestamp((start_ms+(a+j)*60000)/1000,dt.timezone.utc).isoformat(),'nav':float(marks[j])} for j in range(0,len(marks),60)]);eq*=1+net_cash(t,fe,fx)/10000;peak=max(peak,eq);ddclose=min(ddclose,eq/peak-1)
  MTM.append({'family':family,'fee_roundtrip_bps':cost,'unit_exposure_cash_return':eq-1,'minute_close_mtm_dd':ddclose,'adverse_minute_mark_vs_close_peak_dd':ddadverse,'funding_unknown':True,'native_MEXC_basis_unknown':True,'true_continuous_path_unknown':True});csvout('nav_'+family+'_'+str(cost)+'.csv',sample)
 # Capital and minimum lot effects using current public specification, historical prices only.
 spec=json.loads((P/'contract_metadata.json').read_text())['parameters'];size=float(spec['contractSize']);step=float(spec['volUnit']);minv=float(spec['minVol'])
 for initial in [100,250,500,1000]:
  for extra in [0,2,5]:
   eq=float(initial);peak=eq;mdd=0.;skip=0;downs=[];minn=[];returns=[]
   for t in tt:
    desired=t['weight']*eq;cap=min(desired,eq/(1+16/10000+extra/10000));q=math.floor(cap/(t['entry_px']*size)/step)*step
    if q<minv:skip+=1;returns.append(0);continue
    notional=q*size*t['entry_px'];minn.append(minv*size*t['entry_px']);downs.append(1-notional/desired);net=notional*(t['side']*(t['exit_px']/t['entry_px']-1)-.0008-.0008*t['exit_px']/t['entry_px']-extra/10000);returns.append(net/eq);eq+=net;peak=max(peak,eq);mdd=min(mdd,eq/peak-1)
   CAP.append({'family':family,'initial_USDT':initial,'fee_bps_per_side':8,'extra_cost_bps':extra,'ending_cash_simulated_USDT':eq,'pnl_simulated_USDT':eq-initial,'realized_only_dd':mdd,'skipped_below_min_lot':skip,'avg_notional_reduction_from_rounding':float(np.mean(downs)) if downs else None,'historical_minimum_order_notional_min':min(minn) if minn else None,'historical_minimum_order_notional_max':max(minn) if minn else None,'contract_size_current_applied_retrospectively':size,'zero_funding_assumption_not_certification':True,'no_leverage_above_one':True,'not_same_as_frozen_position_sizing':True})
 # Fixed-horizon 80% power sensitivity, normal IID approximation; not a proposed stop rule.
 sd=float(np.std([t['canonical_base_bps'] for t in tt],ddof=1))
 for target in [1,5,10]:POWER.append({'family':family,'net_edge_bps_to_detect':target,'sample_sd_bps':sd,'trades_approx_onesided_alpha05_power80':math.ceil(((1.6448536269514722+.8416212335729143)*sd/target)**2),'assumption':'normal IID known variance approximation, excludes dependence, costs uncertainty, multiplicity'})
# Reconcile phase 0 figures including LICP without pooling it with the candidates.
prior=json.loads((D/'prior_metrics.json').read_text());pmap={'ETF':'ETF_OOS_2025','OPTIONS':'OPTIONS_V21_OOS_2025'}
for fam,oldname in pmap.items():
 a=next(x for x in MET if x['family']==fam and x['scenario']=='FROZEN_BASE10');b=next(x for x in prior if x['dataset']==oldname and x['scenario']=='BASE10')
 for k,oldk in [('mean','expectancy'),('win_rate','win_rate'),('payoff','payoff'),('profit_factor','profit_factor')]:ck('phase0_'+fam+'_'+k,a[k],b[oldk])
licp=next(x for x in prior if x['dataset']=='LICP_SOL_FORWARD' and x['scenario']=='BASE16');ck('LICP_phase0_expectancy',licp['expectancy'],-11.295823284750451)
for filename,obj in [('metrics.json',MET),('bootstrap.json',BOOT),('concentration.json',CONC),('mtm.json',MTM),('capital.json',CAP)]:dump(filename,obj)
for filename,obj in [('all_412_trades.csv',TR),('cost_matrix.csv',COST),('diagnostic_groups.csv',GROUP),('concentration.csv',CONC),('execution_delays.csv',DELAY),('loss_runs_iid.csv',RUN),('capital.csv',CAP),('sample_size_power.csv',POWER),('metrics.csv',MET),('mtm.csv',MTM)]:csvout(filename,obj)
dump('validation.json',{'all_passed':all(x['passed'] for x in CHECK),'checks':CHECK,'daily_rows':len(DAILY),'minute_rows':len(minute),'market_years':[2024,2025],'ETF_2026_outcomes_accessed':False})
# Audit-ready complete return distribution and causal source context.
csvout('daily_context_2024_2025.csv',[{'date':k,**DAILY[k]} for k in keys]);csvout('minute_delay_quotes_2025.csv',[{'date':k,'delay_min':m,'open':float(minute[idx(k,m),0])} for k in keys if k.startswith('2025') for m in [0,1,5,15,60]])
print('METRICS',[(x['family'],x['scenario'],round(x['mean'],4),x.get('simple_cash_equity_dd')) for x in MET if x['scenario'] in ['FROZEN_BASE10','OBSERVED_TAKER16_TRANSFER','TAKER_TAKER_OBSERVED_RATE_TRANSFER_EXTRA0']]);print('MTM',MTM);print('CHECKS',len(CHECK));print('CAPITAL',[(x['family'],x['initial_USDT'],round(x['pnl_simulated_USDT'],2)) for x in CAP if x['extra_cost_bps']==2])

# Descriptive dependent-resampling loss risk; does not estimate probability of a true edge.
LOSS=[]
for fam in ['ETF','OPTIONS']:
 tt=[t for t in TR if t['family']==fam];n=len(tt)
 for cost in [10,16,20]:
  v=np.array([net_cash(t,cost/2,cost/2) for t in tt]);rng=np.random.default_rng(20261021);starts=rng.integers(0,n,size=(20000,(n+3)//4));ix=((starts[:,:,None]+np.arange(4))%n).reshape(20000,-1)[:,:n];sample=v[ix];running=np.zeros(20000,dtype=int);longest=np.zeros(20000,dtype=int)
  for j in range(n):running=np.where(sample[:,j]<0,running+1,0);longest=np.maximum(longest,running)
  eq=np.cumprod(1+sample/10000,axis=1);peak=np.maximum.accumulate(np.column_stack([np.ones(20000),eq]),axis=1)[:,1:];dd=np.min(eq/peak-1,axis=1)
  row={'family':fam,'fee_roundtrip_bps':cost,'n':n,'block':4,'replications':20000,'resample_fraction_terminal_cash_loss':float(np.mean(eq[:,-1]<1)),'drawdown_quantiles_05_50_95':np.quantile(dd,[.05,.5,.95]).tolist(),'conditional_stationarity_assumption':True,'not_true_edge_probability':True}
  for k in [3,5,7,10,20]:row['resample_fraction_max_losing_run_ge_'+str(k)]=float(np.mean(longest>=k))
  for threshold in [.1,.2,.3]:row['resample_fraction_dd_worse_than_'+str(threshold)]=float(np.mean(dd < -threshold))
  LOSS.append(row)
dump('loss_risk_block4.json',LOSS);csvout('loss_risk_block4.csv',LOSS)
for name,actual,expected in [('iid_n1',run_probability(1,.6,1),.6),('iid_all3',run_probability(3,.6,3),.6**3),('iid_never_loss',run_probability(49,0,5),0.),('iid_certain_loss',run_probability(49,1,5),1.)]:ck(name,actual,expected)
ck('long_cash_fee_identity',(.1-.0008-.0008*1.1)*10000,983.2);ck('short_cash_fee_identity',(-.1-.0008-.0008*1.1)*10000,-1016.8)
dump('validation.json',{'all_passed':all(x['passed'] for x in CHECK),'checks':CHECK,'daily_rows':len(DAILY),'minute_rows':len(minute),'market_years':[2024,2025],'ETF_2026_outcomes_accessed':False})
