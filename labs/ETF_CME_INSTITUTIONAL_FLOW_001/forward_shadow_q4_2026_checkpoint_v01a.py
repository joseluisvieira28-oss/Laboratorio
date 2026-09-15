#!/usr/bin/env python3
import csv, io, json, os, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

LAB='ETF-CME-INSTFLOW-001'
STUDY='ETF-CME-INSTFLOW-001-FORWARD-SHADOW-Q4-2026-V0.1A'
DATASET='6dca-aqww'
CODE='133741'
PRIOR_ASOF=datetime(2026,9,8,tzinfo=timezone.utc).date()
FIRST_ASOF=datetime(2026,9,15,tzinfo=timezone.utc).date()
LAST_ASOF=datetime(2026,12,15,tzinfo=timezone.utc).date()
LATEST_EXIT=datetime(2026,12,31,tzinfo=timezone.utc).date()
OUT='artifacts/etf_cme_forward_shadow_q4_2026_v01a'
os.makedirs(OUT,exist_ok=True)
BASE=f'https://publicreporting.cftc.gov/resource/{DATASET}.csv'


def fetch_rows(params):
    url=BASE+'?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={'User-Agent':'ETF-CME-INSTFLOW-001-forward-shadow/0.1A'})
    with urllib.request.urlopen(req,timeout=120) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))


def parse_row(row):
    d=datetime.fromisoformat(row['report_date_as_yyyy_mm_dd'].replace('Z','+00:00')).date()
    return {
        'as_of': d,
        'oi': float(row['open_interest_all']),
        'nl': float(row['noncomm_positions_long_all']),
        'ns': float(row['noncomm_positions_short_all']),
    }


def fail_receipt(classification, error):
    receipt={
        'lab':LAB,
        'study_id':STUDY,
        'stage':'PROSPECTIVE_SOURCE_ONLY_CHECKPOINT',
        'classification':classification,
        'error':str(error),
        'required_prior_state_as_of':PRIOR_ASOF.isoformat(),
        'outcomes_fetched':False,
        'new_market_outcomes_accessed':False,
        'pre_freeze_2026_outcomes_accessed':False,
        'live_trading':False,
        'exchange_mutation':False,
        'post_outcome_tuning':False,
        'tier_effect':'NONE_AUTOMATIC',
    }
    json.dump(receipt,open(os.path.join(OUT,'forward_shadow_checkpoint_receipt_v01a.json'),'w'),indent=2,sort_keys=True)
    print(json.dumps(receipt,indent=2,sort_keys=True))
    raise SystemExit(2)

try:
    prior_where=(f"cftc_contract_market_code='{CODE}' AND report_date_as_yyyy_mm_dd < "
                 f"'{FIRST_ASOF.isoformat()}T00:00:00.000'")
    prior_raw=fetch_rows({'$limit':'1','$order':'report_date_as_yyyy_mm_dd DESC','$where':prior_where})
    if len(prior_raw)!=1:
        fail_receipt('SOURCE_DATA_BLOCKED',f'PRIOR_STATE_ROW_COUNT {len(prior_raw)}/1')
    prior=parse_row(prior_raw[0])
    if prior['as_of']!=PRIOR_ASOF:
        fail_receipt('SOURCE_DATA_BLOCKED',f'PRIOR_STATE_DATE_MISMATCH {prior["as_of"]} != {PRIOR_ASOF}')

    prospective_where=(f"cftc_contract_market_code='{CODE}' AND report_date_as_yyyy_mm_dd between "
                       f"'{FIRST_ASOF.isoformat()}T00:00:00.000' and '{LAST_ASOF.isoformat()}T23:59:59.999'")
    prospective_raw=fetch_rows({'$limit':'5000','$order':'report_date_as_yyyy_mm_dd ASC','$where':prospective_where})
    parsed=[parse_row(r) for r in prospective_raw]
except SystemExit:
    raise
except Exception as e:
    fail_receipt('SOURCE_DATA_BLOCKED',e)

seen=set()
for row in parsed:
    d=row['as_of']
    if not (FIRST_ASOF <= d <= LAST_ASOF):
        fail_receipt('SOURCE_DATA_BLOCKED',f'CFTC_ROW_OUTSIDE_PROSPECTIVE_WINDOW {d}')
    if d in seen:
        fail_receipt('SOURCE_DATA_BLOCKED',f'DUPLICATE_PROSPECTIVE_ASOF {d}')
    seen.add(d)

# Build prospective signals causally. The exact 2026-09-08 row is used only as state
# for the first delta; no BTC outcome tied to that prior row is fetched or accessed.
signals=[]
prev=prior
for cur in parsed:
    if cur['oi']==0:
        fail_receipt('SOURCE_DATA_BLOCKED',f'ZERO_OPEN_INTEREST {cur["as_of"]}')
    signal=((cur['nl']-cur['ns'])-(prev['nl']-prev['ns']))/cur['oi']
    entry=cur['as_of']+timedelta(days=8)
    exit_=entry+timedelta(days=7)
    if exit_>LATEST_EXIT:
        fail_receipt('SOURCE_DATA_BLOCKED',f'EXIT_AFTER_FROZEN_LATEST {exit_}')
    signals.append({
        'as_of':cur['as_of'].isoformat(),
        'predecessor_as_of':prev['as_of'].isoformat(),
        'entry':entry.isoformat(),
        'exit':exit_.isoformat(),
        'signal':signal,
        'outcome_status':'NOT_FETCHED_SOURCE_ONLY_CHECKPOINT',
    })
    prev=cur

# This checkpoint never fetches BTC outcomes, even when a frozen window has elapsed.
today=datetime.now(timezone.utc).date()
fully_elapsed=[s for s in signals if datetime.fromisoformat(s['exit']).date() < today]
if len(parsed)==0:
    classification='WAITING_PROSPECTIVE_DATA'
elif len(fully_elapsed)==0:
    classification='WAITING_COMPLETE_OUTCOME'
else:
    classification='PROSPECTIVE_OUTCOME_ELIGIBLE_BUT_NOT_FETCHED'

receipt={
    'lab':LAB,
    'study_id':STUDY,
    'stage':'PROSPECTIVE_SOURCE_ONLY_CHECKPOINT',
    'classification':classification,
    'supersedes_for_execution':'ETF-CME-INSTFLOW-001-FORWARD-SHADOW-Q4-2026-V0.1',
    'technical_correction':'EXACT_PRIOR_STATE_FOR_FIRST_DELTA_ONLY',
    'required_prior_state_as_of':PRIOR_ASOF.isoformat(),
    'prior_state_as_of':prior['as_of'].isoformat(),
    'prior_state_used_for_signal_only':True,
    'prior_state_btc_outcome_accessed':False,
    'first_allowed_as_of':FIRST_ASOF.isoformat(),
    'last_allowed_as_of':LAST_ASOF.isoformat(),
    'cftc_rows_seen':len(parsed),
    'prospective_signal_count':len(signals),
    'prospective_rows':[
        {'as_of':x['as_of'].isoformat(),'oi':x['oi'],'nl':x['nl'],'ns':x['ns']} for x in parsed
    ],
    'prospective_signals':signals,
    'fully_elapsed_signal_windows':fully_elapsed,
    'outcomes_fetched':False,
    'new_market_outcomes_accessed':False,
    'pre_freeze_2026_outcomes_accessed':False,
    'live_trading':False,
    'exchange_mutation':False,
    'post_outcome_tuning':False,
    'tier_effect':'NONE_AUTOMATIC',
}
json.dump(receipt,open(os.path.join(OUT,'forward_shadow_checkpoint_receipt_v01a.json'),'w'),indent=2,sort_keys=True)
print(json.dumps(receipt,indent=2,sort_keys=True))
