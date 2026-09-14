#!/usr/bin/env python3
import csv, hashlib, json, urllib.parse, urllib.request, urllib.error
from collections import Counter
from datetime import datetime
from pathlib import Path

DATASET='gpe5-46if'
CODE='133741'
START='2018-01-01T00:00:00.000'
END='2024-12-31T00:00:00.000'
OUT=Path('source_audit_output')
OUT.mkdir(exist_ok=True)

fields=[
 'id','market_and_exchange_names','report_date_as_yyyy_mm_dd','yyyy_report_week_ww',
 'contract_market_name','cftc_contract_market_code','commodity_name','open_interest_all',
 'dealer_positions_long_all','dealer_positions_short_all','dealer_positions_spread_all',
 'asset_mgr_positions_long','asset_mgr_positions_short','asset_mgr_positions_spread',
 'lev_money_positions_long','lev_money_positions_short','lev_money_positions_spread'
]
select=','.join(fields)
where=(f"cftc_contract_market_code='{CODE}' AND "
       f"report_date_as_yyyy_mm_dd between '{START}' and '{END}'")
params=urllib.parse.urlencode({'$select':select,'$where':where,'$order':'report_date_as_yyyy_mm_dd','$limit':5000})
url=f'https://publicreporting.cftc.gov/resource/{DATASET}.json?{params}'
req=urllib.request.Request(url,headers={'User-Agent':'INSTITUTIONAL-FLOW-001-source-audit/0.1','Accept':'application/json'})
try:
    with urllib.request.urlopen(req,timeout=120) as r:
        rows=json.loads(r.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    body=e.read().decode('utf-8','replace')
    print('CFTC_HTTP_ERROR',e.code,body[:4000])
    raise

required=['id','report_date_as_yyyy_mm_dd','cftc_contract_market_code','open_interest_all','asset_mgr_positions_long','asset_mgr_positions_short']
missing_fields=[f for f in required if rows and f not in rows[0]]

def dt(s): return datetime.fromisoformat(s.replace('Z','+00:00')).date()
dates=[dt(r['report_date_as_yyyy_mm_dd']) for r in rows if r.get('report_date_as_yyyy_mm_dd')]
ids=[r.get('id','') for r in rows]
code_bad=[r for r in rows if r.get('cftc_contract_market_code')!=CODE]
null_required=[]; nonpos_oi=[]
for r in rows:
    for f in required:
        if r.get(f) in (None,''):
            null_required.append((r.get('id'),f))
    try:
        if float(r.get('open_interest_all') or 0)<=0: nonpos_oi.append(r.get('id'))
    except Exception: nonpos_oi.append(r.get('id'))

weekday_counts=Counter(d.weekday() for d in dates)
non_tuesday_dates=[str(d) for d in dates if d.weekday()!=1]
dup_dates=[str(d) for d,c in Counter(dates).items() if c>1]
dup_ids=[i for i,c in Counter(ids).items() if i and c>1]
gaps=[]
for a,b in zip(dates,dates[1:]):
    dd=(b-a).days
    if dd>14: gaps.append({'from':str(a),'to':str(b),'days':dd})

ledger=OUT/'CFTC_TFF_BTC_133741_SOURCE_LEDGER_V01.csv'
with ledger.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
    w.writeheader()
    for r in rows: w.writerow({k:r.get(k,'') for k in fields})
ledger_sha=hashlib.sha256(ledger.read_bytes()).hexdigest()

report={
 'lab':'INSTITUTIONAL-FLOW-001','mode':'SOURCE_DATA_AUDIT_ONLY','dataset':DATASET,
 'source_url_base':f'https://publicreporting.cftc.gov/resource/{DATASET}.json',
 'cftc_contract_market_code':CODE,'requested_window':{'start':'2018-01-01','end':'2024-12-31'},
 'rows':len(rows),'date_min':str(min(dates)) if dates else None,'date_max':str(max(dates)) if dates else None,
 'unique_dates':len(set(dates)),'duplicate_dates':dup_dates,'duplicate_ids':dup_ids,
 'missing_fields':missing_fields,'null_required_count':len(null_required),'nonpositive_open_interest_count':len(nonpos_oi),
 'wrong_contract_code_count':len(code_bad),'weekday_counts':dict(weekday_counts),'non_tuesday_report_dates':non_tuesday_dates,
 'gaps_gt_14_days':gaps,'min_required_weeks':250,'sample_gate_pass':len(set(dates))>=250,
 'field_gate_pass':not missing_fields and not null_required and not nonpos_oi and not code_bad,
 'uniqueness_gate_pass':not dup_dates and not dup_ids,
 'audit_categories_retained':['dealer_intermediary','asset_manager_institutional','leveraged_money'],
 'source_ledger_file':ledger.name,'source_ledger_sha256':ledger_sha,
 'publication_timing_rule':'CFTC reports Tuesday positions, generally published Friday 15:30 ET; holiday/shutdown/cyber delay periods require separately frozen publication-timing policy before Discovery.',
 'publication_timing_gate_complete':False,'btc_price_coverage_gate_complete':False,
 'outcomes_computed':False,'btc_returns_computed':False,'pnl_computed':False,
 'holdout_2025_accessed':False,'year_2026_accessed':False,'live_trading_authorized':False,
}
report['structural_status']='SOURCE_DATA_STRUCTURAL_PASS' if report['sample_gate_pass'] and report['field_gate_pass'] and report['uniqueness_gate_pass'] else 'SOURCE_DATA_BLOCKED'
report['status']='SOURCE_DATA_PENDING_TIMING_AND_PRICE' if report['structural_status']=='SOURCE_DATA_STRUCTURAL_PASS' else 'SOURCE_DATA_BLOCKED'
(OUT/'CFTC_TFF_SOURCE_AUDIT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
print('NO BTC RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
raise SystemExit(0 if report['structural_status']=='SOURCE_DATA_STRUCTURAL_PASS' else 2)
