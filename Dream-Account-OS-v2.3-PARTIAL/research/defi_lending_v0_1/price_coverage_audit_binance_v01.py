#!/usr/bin/env python3
import csv, io, json, urllib.request, zipfile, hashlib
from calendar import monthrange
from datetime import date, datetime, timezone
from pathlib import Path

OUT=Path('source_audit_output'); OUT.mkdir(exist_ok=True)
START=date(2019,6,1); END=date(2024,12,31)
BASE='https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d'

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'DEFI-LENDING-001-price-coverage/0.1'})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()

def months(a,b):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield y,m
        m+=1
        if m==13: y,m=y+1,1

seen=[]; manifest=[]
for y,m in months(START,END):
    stem=f'BTCUSDT-1d-{y:04d}-{m:02d}.zip'; url=f'{BASE}/{stem}'
    raw=fetch(url); zsha=hashlib.sha256(raw).hexdigest(); checksum=None
    try:
        chk=fetch(url+'.CHECKSUM').decode('utf-8','replace').strip().split()[0].lower(); checksum=(chk==zsha)
        if not checksum: raise RuntimeError(f'checksum mismatch {stem}')
    except Exception as e:
        if 'checksum mismatch' in str(e): raise
    z=zipfile.ZipFile(io.BytesIO(raw)); names=z.namelist(); assert len(names)==1
    n=0
    for row in csv.reader(io.StringIO(z.read(names[0]).decode('utf-8-sig'))):
        if not row: continue
        try: t=int(row[0])
        except ValueError: continue
        if t>10**15: t//=1000
        dt=datetime.fromtimestamp(t/1000,tz=timezone.utc)
        if (dt.hour,dt.minute,dt.second)!=(0,0,0): raise RuntimeError('non-midnight kline')
        d=dt.date()
        if START<=d<=END: seen.append(d)
        n+=1
    manifest.append({'file':stem,'sha256':zsha,'checksum_match':checksum,'rows':n})

uniq=sorted(set(seen)); expected=[]; d=START
from datetime import timedelta
while d<=END: expected.append(d); d+=timedelta(days=1)
missing=sorted(set(expected)-set(uniq)); extra=sorted(set(uniq)-set(expected))
report={
 'lab':'DEFI-LENDING-001','mode':'PRICE_COVERAGE_ONLY','source':'Binance Data Vision BTCUSDT spot 1d monthly klines',
 'window':{'start':str(START),'end':str(END)},'monthly_archives':len(manifest),'daily_rows':len(uniq),'expected_rows':len(expected),
 'missing_dates':[str(x) for x in missing],'extra_dates':[str(x) for x in extra],
 'coverage_pass':len(missing)==0 and len(extra)==0 and len(uniq)==len(expected),
 'price_values_evaluated':False,'returns_computed':False,'pnl_computed':False,'holdout_2025_accessed':False,'year_2026_accessed':False,
}
(OUT/'BINANCE_BTCUSDT_PRICE_COVERAGE_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
(OUT/'BINANCE_BTCUSDT_1D_ARCHIVE_MANIFEST_V01.json').write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
print('TIMESTAMPS ONLY / NO PRICE VALUES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
raise SystemExit(0 if report['coverage_pass'] else 2)
