import csv,json,hashlib,math,statistics
import sys
from pathlib import Path
from datetime import datetime
symbol=sys.argv[1] if len(sys.argv)>1 else 'PUT'
p=Path(symbol+'_History.csv')
rows=[]
for r in csv.DictReader(p.open()):
 d=datetime.strptime(r['DATE'],'%m/%d/%Y')
 if datetime(2007,1,3)<=d<=datetime(2026,9,30): rows.append((d,float(r[symbol])))
rows.sort()
assert rows and len({d for d,v in rows})==len(rows)
assert all(math.isfinite(v) and v>0 for d,v in rows)
months={}
for d,v in rows: months[d.strftime('%Y-%m')]=(d,v)
assert len(months)==237, 'Missing or unexpected month: do not silently bridge'
def metrics(end):
 a=[(d,v) for d,v in rows if d<=datetime.fromisoformat(end)]
 m=[(d,v) for d,v in months.values() if d<=datetime.fromisoformat(end)]
 levels=[a[0]]+m
 rets=[levels[i][1]/levels[i-1][1]-1 for i in range(1,len(levels))]
 peak=levels[0][1];dd=0
 for _,v in levels: peak=max(peak,v);dd=min(dd,v/peak-1)
 years=(a[-1][0]-a[0][0]).days/365.25
 annual={}
 for y in (2008,2020,2022):
  prev=months.get(str(y-1)+'-12');last=months.get(str(y)+'-12')
  annual[y]=last[1]/prev[1]-1 if prev and last else None
 k=math.ceil(len(rets)*.05)
 assert abs(math.prod(1+r for r in rets)-a[-1][1]/a[0][1])<1e-10
 return dict(start=str(a[0][0].date()),end=str(a[-1][0].date()),n_monthly_returns=len(rets),cagr=(a[-1][1]/a[0][1])**(1/years)-1,vol=statistics.stdev(rets)*math.sqrt(12),month_end_max_drawdown=dd,worst_month=min(rets),es95_mean_worst_ceil5pct=sum(sorted(rets)[:k])/k,calendar_years=annual,sharpe=None,notes='First Jan2007 return is partial from Jan03. No cash series; Sharpe not computed.')
out={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source':'https://cdn.cboe.com/api/global/us_indices/daily_prices/'+symbol+'_History.csv','cutoff':'2026-09-30','metrics':[metrics('2026-03-31'),metrics('2026-09-30')]}
Path(symbol+'_CALCULATIONS.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
