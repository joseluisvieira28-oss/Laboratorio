#!/usr/bin/env python3
"""Fixed, checksum-verified, public-data discovery. No account/exchange actions."""
import concurrent.futures as cf
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import statistics as st
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = Path('research/index_rebalance_forced_flow')
EVENTS = [
 ('2024-04','NEAR','ADD','2024-03-19','2024-04-02'),
 ('2024-04','XLM','DELETE','2024-03-19','2024-04-02'),
 ('2024-07','HBAR','ADD','2024-06-20','2024-07-02'),
 ('2024-07','RNDR','ADD','2024-06-20','2024-07-02'),
 ('2024-07','DOGE','DELETE','2024-06-20','2024-07-02'),
 ('2024-07','SHIB','DELETE','2024-06-20','2024-07-02'),
 ('2024-10','XLM','ADD','2024-09-18','2024-10-02'),
 ('2024-10','ATOM','DELETE','2024-09-18','2024-10-02'),
 ('2025-01','SUI','ADD','2025-01-03','2025-01-31'),
 ('2025-01','AAVE','ADD','2025-01-03','2025-01-31'),
 ('2025-01','RENDER','DELETE','2025-01-03','2025-01-31'),
 ('2025-01','ETC','DELETE','2025-01-03','2025-01-31'),
 ('2025-10','CRO','ADD','2025-10-03','2025-10-31'),
 ('2025-10','FIL','DELETE','2025-10-03','2025-10-31'),
]
BASE = 'https://data.binance.vision/data/spot/daily/klines'

def boundaries(e):
    ent = datetime.fromisoformat(e[3]).replace(tzinfo=timezone.utc) + timedelta(days=2)
    impl = datetime.fromisoformat(e[4]).replace(hour=16,tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc)
    return ent, impl - timedelta(minutes=6)

def url(pair, day):
    assert 2024 <= int(day[:4]) <= 2025, 'holdout forbidden'
    return f'{BASE}/{pair}/1m/{pair}-1m-{day}.zip'

def get(u):
    assert u.startswith(BASE + '/'), 'public archive allowlist'
    err = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'CryptoLabIndexV03/1.0'}),timeout=30) as r:
                return r.read()
        except Exception as x:
            err = x
    raise err

def load(key):
    pair, day = key
    u = url(pair,day)
    try:
        checksum = get(u+'.CHECKSUM').decode('ascii').strip().split()[0].lower()
        if len(checksum)!=64 or any(c not in '0123456789abcdef' for c in checksum):
            raise ValueError('invalid checksum receipt')
        raw = get(u)
        digest = hashlib.sha256(raw).hexdigest()
        if digest != checksum:
            raise ValueError('checksum mismatch')
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            files=[n for n in z.namelist() if n.endswith('.csv')]
            if len(files)!=1: raise ValueError('ambiguous archive member')
            content=z.read(files[0]).decode('utf-8')
        bars={}
        for p in csv.reader(io.StringIO(content)):
            if not p: continue
            if not p[0].isdigit(): raise ValueError('unexpected nonnumeric timestamp')
            t=int(p[0]); t=t//1000 if t>10**14 else t
            close_t=int(p[6]); close_t=close_t//1000 if close_t>10**14 else close_t
            vals=[float(p[i]) for i in (1,2,3,4)]
            if t in bars or t%60000 or not all(math.isfinite(x) and x>0 for x in vals):
                raise ValueError('invalid/duplicate bar')
            op,hi,lo,cl=vals
            if not(lo<=op<=hi and lo<=cl<=hi) or not(t<=close_t<t+60000):
                raise ValueError('invalid bar geometry/time')
            bars[t]=(op,cl)
        return key, bars, {'url':u,'sha256':digest,'bars':len(bars),'status':'VERIFIED'}
    except Exception as x:
        return key, None, {'url':u,'status':'SOURCE_INCOMPLETE','error':f'{type(x).__name__}: {x}'}

def median(xs): return st.median(xs) if xs else None
def positive(x): return x is not None and x>0

def analyze(rows):
    valid=[r for r in rows if r['market_valid']]
    sx=[r['signed_exbtc'] for r in valid]
    sr=[r['signed_raw'] for r in valid]
    sn=[r['net_model_signed_exbtc'] for r in valid]
    quarters=sorted({r['quarter'] for r in valid})
    loo=[median(sx[:i]+sx[i+1:]) for i in range(len(sx))]
    qloo={q:median([r['signed_exbtc'] for r in valid if r['quarter']!=q]) for q in quarters}
    netqloo={q:median([r['net_model_signed_exbtc'] for r in valid if r['quarter']!=q]) for q in quarters}
    pos=[x for x in sx if x>0]
    conc=max(pos)/sum(pos) if pos else None
    hit=sum(x>0 for x in sx)/len(sx) if sx else 0
    adds=median([r['signed_exbtc'] for r in valid if r['action']=='ADD'])
    deletes=median([r['signed_exbtc'] for r in valid if r['action']=='DELETE'])
    gates={
      'n_ge_12':len(valid)>=12,
      'median_signed_exbtc_gt_1pct':median(sx) is not None and median(sx)>.01,
      'hit_ge_65pct':hit>=.65,
      'median_signed_raw_gt_0':positive(median(sr)),
      'loo_all_positive':bool(loo) and all(positive(x) for x in loo),
      'quarter_loo_all_positive':bool(qloo) and all(positive(x) for x in qloo.values()),
      'concentration_le_35pct':conc is not None and conc<=.35,
      'median_add_exbtc_gt_0':positive(adds),
      'median_delete_signed_exbtc_gt_0':positive(deletes),
      'net_model_median_gt_0':positive(median(sn)),
      'net_model_quarter_loo_all_positive':bool(netqloo) and all(positive(x) for x in netqloo.values()),
    }
    return {'n_source':len(rows),'n_market_valid':len(valid),'quarter_clusters':len(quarters),
      'median_signed_exbtc':median(sx),'positive_count':sum(x>0 for x in sx),'hit_signed_exbtc':hit,
      'median_signed_raw':median(sr),'median_net_model_signed_exbtc':median(sn),
      'loo_medians':loo,'quarter_loo_medians':qloo,'net_quarter_loo_medians':netqloo,
      'positive_concentration':conc,'median_add_exbtc':adds,'median_delete_signed_exbtc':deletes,
      'gates':gates,'verdict':'SURVIVES_DISCOVERY' if all(gates.values()) else 'NO_EDGE_DISCOVERY',
      'execution_proven':False,'holdout_2026_opened':False}

def main():
    for name in ('V03_SOURCE_ADJUDICATION_2026-10-06.md','V03_PRE_OUTCOME_ANALYSIS_FREEZE_2026-10-06.md','V03_OUTCOME_ACTIVATION_2026-10-06.md'):
        if not (ROOT/name).is_file(): raise SystemExit('BLOCKED missing authority: '+name)
    out=Path('index_v03_evidence')
    if out.exists(): raise SystemExit('BLOCKED existing evidence; no repeated discovery')
    out.mkdir()
    keys=set()
    for e in EVENTS:
        for dt in boundaries(e):
            keys.add((e[1]+'USDT',dt.date().isoformat()))
            keys.add(('BTCUSDT',dt.date().isoformat()))
    data={}; receipts=[]
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for key,bars,receipt in pool.map(load,sorted(keys)):
            data[key]=bars; receipts.append(receipt)
    prepared=[]
    for e in EVENTS:
        ent,exitopen=boundaries(e)
        refs=[(e[1]+'USDT',ent),(e[1]+'USDT',exitopen),('BTCUSDT',ent),('BTCUSDT',exitopen)]
        present=all(data.get((pair,dt.date().isoformat())) is not None and int(dt.timestamp()*1000) in data[(pair,dt.date().isoformat())] for pair,dt in refs)
        prepared.append((e,ent,exitopen,present))
    n=sum(p[3] for p in prepared)
    if n<12:
        result={'summary':{'verdict':'SOURCE_BLOCKED','n_source':14,'n_market_valid':n,'outcomes_computed':False,'holdout_2026_opened':False},'receipts':receipts}
    else:
        rows=[]
        for e,ent,exitopen,present in prepared:
            q,sym,act,pub,impl=e
            row={'quarter':q,'symbol':sym,'action':act,'conservative_public_date':pub,'implementation_date':impl,'market_valid':present,'entry_utc':ent.isoformat(),'exit_bar_open_utc':exitopen.isoformat()}
            if present:
                def bar(pair,dt): return data[(pair,dt.date().isoformat())][int(dt.timestamp()*1000)]
                pe=bar(sym+'USDT',ent)[0]; px=bar(sym+'USDT',exitopen)[1]
                be=bar('BTCUSDT',ent)[0]; bx=bar('BTCUSDT',exitopen)[1]
                ra=px/pe-1; rb=bx/be-1; direction=1 if act=='ADD' else -1
                days=(exitopen+timedelta(minutes=1)-ent).total_seconds()/86400
                cost=.008+.001*days
                row.update(entry_price=pe,exit_price=px,btc_entry_price=be,btc_exit_price=bx,r_asset=ra,r_btc=rb,signed_raw=direction*ra,signed_exbtc=direction*(ra-rb),holding_days=days,cost_model=cost,net_model_signed_exbtc=direction*(ra-rb)-cost)
            else: row['exclusion']='SOURCE_INCOMPLETE; no outcome imputation'
            rows.append(row)
        result={'summary':analyze(rows),'events':rows,'receipts':receipts}
    result['authority_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('V03_*.md')}
    result['runner_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('INDEX_V03_RESULT_BEGIN')
    print(json.dumps(result,sort_keys=True))
    print('INDEX_V03_RESULT_END')

if __name__=='__main__': main()
