#!/usr/bin/env python3
import csv, io, json, urllib.parse, urllib.request
from collections import Counter
from datetime import date, datetime
from pathlib import Path

DATASET='gpe5-46if'
CODE='133741'
START='2018-01-01T00:00:00.000'
END='2024-12-31T00:00:00.000'
OUT=Path('source_audit_output')
OUT.mkdir(exist_ok=True)

select = ','.join([
    'id','market_and_exchange_names','report_date_as_yyyy_mm_dd','yyyy_report_week_ww',
    'contract_market_name','cftc_contract_market_code','commodity_name','open_interest_all',
    'asset_mgr_positions_long','asset_mgr_positions_short','asset_mgr_positions_spread_all',
    'lev_money_positions_long_all','lev_money_positions_short_all'
])
query=(f"SELECT {select} WHERE cftc_contract_market_code='{CODE}' "
       f"AND report_date_as_yyyy_mm_dd between '{START}' and '{END}' "
       f"ORDER BY report_date_as_yyyy_mm_dd")
params=urllib.parse.urlencode({'pageNumber':1,'pageSize':5000,'query':query})
url=f'https://publicreporting.cftc.gov/api/v3/views/{DATASET}/query.csv?{params}'
req=urllib.request.Request(url,headers={'User-Agent':'INSTITUTIONAL-FLOW-001-source-audit/0.1'})
with urllib.request.urlopen(req,timeout=120) as r:
    raw=r.read()
rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))

required=['id','report_date_as_yyyy_mm_dd','cftc_contract_market_code','open_interest_all','asset_mgr_positions_long','asset_mgr_positions_short']
missing_fields=[f for f in required if rows and f not in rows[0]]

def dt(s): return datetime.fromisoformat(s.replace('Z','+00:00')).date()
dates=[dt(r['report_date_as_yyyy_mm_dd']) for r in rows if r.get('report_date_as_yyyy_mm_dd')]
ids=[r.get('id','') for r in rows]
code_bad=[r for r in rows if r.get('cftc_contract_market_code')!=CODE]
null_required=[]
nonpos_oi=[]
for r in rows:
    for f in required:
        if r.get(f) in (None,''):
            null_required.append((r.get('id'),f))
    try:
        if float(r.get('open_interest_all') or 0)<=0: nonpos_oi.append(r.get('id'))
    except Exception: nonpos_oi.append(r.get('id'))

weekday_counts=Counter(d.weekday() for d in dates)
dup_dates=[str(d) for d,c in Counter(dates).items() if c>1]
dup_ids=[i for i,c in Counter(ids).items() if i and c>1]
gaps=[]
for a,b in zip(dates,dates[1:]):
    dd=(b-a).days
    if dd>14: gaps.append({'from':str(a),'to':str(b),'days':dd})

report={
 'lab':'INSTITUTIONAL-FLOW-001',
 'mode':'SOURCE_DATA_AUDIT_ONLY',
 'dataset':DATASET,
 'cftc_contract_market_code':CODE,
 'requested_window':{'start':'2018-01-01','end':'2024-12-31'},
 'rows':len(rows),
 'date_min':str(min(dates)) if dates else None,
 'date_max':str(max(dates)) if dates else None,
 'unique_dates':len(set(dates)),
 'duplicate_dates':dup_dates,
 'duplicate_ids':dup_ids,
 'missing_fields':missing_fields,
 'null_required_count':len(null_required),
 'nonpositive_open_interest_count':len(nonpos_oi),
 'wrong_contract_code_count':len(code_bad),
 'weekday_counts':dict(weekday_counts),
 'gaps_gt_14_days':gaps,
 'min_required_weeks':250,
 'sample_gate_pass':len(set(dates))>=250,
 'field_gate_pass':not missing_fields and not null_required and not nonpos_oi and not code_bad,
 'uniqueness_gate_pass':not dup_dates and not dup_ids,
 'publication_timing_rule':'CFTC reports Tuesday positions, generally published Friday 15:30 ET; actual holiday-shift release dates require schedule-aware handling before Discovery.',
 'outcomes_computed':False,
 'btc_returns_computed':False,
 'pnl_computed':False,
 'holdout_2025_accessed':False,
 'year_2026_accessed':False,
 'live_trading_authorized':False,
}
report['status']='SOURCE_DATA_PASS' if report['sample_gate_pass'] and report['field_gate_pass'] and report['uniqueness_gate_pass'] else 'SOURCE_DATA_BLOCKED'
(OUT/'CFTC_TFF_SOURCE_AUDIT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
print('NO BTC RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
raise SystemExit(0 if report['status']=='SOURCE_DATA_PASS' else 2)
