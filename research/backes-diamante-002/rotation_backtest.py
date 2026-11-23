#!/usr/bin/env python3
"""BACKES-002: independent public-source ETH/BTC spot rotation; NO TRADING."""
import concurrent.futures as cf
import csv,datetime as dt,hashlib,io,json,math,pathlib,random,statistics,time,urllib.request,zipfile,sys
START=dt.date(2018,1,1); END=dt.date(2026,11,22)
SYMS=('BTCUSDT','ETHUSDT','ETHBTC')
ROOT='https://data.binance.vision/data/spot'
OUT=pathlib.Path('research/backes-diamante-002/results')
CACHE=pathlib.Path('/tmp/backes-002-binance')
COSTS=(5,10,20,35,100)

def jobs():
    x=[]
    for sym in SYMS:
        m=START
        while m<dt.date(2026,11,1):
            y=f'{m:%Y-%m}'; name=f'{sym}-1d-{y}.zip'
            x.append((sym,name,f'{ROOT}/monthly/klines/{sym}/1d/{name}'))
            m=(m.replace(day=28)+dt.timedelta(days=4)).replace(day=1)
        d=dt.date(2026,11,1)
        while d<=END:
            name=f'{sym}-1d-{d:%Y-%m-%d}.zip'
            x.append((sym,name,f'{ROOT}/daily/klines/{sym}/1d/{name}'))
            d+=dt.timedelta(days=1)
    return x

def download(item):
    sym,name,url=item
    dest=CACHE/sym/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    for attempt in range(3):
        try:
            if dest.exists() and zipfile.is_zipfile(dest):
                data=dest.read_bytes()
            else:
                request=urllib.request.Request(url,headers={'User-Agent':'CryptoLab-Research/1.0'})
                with urllib.request.urlopen(request,timeout=30) as r:
                    data=r.read(3_000_000)
                if not zipfile.is_zipfile(io.BytesIO(data)): raise ValueError('invalid ZIP')
                dest.write_bytes(data)
            return {'symbol':sym,'file':str(dest.relative_to(CACHE)),'url':url,
                    'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
        except Exception:
            if attempt==2: raise
            time.sleep(attempt+1)

def parse(entries,sym):
    raw={}
    for record in sorted((q for q in entries if q['symbol']==sym),key=lambda x:x['file']):
        with zipfile.ZipFile(CACHE/record['file']) as archive:
            names=[q for q in archive.namelist() if q.endswith('.csv')]
            if len(names)!=1:raise ValueError('bad member count')
            with archive.open(names[0]) as stream:
                for line in csv.reader(io.TextIOWrapper(stream,encoding='utf-8-sig')):
                    if not line or not line[0].isdigit():continue
                    ms=int(line[0]); ms=ms//1000 if ms>10**14 else ms
                    when=dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc)
                    day=when.date()
                    if day<START or day>END:continue
                    if when.time()!=dt.time():raise ValueError('non-midnight candle '+sym+' '+str(day))
                    o,h,l,c=map(float,line[1:5])
                    if min(o,h,l,c)<=0 or not all(math.isfinite(v) for v in (o,h,l,c)) or h<max(o,c,l) or l>min(o,c,h):raise ValueError('bad OHLC')
                    if day in raw:raise ValueError('duplicate '+sym+' '+str(day))
                    raw[day]=(o,h,l,c)
    n=(END-START).days+1
    if len(raw)!=n or any(START+dt.timedelta(days=i) not in raw for i in range(n)):
        raise ValueError('SOURCE_BLOCKED gaps '+sym+' found '+str(len(raw))+' expected '+str(n))
    weekly=[]
    for i in range(0,n,7):
        dates=[START+dt.timedelta(days=j) for j in range(i,i+7)]
        if len(dates)!=7:raise ValueError('partial week')
        candles=[raw[d] for d in dates]
        weekly.append({'date':str(dates[0]),'open':candles[0][0],
            'high':max(k[1] for k in candles),'low':min(k[2] for k in candles),
            'close':candles[-1][3]})
    return weekly

def signals(ratio):
    confirmed=[]; states=[]
    for t in range(len(ratio)):
        j=t-3
        if j>=3:
            low=ratio[j]['low']
            if low<min(ratio[k]['low'] for k in range(j-3,j)) and low<min(ratio[k]['low'] for k in range(j+1,t+1)):
                confirmed.append((j,low))
        rise=len(confirmed)>1 and confirmed[-1][1]>confirmed[-2][1]
        momentum=t>=4 and ratio[t]['close']>ratio[t-4]['close']
        states.append('ETH' if rise and momentum else 'BTC')
    return states

def drawdown(xs):
    peak=xs[0]; worst=0.
    for x in xs:
        peak=max(peak,x);worst=min(worst,x/peak-1)
    return worst

def simulate(btc,eth,sigs,year_a,year_b,bps,double=False):
    ix=[i for i,w in enumerate(btc) if year_a<=int(w['date'][:4])<=year_b]
    if not ix:raise ValueError('empty evaluation period')
    names=('BTC','ETH','MIX','ROT')
    values={k:1. for k in names};weights={k:(0.,0.) for k in names}
    paths={k:[1.] for k in names};rets={k:[] for k in names}
    switches=0;cost=bps/10000
    for j,i in enumerate(ix):
        nexti=ix[j+1] if j+1<len(ix) else None
        br=(btc[nexti]['open'] if nexti is not None else btc[i]['close'])/btc[i]['open']
        er=(eth[nexti]['open'] if nexti is not None else eth[i]['close'])/eth[i]['open']
        alloc={'BTC':(1.,0.),'ETH':(0.,1.),'MIX':(.5,.5),
               'ROT':(0.,1.) if i>0 and sigs[i-1]=='ETH' else (1.,0.)}
        for k in names:
            pb,pe=weights[k];wb,we=alloc[k];original=values[k]
            traded=max(abs(wb-pb),abs(we-pe))
            if k=='ROT' and j>0 and traded>.5:switches+=1
            legs=2 if k=='ROT' and j>0 and double else 1
            values[k]*=(1-cost*traded*legs)
            growth=wb*br+we*er;values[k]*=growth
            weights[k]=(wb*br/growth,we*er/growth)
            paths[k].append(values[k]);rets[k].append(values[k]/original-1)
    years=len(ix)*7/365.25
    result={}
    for k in names:
        v=values[k]
        result[k]={'total_return_pct':round((v-1)*100,4),
          'cagr_pct':round((v**(1/years)-1)*100,4),
          'max_drawdown_pct':round(drawdown(paths[k])*100,4)}
    return result,switches,rets

def bootstrap(a,b):
    diff=[u-v for u,v in zip(a,b)];n=len(diff);size=min(8,n);rng=random.Random(7430)
    samples=[]
    for _ in range(2000):
        z=[]
        while len(z)<n:
            s=rng.randint(0,n-size);z.extend(diff[s:s+size])
        samples.append(statistics.mean(z[:n]))
    samples.sort()
    return {'mean_weekly_excess_pct':round(statistics.mean(diff)*100,5),
            'ci95_lower_pct':round(samples[50]*100,5),
            'ci95_upper_pct':round(samples[1950]*100,5)}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    j=jobs();errors=[];entries=[]
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        futures={pool.submit(download,item):item for item in j}
        for f in cf.as_completed(futures):
            try:entries.append(f.result())
            except Exception as exc:errors.append(str(futures[f])+': '+repr(exc))
    (OUT/'source_manifest.json').write_text(json.dumps(
        {'start':str(START),'end':str(END),'files':sorted(entries,key=lambda r:r['file']),
        'source_errors':errors},indent=2))
    if errors:
        (OUT/'RESULT.md').write_text('# SOURCE_BLOCKED\n\n'+ '\n'.join(errors[:20])+'\n')
        sys.exit('SOURCE_BLOCKED: inaccessible archives, no backtest')
    try:
        w={s:parse(entries,s) for s in SYMS}
        for a,b,c in zip(w['BTCUSDT'],w['ETHUSDT'],w['ETHBTC']):
            if a['date']!=b['date'] or a['date']!=c['date'] or not(.9<c['open']/(b['open']/a['open'])<1.1):
                raise ValueError('cross quote date/price mismatch '+a['date'])
    except Exception as e:
        (OUT/'RESULT.md').write_text('# SOURCE_BLOCKED\n\n'+str(e)+'\n');raise
    sig=signals(w['ETHBTC']);records=[]
    for p in ((2018,2022),(2023,2024),(2025,2026),(2018,2026)):
        for bps in COSTS:
            for double in ((False,True) if bps in (10,35) else (False,)):
                result,switches,rets=simulate(w['BTCUSDT'],w['ETHUSDT'],sig,*p,bps,double)
                rec={'period':str(p[0])+'-'+str(p[1]),'bps_each_leg':bps,
                     'two_legs_on_switch':double,'n_weeks':len(rets['ROT']),
                     'switches':switches,'strategies':result}
                if p==(2025,2026):
                    rec['bootstrap']={k:bootstrap(rets['ROT'],rets[k]) for k in ('BTC','ETH','MIX')}
                records.append(rec)
    (OUT/'results.json').write_text(json.dumps({'experiment':'BACKES-DIAMANTE-002',
       'note':'independent lab hypothesis; NOT Backes proprietary strategy',
       'trades_executed':0,'cutoff':str(END),'weekly_rows':len(sig),'source_files':len(entries),
       'results':records},indent=2))
    t=next(x for x in records if x['period']=='2025-2026' and x['bps_each_leg']==10 and not x['two_legs_on_switch'])
    lines=['# BACKES-DIAMANTE-002 — Resultado retrospectivo','',
     'Dados: Binance Spot; SHA256 de cada ZIP no source_manifest.json.',
     'Regra do laboratório, NÃO regra privada de Augusto Backes. Sem trades reais.',
     'Os custos são cenários, não comissões específicas da conta.','',
     '## 2025–2026 até 22 de novembro UTC; 10 bps por operação','',
     '| Sistema | Retorno líquido | CAGR | DD máximo |','|---|---:|---:|---:|']
    for key in ('BTC','ETH','MIX','ROT'):
        v=t['strategies'][key]
        lines.append(f"| {key} | {v['total_return_pct']}% | {v['cagr_pct']}% | {v['max_drawdown_pct']}% |")
    lines+=['',f"Rotação: {t['switches']} mudanças de ativo.",'',
     '## Bootstrap semanal em blocos (8 semanas), excesso ROT vs benchmark']
    for key,value in t['bootstrap'].items():
        lines.append(f"- {key}: {value}")
    lines+=['','## Sensibilidade a custos','',
        '| bps por lado | BTC | ETH | 50/50 | ROT |',
        '|---:|---:|---:|---:|---:|']
    for bps in COSTS:
        s=next(x for x in records if x['period']=='2025-2026' and x['bps_each_leg']==bps and not x['two_legs_on_switch'])
        lines.append('| '+str(bps)+' | '+' | '.join(str(s['strategies'][k]['total_return_pct'])+'%' for k in ('BTC','ETH','MIX','ROT'))+' |')
    lines+=['','**Gate:** comparação retrospectiva, não prova de edge independente ou prospetivo.',
       'A hipótese foi formulada em novembro 2026; a janela 2025–2026 não é realmente OOS de desenvolvimento.',
       'É necessário replicação prospetiva congelada com custos e liquidez reais.']
    (OUT/'RESULT.md').write_text('\n'.join(lines)+'\n')
    print('SOURCE_OK',len(entries),'ZIPs',len(sig),'weeks')
if __name__=='__main__':main()
