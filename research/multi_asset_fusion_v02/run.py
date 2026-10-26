"""V0.2: validate all sources before calling any economic function.
Public data only. Inputs restricted to frozen inventory and 20 recovery ZIPs.
"""
import argparse, csv, datetime as dt, hashlib, io, json, re, sys, zipfile
from decimal import Decimal as D
from pathlib import Path
import reference_replay as r

ROOT=Path(__file__).parent
FREEZE='9c2e9456877093ecb4f74cdd8a63aabae21de0ce'
DATES=('2022-02-26','2022-02-27','2022-02-28','2022-04-01','2022-04-02')
def blob(raw): return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def read_rows(raw,check,name):
    m=re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?(\S+)',check.decode().strip())
    r.gate(m and m[1].lower()==r.sha(raw) and m[2]==name,'CHECKSUM:'+name)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        r.gate(z.namelist()==[name[:-4]+'.csv'],'ZIP_MEMBERS:'+name)
        rows=list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode('utf-8-sig'))))
    if rows and rows[0][0]=='open_time':rows=rows[1:]
    return rows
def validate(rows,expected,step):
    times=[]
    for row in rows:
        r.gate(len(row)==12,'WIDTH')
        v=[D(x) for x in row[:11]]
        r.gate(all(x.is_finite() for x in v),'NONFINITE')
        t=int(row[0]);times.append(t)
        r.gate(v[0]==t and v[6]==t+step-1 and v[8]>=0 and v[8]==int(v[8]),'CLOCK_TRADES')
        o,h,l,c=v[1:5]
        r.gate(0<l<=min(o,c)<=max(o,c)<=h and all(v[i]>=0 for i in (5,7,9,10)),'VALUES')
    r.gate(len(times)==len(set(times)) and times==sorted(times),'DUPLICATE_OR_ORDER')
    r.gate(set(times)==set(expected),'GAP_OR_UNEXPECTED_TIMESTAMP')
    return dict(zip(times,rows))
def whitelist(a,tf,y,m):
    step=86400000 if tf=='1d' else 3600000
    return {r.stamp(dt.datetime.fromisoformat(day).replace(tzinfo=r.UTC))+i*step for day in DATES if a in ('SOLUSDT','XRPUSDT') and day[:7]==f'{y}-{m:02d}' for i in range(1 if tf=='1d' else 24)}
def source_gate(cache,recovery,out):
    refraw=(ROOT/'reference_source_audit.json').read_bytes()
    r.gate(blob(refraw)=='6d0c03fa587e7b87823680a9e200df5472340bf9','REFERENCE_AUDIT_BLOB')
    r.gate(blob((ROOT/'reference_replay.py').read_bytes())=='2b85e1c5bd02839e953a55e8ce76426d2f92a485','REFERENCE_REPLAY_BLOB')
    refs={x['url']:x for x in json.loads(refraw)['manifest']}
    manifests=[]; provenance=[]; candles={}; recovered={}; api_receipts=[]
    daily_count=0;added=0
    # Revalidate captured API bodies against original evidence manifest and request receipts.
    oldhash=json.loads((recovery/'SHA256SUMS.json').read_text())
    evraw=(recovery/'api_evidence_retry.json').read_bytes()
    r.gate(r.sha(evraw)==oldhash['api_evidence_retry.json'],'API_EVIDENCE_MANIFEST')
    apiev=json.loads(evraw)
    for a in ('SOLUSDT','XRPUSDT'):
        for tf in ('1d','1h'):
            for start,end in (('2022-02-26','2022-03-01'),('2022-04-01','2022-04-03')):
                file=recovery/f'api_{a}_{tf}_{start}.json';raw=file.read_bytes()
                r.gate(r.sha(raw)==oldhash[file.name],'API_CAPTURE_HASH')
                step=86400000 if tf=='1d' else 3600000
                begin=r.stamp(dt.datetime.fromisoformat(start).replace(tzinfo=r.UTC));stop=r.stamp(dt.datetime.fromisoformat(end).replace(tzinfo=r.UTC))
                url=f'https://fapi.binance.com/fapi/v1/klines?symbol={a}&interval={tf}&startTime={begin}&endTime={stop-1}&limit=1000'
                ev=next(x for x in apiev if x.get('url')==url)
                r.gate(ev.get('sha256')==r.sha(raw),'API_RECEIPT_HASH')
                rows=json.loads(raw);r.gate(rows==ev['rows'],'API_RECEIPT_ROWS')
                validate([[str(v) for v in row] for row in rows],range(begin,stop,step),step)
                recovered[a,tf,start]={int(x[0]):x for x in rows}
                api_receipts.append(dict(url=url,sha256=r.sha(raw),rows=len(rows),capture='prior public response revalidated; not fresh fetch'))
                (out/file.name).write_bytes(raw)
    for kind,a,tf,y,m,name,url in r.inventory():
        file=cache/r.cache_name(kind,name);raw=file.read_bytes();check=Path(str(file)+'.CHECKSUM').read_bytes()
        ref=refs[url]
        r.gate(r.sha(raw)==ref['zip_sha256'] and r.sha(check)==ref['checksum_sha256'],'MONTHLY_REFERENCE_HASH:'+name)
        step=86400000 if tf=='1d' else 3600000
        begin=r.stamp(dt.datetime(y,m,1,tzinfo=r.UTC));count=r.calendar.monthrange(y,m)[1]*(1 if tf=='1d' else 24)
        expected=set(range(begin,begin+count*step,step));missing=whitelist(a,tf,y,m)
        monthly=validate(read_rows(raw,check,name),expected-missing,step)
        bars=dict(monthly); origins={t:'monthly' for t in monthly}
        for day in DATES:
            if a not in ('SOLUSDT','XRPUSDT') or day[:7]!=f'{y}-{m:02d}':continue
            dn=f'{a}-{tf}-{day}.zip';df=recovery/dn;dr=df.read_bytes();dc=Path(str(df)+'.CHECKSUM').read_bytes()
            b=r.stamp(dt.datetime.fromisoformat(day).replace(tzinfo=r.UTC));de=range(b,b+86400000,step)
            daily=validate(read_rows(dr,dc,dn),de,step)
            r.gate(not (daily.keys() & bars.keys()),'OVERLAP')
            start='2022-02-26' if m==2 else '2022-04-01';api=recovered[a,tf,start]
            for t,row in daily.items():r.gate([D(x) for x in row[:11]]==[D(str(x)) for x in api[t][:11]],'API_11_FIELDS')
            bars.update(daily);origins.update({t:'daily' for t in daily});daily_count+=1;added+=len(daily)
            manifests.append(dict(url=url.replace('/monthly/','/daily/').replace(name,dn),zip_sha256=r.sha(dr),checksum_sha256=r.sha(dc),rows=len(daily),role='recovery'))
            (out/(dn+'.CHECKSUM')).write_bytes(dc)
        r.gate(set(bars)==expected and set(bars)-set(monthly)==missing,'EXACT_RECOVERY')
        target=candles.setdefault((kind,a,tf),{});r.gate(not(target.keys() & bars.keys()),'CROSS_MONTH_DUPLICATE')
        target.update({t:(float(row[1]),float(row[4])) for t,row in bars.items()})
        for t in sorted(missing):provenance.append(dict(asset=a,timeframe=tf,timestamp=t,source='daily',monthly_absent=True))
        manifests.append(dict(url=url,zip_sha256=r.sha(raw),checksum_sha256=r.sha(check),rows=len(monthly),role='primary',unchanged_rows=len(monthly)))
        if missing:recovered[a,tf,y,m]=bars
    r.gate(len(manifests)==339 and daily_count==20 and added==250 and len(provenance)==250,'COUNTS')
    for a in ('SOLUSDT','XRPUSDT'):
        for day in DATES:
            date=dt.datetime.fromisoformat(day).replace(tzinfo=r.UTC);t=r.stamp(date)
            d=recovered[a,'1d',2022,date.month][t];h=[recovered[a,'1h',2022,date.month][t+i*3600000] for i in range(24)]
            r.gate([D(d[i]) for i in (1,2,3,4,5)]==[D(h[0][1]),max(D(x[2]) for x in h),min(D(x[3]) for x in h),D(h[-1][4]),sum(D(x[5]) for x in h)],'D1_H1_OHLCV')
    r.write_json(out/'manifest.json',manifests);r.write_json(out/'provenance.json',provenance);r.write_json(out/'api_receipts.json',api_receipts)
    r.listing_gate(ROOT/'listings.json')
    r.write_json(out/'source_gate.json',dict(status='PASS',monthly=319,daily=20,recovered=250,api_fields=11,ohlcv_asset_days=10,no_other_replacement=True,holdout_access=False,protocol_commit=FREEZE))
    return candles
def main():
    p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);p.add_argument('--recovery',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--economics',action='store_true');x=p.parse_args()
    x.out.mkdir(parents=True,exist_ok=False)
    try:
        candles=source_gate(x.cache,x.recovery,x.out)
        if x.economics:
            rows=r.reconstruct(candles)
            report=dict(classification='EXPLORATORY_DISCOVERY_NOT_OOS_EDGE_NOT_CERTIFIED',protocol_commit=FREEZE,results=r.summarize(rows),inference=r.inference(rows))
            r.write_json(x.out/'report.json',report)
            with (x.out/'daily.csv').open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        code=0
    except Exception as e:
        r.write_json(x.out/'source_gate.json',dict(status='FAIL_CLOSED',error=type(e).__name__+': '+str(e),economic_results='NOT_CALCULATED',holdout_access=False,protocol_commit=FREEZE));code=2
    r.write_json(x.out/'exit_evidence.json',dict(exit_code=code,economics_requested=x.economics,protocol_commit=FREEZE))
    print((x.out/'source_gate.json').read_text());return code
if __name__=='__main__':sys.exit(main())
