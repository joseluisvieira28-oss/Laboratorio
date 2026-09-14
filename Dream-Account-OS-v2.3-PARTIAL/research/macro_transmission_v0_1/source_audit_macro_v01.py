#!/usr/bin/env python3
import csv, hashlib, io, json, urllib.request
from datetime import date
from pathlib import Path

OUT=Path('source_audit_output'); OUT.mkdir(exist_ok=True)
START=date(2018,4,1); END=date(2024,12,30)
SERIES={
 'DGS2':'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2&cosd=2018-04-01&coed=2024-12-30',
 'NASDAQCOM':'https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM&cosd=2018-04-01&coed=2024-12-30',
}

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'MACRO-TRANSMISSION-001-source-audit/0.1'})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()

def parse(name, raw):
    text=raw.decode('utf-8-sig')
    rows=list(csv.DictReader(io.StringIO(text)))
    assert rows and 'observation_date' in rows[0] and name in rows[0], (name, rows[:1])
    out={}; dup=[]; missing=[]
    for r in rows:
        d=date.fromisoformat(r['observation_date'])
        if not (START<=d<=END): continue
        if d in out: dup.append(str(d))
        v=r[name].strip()
        out[d]=v
        if v in ('','.','NA','N/A'): missing.append(str(d))
        else: float(v)
    return out,dup,missing,text

series={}; manifest=[]
for name,url in SERIES.items():
    raw=fetch(url); sha=hashlib.sha256(raw).hexdigest()
    vals,dup,missing,text=parse(name,raw)
    (OUT/f'{name}_20180401_20241230.csv').write_bytes(raw)
    series[name]=vals
    manifest.append({'series':name,'url':url,'sha256':sha,'rows_in_window':len(vals),'duplicates':dup,'missing_or_null_dates':missing})

common=sorted(set(series['DGS2']) & set(series['NASDAQCOM']))
paired_valid=[]
for d in common:
    a=series['DGS2'][d].strip(); b=series['NASDAQCOM'][d].strip()
    if a not in ('','.','NA','N/A') and b not in ('','.','NA','N/A'):
        paired_valid.append(d)

report={
 'lab':'MACRO-TRANSMISSION-001','mode':'SOURCE_DATA_AUDIT_ONLY',
 'window':{'start':str(START),'end':str(END)},
 'series_manifest':manifest,
 'common_calendar_dates':len(common),'paired_valid_dates':len(paired_valid),
 'paired_valid_min':str(min(paired_valid)) if paired_valid else None,
 'paired_valid_max':str(max(paired_valid)) if paired_valid else None,
 'min_required_paired':1000,
 'uniqueness_pass':all(not x['duplicates'] for x in manifest),
 'sample_pass':len(paired_valid)>=1000,
 'timing_authority':{
   'us2y':'U.S. Treasury daily par curve uses indicative market quotations obtained around 15:30 ET each business day',
   'nasdaq':'NASDAQCOM is daily market-close index value, typically 16:00 ET',
   'frozen_btc_entry':'00:00 UTC next calendar day'
 },
 'macro_signal_computed':False,'btc_price_values_evaluated':False,
 'btc_returns_computed':False,'pnl_computed':False,
 'holdout_2025_accessed':False,'year_2026_accessed':False,
}
report['structural_pass']=report['uniqueness_pass'] and report['sample_pass']
(OUT/'MACRO_SOURCE_MANIFEST_V01.json').write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8')
(OUT/'MACRO_SOURCE_AUDIT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
print('MACRO SOURCE ONLY / NO SIGNAL / NO BTC PRICES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
raise SystemExit(0 if report['structural_pass'] else 2)
