#!/usr/bin/env python3
import csv, io, json, os, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

LAB='ETF-CME-INSTFLOW-001'
DATASET='6dca-aqww'
CODE='133741'
FIRST_ASOF=datetime(2026,9,15,tzinfo=timezone.utc).date()
LAST_ASOF=datetime(2026,12,15,tzinfo=timezone.utc).date()
LATEST_EXIT=datetime(2026,12,31,tzinfo=timezone.utc).date()
OUT='artifacts/etf_cme_forward_shadow_q4_2026_v01'
os.makedirs(OUT,exist_ok=True)

base=f'https://publicreporting.cftc.gov/resource/{DATASET}.csv'
where=(f"cftc_contract_market_code='{CODE}' AND report_date_as_yyyy_mm_dd between "
       f"'{FIRST_ASOF.isoformat()}T00:00:00.000' and '{LAST_ASOF.isoformat()}T23:59:59.999'")
url=base+'?'+urllib.parse.urlencode({'$limit':'5000','$order':'report_date_as_yyyy_mm_dd ASC','$where':where})
req=urllib.request.Request(url,headers={'User-Agent':'ETF-CME-INSTFLOW-001-forward-shadow/0.1'})
try:
    with urllib.request.urlopen(req,timeout=120) as r: raw=r.read()
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
except Exception as e:
    receipt={'lab':LAB,'study_id':'ETF-CME-INSTFLOW-001-FORWARD-SHADOW-Q4-2026-V0.1','classification':'SOURCE_DATA_BLOCKED','error':str(e),'new_market_outcomes_accessed':False,'pre_freeze_2026_outcomes_accessed':False,'live_trading':False,'exchange_mutation':False}
    json.dump(receipt,open(os.path.join(OUT,'forward_shadow_checkpoint_receipt.json'),'w'),indent=2,sort_keys=True)
    print(json.dumps(receipt,indent=2)); raise SystemExit(2)

parsed=[]
for row in rows:
    d=datetime.fromisoformat(row['report_date_as_yyyy_mm_dd'].replace('Z','+00:00')).date()
    if not (FIRST_ASOF <= d <= LAST_ASOF):
        raise SystemExit('FAIL_CLOSED: CFTC row outside prospective window')
    oi=float(row['open_interest_all']); nl=float(row['noncomm_positions_long_all']); ns=float(row['noncomm_positions_short_all'])
    parsed.append({'as_of':d,'oi':oi,'nl':nl,'ns':ns})

# No outcome is touched until a prospective signal has a fully elapsed frozen exit.
today=datetime.now(timezone.utc).date()
complete=[]
for i in range(1,len(parsed)):
    cur=parsed[i]; prev=parsed[i-1]
    entry=cur['as_of']+timedelta(days=8); exit_=entry+timedelta(days=7)
    if exit_>LATEST_EXIT or exit_>=today:
        continue
    # Signal may be computed only for prospective rows. BTC outcome fetch is deliberately deferred
    # to a later checkpoint once a complete frozen outcome exists.
    signal=((cur['nl']-cur['ns'])-(prev['nl']-prev['ns']))/cur['oi'] if cur['oi'] else None
    complete.append({'as_of':cur['as_of'].isoformat(),'entry':entry.isoformat(),'exit':exit_.isoformat(),'signal':signal,'outcome_status':'ELIGIBLE_BUT_NOT_FETCHED_IN_THIS_SOURCE_ONLY_CHECKPOINT'})

if len(parsed)==0:
    classification='WAITING_PROSPECTIVE_DATA'
elif len(complete)==0:
    classification='WAITING_COMPLETE_OUTCOME'
else:
    classification='PROSPECTIVE_OUTCOME_ELIGIBLE'

receipt={
 'lab':LAB,
 'study_id':'ETF-CME-INSTFLOW-001-FORWARD-SHADOW-Q4-2026-V0.1',
 'stage':'PROSPECTIVE_SOURCE_ONLY_CHECKPOINT',
 'classification':classification,
 'first_allowed_as_of':FIRST_ASOF.isoformat(),
 'last_allowed_as_of':LAST_ASOF.isoformat(),
 'cftc_rows_seen':len(parsed),
 'prospective_rows':[{k:(v.isoformat() if hasattr(v,'isoformat') else v) for k,v in x.items()} for x in parsed],
 'fully_elapsed_signal_windows':complete,
 'outcomes_fetched':False,
 'new_market_outcomes_accessed':False,
 'pre_freeze_2026_outcomes_accessed':False,
 'live_trading':False,
 'exchange_mutation':False,
 'post_outcome_tuning':False,
 'tier_effect':'NONE_AUTOMATIC'
}
json.dump(receipt,open(os.path.join(OUT,'forward_shadow_checkpoint_receipt.json'),'w'),indent=2,sort_keys=True)
print(json.dumps(receipt,indent=2,sort_keys=True))
