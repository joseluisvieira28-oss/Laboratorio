#!/usr/bin/env python3
import csv, hashlib, io, json, math, random, urllib.request, zipfile
from calendar import monthrange
from datetime import date, datetime, timezone
from pathlib import Path

ROOT=Path('.')
AUDIT=ROOT/'source_audit_output'
OUT=ROOT/'discovery_output'; OUT.mkdir(exist_ok=False)
CONTRACT=ROOT/'IF_CFTC_001_DISCOVERY_CONTRACT_V01.json'
LEDGER=AUDIT/'CFTC_TFF_BTC_133741_SOURCE_LEDGER_V01.csv'
CAL=AUDIT/'CFTC_PUBLICATION_EVENT_CALENDAR_V01.json'
POLICY=ROOT/'PUBLICATION_TIMING_POLICY_V01.json'
EXPECTED_LEDGER='a53879c7555f0946a72f502f7ba33c645d3c033ee8f40eb8d8f32c1c0372090c'
EXPECTED_POLICY='442eb0dd2f81878d8328cc970eab519aef1edb581a43566a328cc01c83030065'
BASE='https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d'
START=date(2018,4,1); END=date(2024,12,31)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def d(s): return date.fromisoformat(s[:10])
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'INSTITUTIONAL-FLOW-001-discovery/0.1'})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()
def months(a,b):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield y,m
        m+=1
        if m==13: y,m=y+1,1

def quantile(xs,q):
    ys=sorted(xs)
    if not ys: return None
    pos=(len(ys)-1)*q; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi: return ys[lo]
    return ys[lo]*(hi-pos)+ys[hi]*(pos-lo)

contract=json.loads(CONTRACT.read_text())
assert contract['status']=='FROZEN_PRE_OUTCOME'
assert contract['holdout_2025']=='LOCKED' and contract['year_2026']=='FORBIDDEN'
assert contract['post_outcome_tuning'] is False and contract['live_trading'] is False
assert sha(LEDGER)==EXPECTED_LEDGER,(sha(LEDGER),EXPECTED_LEDGER)
assert sha(POLICY)==EXPECTED_POLICY,(sha(POLICY),EXPECTED_POLICY)
assert contract['source_ledger_sha256_expected']==EXPECTED_LEDGER
assert contract['publication_timing_policy_sha256_expected']==EXPECTED_POLICY

events=json.loads(CAL.read_text())
event_by_report={x['report_date']:x for x in events}
rows=list(csv.DictReader(LEDGER.open(encoding='utf-8')))
assert len(rows)==352
candidates=[]
for i in range(1,len(rows)):
    prev,cur=rows[i-1],rows[i]
    pe=event_by_report[prev['report_date_as_yyyy_mm_dd'][:10]]
    ce=event_by_report[cur['report_date_as_yyyy_mm_dd'][:10]]
    if not (pe['eligible_for_future_discovery'] and ce['eligible_for_future_discovery']):
        continue
    oi=float(cur['open_interest_all']); assert oi>0
    p_oi=float(prev['open_interest_all']); assert p_oi>0
    share=(float(cur['asset_mgr_positions_long'])-float(cur['asset_mgr_positions_short']))/oi
    prev_share=(float(prev['asset_mgr_positions_long'])-float(prev['asset_mgr_positions_short']))/p_oi
    signal=share-prev_share
    if signal==0: continue
    entry=d(ce['entry_date']); exitd=d(ce['exit_date'])
    assert entry<=END and exitd<=END
    candidates.append({'report_date':ce['report_date'],'entry_date':entry,'exit_date':exitd,'signal':signal,'direction':1 if signal>0 else -1})

opens={}; archive_manifest=[]
for y,m in months(START,END):
    stem=f'BTCUSDT-1d-{y:04d}-{m:02d}.zip'; url=f'{BASE}/{stem}'
    raw=fetch(url); zsha=hashlib.sha256(raw).hexdigest()
    try:
        chk=fetch(url+'.CHECKSUM').decode('utf-8','replace').strip().split()[0].lower()
        assert chk==zsha,(stem,chk,zsha)
        checksum=True
    except Exception as e:
        if isinstance(e,AssertionError): raise
        checksum=None
    z=zipfile.ZipFile(io.BytesIO(raw)); names=z.namelist(); assert len(names)==1
    content=z.read(names[0]).decode('utf-8-sig')
    n=0
    for row in csv.reader(io.StringIO(content)):
        if not row: continue
        try: ts=int(row[0])
        except ValueError: continue
        if ts>10**15: ts//=1000
        dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc); assert (dt.hour,dt.minute,dt.second)==(0,0,0)
        dd=dt.date(); op=float(row[1]); assert op>0
        assert dd not in opens
        opens[dd]=op; n+=1
    assert n==monthrange(y,m)[1],(stem,n)
    archive_manifest.append({'file':stem,'sha256':zsha,'checksum_match':checksum,'rows':n})
assert min(opens)==START and max(opens)==END and len(opens)==2467

trades=[]
for x in candidates:
    assert x['entry_date'] in opens and x['exit_date'] in opens
    entry=opens[x['entry_date']]; exitp=opens[x['exit_date']]
    gross=(exitp/entry-1.0)*10000.0*x['direction']
    t={
      'report_date':x['report_date'],'entry_date':str(x['entry_date']),'exit_date':str(x['exit_date']),
      'signal':x['signal'],'direction':'LONG' if x['direction']>0 else 'SHORT',
      'gross_bps':gross,'net6_bps':gross-6.0,'net10_bps':gross-10.0,'net20_bps':gross-20.0,
      'entry_year':x['entry_date'].year
    }
    trades.append(t)

assert trades and all(t['exit_date']<='2024-12-31' for t in trades)
N=len(trades)
def mean(key): return sum(t[key] for t in trades)/N
def median(vals):
    s=sorted(vals); n=len(s); return s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2

gross_mean=mean('gross_bps'); net6=mean('net6_bps'); net10=mean('net10_bps'); net20=mean('net20_bps')
med_gross=median([t['gross_bps'] for t in trades])
pos=sum(t['net10_bps'] for t in trades if t['net10_bps']>0); neg=-sum(t['net10_bps'] for t in trades if t['net10_bps']<0)
pf=(pos/neg) if neg>0 else (1e99 if pos>0 else 0.0)
win=sum(1 for t in trades if t['net10_bps']>0)/N
wealth=1.0; peak=1.0; maxdd=0.0
for t in trades:
    wealth*=1.0+t['net10_bps']/10000.0
    peak=max(peak,wealth); maxdd=min(maxdd,wealth/peak-1.0)

years={}
for y in sorted({t['entry_year'] for t in trades}):
    ys=[t for t in trades if t['entry_year']==y]
    years[str(y)]={
      'n':len(ys),'gross_mean_bps':sum(t['gross_bps'] for t in ys)/len(ys),
      'net10_mean_bps':sum(t['net10_bps'] for t in ys)/len(ys),
      'gross_sum_bps':sum(t['gross_bps'] for t in ys),
      'net10_sum_bps':sum(t['net10_bps'] for t in ys)
    }
nonneg_years=sum(1 for v in years.values() if v['net10_mean_bps']>=0)
last4=[str(y) for y in (2021,2022,2023,2024) if str(y) in years]
last4_nonneg=sum(1 for y in last4 if years[y]['net10_mean_bps']>=0)
posgross_by_year={y:sum(max(t['gross_bps'],0.0) for t in trades if str(t['entry_year'])==y) for y in years}
total_posgross=sum(posgross_by_year.values())
max_year_posgross_share=max(posgross_by_year.values())/total_posgross if total_posgross>0 else 1.0

rng=random.Random(contract['bootstrap']['seed']); vals=[t['net10_bps'] for t in trades]; boots=[]
for _ in range(9999):
    boots.append(sum(vals[rng.randrange(N)] for __ in range(N))/N)
boot_ci=[quantile(boots,0.025),quantile(boots,0.975)]
boot_p_nonpos=sum(1 for x in boots if x<=0)/len(boots)

longs=sum(1 for t in trades if t['direction']=='LONG'); shorts=N-longs
checks={
 'n_min_200':N>=200,
 'mean_net10_gt_0':net10>0,
 'profit_factor_net10_gt_1':pf>1,
 'median_gross_gt_0':med_gross>0,
 'at_least_4_calendar_years_nonnegative_net10':nonneg_years>=4,
 'at_least_3_last4_years_nonnegative_net10':last4_nonneg>=3,
 'single_year_positive_gross_contribution_le_0_60':max_year_posgross_share<=0.60,
 'provenance_timestamp_firewall_pass':True,
 '2025_unopened':True,
 '2026_unopened':True
}
promote=all(checks.values())
classification='MVE0_SURVIVES_DISCOVERY' if promote else 'DISCOVERY_FAIL_NO_PROMOTION'
report={
 'lab':'INSTITUTIONAL-FLOW-001','mve_id':'IF-CFTC-001','version':'DISCOVERY_V0.1',
 'classification':classification,'promotion_pass':promote,'checks':checks,
 'n_trades':N,'long_count':longs,'short_count':shorts,
 'gross_mean_bps':gross_mean,'net6_mean_bps':net6,'net10_mean_bps':net10,'net20_mean_bps':net20,
 'median_gross_bps':med_gross,'profit_factor_net10':pf,'win_rate_net10':win,
 'cumulative_net10_return_pct':(wealth-1.0)*100.0,'max_drawdown_net10_pct':maxdd*100.0,
 'annual_breakdown':years,'nonnegative_year_count':nonneg_years,'last4_nonnegative_year_count':last4_nonneg,
 'max_single_year_positive_gross_share':max_year_posgross_share,
 'bootstrap_net10_mean_bps_ci95':boot_ci,'bootstrap_p_mean_nonpositive':boot_p_nonpos,
 'source_ledger_sha256':sha(LEDGER),'publication_timing_policy_sha256':sha(POLICY),
 'contract_sha256':sha(CONTRACT),'binance_archives':len(archive_manifest),
 'btc_returns_computed':True,'pnl_computed':True,'holdout_2025_accessed':False,'year_2026_accessed':False,
 'live_trading_authorized':False,'post_outcome_tuning_authorized':False
}
with (OUT/'IF_CFTC_001_TRADES_V01.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(trades[0].keys())); w.writeheader(); w.writerows(trades)
(OUT/'IF_CFTC_001_BINANCE_ARCHIVE_MANIFEST_V01.json').write_text(json.dumps(archive_manifest,indent=2,sort_keys=True))
(OUT/'IF_CFTC_001_DISCOVERY_RESULT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
print(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
print('DECISION:',classification)
print('2025 ACCESSED: NO')
print('2026 ACCESSED: NO')
print('LIVE TRADING AUTHORIZED: NO')
print('NO POST-OUTCOME TUNING AUTHORIZED')
