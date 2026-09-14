#!/usr/bin/env python3
import csv, io, json, math, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

LAB='ETF-CME-INSTFLOW-001'
EXPECTED_RAW_SHA='23078f98aef136e26c5ca867a6d792c36d324f26caa870865879da0a64ae4900'
SOURCE_DIR=os.environ.get('SOURCE_GATE_DIR','source_gate')
OUT=os.environ.get('OUT_DIR','artifacts/etf_cme_discovery_v01')
os.makedirs(OUT,exist_ok=True)

# Bind exact canonical source gate receipt and bytes.
receipt=json.load(open(os.path.join(SOURCE_DIR,'source_data_gate_receipt.json'),encoding='utf-8'))
raw_path=os.path.join(SOURCE_DIR,'cftc_legacy_futures_133741_2018_2024.csv')
import hashlib
raw_bytes=open(raw_path,'rb').read(); raw_sha=hashlib.sha256(raw_bytes).hexdigest()
assert receipt['status']=='SOURCE_DATA_GATE_PASS'
assert raw_sha==EXPECTED_RAW_SHA==receipt['raw_sha256']
assert receipt['year_2025_accessed'] is False and receipt['year_2026_accessed'] is False
assert receipt['outcomes_computed'] is False and receipt['returns_computed'] is False and receipt['pnl_computed'] is False and receipt['signal_values_computed'] is False

rows=list(csv.DictReader(io.StringIO(raw_bytes.decode('utf-8-sig'))))
rows.sort(key=lambda r:r['report_date_as_yyyy_mm_dd'])

# Frozen signal: delta(noncommercial long-short) / current open interest.
signals=[]
prev_net=None
for r in rows:
    d=datetime.fromisoformat(r['report_date_as_yyyy_mm_dd'].replace('Z','+00:00')).date()
    nl=float(r['noncomm_positions_long_all']); ns=float(r['noncomm_positions_short_all']); oi=float(r['open_interest_all'])
    net=nl-ns
    if prev_net is not None:
        sig=(net-prev_net)/oi
        info_date=d+timedelta(days=8)
        entry=info_date
        exitd=entry+timedelta(days=7)
        # Frozen protection: never request/use outcome beyond 2024-12-31.
        if exitd <= datetime(2024,12,31).date():
            signals.append({'as_of':d,'signal':sig,'entry':entry,'exit':exitd})
    prev_net=net

# Fetch only required BTCUSDT daily opens, bounded through 2024-12-31.
min_d=min(x['entry'] for x in signals); max_d=max(x['exit'] for x in signals)
assert max_d <= datetime(2024,12,31).date()
start_ms=int(datetime(min_d.year,min_d.month,min_d.day,tzinfo=timezone.utc).timestamp()*1000)
end_ms=int(datetime(max_d.year,max_d.month,max_d.day,tzinfo=timezone.utc).timestamp()*1000)

prices={}
cur=start_ms
endpoint='https://data-api.binance.vision/api/v3/klines'
while cur<=end_ms:
    params={'symbol':'BTCUSDT','interval':'1d','startTime':str(cur),'endTime':str(end_ms),'limit':'1000'}
    url=endpoint+'?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={'User-Agent':'ETF-CME-INSTFLOW-001/0.1 discovery'})
    with urllib.request.urlopen(req,timeout=120) as resp: batch=json.loads(resp.read().decode())
    if not batch: break
    for k in batch:
        dt=datetime.fromtimestamp(k[0]/1000,tz=timezone.utc).date(); prices[dt]=float(k[1])
    nxt=int(batch[-1][0])+86400000
    if nxt<=cur: raise RuntimeError('non-advancing Binance pagination')
    cur=nxt

records=[]; missing=[]
for x in signals:
    ep=prices.get(x['entry']); xp=prices.get(x['exit'])
    if ep is None or xp is None:
        missing.append({'entry':x['entry'].isoformat(),'exit':x['exit'].isoformat()}); continue
    ret=xp/ep-1.0
    pos=1 if x['signal']>0 else (-1 if x['signal']<0 else 0)
    gross=pos*ret
    net10=gross-(0.001 if pos else 0.0)
    net20=gross-(0.002 if pos else 0.0)
    records.append({**x,'return':ret,'position':pos,'gross':gross,'net10':net10,'net20':net20})

# Missing prices are fail-closed before scientific classification.
if missing:
    close={'lab':LAB,'classification':'DATA_FAILURE','reason':'MISSING_BTCUSDT_DAILY_PRICES','missing':missing,'year_2025_accessed':False,'year_2026_accessed':False}
    json.dump(close,open(os.path.join(OUT,'discovery_closeout.json'),'w'),indent=2)
    print(json.dumps(close,indent=2)); sys.exit(2)

n=len(records)
if n<300:
    close={'lab':LAB,'classification':'INSUFFICIENT_SAMPLE','evaluable_weeks':n,'minimum':300,'year_2025_accessed':False,'year_2026_accessed':False}
    json.dump(close,open(os.path.join(OUT,'discovery_closeout.json'),'w'),indent=2)
    print(json.dumps(close,indent=2)); sys.exit(0)

# OLS y = alpha + beta*x with HAC Newey-West lag=2.
x=[r['signal'] for r in records]; y=[r['return'] for r in records]
sx=sum(x); sy=sum(y); sxx=sum(v*v for v in x); sxy=sum(a*b for a,b in zip(x,y))
den=n*sxx-sx*sx
beta=(n*sxy-sx*sy)/den; alpha=(sy-beta*sx)/n
u=[yy-alpha-beta*xx for xx,yy in zip(x,y)]
# X'X inverse for [1,x]
inv00=sxx/den; inv01=-sx/den; inv11=n/den
# HAC meat S = sum_t z_t z_t' + weights * lag cross-products, z_t=X_t*u_t
S00=S01=S11=0.0
z=[(u[i],x[i]*u[i]) for i in range(n)]
for a,b in z: S00+=a*a; S01+=a*b; S11+=b*b
L=2
for lag in range(1,L+1):
    w=1-lag/(L+1)
    c00=c01=c10=c11=0.0
    for t in range(lag,n):
        a0,a1=z[t]; b0,b1=z[t-lag]
        c00+=a0*b0; c01+=a0*b1; c10+=a1*b0; c11+=a1*b1
    S00+=w*(c00+c00); S01+=w*(c01+c10); S11+=w*(c11+c11)
# V = invXX * S * invXX ; beta variance element [1,1]
t00=inv00*S00+inv01*S01; t01=inv00*S01+inv01*S11
t10=inv01*S00+inv11*S01; t11=inv01*S01+inv11*S11
vbeta=t10*inv01+t11*inv11
se_beta=math.sqrt(max(vbeta,0.0)); tstat=beta/se_beta if se_beta>0 else float('inf')
normal_cdf=lambda z: 0.5*(1+math.erf(z/math.sqrt(2)))
p_one=1-normal_cdf(tstat)

def mean(vals): return sum(vals)/len(vals)
def pf(vals):
    pos=sum(v for v in vals if v>0); neg=-sum(v for v in vals if v<0)
    return pos/neg if neg>0 else float('inf')
base=[r['net10'] for r in records]; stress=[r['net20'] for r in records]; gross=[r['gross'] for r in records]
years={}
for yr in range(2018,2025):
    vals=[r['net10'] for r in records if r['entry'].year==yr]
    years[str(yr)]={'n':len(vals),'net_mean':mean(vals) if vals else None,'net_pnl':sum(vals)}
nonneg=sum(1 for v in years.values() if v['n']>0 and v['net_pnl']>=0)
pos_gross_by_year={str(yr):sum(max(0,r['gross']) for r in records if r['entry'].year==yr) for yr in range(2018,2025)}
tot_pos=sum(pos_gross_by_year.values())
max_share=max((v/tot_pos if tot_pos>0 else 0.0) for v in pos_gross_by_year.values())
criteria={
 'minimum_evaluable_weeks':n>=300,
 'beta_positive':beta>0,
 'one_sided_hac_p_max_0_10':p_one<=0.10,
 'base_net_mean_positive':mean(base)>0,
 'base_profit_factor_gt_1':pf(base)>1.0,
 'minimum_5_of_7_nonnegative_years':nonneg>=5,
 'max_single_year_share_positive_gross_pnl_le_0_40':max_share<=0.40,
}
classification='DISCOVERY_SURVIVES_MVE0' if all(criteria.values()) else 'DISCOVERY_FAIL_NO_PROMOTION'
close={
 'lab':LAB,'protocol_version':'V0.1','classification':classification,'source_gate_run_id':34814165080,'source_raw_sha256':raw_sha,
 'evaluable_weeks':n,'beta':beta,'hac_lag_weeks':2,'hac_se_beta':se_beta,'one_sided_hac_p':p_one,
 'base_cost_bps':10,'base_net_mean':mean(base),'base_profit_factor':pf(base),
 'stress_cost_bps':20,'stress_net_mean':mean(stress),'stress_profit_factor':pf(stress),
 'nonnegative_years':nonneg,'yearly':years,'positive_gross_pnl_by_year':pos_gross_by_year,'max_single_year_share_positive_gross_pnl':max_share,
 'criteria':criteria,'discovery_executed_exactly_once_by_this_run':True,
 'latest_outcome_date_used':max(r['exit'] for r in records).isoformat(),
 'year_2025_accessed':False,'year_2026_accessed':False,'live_trading':False,'exchange_mutation':False
}
json.dump(close,open(os.path.join(OUT,'discovery_closeout.json'),'w'),indent=2,sort_keys=True,default=str)
with open(os.path.join(OUT,'discovery_ledger.csv'),'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['as_of','signal','entry','exit','return','position','gross','net10','net20']); w.writeheader()
    for r in records: w.writerow({k:(v.isoformat() if hasattr(v,'isoformat') else v) for k,v in r.items()})
print(json.dumps(close,indent=2,sort_keys=True,default=str))
