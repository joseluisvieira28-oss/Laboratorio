#!/usr/bin/env python3
import csv, hashlib, io, json, urllib.request, zipfile
from calendar import monthrange
from datetime import date, datetime, timezone
from pathlib import Path

OUT=Path('source_audit_output'); OUT.mkdir(exist_ok=True)
START=date(2018,4,1); END=date(2024,12,31)
BASE='https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d'

def months(a,b):
    y,m=a.year,a.month
    while (y,m) <= (b.year,b.month):
        yield y,m
        m+=1
        if m==13: y,m=y+1,1

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'INSTITUTIONAL-FLOW-001-price-coverage/0.1'})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()

all_dates=[]; manifests=[]
for y,m in months(START,END):
    stem=f'BTCUSDT-1d-{y:04d}-{m:02d}.zip'
    url=f'{BASE}/{stem}'
    raw=fetch(url)
    sha=hashlib.sha256(raw).hexdigest()
    checksum_text=None; checksum_match=None
    try:
        checksum_text=fetch(url+'.CHECKSUM').decode('utf-8','replace').strip()
        expected=checksum_text.split()[0].lower()
        checksum_match=(expected==sha)
    except Exception:
        checksum_match=None
    z=zipfile.ZipFile(io.BytesIO(raw))
    names=z.namelist()
    assert len(names)==1,(stem,names)
    content=z.read(names[0]).decode('utf-8-sig')
    dates=[]
    for row in csv.reader(io.StringIO(content)):
        if not row: continue
        try: ts=int(row[0])
        except ValueError: continue
        if ts>10**15: ts//=1000
        d=datetime.fromtimestamp(ts/1000,tz=timezone.utc)
        assert d.hour==0 and d.minute==0 and d.second==0,(stem,row[0],d.isoformat())
        dates.append(d.date())
    assert len(dates)==len(set(dates)),stem
    expected_dates=[date(y,m,d) for d in range(1,monthrange(y,m)[1]+1)]
    assert dates==expected_dates,(stem,dates[:2],dates[-2:],len(dates),len(expected_dates))
    all_dates.extend(dates)
    manifests.append({'file':stem,'sha256':sha,'checksum_available':checksum_match is not None,'checksum_match':checksum_match,'rows':len(dates)})

expected=[]
d=START
from datetime import timedelta
while d<=END:
    expected.append(d); d+=timedelta(days=1)
missing=sorted(set(expected)-set(all_dates)); extra=sorted(set(all_dates)-set(expected))
report={
 'lab':'INSTITUTIONAL-FLOW-001','mode':'PRICE_COVERAGE_ONLY','source':'Binance Data Vision BTCUSDT spot 1d monthly klines',
 'window':{'start':str(START),'end':str(END)},'daily_rows':len(all_dates),'expected_rows':len(expected),
 'date_min':str(min(all_dates)) if all_dates else None,'date_max':str(max(all_dates)) if all_dates else None,
 'missing_dates':[str(x) for x in missing],'extra_dates':[str(x) for x in extra],
 'monthly_archives':len(manifests),'all_available_checksums_match':all(x['checksum_match'] is not False for x in manifests),
 'coverage_pass':not missing and not extra and len(all_dates)==len(expected),
 'price_values_evaluated':False,'returns_computed':False,'pnl_computed':False,
 'holdout_2025_accessed':False,'year_2026_accessed':False
}
(OUT/'BINANCE_BTCUSDT_1D_ARCHIVE_MANIFEST_V01.json').write_text(json.dumps(manifests,indent=2,sort_keys=True),encoding='utf-8')
(OUT/'BINANCE_BTCUSDT_PRICE_COVERAGE_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
print('TIMESTAMPS ONLY / PRICE VALUES NOT EVALUATED / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
raise SystemExit(0 if report['coverage_pass'] else 2)
