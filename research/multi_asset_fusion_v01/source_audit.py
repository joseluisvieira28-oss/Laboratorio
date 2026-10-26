"""Inspect every fixed source archive; never calculate signals or returns.
Records all failures instead of stopping at the first failed month.
"""
import argparse, collections, csv, datetime as dt, io, json, re, sys, zipfile
from pathlib import Path
import replay as r
def audit(cache):
    manifest=[]
    for kind,a,tf,y,m,name,url in r.inventory():
        item=dict(url=url,asset=a,venue=kind,timeframe=tf,month=f'{y}-{m:02d}')
        file=cache/r.cache_name(kind,name)
        try:
            raw=file.read_bytes();check=Path(str(file)+'.CHECKSUM').read_bytes()
            item.update(zip_sha256=r.sha(raw),checksum_sha256=r.sha(check))
            match=re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?(\S+)',check.decode('ascii').strip())
            item['checksum_matches']=bool(match and match[1].lower()==r.sha(raw) and match[2]==name)
            try:
                bars=r.parse_archive(raw,check,name,tf,y,m)
                item.update(status='PASS',candles=len(bars))
            except r.GateError as e:
                item.update(status='FAIL_CLOSED',error=str(e))
                # Diagnostic timestamps only; no prices, interpolation or economic output.
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    text=z.read(name[:-4]+'.csv').decode('utf-8-sig')
                clocks=[int(row[0]) for row in csv.reader(io.StringIO(text)) if row and row[0]!='open_time']
                step=86_400_000 if tf=='1d' else 3_600_000
                first=r.stamp(dt.datetime(y,m,1,tzinfo=r.UTC))
                n=r.calendar.monthrange(y,m)[1]*(1 if tf=='1d' else 24)
                expected=set(range(first,first+n*step,step))
                iso=lambda t:dt.datetime.fromtimestamp(t/1000,r.UTC).isoformat()
                item.update(candles=len(clocks),expected_candles=n,
                    missing_open_utc=[iso(t) for t in sorted(expected-set(clocks))],
                    unexpected_open_utc=[iso(t) for t in sorted(set(clocks)-expected)],
                    duplicate_open_utc=[iso(t) for t,n in collections.Counter(clocks).items() if n>1])
        except (OSError,ValueError,UnicodeError,zipfile.BadZipFile,KeyError) as e:
            item.update(status='FAIL_CLOSED',error=type(e).__name__+': '+str(e))
        manifest.append(item)
    return dict(status='ALL_ARCHIVES_PASS' if all(i['status']=='PASS' for i in manifest) else 'FAIL_CLOSED',
                economic_results='NOT_CALCULATED_BY_THIS_AUDITOR',archive_pairs=len(manifest),
                passed=sum(i['status']=='PASS' for i in manifest),
                checksum_matches=sum(i.get('checksum_matches',False) for i in manifest),
                failed=sum(i['status']!='PASS' for i in manifest),holdout_access=False,manifest=manifest)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,default=Path('archives'));p.add_argument('--receipt',type=Path,default=Path('source_audit.json'))
    x=p.parse_args();result=audit(x.cache);r.write_json(x.receipt,result)
    print(json.dumps({k:v for k,v in result.items() if k!='manifest'}))
    for i in result['manifest']:
        if i['status']!='PASS':print(json.dumps(i))
    sys.exit(0 if result['status']=='ALL_ARCHIVES_PASS' else 2)
