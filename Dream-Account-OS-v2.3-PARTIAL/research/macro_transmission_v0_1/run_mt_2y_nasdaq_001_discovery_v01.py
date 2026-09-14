#!/usr/bin/env python3
import csv, hashlib, io, json, math, random, urllib.request, zipfile
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT=Path('.')
OUT=ROOT/'discovery_output'; OUT.mkdir(exist_ok=False)
CONTRACT=json.loads((ROOT/'MT_2Y_NASDAQ_001_DISCOVERY_CONTRACT_V01.json').read_text())
assert CONTRACT['status']=='FROZEN_PRE_OUTCOME'
assert CONTRACT['holdout_2025']=='LOCKED' and CONTRACT['year_2026']=='FORBIDDEN'
assert CONTRACT['post_outcome_tuning'] is False and CONTRACT['live_trading'] is False
START=date(2018,4,1); END_INPUT=date(2024,12,30); LAST_EXIT=date(2024,12,31)
FRED={
 'DGS2':'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2&cosd=2018-04-01&coed=2024-12-30',
 'NASDAQCOM':'https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM&cosd=2018-04-01&coed=2024-12-30',
}
BASE='https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d'

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'MACRO-TRANSMISSION-001-discovery/0.1'})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def months(a,b):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield y,m
        m+=1
        if m==13: y,m=y+1,1

def parse_fred(name,raw):
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))); out={}
    for r in rows:
        d=date.fromisoformat(r['observation_date'])
        if not (START<=d<=END_INPUT): continue
        v=r[name].strip()
        if v in ('','.','NA','N/A'): out[d]=None
        else: out[d]=float(v)
    return out

def median(xs):
    s=sorted(xs); n=len(s)
    return s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2

def quantile(xs,q):
    s=sorted(xs); p=(len(s)-1)*q; lo=int(math.floor(p)); hi=int(math.ceil(p))
    if lo==hi: return s[lo]
    return s[lo]*(hi-p)+s[hi]*(p-lo)

series={}; source_manifest=[]
for name,url in FRED.items():
    raw=fetch(url); h=sha_bytes(raw)
    exp=CONTRACT['expected_source_sha256'][f'{name}_20180401_20241230.csv']
    assert h==exp,(name,h,exp)
    series[name]=parse_fred(name,raw)
    source_manifest.append({'series':name,'sha256':h,'url':url})

# Frozen binding: consecutive paired-valid U.S. business-day observations only.
paired=[]
for d in sorted(set(series['DGS2']) & set(series['NASDAQCOM'])):
    if series['DGS2'][d] is not None and series['NASDAQCOM'][d] is not None:
        paired.append(d)

candidates=[]
for i in range(1,len(paired)):
    prev,t=paired[i-1],paired[i]
    # Do not bridge an internal missing business-day observation in either series.
    between=[]
    x=prev+timedelta(days=1)
    while x<t:
        if x.weekday()<5: between.append(x)
        x+=timedelta(days=1)
    if any((series['DGS2'].get(x) is None or series['NASDAQCOM'].get(x) is None) for x in between):
        continue
    nas_ret=series['NASDAQCOM'][t]/series['NASDAQCOM'][prev]-1.0
    ychg=series['DGS2'][t]-series['DGS2'][prev]
    direction=0
    if nas_ret>0 and ychg<0: direction=1
    elif nas_ret<0 and ychg>0: direction=-1
    if direction==0: continue
    entry=t+timedelta(days=1); exitd=entry+timedelta(days=1)
    if exitd>LAST_EXIT: continue
    candidates.append({'macro_date':t,'prev_macro_date':prev,'entry_date':entry,'exit_date':exitd,'nasdaq_return':nas_ret,'dgs2_change':ychg,'direction':direction})

opens={}; archives=[]
for y,m in months(START,LAST_EXIT):
    stem=f'BTCUSDT-1d-{y:04d}-{m:02d}.zip'; url=f'{BASE}/{stem}'
    raw=fetch(url); zsha=sha_bytes(raw)
    try:
        chk=fetch(url+'.CHECKSUM').decode('utf-8','replace').strip().split()[0].lower()
        assert chk==zsha,(stem,chk,zsha); checksum=True
    except Exception as e:
        if isinstance(e,AssertionError): raise
        checksum=None
    z=zipfile.ZipFile(io.BytesIO(raw)); names=z.namelist(); assert len(names)==1
    n=0
    for row in csv.reader(io.StringIO(z.read(names[0]).decode('utf-8-sig'))):
        if not row: continue
        try: ts=int(row[0])
        except ValueError: continue
        if ts>10**15: ts//=1000
        dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc); assert (dt.hour,dt.minute,dt.second)==(0,0,0)
        dd=dt.date(); op=float(row[1]); assert op>0 and dd not in opens
        opens[dd]=op; n+=1
    assert n==monthrange(y,m)[1],(stem,n)
    archives.append({'file':stem,'sha256':zsha,'checksum_match':checksum,'rows':n})
assert min(opens)==START and max(opens)==LAST_EXIT and len(opens)==2467

trades=[]
for c in candidates:
    assert c['entry_date'] in opens and c['exit_date'] in opens
    gross=(opens[c['exit_date']]/opens[c['entry_date']]-1.0)*10000.0*c['direction']
    trades.append({
      'macro_date':str(c['macro_date']),'prev_macro_date':str(c['prev_macro_date']),
      'entry_date':str(c['entry_date']),'exit_date':str(c['exit_date']),
      'nasdaq_return':c['nasdaq_return'],'dgs2_change':c['dgs2_change'],
      'direction':'LONG' if c['direction']>0 else 'SHORT',
      'gross_bps':gross,'net6_bps':gross-6.0,'net10_bps':gross-10.0,'net20_bps':gross-20.0,
      'entry_year':c['entry_date'].year
    })
N=len(trades); assert N>0
mean=lambda k: sum(t[k] for t in trades)/N
gross=mean('gross_bps'); net6=mean('net6_bps'); net10=mean('net10_bps'); net20=mean('net20_bps')
med=median([t['gross_bps'] for t in trades])
pos=sum(t['net10_bps'] for t in trades if t['net10_bps']>0); neg=-sum(t['net10_bps'] for t in trades if t['net10_bps']<0)
pf=pos/neg if neg>0 else (1e99 if pos>0 else 0.0)
win=sum(t['net10_bps']>0 for t in trades)/N
wealth=1.0; peak=1.0; maxdd=0.0
for t in trades:
    wealth*=1+t['net10_bps']/10000.0; peak=max(peak,wealth); maxdd=min(maxdd,wealth/peak-1.0)
years={}
for y in sorted({t['entry_year'] for t in trades}):
    ys=[t for t in trades if t['entry_year']==y]
    years[str(y)]={'n':len(ys),'gross_mean_bps':sum(t['gross_bps'] for t in ys)/len(ys),'net10_mean_bps':sum(t['net10_bps'] for t in ys)/len(ys),'gross_sum_bps':sum(t['gross_bps'] for t in ys),'net10_sum_bps':sum(t['net10_bps'] for t in ys)}
nonneg=sum(v['net10_mean_bps']>=0 for v in years.values())
last4=sum(years.get(str(y),{'net10_mean_bps':-1e99})['net10_mean_bps']>=0 for y in (2021,2022,2023,2024))
posgross_by_year={str(y):sum(max(t['gross_bps'],0.0) for t in trades if t['entry_year']==y) for y in sorted({t['entry_year'] for t in trades})}
tot=sum(posgross_by_year.values()); maxshare=max(posgross_by_year.values())/tot if tot>0 else 1.0
rng=random.Random(CONTRACT['bootstrap']['seed']); vals=[t['net10_bps'] for t in trades]; boots=[]
for _ in range(CONTRACT['bootstrap']['resamples']):
    boots.append(sum(vals[rng.randrange(N)] for __ in range(N))/N)
ci=[quantile(boots,0.025),quantile(boots,0.975)]; p_nonpos=sum(x<=0 for x in boots)/len(boots)
checks={
 'n_min_500':N>=500,
 'mean_net10_gt_0':net10>0,
 'profit_factor_net10_gt_1':pf>1,
 'median_gross_gt_0':med>0,
 'at_least_4_calendar_years_nonnegative_net10':nonneg>=4,
 'at_least_3_of_2021_2024_nonnegative_net10':last4>=3,
 'single_year_positive_gross_contribution_le_0_60':maxshare<=0.60,
 'provenance_timestamp_firewall_pass':True,
 '2025_unopened':True,
 '2026_unopened':True
}
promote=all(checks.values()); classification='MVE0_SURVIVES_DISCOVERY' if promote else 'DISCOVERY_FAIL_NO_PROMOTION'
report={
 'lab':'MACRO-TRANSMISSION-001','mve_id':'MT-2Y-NASDAQ-001','version':'DISCOVERY_V0.1',
 'classification':classification,'promotion_pass':promote,'checks':checks,
 'n_trades':N,'long_count':sum(t['direction']=='LONG' for t in trades),'short_count':sum(t['direction']=='SHORT' for t in trades),
 'gross_mean_bps':gross,'net6_mean_bps':net6,'net10_mean_bps':net10,'net20_mean_bps':net20,
 'median_gross_bps':med,'profit_factor_net10':pf,'win_rate_net10':win,
 'cumulative_net10_return_pct':(wealth-1)*100,'max_drawdown_net10_pct':maxdd*100,
 'annual_breakdown':years,'nonnegative_year_count':nonneg,'last4_nonnegative_year_count':last4,
 'max_single_year_positive_gross_share':maxshare,
 'bootstrap_net10_mean_bps_ci95':ci,'bootstrap_p_mean_nonpositive':p_nonpos,
 'source_manifest':source_manifest,'binance_archives':len(archives),
 'btc_price_values_evaluated':True,'btc_returns_computed':True,'pnl_computed':True,
 'holdout_2025_accessed':False,'year_2026_accessed':False,'live_trading_authorized':False,'post_outcome_tuning_authorized':False,
 'contract_sha256':sha_file(ROOT/'MT_2Y_NASDAQ_001_DISCOVERY_CONTRACT_V01.json')
}
with (OUT/'MT_2Y_NASDAQ_001_TRADES_V01.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(trades[0].keys())); w.writeheader(); w.writerows(trades)
(OUT/'MT_2Y_NASDAQ_001_DISCOVERY_RESULT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
(OUT/'MT_2Y_NASDAQ_001_BINANCE_ARCHIVE_MANIFEST_V01.json').write_text(json.dumps(archives,indent=2,sort_keys=True))
print(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
print('DECISION:',classification)
print('2025 ACCESSED: NO')
print('2026 ACCESSED: NO')
print('LIVE TRADING AUTHORIZED: NO')
print('NO POST-OUTCOME TUNING AUTHORIZED')
