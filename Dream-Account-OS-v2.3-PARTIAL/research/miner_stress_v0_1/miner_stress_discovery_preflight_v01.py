#!/usr/bin/env python3
import hashlib, json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'source_gate_package'
OUT=ROOT/'preflight_output'
CONTRACT=ROOT/'MS_HASHDIFF_7D_001_DISCOVERY_CONTRACT_V01.json'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def utc_date(ts):
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).date()

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
actual={}
for name,exp in expected.items():
    p=SRC/name
    assert p.is_file(), f'MISSING_BOUND_SOURCE_FILE:{name}'
    got=sha256(p); actual[name]=got
    assert got==exp, (name, got, exp)

audit=json.loads((SRC/'MINER_STRESS_001_SOURCE_AUDIT_V01.json').read_text())
cov=json.loads((SRC/'MINER_STRESS_001_BTC_COVERAGE_V01.json').read_text())
assert audit['classification']=='MINER_SOURCE_PASS' and audit['structural_pass'] is True
assert audit['common_timestamp_count']==2557
assert audit['common_min_utc'].startswith('2018-01-01')
assert audit['common_max_utc'].startswith('2024-12-31')
assert audit['btc_price_values_evaluated'] is False
assert audit['btc_returns_computed'] is False and audit['pnl_computed'] is False
assert audit['holdout_2025_accessed'] is False and audit['year_2026_accessed'] is False
assert cov['coverage_pass'] is True and cov['archives_ok']==84 and cov['expected_days']==2557
assert cov['unique_days']==2557 and cov['missing_dates']==[]
assert cov['btc_price_values_evaluated'] is False
assert cov['btc_returns_computed'] is False and cov['pnl_computed'] is False
assert cov['holdout_2025_accessed'] is False and cov['year_2026_accessed'] is False

hr=json.loads((SRC/'hash_rate_raw.json').read_text())
df=json.loads((SRC/'difficulty_raw.json').read_text())
assert hr['status']=='ok' and hr['period']=='day' and 'Hash Rate' in hr['name']
assert df['status']=='ok' and df['period']=='day' and 'Difficulty' in df['name']
hdates=[utc_date(v['x']) for v in hr['values']]
ddates=[utc_date(v['x']) for v in df['values']]
assert len(hdates)==len(set(hdates))==2557
assert len(ddates)==len(set(ddates))==2557
assert hdates==ddates
assert hdates[0].isoformat()=='2018-01-01' and hdates[-1].isoformat()=='2024-12-31'
for a,b in zip(hdates,hdates[1:]):
    assert b-a==timedelta(days=1)

date_set=set(hdates)
structural=[]
for t in hdates:
    lag=t-timedelta(days=7)
    entry=t+timedelta(days=1)
    exitd=entry+timedelta(days=7)
    if lag in date_set and entry in date_set and exitd in date_set and exitd.year<=2024:
        structural.append(t)
assert structural[0].isoformat()=='2018-01-08'
assert structural[-1].isoformat()=='2024-12-23'
assert len(structural)==2542

def signal(r_now,r_lag):
    assert r_now>0 and r_lag>0
    return r_now/r_lag-1.0
assert signal(2.0,1.0)>0
assert signal(1.0,2.0)<0
assert signal(1.0,1.0)==0.0

OUT.mkdir(exist_ok=True)
receipt={
 'lab':'MINER-STRESS-001',
 'mve_id':'MS-HASHDIFF-7D-001',
 'classification':'PREOUTCOME_PREFLIGHT_PASS',
 'contract_sha256':sha256(CONTRACT),
 'bound_source_file_sha256':actual,
 'source_gate_run_id':c['source_gate']['run_id'],
 'source_gate_artifact_id':c['source_gate']['artifact_id'],
 'source_gate_artifact_zip_sha256':c['source_gate']['artifact_zip_sha256'],
 'source_rows':2557,
 'structural_signal_dates_before_zero_signal_rule':len(structural),
 'structural_signal_date_min':structural[0].isoformat(),
 'structural_signal_date_max':structural[-1].isoformat(),
 'formula_sign_tests_pass':True,
 'btc_price_values_opened':False,
 'btc_returns_computed':False,
 'pnl_computed':False,
 'performance_statistics_computed':False,
 'holdout_2025_accessed':False,
 'year_2026_accessed':False,
 'live_trading_authorized':False,
 'exchange_mutation_authorized':False,
 'discovery_outcomes_authorized_by_preflight':False
}
(OUT/'MINER_STRESS_001_DISCOVERY_PREFLIGHT_V01.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt,indent=2,sort_keys=True))
print('PREOUTCOME_PREFLIGHT_PASS / NO BTC PRICE VALUES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
