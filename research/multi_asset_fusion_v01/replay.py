"""Frozen Discovery replay. Public GET only with --fetch; no exchange execution.
Only 2021-12 warmup and 2022-23 candles are addressable. Requires numpy.
"""
import argparse, calendar, csv, datetime as dt, hashlib, io, json, math, re
import sys, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np

ASSETS = ('SOLUSDT','ETHUSDT','BNBUSDT','XRPUSDT','LINKUSDT')
REFERENCE = 'AVAXUSDT'
COSTS = (0,4,8,14,20)
MONTHS = ((2021,12),)+tuple((y,m) for y in (2022,2023) for m in range(1,13))
UTC = dt.timezone.utc
START = dt.datetime(2022,1,1,tzinfo=UTC)
BASE = 'https://data.binance.vision/data/'
ARMS = ('baseline','fusion','opposite')
class GateError(Exception): pass
def gate(ok, msg):
    if not ok: raise GateError(msg)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def stamp(d): return int(d.timestamp()*1000)
def specs():
    yield ('spot','BTCUSDT','1d')
    for a in ASSETS+(REFERENCE,):
        yield ('futures/um',a,'1d')
        yield ('futures/um',a,'1h')
def inventory():
    for kind,a,tf in specs():
        for y,m in MONTHS:
            if tf=='1h' and y==2021: continue
            name=f'{a}-{tf}-{y:04d}-{m:02d}.zip'
            yield kind,a,tf,y,m,name,BASE+f'{kind}/monthly/klines/{a}/{tf}/{name}'
def cache_name(kind,name): return kind.replace('/','_')+'__'+name
def read_url(url,limit):
    # This function is only called with fixed inventory URLs; redirects stay HTTPS.
    req=urllib.request.Request(url,headers={'User-Agent':'FusionDiscoveryAudit/1.0'})
    with urllib.request.urlopen(req,timeout=30) as r:
        gate(r.url.startswith('https://'), 'NON_HTTPS_REDIRECT')
        raw=r.read(limit+1)
        gate(len(raw)<=limit,'SOURCE_SIZE_LIMIT')
        return raw,dict(r.headers)
def fetch_all(folder):
    folder.mkdir(parents=True,exist_ok=True)
    def fetch(item):
        kind,a,tf,y,m,name,url=item
        file=folder/cache_name(kind,name)
        receipt={'url':url,'retrieved_at':dt.datetime.now(UTC).isoformat()}
        try:
            for suffix,limit in (('.CHECKSUM',1000),('',6_000_000)):
                dest=Path(str(file)+suffix)
                if not dest.exists():
                    raw,headers=read_url(url+suffix,limit)
                    dest.write_bytes(raw)
                    receipt['headers'+suffix]=headers
            receipt['status']='CACHED_PAIR_PRESENT_NOT_YET_VERIFIED'
        except Exception as e:
            receipt.update(status='SOURCE_BLOCKED',error=type(e).__name__+': '+str(e))
        return receipt
    with ThreadPoolExecutor(max_workers=4) as pool: receipts=list(pool.map(fetch,inventory()))
    return receipts
def parse_archive(raw,checksum,name,tf,y,m):
    gate(0<len(raw)<=6_000_000,'ZIP_SIZE:'+name)
    try: match=re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?(\S+)',checksum.decode('ascii').strip())
    except UnicodeError: raise GateError('CHECKSUM_ENCODING:'+name)
    gate(match is not None and match[2]==name,'CHECKSUM_FILENAME:'+name)
    gate(match[1].lower()==sha(raw),'CHECKSUM_MISMATCH:'+name)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            entries=z.infolist()
            gate(len(entries)==1 and entries[0].filename==name[:-4]+'.csv','ZIP_MEMBERS:'+name)
            gate(entries[0].file_size<=22_000_000,'ZIP_EXPANSION:'+name)
            text=z.read(entries[0]).decode('utf-8-sig')
    except (zipfile.BadZipFile,UnicodeError,RuntimeError) as e: raise GateError('BAD_ZIP:'+str(e))
    step=86_400_000 if tf=='1d' else 3_600_000
    first=stamp(dt.datetime(y,m,1,tzinfo=UTC))
    expected=calendar.monthrange(y,m)[1]*(1 if tf=='1d' else 24)
    bars={}
    for row in csv.reader(io.StringIO(text)):
        if not row: raise GateError('EMPTY_ROW:'+name)
        if not bars and row[0]=='open_time': continue
        gate(len(row)==12,'ROW_WIDTH:'+name)
        try:
            t=int(row[0]); end=int(row[6]); op,hi,lo,cl=map(float,row[1:5])
            vol=float(row[5])
        except ValueError: raise GateError('ROW_VALUE:'+name)
        gate(all(math.isfinite(v) and v>0 for v in (op,hi,lo,cl)) and math.isfinite(vol) and vol>=0,'BAD_PRICE:'+name)
        gate(lo<=min(op,cl)<=max(op,cl)<=hi,'OHLC:'+name)
        gate(first<=t<first+expected*step and (t-first)%step==0 and end==t+step-1,'CLOCK_OR_HOLDOUT:'+name)
        gate(t not in bars,'DUPLICATE:'+name)
        bars[t]=(op,cl)
    gate(set(bars)==set(range(first,first+expected*step,step)),'INCOMPLETE_MONTH:'+name)
    return bars
def load_archives(folder):
    candles={}; manifest=[]
    for kind,a,tf,y,m,name,url in inventory():
        file=folder/cache_name(kind,name)
        gate(file.is_file() and Path(str(file)+'.CHECKSUM').is_file(),'MISSING_ARCHIVE:'+name)
        raw=file.read_bytes(); check=Path(str(file)+'.CHECKSUM').read_bytes()
        bars=parse_archive(raw,check,name,tf,y,m)
        target=candles.setdefault((kind,a,tf),{})
        gate(not (target.keys() & bars.keys()),'CROSS_MONTH_DUPLICATE')
        target.update(bars)
        manifest.append(dict(url=url,zip_sha256=sha(raw),checksum_sha256=sha(check),candles=len(bars)))
    gate(len(manifest)==319,'INVENTORY_COUNT')
    return candles,manifest
def listing_gate(path):
    evidence=json.loads(path.read_text(encoding='utf-8'))
    gate(set(evidence)==set(ASSETS+(REFERENCE,)),'LISTING_UNIVERSE')
    for a,e in evidence.items():
        gate(e['symbol']==a and e['venue']=='Binance USD-M perpetual' and e['quote']=='USDT','LISTING_IDENTITY:'+a)
        launch=dt.datetime.fromisoformat(e['launch_utc'].replace('Z','+00:00'))
        gate(launch.tzinfo is not None and launch<dt.datetime(2021,12,1,tzinfo=UTC),'LISTING_TOO_LATE:'+a)
        gate(e['source_url'].startswith('https://www.binance.com/') and bool(e['reviewed_evidence']),'LISTING_SOURCE:'+a)
    return evidence
def side(old,new): return (new>old)-(new<old)
def reconstruct(candles):
    rows=[]
    btc=candles['spot','BTCUSDT','1d']
    for a in ASSETS+(REFERENCE,):
        daily=candles['futures/um',a,'1d']; hourly=candles['futures/um',a,'1h']
        for i in range(730):
            day=START+dt.timedelta(days=i)
            old=stamp(day-dt.timedelta(days=21)); new=stamp(day-dt.timedelta(days=1))
            try:
                s=side(daily[old][1],daily[new][1]); b=side(btc[old][1],btc[new][1])
                entry=hourly[stamp(day+dt.timedelta(hours=1))][0]
                exit=hourly[stamp(day+dt.timedelta(hours=2))][0]
            except KeyError as e: raise GateError('CAUSAL_BAR_MISSING:'+a+':'+day.isoformat()) from e
            rows.append(dict(asset=a,date=day.date().isoformat(),year=day.year,asset20=s,btc20=b,
                             signal_known_at=day.isoformat(),entry_utc=(day+dt.timedelta(hours=1)).isoformat(),
                             exit_utc=(day+dt.timedelta(hours=2)).isoformat(),entry=entry,exit=exit,
                             gross_bps=s*(exit/entry-1)*10000,
                             baseline=bool(s),fusion=bool(s and s==b),opposite=bool(s and s==-b)))
    return rows
def ledger(rows,arm,cost): return np.array([r['gross_bps']-cost if r[arm] else 0. for r in rows])
def metrics(values,active):
    values=np.asarray(values); active=np.asarray(active,dtype=bool); traded=values[active]
    positive=float(values[values>0].sum()); negative=float(-values[values<0].sum())
    curve=np.r_[0.,values.cumsum()]
    return dict(days=len(values),trades=int(active.sum()),total_net_bps=float(values.sum()),
                mean_bps_per_calendar_day=float(values.mean()) if len(values) else None,
                mean_bps_per_trade=float(traded.mean()) if len(traded) else None,
                profit_factor=positive/negative if negative else None,
                profitable_trade_pct=float(100*(traded>0).mean()) if len(traded) else None,
                max_drawdown_bps=float((np.maximum.accumulate(curve)-curve).max()),
                remove_top_winners_total={str(k):float(values.sum()-sum(sorted((v for v in traded if v>0),reverse=True)[:k])) for k in (1,3,5)})
def summarize(rows):
    out={}
    for a in ASSETS+(REFERENCE,):
        rs=[r for r in rows if r['asset']==a]
        out[a]={}
        for cost in COSTS:
            result={}
            for arm in ARMS:
                v=ledger(rs,arm,cost); active=[r[arm] for r in rs]
                result[arm]=metrics(v,active)
                result[arm]['by_year']={str(y):metrics(v[[r['year']==y for r in rs]],np.array(active)[[r['year']==y for r in rs]]) for y in (2022,2023)}
                # Direction diagnostics retain all calendar days in denominator.
                result[arm]['by_direction']={str(s):metrics(np.where([r['asset20']==s for r in rs],v,0),[r[arm] and r['asset20']==s for r in rs]) for s in (-1,1)}
            result['fusion_minus_baseline_bps_per_day']=float((ledger(rs,'fusion',cost)-ledger(rs,'baseline',cost)).mean())
            out[a][str(cost)]=result
    return out
def holm(pvalues):
    order=np.argsort(pvalues); adjusted=np.empty(len(order)); prev=0.
    for rank,i in enumerate(order):
        prev=max(prev,min(1.,(len(order)-rank)*pvalues[i]));adjusted[i]=prev
    return adjusted.tolist()
def inference(rows):
    # Paired block resamples share dates across assets/costs, preserving dependence.
    arrays=[]; labels=[]; fusion_by_cost={}
    for a in ASSETS:
        rs=[r for r in rows if r['asset']==a]
        for c in COSTS:
            arrays.append(ledger(rs,'fusion',c)-ledger(rs,'baseline',c));labels.append((a,c))
    matrix=np.array(arrays).T; observed=matrix.mean(axis=0)
    rng=np.random.default_rng(271); samples=[]
    for _ in range(100):
        indices=[]
        for offset in (0,365):
            starts=rng.integers(0,336,size=(100,13))
            indices.append((starts[:,:,None]+np.arange(30)).reshape(100,-1)[:,:365]+offset)
        idx=np.concatenate(indices,axis=1)
        samples.append(matrix[idx].mean(axis=1))
    boot=np.concatenate(samples)
    # Centered, two-sided bootstrap approximation, exploratory and conditional.
    p=((np.abs(boot-observed)>=np.abs(observed)).sum(axis=0)+1)/10001
    adj=holm(p); ci=np.quantile(boot,[.025,.975],axis=0)
    tests=[dict(asset=a,cost_bps=c,delta_bps_day=float(observed[i]),ci95=[float(ci[0,i]),float(ci[1,i])],
                p_centered_bootstrap=float(p[i]),p_holm_25=adj[i]) for i,(a,c) in enumerate(labels)]
    for c in COSTS:
        fv=np.array([ledger([r for r in rows if r['asset']==a],'fusion',c) for a in ASSETS]).T
        bv=np.array([ledger([r for r in rows if r['asset']==a],'baseline',c) for a in ASSETS]).T
        fusion_by_cost[str(c)]=dict(correlation_calendar_daily=np.corrcoef(fv.T).tolist(),
          equal_weight_research_basket=metrics(fv.mean(axis=1),np.any(fv!=0,axis=1)),
          delta_bps_day=float((fv-bv).mean()),
          leave_one_asset_out={a:dict(fusion_mean_bps_day=float(np.delete(fv,i,axis=1).mean()),delta_bps_day=float(np.delete(fv-bv,i,axis=1).mean())) for i,a in enumerate(ASSETS)})
    return dict(method='year-stratified noncircular paired moving block L30, 10000, seed271; centered two-sided approximate p; Holm25; exploratory only',
                tests=tests,asset_order=list(ASSETS),cross_asset=fusion_by_cost)
def write_json(path,obj): path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,default=Path('archives'))
    p.add_argument('--out',type=Path,default=Path('results'))
    p.add_argument('--listings',type=Path,default=Path(__file__).with_name('listings.json'))
    p.add_argument('--fetch',action='store_true')
    x=p.parse_args();x.out.mkdir(parents=True,exist_ok=True)
    # Each invocation gets a fresh result directory; never leave old PASS evidence on failure.
    gate(not any((x.out/n).exists() for n in ('report.json','daily.csv','source_gate.json')),'OUTPUT_ALREADY_USED')
    try:
        if x.fetch:
            receipts=fetch_all(x.cache);write_json(x.out/'fetch_receipts.json',receipts)
            gate(all(r['status']!='SOURCE_BLOCKED' for r in receipts),'PUBLIC_FETCH_BLOCKED: see fetch_receipts.json')
        listings=listing_gate(x.listings)
        candles,manifest=load_archives(x.cache)
        write_json(x.out/'manifest.json',manifest)
        rows=reconstruct(candles)
        report=dict(status='DISCOVERY_DESCRIPTIVE_ONLY_NO_LIVE_GO',protocol_freeze_commit='9273b1446977d23b4896d73d54d27d497fdc528c',
                    source_pairs=len(manifest),source_manifest_sha256=sha((x.out/'manifest.json').read_bytes()),
                    listing_evidence=listings,results=summarize(rows),inference=inference(rows),
                    limitations=['current archive revisions, not historical receipt','OHLC opens not fills; costs hypothetical','survivorship and prior research selection','five correlated assets and 25 cost comparisons; broader historical multiplicity unknown','AVAX reference exposed and excluded from inference/basket','no holdout touched; no independent edge validation'])
        with (x.out/'daily.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        write_json(x.out/'report.json',report)
        write_json(x.out/'source_gate.json',dict(status='ARCHIVE_REPLAY_PASS',pairs=len(manifest),days_per_asset=730,assets=list(ASSETS),reference=REFERENCE,
                  authentic_historical_receipt='UNPROVEN',executable_fills='UNPROVEN',holdout_access=False))
        print('ARCHIVE_REPLAY_PASS: 319 pairs, 4380 rows; DISCOVERY ONLY')
        return 0
    except (GateError,OSError,ValueError,KeyError,zipfile.BadZipFile) as e:
        write_json(x.out/'source_gate.json',dict(status='FAIL_CLOSED',error=str(e),economic_results='NOT_REPORTED',holdout_access=False))
        print('FAIL_CLOSED: '+str(e),file=sys.stderr);return 2
if __name__=='__main__': sys.exit(main())
