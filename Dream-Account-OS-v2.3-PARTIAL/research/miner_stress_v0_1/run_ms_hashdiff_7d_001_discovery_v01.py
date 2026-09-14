#!/usr/bin/env python3
import csv, hashlib, io, json, math, os, random, statistics, urllib.request, zipfile
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'source_gate_package'
OUT=ROOT/'discovery_output'
CONTRACT=ROOT/'MS_HASHDIFF_7D_001_DISCOVERY_CONTRACT_V01.json'
EXPECTED_CONTRACT_SHA256='a761fee0a59d5aee013d7e42ae42e429e884a2976bae404b823471a3c468d6e4'
BASE='https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d'
START=date(2018,1,1); END=date(2024,12,31)

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def sha256_file(p): return sha256_bytes(p.read_bytes())
def utc_date(ts): return datetime.fromtimestamp(int(ts),tz=timezone.utc).date()
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'MINER-STRESS-001-discovery/0.1'})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()
def iter_months():
    for y in range(2018,2025):
        for m in range(1,13):
            yield y,m
def quantile(xs,q):
    ys=sorted(xs)
    if not ys: return None
    pos=(len(ys)-1)*q; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi: return ys[lo]
    return ys[lo]*(hi-pos)+ys[hi]*(pos-lo)
def circular_block_bootstrap_means(vals, block_len, resamples, seed):
    n=len(vals); rng=random.Random(seed); out=[]
    for _ in range(resamples):
        sample=[]
        while len(sample)<n:
            s=rng.randrange(n)
            sample.extend(vals[(s+j)%n] for j in range(block_len))
        out.append(sum(sample[:n])/n)
    return out

if os.environ.get('MS_DISCOVERY_AUTHORIZATION')!='AUTHORIZED_ONE_SHOT':
    raise SystemExit('DISCOVERY_LOCKED: explicit one-shot workflow authorization token absent')

assert sha256_file(CONTRACT)==EXPECTED_CONTRACT_SHA256
c=json.loads(CONTRACT.read_text())
assert c['status']=='FROZEN_PRE_OUTCOME_IMPLEMENTATION'
assert c['holdout_2025']=='LOCKED' and c['year_2026']=='LOCKED'
assert c['live_trading'] is False and c['exchange_mutation'] is False
assert c['post_outcome_tuning'] is False and c['rerun_for_outcome_improvement'] is False

expected={
 'MINER_STRESS_001_SOURCE_AUDIT_V01.json':c['source_gate']['source_audit_sha256'],
 'MINER_STRESS_001_BTC_COVERAGE_V01.json':c['source_gate']['btc_coverage_sha256'],
 'hash_rate_raw.json':c['source_gate']['hash_rate_raw_sha256'],
 'difficulty_raw.json':c['source_gate']['difficulty_raw_sha256'],
}
for name,exp in expected.items():
    p=SRC/name
    assert p.is_file(), f'MISSING_BOUND_SOURCE_FILE:{name}'
    assert sha256_file(p)==exp,(name,sha256_file(p),exp)

audit=json.loads((SRC/'MINER_STRESS_001_SOURCE_AUDIT_V01.json').read_text())
coverage=json.loads((SRC/'MINER_STRESS_001_BTC_COVERAGE_V01.json').read_text())
assert audit['classification']=='MINER_SOURCE_PASS' and audit['structural_pass'] is True
assert audit['common_timestamp_count']==2557
assert audit['holdout_2025_accessed'] is False and audit['year_2026_accessed'] is False
assert coverage['coverage_pass'] is True and coverage['archives_ok']==84 and coverage['unique_days']==2557
assert coverage['holdout_2025_accessed'] is False and coverage['year_2026_accessed'] is False

hr=json.loads((SRC/'hash_rate_raw.json').read_text())
df=json.loads((SRC/'difficulty_raw.json').read_text())
h={utc_date(v['x']):float(v['y']) for v in hr['values']}
d={utc_date(v['x']):float(v['y']) for v in df['values']}
assert len(h)==len(d)==2557 and set(h)==set(d)
assert min(h)==START and max(h)==END
assert all(v>0 and math.isfinite(v) for v in h.values())
assert all(v>0 and math.isfinite(v) for v in d.values())

ratios={k:h[k]/d[k] for k in h}
candidates=[]
for t in sorted(ratios):
    lag=t-timedelta(days=7)
    entry=t+timedelta(days=1)
    exitd=entry+timedelta(days=7)
    if lag not in ratios or entry not in ratios or exitd not in ratios:
        continue
    assert exitd<=END
    s=ratios[t]/ratios[lag]-1.0
    if s==0.0:
        continue
    candidates.append({'signal_date':t,'entry_date':entry,'exit_date':exitd,'signal':s,'direction':1 if s>0 else -1})
assert len(candidates)>=500
assert all(x['signal_date']<=date(2024,12,23) and x['exit_date']<=END for x in candidates)

opens={}; archive_manifest=[]
for y,m in iter_months():
    stem=f'BTCUSDT-1d-{y:04d}-{m:02d}.zip'; url=f'{BASE}/{stem}'
    raw=fetch(url); zsha=sha256_bytes(raw)
    checksum_match=None
    try:
        chk=fetch(url+'.CHECKSUM').decode('utf-8','replace').strip().split()[0].lower()
        assert chk==zsha,(stem,chk,zsha)
        checksum_match=True
    except Exception as e:
        if isinstance(e,AssertionError): raise
        checksum_match=None
    z=zipfile.ZipFile(io.BytesIO(raw)); names=z.namelist(); assert len(names)==1
    content=z.read(names[0]).decode('utf-8-sig')
    seen=0
    for row in csv.reader(io.StringIO(content)):
        if not row: continue
        try: ts=int(row[0])
        except ValueError: continue
        if ts>10**15: ts//=1000
        dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc)
        assert (dt.hour,dt.minute,dt.second)==(0,0,0)
        dd=dt.date(); op=float(row[1])
        assert START<=dd<=END and op>0 and math.isfinite(op)
        assert dd not in opens
        opens[dd]=op; seen+=1
    assert seen==monthrange(y,m)[1],(stem,seen)
    archive_manifest.append({'file':stem,'sha256':zsha,'checksum_match':checksum_match,'rows':seen})
assert len(archive_manifest)==84
assert len(opens)==2557 and min(opens)==START and max(opens)==END

trades=[]
for x in candidates:
    entry=opens[x['entry_date']]; exitp=opens[x['exit_date']]
    gross=(exitp/entry-1.0)*10000.0*x['direction']
    trades.append({'signal_date':x['signal_date'].isoformat(),'entry_date':x['entry_date'].isoformat(),'exit_date':x['exit_date'].isoformat(),'signal':x['signal'],'direction':'LONG' if x['direction']>0 else 'SHORT','gross_bps':gross,'net6_bps':gross-6.0,'net10_bps':gross-10.0,'net20_bps':gross-20.0,'entry_year':x['entry_date'].year})
assert trades and len(trades)==len(candidates)
assert all(t['exit_date']<='2024-12-31' for t in trades)
N=len(trades)

def mean_key(key, xs=trades): return sum(t[key] for t in xs)/len(xs)
gross_mean=mean_key('gross_bps')
net6=mean_key('net6_bps'); net10=mean_key('net10_bps'); net20=mean_key('net20_bps')
med_gross=statistics.median(t['gross_bps'] for t in trades)
pos=sum(t['net10_bps'] for t in trades if t['net10_bps']>0)
neg=-sum(t['net10_bps'] for t in trades if t['net10_bps']<0)
pf=pos/neg if neg>0 else (1e99 if pos>0 else 0.0)
win=sum(1 for t in trades if t['net10_bps']>0)/N
longs=sum(1 for t in trades if t['direction']=='LONG'); shorts=N-longs

years={}
for y in sorted({t['entry_year'] for t in trades}):
    ys=[t for t in trades if t['entry_year']==y]
    years[str(y)]={'n':len(ys),'gross_mean_bps':sum(t['gross_bps'] for t in ys)/len(ys),'gross_sum_bps':sum(t['gross_bps'] for t in ys),'net10_mean_bps':sum(t['net10_bps'] for t in ys)/len(ys),'net10_sum_bps':sum(t['net10_bps'] for t in ys)}
nonneg=sum(1 for v in years.values() if v['net10_mean_bps']>=0)
last4_nonneg=sum(1 for y in ('2021','2022','2023','2024') if y in years and years[y]['net10_mean_bps']>=0)
positive_year_gross={y:max(v['gross_sum_bps'],0.0) for y,v in years.items()}
total_positive_year_gross=sum(positive_year_gross.values())
max_year_share=max(positive_year_gross.values())/total_positive_year_gross if total_positive_year_gross>0 else 1.0

vals=[t['net10_bps'] for t in trades]
b=c['bootstrap']
boots=circular_block_bootstrap_means(vals,b['block_length_trades'],b['resamples'],b['seed'])
ci=[quantile(boots,b['ci'][0]),quantile(boots,b['ci'][1])]
p_nonpos=sum(1 for x in boots if x<=0)/len(boots)

signals=[t['signal'] for t in trades]
sig_sorted=sorted(signals)
signal_summary={'mean':sum(signals)/N,'median':statistics.median(signals),'q05':quantile(signals,0.05),'q25':quantile(signals,0.25),'q75':quantile(signals,0.75),'q95':quantile(signals,0.95),'min':sig_sorted[0],'max':sig_sorted[-1]}

checks={
 'n_trades_min_500':N>=500,
 'mean_net10_gt_0':net10>0,
 'profit_factor_net10_gt_1':pf>1.0,
 'median_gross_gt_0':med_gross>0,
 'bootstrap_one_sided_p_lt_0_10':p_nonpos<0.10,
 'at_least_4_calendar_years_nonnegative_net10':nonneg>=4,
 'at_least_3_of_2021_2024_nonnegative_net10':last4_nonneg>=3,
 'single_positive_year_gross_contribution_le_0_60':max_year_share<=0.60,
 'provenance_timestamp_firewall_pass':True,
 '2025_unopened':True,
 '2026_unopened':True
}
promote=all(checks.values())
classification='MVE0_SURVIVES_DISCOVERY' if promote else 'DISCOVERY_FAIL_NO_PROMOTION'

report={
 'lab':'MINER-STRESS-001','mve_id':'MS-HASHDIFF-7D-001','version':'DISCOVERY_V0.1','classification':classification,'promotion_pass':promote,'checks':checks,
 'n_trades':N,'long_count':longs,'short_count':shorts,'gross_mean_bps':gross_mean,'net6_mean_bps':net6,'net10_mean_bps':net10,'net20_mean_bps':net20,
 'median_gross_bps':med_gross,'profit_factor_net10':pf,'win_rate_net10':win,'annual_breakdown':years,'nonnegative_year_count':nonneg,'last4_nonnegative_year_count':last4_nonneg,
 'max_single_positive_year_gross_share':max_year_share,'bootstrap_method':b['method'],'bootstrap_block_length_trades':b['block_length_trades'],'bootstrap_net10_mean_bps_ci95':ci,'bootstrap_p_mean_nonpositive':p_nonpos,
 'signal_summary':signal_summary,'source_gate_run_id':c['source_gate']['run_id'],'source_gate_artifact_id':c['source_gate']['artifact_id'],'source_gate_artifact_zip_sha256':c['source_gate']['artifact_zip_sha256'],
 'source_audit_sha256':sha256_file(SRC/'MINER_STRESS_001_SOURCE_AUDIT_V01.json'),'hash_rate_raw_sha256':sha256_file(SRC/'hash_rate_raw.json'),'difficulty_raw_sha256':sha256_file(SRC/'difficulty_raw.json'),'contract_sha256':sha256_file(CONTRACT),
 'binance_archives':len(archive_manifest),'overlapping_trade_event_study':True,'portfolio_compounding_or_drawdown_reported':False,
 'btc_price_values_opened':True,'btc_returns_computed':True,'pnl_computed':True,'holdout_2025_accessed':False,'year_2026_accessed':False,'live_trading_authorized':False,'exchange_mutation_authorized':False,'post_outcome_tuning_authorized':False
}

OUT.mkdir(exist_ok=False)
with (OUT/'MS_HASHDIFF_7D_001_TRADES_V01.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(trades[0].keys())); w.writeheader(); w.writerows(trades)
(OUT/'MS_HASHDIFF_7D_001_BINANCE_ARCHIVE_MANIFEST_V01.json').write_text(json.dumps(archive_manifest,indent=2,sort_keys=True)+'\n')
(OUT/'MS_HASHDIFF_7D_001_DISCOVERY_RESULT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')
print(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
print('DECISION:',classification)
print('2025 ACCESSED: NO / 2026 ACCESSED: NO / LIVE: NO / EXCHANGE MUTATION: NO')
print('NO POST-OUTCOME TUNING OR OUTCOME-IMPROVEMENT RERUN AUTHORIZED')
