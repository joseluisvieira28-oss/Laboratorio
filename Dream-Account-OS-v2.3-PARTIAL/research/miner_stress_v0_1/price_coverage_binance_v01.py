import io, zipfile, urllib.request, json
from datetime import datetime, timezone
from pathlib import Path

OUT=Path('source_audit_output'); OUT.mkdir(exist_ok=True)
expected=[]
for y in range(2018,2025):
  for m in range(1,13): expected.append((y,m))
dates=set(); archives=[]
for y,m in expected:
  mon=f'{y}-{m:02d}'
  url=f'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-{mon}.zip'
  try:
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
  except Exception as e:
    archives.append({'month':mon,'ok':False,'error':type(e).__name__}); continue
  z=zipfile.ZipFile(io.BytesIO(raw)); name=z.namelist()[0]
  rows=z.read(name).decode().strip().splitlines(); count=0
  for line in rows:
    c=line.split(',');
    if not c or not c[0].isdigit(): continue
    ms=int(c[0]); dt=datetime.fromtimestamp(ms/1000,timezone.utc)
    if dt.year<=2024:
      dates.add(dt.date().isoformat()); count+=1
  archives.append({'month':mon,'ok':True,'rows':count})
start=datetime(2018,1,1,tzinfo=timezone.utc).date(); end=datetime(2024,12,31,tzinfo=timezone.utc).date()
import datetime as d
exp=[]; cur=start
while cur<=end: exp.append(cur.isoformat()); cur+=d.timedelta(days=1)
missing=sorted(set(exp)-dates)
report={'lab':'MINER-STRESS-001','mode':'BTC_TIMESTAMP_ONLY_AUDIT','archives_expected':84,'archives_ok':sum(a['ok'] for a in archives),'unique_days':len(dates),'expected_days':len(exp),'missing_dates':missing,'btc_price_values_evaluated':False,'btc_returns_computed':False,'pnl_computed':False,'holdout_2025_accessed':False,'year_2026_accessed':False,'coverage_pass':len(missing)==0 and len(dates)==len(exp)}
(OUT/'MINER_STRESS_001_BTC_COVERAGE_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True))
print(json.dumps(report,indent=2,sort_keys=True))
raise SystemExit(0 if report['coverage_pass'] else 2)
