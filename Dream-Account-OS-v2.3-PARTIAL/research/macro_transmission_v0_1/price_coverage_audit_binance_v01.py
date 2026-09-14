#!/usr/bin/env python3
import csv, hashlib, io, json, urllib.request, zipfile
from calendar import monthrange
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

OUT=Path('source_audit_output'); OUT.mkdir(exist_ok=True)
START=date(2018,4,1); END=date(2024,12,31)
BASE='https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d'

def months(a,b):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield y,m
        m+=1
        if m==13: y,m=y+1,1

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'MACRO-TRANSMISSION-001-price-coverage/0.1'})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()

all_dates=[]; manifest=[]
for y,m in months(START,END):
    stem=f'BTCUSDT-1d-{y:04d}-{m:02d}.zip'; url=f'{BASE}/{stem}'
    raw=fetch(url); sha=hashlib.sha256(raw).hexdigest()
    checksum_match=None
    try:
        expected=fetch(url+'.CHECKSUM').decode('utf-8','replace').strip().split()[0].lower()
        checksum_match=(expected==sha)
    except Exception:
        pass
    z=zipfile.ZipFile(io.BytesIO(raw)); names=z.namelist(); assert len(names)==1
    dates=[]
    for row in csv.reader(io.StringIO(z.read(names[0]).decode('utf-8-sig'))):
        if not row: continue
        try: ts=int(row[0])
        except ValueError: continue
        if ts>10**15: ts//=1000
        dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc)
        assert (dt.hour,dt.minute,dt.second)==(0,0,0)
        dates.append(dt.date())
    expected_dates=[date(y,m,d) for d in range(1,monthrange(y,m)[1]+1)]
    assert dates==expected_dates,(stem,len(dates),len(expected_dates))
    all_dates.extend(dates)
    manifest.append({'file':stem,'sha256':sha,'checksum_match':checksum_match,'rows':len(dates)})

expected=[]; d=START
while d<=END:
    expected.append(d); d+=timedelta(days=1)
missing=sorted(set(expected)-set(all_dates)); extra=sorted(set(all_dates)-set(expected))
report={
 'lab':'MACRO-TRANSMISSION-001','mode':'PRICE_COVERAGE_ONLY','source':'Binance Data Vision BTCUSDT spot 1d monthly klines',
 'window':{'start':str(START),'end':str(END)},'daily_rows':len(all_dates),'expected_rows':len(expected),
 'missing_dates':[str(x) for x in missing],'extra_dates':[str(x) for x in extra],
 'monthly_archives':len(manifest),'all_available_checksums_match':all(x['checksum_match'] is not False for x in manifest),
 'coverage_pass':not missing and not extra and len(all_dates)==len(expected),
 'price_values_evaluated':False,'returns_computed':False,'pnl_computed':False,
 'holdout_2025_accessed':False,'year_2026_accessed':False
}
(OUT/'BINANCE_BTCUSDT_1D_ARCHIVE_MANIFEST_V01.json').write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8')
(OUT/'BINANCE_BTCUSDT_PRICE_COVERAGE_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
print('TIMESTAMPS ONLY / NO PRICE VALUES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
raise SystemExit(0 if report['coverage_pass'] else 2)
