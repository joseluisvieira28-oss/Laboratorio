from __future__ import annotations
import csv, hashlib, io, json, math, os, random, re, urllib.parse, urllib.request, zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

LAB_ID='CROSS-ASSET-VOL-STRESS-001'
MVE_ID='CAVS-VXSETTLE-W1-001'
YEARS=list(range(2018,2025))
OUT='artifacts/cross_asset_vol_stress_discovery_v01'
os.makedirs(OUT,exist_ok=True)

EXPECTED_CANONICAL_SHA='48c16e171c06f61378ac216d75d76a22491b417ae904936c3538a34dfb6ab1be'
EXPECTED_RAW={
  2018:'c24dc379ac95493e1cd001ad71835127cecd7451eff50f9c8533e281438fb753',
  2019:'da61c06b4f3e0b0ae87eeb698963e903aad152b57d0e7c833219c7129ace564e',
  2020:'e8da1bddeca9fbe80f7d08fed23e010d8358cbb6a10d5d1ee13941d6aba63a5f',
  2021:'37263e615b9a3dc30146ca571b67af5d58103d36d04c1741aec85a06e96547da',
  2022:'2d8a9675e806e80e670f4a9ed777cba2c5339f6d7d6778d0d32740e2a0361998',
  2023:'4f397581859e7f63a9c275aa574c0be5456ce6789f0532b0b34a105eaf1ad649',
  2024:'5d58ab11071d19ca7c3d621a7067fa8e51bdeec148e4cd12e65fec0b95d3d720'
}
CBOE_BASE='https://www-api.cboe.com/us/futures/market_statistics/final_settlement_prices/values/futures/'
EXPECTED_PRODUCT='VX - Cboe Volatility Index (VX) Futures'
BINANCE_BASE='https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d'
START=date(2018,1,1); END=date(2024,12,31)


def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def fetch(url:str,accept='*/*')->bytes:
    if '2025' in url or '2026' in url:
        raise RuntimeError('PROTECTED_YEAR_URL_BLOCKED')
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':accept})
    with urllib.request.urlopen(req,timeout=60) as r:
        b=r.read()
        if not b: raise RuntimeError('EMPTY_RESPONSE')
        return b

def normalize_date(v)->str:
    s=str(v or '').strip()
    m=re.search(r'(20\d{2})-(\d{2})-(\d{2})',s)
    if m: return '-'.join(m.groups())
    for fmt in ('%m/%d/%Y','%m/%d/%y'):
        try: return datetime.strptime(s,fmt).strftime('%Y-%m-%d')
        except ValueError: pass
    raise RuntimeError(f'UNPARSEABLE_EXPIRE_DATE:{s}')

def parse_price(v)->float:
    if isinstance(v,(int,float)) and not isinstance(v,bool): x=float(v)
    else: x=float(str(v or '').replace(',','').replace('$','').strip())
    if not math.isfinite(x) or x<=0: raise RuntimeError(f'INVALID_SETTLEMENT:{v}')
    return x

def response_data(obj):
    if isinstance(obj,dict) and isinstance(obj.get('data'),list): return obj['data']
    if isinstance(obj,dict) and isinstance(obj.get('data'),dict):
        for k in ('data','products','rows'):
            if isinstance(obj['data'].get(k),list): return obj['data'][k]
    if isinstance(obj,dict) and isinstance(obj.get('result'),list): return obj['result']
    if isinstance(obj,list): return obj
    raise RuntimeError('UNEXPECTED_CBOE_RESPONSE_SHAPE')

def is_vx(label:str)->bool:
    if label==EXPECTED_PRODUCT: return True
    norm=' '.join(label.upper().split())
    return norm.startswith('VX -') and 'VOLATILITY INDEX' in norm and 'FUTURES' in norm and 'MINI' not in norm

def rebuild_cboe_source():
    rows=[]; raw_meta={}
    for y in YEARS:
        url=CBOE_BASE+'?'+urllib.parse.urlencode({'year':str(y)})
        b=fetch(url,'application/json,text/plain,*/*')
        actual=sha(b)
        if actual!=EXPECTED_RAW[y]: raise RuntimeError(f'CBOE_RAW_HASH_MISMATCH:{y}:{actual}')
        obj=json.loads(b.decode('utf-8-sig'))
        selected=None
        if isinstance(obj,dict):
            for k in ('selectedYear','selected_year','year'):
                if k in obj and obj[k] not in (None,''):
                    selected=str(obj[k]); break
        if selected is not None and str(y) not in selected: raise RuntimeError(f'CBOE_YEAR_MISMATCH:{y}:{selected}')
        products=response_data(obj)
        matches=[]
        for p in products:
            if isinstance(p,dict):
                label=str(p.get('product') or p.get('name') or '').strip()
                if is_vx(label): matches.append(p)
        if len(matches)!=1: raise RuntimeError(f'CBOE_VX_PRODUCT_COUNT:{y}:{len(matches)}')
        vx=matches[0]
        m=vx.get('monthly_settlement_prices') or []; w=vx.get('weekly_settlement_prices') or []
        for freq,seq in (('monthly',m),('weekly',w)):
            for r in seq:
                d=normalize_date(r.get('expire_date'))
                if not d.startswith(str(y)+'-'): raise RuntimeError(f'CBOE_DATE_OUTSIDE_YEAR:{d}')
                rows.append({'date':d,'settlement':parse_price(r.get('price')),'symbol_name':str(r.get('symbol_name') or '').strip(),'frequency':freq,'calculation_method':str(r.get('calculation_method') or '').strip()})
        raw_meta[str(y)]={'sha256':actual,'monthly_count':len(m),'weekly_count':len(w)}
    by=defaultdict(list)
    for r in rows: by[r['date']].append(r)
    canonical=[]
    for d in sorted(by):
        rr=by[d]; vals=sorted({round(float(x['settlement']),10) for x in rr})
        if len(vals)!=1: raise RuntimeError(f'CBOE_CONFLICT:{d}')
        canonical.append({'date':d,'settlement':float(vals[0]),'symbols':sorted({x['symbol_name'] for x in rr}),'frequencies':sorted({x['frequency'] for x in rr}),'calculation_methods':sorted({x['calculation_method'] for x in rr if x['calculation_method']})})
    lines=['date,settlement,symbols,frequencies,calculation_methods']
    for r in canonical:
        lines.append(','.join([r['date'],f"{r['settlement']:.10f}",json.dumps(r['symbols'],separators=(':',';')).replace(',',';'),json.dumps(r['frequencies'],separators=(':',';')).replace(',',';'),json.dumps(r['calculation_methods'],separators=(':',';')).replace(',',';')]))
    cb=('\n'.join(lines)+'\n').encode()
    if sha(cb)!=EXPECTED_CANONICAL_SHA: raise RuntimeError(f'CBOE_CANONICAL_HASH_MISMATCH:{sha(cb)}')
    if len(canonical)!=366: raise RuntimeError(f'CBOE_CANONICAL_COUNT:{len(canonical)}')
    return canonical,raw_meta

def month_iter():
    y,m=2018,1
    while (y,m)<=(2024,12):
        yield y,m
        m+=1
        if m==13: y+=1; m=1

def parse_checksum(b:bytes)->str:
    t=b.decode('utf-8-sig','replace')
    m=re.search(r'\b([0-9a-fA-F]{64})\b',t)
    if not m: raise RuntimeError('BINANCE_CHECKSUM_PARSE_FAILURE')
    return m.group(1).lower()

def ts_to_date(x:int)->date:
    if x>10**15: sec=x/1_000_000.0
    elif x>10**12: sec=x/1_000.0
    else: sec=float(x)
    return datetime.fromtimestamp(sec,tz=timezone.utc).date()

def load_binance_daily():
    prices={}; meta=[]
    for y,m in month_iter():
        ym=f'{y:04d}-{m:02d}'; fn=f'BTCUSDT-1d-{ym}.zip'
        url=f'{BINANCE_BASE}/{fn}'
        zb=fetch(url,'application/zip,*/*')
        provider=parse_checksum(fetch(url+'.CHECKSUM','text/plain,*/*'))
        actual=sha(zb)
        if actual!=provider: raise RuntimeError(f'BINANCE_ZIP_CHECKSUM_MISMATCH:{ym}')
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            names=[n for n in z.namelist() if n.lower().endswith('.csv')]
            if len(names)!=1: raise RuntimeError(f'BINANCE_MEMBER_COUNT:{ym}:{len(names)}')
            cb=z.read(names[0])
        row_count=0
        for row in csv.reader(io.StringIO(cb.decode('utf-8-sig','replace'))):
            if not row: continue
            try: ts=int(row[0])
            except ValueError: continue
            if len(row)<5: raise RuntimeError(f'BINANCE_ROW_SHORT:{ym}')
            d=ts_to_date(ts)
            if d<START or d>END: continue
            op=float(row[1])
            if not math.isfinite(op) or op<=0: raise RuntimeError(f'BINANCE_INVALID_OPEN:{d}')
            if d in prices: raise RuntimeError(f'BINANCE_DUPLICATE_DATE:{d}')
            prices[d]=op; row_count+=1
        meta.append({'month':ym,'zip_sha256':actual,'provider_checksum':provider,'csv_sha256':sha(cb),'rows_in_window':row_count})
    expected=(END-START).days+1
    if len(prices)!=expected: raise RuntimeError(f'BINANCE_DAILY_COVERAGE:{len(prices)}/{expected}')
    material=json.dumps(meta,sort_keys=True,separators=(',',':')).encode()
    return prices,meta,sha(material)

def pf(values):
    pos=sum(x for x in values if x>0); neg=-sum(x for x in values if x<0)
    if neg==0: return float('inf') if pos>0 else 0.0
    return pos/neg

def percentile(sorted_x,p):
    if not sorted_x: return None
    if len(sorted_x)==1: return sorted_x[0]
    q=(len(sorted_x)-1)*p; lo=int(math.floor(q)); hi=int(math.ceil(q))
    if lo==hi: return sorted_x[lo]
    return sorted_x[lo]*(hi-q)+sorted_x[hi]*(q-lo)

def block_bootstrap(values):
    n=len(values); L=4
    if n<L: return [None,None]
    blocks=[values[i:i+L] for i in range(n-L+1)]
    rng=random.Random(230911); means=[]
    for _ in range(5000):
        s=[]
        while len(s)<n: s.extend(blocks[rng.randrange(len(blocks))])
        x=s[:n]; means.append(sum(x)/n)
    means.sort()
    return [percentile(means,.025),percentile(means,.975)]

def main():
    canonical,raw_meta=rebuild_cboe_source()
    prices,market_meta,market_manifest_sha=load_binance_daily()

    candidate=[]; no_signal=0; outside=0; missing=0
    for i in range(1,len(canonical)):
        cur=canonical[i]; prev=canonical[i-1]
        delta=float(cur['settlement'])-float(prev['settlement'])
        if delta==0:
            no_signal+=1; continue
        direction=-1 if delta>0 else 1
        sd=date.fromisoformat(cur['date']); entry=sd+timedelta(days=2); exitd=entry+timedelta(days=7)
        if entry<START or exitd>END:
            outside+=1; continue
        if entry not in prices or exitd not in prices:
            missing+=1; continue
        candidate.append({'settlement_date':cur['date'],'prev_settlement_date':prev['date'],'settlement':cur['settlement'],'prev_settlement':prev['settlement'],'delta_vx':delta,'direction':'LONG' if direction==1 else 'SHORT','direction_num':direction,'entry_date':entry.isoformat(),'exit_date':exitd.isoformat(),'entry_open':prices[entry],'exit_open':prices[exitd]})

    accepted=[]; suppressed=0; prior_exit=None
    for c in candidate:
        e=date.fromisoformat(c['entry_date']); x=date.fromisoformat(c['exit_date'])
        if prior_exit is not None and e<prior_exit:
            suppressed+=1; continue
        gross=c['direction_num']*(c['exit_open']/c['entry_open']-1.0)*10000.0
        r=dict(c); r['gross_bps']=gross; r['net10_bps']=gross-10.0; r['net20_bps']=gross-20.0
        accepted.append(r); prior_exit=x

    n=len(accepted); v10=[r['net10_bps'] for r in accepted]
    mean_gross=sum(r['gross_bps'] for r in accepted)/n if n else None
    mean10=sum(v10)/n if n else None; mean20=sum(r['net20_bps'] for r in accepted)/n if n else None
    med=None
    if n:
        gs=sorted(r['gross_bps'] for r in accepted); med=(gs[n//2] if n%2 else (gs[n//2-1]+gs[n//2])/2)
    ci=block_bootstrap(v10) if n else [None,None]
    years={}
    for y in YEARS:
        rr=[r['net10_bps'] for r in accepted if r['entry_date'].startswith(str(y)+'-')]
        years[str(y)]={'n':len(rr),'mean_net10_bps':(sum(rr)/len(rr) if rr else None)}
    nonneg_all=sum(1 for y in YEARS if years[str(y)]['n'] and years[str(y)]['mean_net10_bps']>=0)
    nonneg_recent=sum(1 for y in range(2021,2025) if years[str(y)]['n'] and years[str(y)]['mean_net10_bps']>=0)
    pf10=pf(v10) if n else None; wr=sum(x>0 for x in v10)/n if n else None
    gates={
        'n_ge_300':n>=300,
        'mean_net10_gt_0':mean10 is not None and mean10>0,
        'pf_net10_gt_1':pf10 is not None and pf10>1,
        'bootstrap_95_lower_gt_0':ci[0] is not None and ci[0]>0,
        'nonnegative_years_2018_2024_ge_5':nonneg_all>=5,
        'nonnegative_years_2021_2024_ge_3':nonneg_recent>=3,
        'source_binding_pass':True,
        'access_2025':False,'access_2026':False,'live_trading':False,'exchange_mutation':False
    }
    if n<300: classification='INSUFFICIENT_SAMPLE'
    elif all([gates['mean_net10_gt_0'],gates['pf_net10_gt_1'],gates['bootstrap_95_lower_gt_0'],gates['nonnegative_years_2018_2024_ge_5'],gates['nonnegative_years_2021_2024_ge_3']]): classification='SURVIVES_DISCOVERY'
    else: classification='DISCOVERY_FAIL_NO_PROMOTION'

    trade_bytes=('\n'.join(json.dumps(r,sort_keys=True,separators=(',',':')) for r in accepted)+'\n').encode()
    open(os.path.join(OUT,'resolved_trades.jsonl'),'wb').write(trade_bytes)
    result={
        'lab_id':LAB_ID,'mve_id':MVE_ID,'classification':classification,
        'source_binding_pass':True,'cboe_canonical_sha256':EXPECTED_CANONICAL_SHA,'cboe_raw_sha256':{str(k):v for k,v in EXPECTED_RAW.items()},
        'btc_market_manifest_sha256':market_manifest_sha,'btc_monthly_archives_verified':len(market_meta),
        'latest_market_date_opened':'2024-12-31','access_2025':False,'access_2026':False,
        'n_source_settlements':len(canonical),'n_candidate_signals':len(candidate),'n_resolved':n,'suppressed_overlap':suppressed,'no_signal_delta_zero':no_signal,'dropped_outside_window':outside,'dropped_missing_bar':missing,
        'longs':sum(r['direction']=='LONG' for r in accepted),'shorts':sum(r['direction']=='SHORT' for r in accepted),
        'mean_gross_bps':mean_gross,'median_gross_bps':med,'mean_net10_bps':mean10,'mean_net20_bps':mean20,'profit_factor_net10':pf10,'win_rate_net10':wr,
        'bootstrap_mean_net10_95_ci':ci,'bootstrap_repetitions':5000,'bootstrap_seed':230911,'bootstrap_block_trades':4,
        'calendar_years':years,'nonnegative_years_2018_2024':nonneg_all,'nonnegative_years_2021_2024':nonneg_recent,'gates':gates,
        'trades_sha256':sha(trade_bytes),'orders_submitted':False,'live_trading':False,'exchange_mutation':False,'full_oos_or_live_promotion_authorized':False
    }
    open(os.path.join(OUT,'result.json'),'w',encoding='utf-8').write(json.dumps(result,indent=2,sort_keys=True))
    open(os.path.join(OUT,'btc_market_manifest.json'),'w',encoding='utf-8').write(json.dumps(market_meta,indent=2,sort_keys=True))
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
