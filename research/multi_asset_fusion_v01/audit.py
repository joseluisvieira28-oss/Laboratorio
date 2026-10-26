"""Second arithmetic replay using Decimal and ZIP CSV rows, not replay functions.
Checks manifest hashes, all ledger rows and every arm/cost/year/direction total.
Source parser validity is established by replay.py; this is a second arithmetic check,
not an independent researcher or independent data source.
"""
import argparse, csv, datetime as dt, hashlib, io, json, zipfile
from decimal import Decimal
from pathlib import Path
UTC=dt.timezone.utc
def sha(b):return hashlib.sha256(b).hexdigest()
def audit(cache,out):
    report=json.loads((out/'report.json').read_text())
    manifest=json.loads((out/'manifest.json').read_text())
    if sha((out/'manifest.json').read_bytes())!=report['source_manifest_sha256']:raise ValueError('MANIFEST_HASH')
    source={}
    for item in manifest:
        parts=item['url'].split('/');name=parts[-1];a=parts[-3];tf=parts[-2]
        kind='spot' if '/spot/' in item['url'] else 'futures_um'
        p=cache/(kind+'__'+name);raw=p.read_bytes();ch=Path(str(p)+'.CHECKSUM').read_bytes()
        if sha(raw)!=item['zip_sha256'] or sha(ch)!=item['checksum_sha256']:raise ValueError('SOURCE_HASH')
        if ch.decode().split()!=[sha(raw),name]:raise ValueError('COMPANION_HASH')
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            text=z.read(name[:-4]+'.csv').decode('utf-8-sig')
        d=source.setdefault((kind,a,tf),{})
        for row in csv.reader(io.StringIO(text)):
            if row[0]=='open_time':continue
            d[int(row[0])]=(Decimal(row[1]),Decimal(row[4]))
    with (out/'daily.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    if len(rows)!=4380:raise ValueError('ROW_COUNT')
    sums={};seen=set()
    for row in rows:
        a=row['asset'];day=dt.datetime.fromisoformat(row['date']).replace(tzinfo=UTC)
        identity=a,row['date']
        if identity in seen:raise ValueError('DUPLICATE_LEDGER')
        seen.add(identity)
        if day.year not in (2022,2023):raise ValueError('HOLDOUT')
        old=int((day-dt.timedelta(days=21)).timestamp()*1000);new=int((day-dt.timedelta(days=1)).timestamp()*1000)
        def sign(x,y):return int(y>x)-int(y<x)
        d=source['futures_um',a,'1d'];b=source['spot','BTCUSDT','1d']
        s=sign(d[old][1],d[new][1]);btc=sign(b[old][1],b[new][1])
        h=source['futures_um',a,'1h']
        ent=h[int((day+dt.timedelta(hours=1)).timestamp()*1000)][0]
        ext=h[int((day+dt.timedelta(hours=2)).timestamp()*1000)][0]
        gross=Decimal(s)*(ext/ent-1)*10000
        if s!=int(row['asset20']) or btc!=int(row['btc20']):raise ValueError('SIDE')
        if abs(gross-Decimal(row['gross_bps']))>Decimal('0.0000001'):raise ValueError('GROSS')
        if ent!=Decimal(row['entry']) or ext!=Decimal(row['exit']):raise ValueError('PRICE')
        for arm,on in {'baseline':bool(s),'fusion':bool(s and s==btc),'opposite':bool(s and s==-btc)}.items():
            if row[arm]!=str(on):raise ValueError('MASK')
            for cost in (0,4,8,14,20):
                for group in ('all',str(day.year),'side'+str(s)):
                    key=a,cost,arm,group
                    total,n=sums.get(key,(Decimal(0),0))
                    sums[key]=(total+(gross-cost if on else 0),n+int(on))
    for (a,cost,arm,group),(total,n) in sums.items():
        m=report['results'][a][str(cost)][arm]
        if group in ('2022','2023'):m=m['by_year'][group]
        elif group.startswith('side'):
            if group=='side0':continue
            m=m['by_direction'][group[4:]]
        if abs(total-Decimal(str(m['total_net_bps'])))>Decimal('0.00001') or n!=m['trades']:raise ValueError('TOTAL_OR_COUNT')
    return dict(status='SECOND_DECIMAL_ARITHMETIC_REPLAY_PASS',verified_pairs=len(manifest),ledger_rows=len(rows),checked_group_totals=len(sums),
                independent_source=False,independent_researcher=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,default=Path('archives'));p.add_argument('--out',type=Path,default=Path('results'))
    x=p.parse_args();result=audit(x.cache,x.out);(x.out/'arithmetic_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
