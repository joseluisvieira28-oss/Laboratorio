#!/usr/bin/env python3
import json, hashlib, urllib.parse, urllib.request
from datetime import datetime, timezone, date
from pathlib import Path

OUT=Path('source_audit_output'); OUT.mkdir(exist_ok=True)
ASSET='0x39AA39c021dfbaE8faC545936693aC917d5E7563'
START=date(2019,6,1); END=date(2024,12,30)
BASE='https://api.compound.finance/api/v2/market_history/graph'

def ts(d): return int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp())
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'DEFI-LENDING-001-source-audit/0.1','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()

chunks=[]; all_rates=[]
for y in range(2019,2025):
    a=max(START,date(y,1,1)); b=min(END,date(y,12,31))
    if a>b: continue
    nd=(b-a).days+1
    q=urllib.parse.urlencode({'asset':ASSET,'min_block_timestamp':ts(a),'max_block_timestamp':ts(b),'num_buckets':nd})
    url=BASE+'?'+q
    raw=fetch(url); obj=json.loads(raw)
    if isinstance(obj,dict) and obj.get('error') not in (None,0,'0',{}):
        raise RuntimeError(f'Compound API error for {y}: {obj.get("error")}')
    rates=obj.get('borrow_rates') or []
    chunks.append({'year':y,'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'borrow_rate_rows':len(rates)})
    (OUT/f'COMPOUND_CUSDC_MARKET_HISTORY_{y}.json').write_bytes(raw)
    for r in rates:
        t=int(r['block_timestamp']); rate=float(r['rate'])
        d=datetime.fromtimestamp(t,tz=timezone.utc).date()
        if START<=d<=END: all_rates.append((t,d,rate))

all_rates.sort(key=lambda x:x[0])
timestamps=[x[0] for x in all_rates]
dates=[x[1] for x in all_rates]
duplicates=sorted({t for t in timestamps if timestamps.count(t)>1})
unique_ts=sorted(set(timestamps))
unique_dates=sorted(set(dates))
max_gap_days=max(((b-a).days for a,b in zip(unique_dates,unique_dates[1:])),default=None)
report={
 'lab':'DEFI-LENDING-001','mve_id':'DL-CUSDC-BORROW-001','mode':'SOURCE_DATA_AUDIT_ONLY',
 'source':'Compound v2 MarketHistoryService','asset':'cUSDC','asset_address':ASSET,
 'window':{'start':str(START),'end':str(END)},'chunks':chunks,
 'borrow_rate_rows':len(all_rates),'unique_timestamps':len(unique_ts),'unique_dates':len(unique_dates),
 'min_date':str(min(unique_dates)) if unique_dates else None,'max_date':str(max(unique_dates)) if unique_dates else None,
 'duplicate_timestamp_count':len(duplicates),'max_gap_days':max_gap_days,'min_required_observations':1500,
 'sample_pass':len(unique_ts)>=1500,'uniqueness_pass':len(duplicates)==0,
 'source_values_read':True,'signal_computed':False,'btc_price_values_evaluated':False,'btc_returns_computed':False,'pnl_computed':False,
 'holdout_2025_accessed':False,'year_2026_accessed':False,
}
report['structural_pass']=report['sample_pass'] and report['uniqueness_pass'] and report['min_date'] is not None and report['max_date'] is not None
(OUT/'COMPOUND_CUSDC_SOURCE_AUDIT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
(OUT/'COMPOUND_CUSDC_SOURCE_MANIFEST_V01.json').write_text(json.dumps(chunks,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
print('SOURCE ONLY / SIGNAL NOT COMPUTED / NO BTC PRICES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
raise SystemExit(0 if report['structural_pass'] else 2)
