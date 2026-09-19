from __future__ import annotations

import argparse, csv, hashlib, json, math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from random import Random
from statistics import mean, median
from typing import Any

EXPERIMENT_ID='EMA-CROSSOVER-INTERMEDIATE-MEXC-REP-001'
SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','BNBUSDT','XRPUSDT','DOGEUSDT')
TF_MS={'2H':2*3600_000,'4H':4*3600_000,'6H':6*3600_000,'8H':8*3600_000}
PAIRS={'EMA20x50':(20,50),'EMA50x200':(50,200)}
FIFTEEN_MS=900_000
START_MS=int(datetime(2023,2,1,tzinfo=timezone.utc).timestamp()*1000)
END_MS=int(datetime(2024,12,31,16,0,tzinfo=timezone.utc).timestamp()*1000)
BASE_COST_BPS=10.0
STRESS_COST_BPS=14.0
H=6
MIN_N=50
BOOT_REPS=5000
BOOT_SEED=20260919
P_MAX=0.10
Q_MAX=0.10
RAW_HEADER=('open_time','open','high','low','close','volume','amount','close_time')
EXPECTED_FP={
'BTCUSDT':'fba38a205b911fad0494b86174ef06a2d04a5908b0617a27efb74f067f8cf1d9',
'ETHUSDT':'5a6433eb8703a9bcd0714fc6485ccc965cf754941ee6c69981158a7f11f36b7f',
'SOLUSDT':'db013d47799b99a7c827740cf03c8e7e27b08c317097836143c855f1a51dde9b',
'BNBUSDT':'ec43c0ab51dbf80fcde273c7d817b7cf9995e1614dfa5c05de4f664b9880437a',
'XRPUSDT':'9b15ebea40555f5d6def5aab65cc5485db8120e0a6fa74f53ac4bb981a004427',
'DOGEUSDT':'786a0129a2a7c9b58e2a465383d4849cedc3192e2c24bf8e4474ee709a3323fe'}
PARENT_MEAN={
'2H:EMA20x50':6.82137361092228,'2H:EMA50x200':102.39823452941486,
'4H:EMA20x50':50.16199467086497,'4H:EMA50x200':-45.24582017280156,
'6H:EMA20x50':164.86578966409527,'6H:EMA50x200':95.07867564861247,
'8H:EMA20x50':76.80231204380571,'8H:EMA50x200':107.87775066141853}

@dataclass(frozen=True)
class Bar:
    t:int; o:float; h:float; l:float; c:float; v:float


def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for ch in iter(lambda:f.read(1024*1024),b''): h.update(ch)
    return h.hexdigest()

def prefix(sym:str)->str:
    return sym[:-4]+'_USDT'

def verify_and_load(root:Path):
    raw=root/'tfg_pbr01_1d_raw'; mans=root/'tfg_pbr01_1d_manifests'; recs=root/'tfg_pbr01_1d_receipts'
    gate=json.loads((recs/'TFG_PBR01_1D_PARENT_CORPUS_IDENTITY_GATE_V0.1.json').read_text())
    assert gate['status']=='PASS_EXACT_PARENT_CORPUS_IDENTITY_GATE'
    assert gate['total_detected_gap_count']==36 and gate['total_missing_candle_count']==102
    assert gate['validation_2025_market_bytes_accessed'] is False and gate['holdout_2026_market_bytes_accessed'] is False
    out={}; audit={}; total_files=0
    for sym in SYMBOLS:
        m=json.loads((mans/f'{sym}_MANIFEST.json').read_text())
        assert m['status']=='PASS_CORPUS_AUDIT_ONLY_WITH_GAPS'
        assert m['fingerprint']==EXPECTED_FP[sym]
        assert m['expected_month_count']==23 and m['passed_month_count']==23 and m['total_row_count']==67183
        assert m['total_detected_gap_count']==6 and m['total_missing_candle_count']==17
        rows=[]; prev=None
        for mm in m['months']:
            p=raw/mm['source_file_name']; total_files+=1
            assert p.is_file() and sha256_file(p)==mm['source_sha256']
            with p.open('r',encoding='utf-8-sig',newline='') as fh:
                r=csv.reader(fh); hdr=tuple(next(r)); assert hdr==RAW_HEADER
                for x in r:
                    if not x: continue
                    t=int(x[0]); close_t=int(x[7])
                    assert t%FIFTEEN_MS==0 and close_t==t+FIFTEEN_MS
                    o,hi,lo,c,v=map(float,(x[1],x[2],x[3],x[4],x[5]))
                    assert min(o,hi,lo,c)>0 and v>=0 and hi>=max(o,c,lo) and lo<=min(o,c,hi)
                    if START_MS<=t<END_MS:
                        if prev is not None: assert t>prev
                        prev=t; rows.append(Bar(t,o,hi,lo,c,v))
        assert len(rows)==67151,(sym,len(rows))
        out[sym]=rows
        gaps=sum(1 for a,b in zip(rows,rows[1:]) if b.t-a.t!=FIFTEEN_MS)
        missing=sum((b.t-a.t)//FIFTEEN_MS-1 for a,b in zip(rows,rows[1:]) if b.t-a.t>FIFTEEN_MS)
        assert gaps==6 and missing==17,(sym,gaps,missing)
        audit[sym]={'effective_15m_rows':len(rows),'gap_count':gaps,'missing_candles':missing,'fingerprint':m['fingerprint']}
    assert total_files==138,total_files
    return out,audit

def aggregate(src:list[Bar], ms:int):
    n=ms//FIFTEEN_MS; buckets=defaultdict(list)
    for b in src: buckets[b.t-(b.t%ms)].append(b)
    out=[]; incomplete=0
    for t in sorted(buckets):
        xs=sorted(buckets[t],key=lambda z:z.t)
        exp=[t+i*FIFTEEN_MS for i in range(n)]
        if len(xs)!=n or [x.t for x in xs]!=exp:
            incomplete+=1; continue
        out.append(Bar(t,xs[0].o,max(x.h for x in xs),min(x.l for x in xs),xs[-1].c,sum(x.v for x in xs)))
    return out,incomplete

def split_segments(bs:list[Bar],ms:int):
    if not bs:return []
    segs=[[bs[0]]]
    for b in bs[1:]:
        if b.t-segs[-1][-1].t==ms: segs[-1].append(b)
        else: segs.append([b])
    return segs

def ema(vals:list[float],n:int):
    out=[None]*len(vals)
    if len(vals)<n:return out
    x=sum(vals[:n])/n; out[n-1]=x; a=2/(n+1)
    for i in range(n,len(vals)):
        x=a*vals[i]+(1-a)*x; out[i]=x
    return out

def events_for_segment(seg:list[Bar],sym:str,tf:str):
    cls=[b.c for b in seg]; e20,e50,e200=ema(cls,20),ema(cls,50),ema(cls,200)
    em={20:e20,50:e50,200:e200}; ev=[]
    for pair,(fast,slow) in PAIRS.items():
        ef,es=em[fast],em[slow]
        for i in range(max(slow-1,1),len(seg)-1):
            if None in (ef[i-1],es[i-1],ef[i],es[i]): continue
            d0=float(ef[i-1])-float(es[i-1]); d1=float(ef[i])-float(es[i])
            direction=1 if d0<=0<d1 else (-1 if d0>=0>d1 else 0)
            if not direction: continue
            entry_i=i+1; exit_i=entry_i+H
            if exit_i>=len(seg): continue
            entry=seg[entry_i].o; exitp=seg[exit_i].o
            gross=direction*(exitp/entry-1.0)*10_000
            base=gross-BASE_COST_BPS; stress=gross-STRESS_COST_BPS
            ev.append({'cell':f'{tf}:{pair}','timeframe':tf,'pair':pair,'symbol':sym,
                       'direction':direction,'signal_open_time':seg[i].t,'entry_open_time':seg[entry_i].t,
                       'exit_open_time':seg[exit_i].t,'entry':entry,'exit':exitp,
                       'gross_bps':gross,'base_net_bps':base,'stress_net_bps':stress})
    return ev

def pf(vals):
    pos=sum(x for x in vals if x>0); neg=-sum(x for x in vals if x<0)
    return pos/neg if neg>0 else None

def concentration(vals):
    pos=[x for x in vals if x>0]
    return max(pos)/sum(pos) if pos and sum(pos)>0 else None

def metrics(events,key='base_net_bps'):
    vals=[float(e[key]) for e in events]
    return {'n':len(vals),'mean':mean(vals) if vals else None,'median':median(vals) if vals else None,
            'pf':pf(vals),'positive_fraction':sum(x>0 for x in vals)/len(vals) if vals else None,
            'largest_positive_share':concentration(vals),
            'symbol_distribution':dict(sorted(Counter(e['symbol'] for e in events).items()))}

def bootstrap(events):
    groups=defaultdict(list)
    for e in events: groups[e['entry_open_time']//86_400_000].append(float(e['base_net_bps']))
    days=sorted(groups); vals=[v for d in days for v in groups[d]]
    if not vals:return {'days':0,'lower95':None,'upper95':None,'p_one_sided':None}
    sums={d:sum(groups[d]) for d in days}; ns={d:len(groups[d]) for d in days}; rng=Random(BOOT_SEED); draws=[]
    for _ in range(BOOT_REPS):
        s=0.0;n=0
        for __ in range(len(days)):
            d=days[rng.randrange(len(days))]; s+=sums[d]; n+=ns[d]
        draws.append(s/n)
    draws.sort()
    def pct(p):
        pos=(len(draws)-1)*p; lo=int(pos); hi=min(lo+1,len(draws)-1); f=pos-lo
        return draws[lo]*(1-f)+draws[hi]*f
    p=(sum(x<=0 for x in draws)+1)/(len(draws)+1)
    return {'days':len(days),'lower95':pct(.025),'upper95':pct(.975),'p_one_sided':p}

def bh(items):
    s=sorted(items,key=lambda x:x[1]); m=len(s); qs=[min(1,p*m/(i+1)) for i,(_,p) in enumerate(s)]
    for i in range(m-2,-1,-1): qs[i]=min(qs[i],qs[i+1])
    return {k:q for (k,_),q in zip(s,qs)}

def year_metrics(events):
    out={}
    for y in (2023,2024):
        xs=[e for e in events if datetime.fromtimestamp(e['entry_open_time']/1000,tz=timezone.utc).year==y]
        out[str(y)]=metrics(xs)
    return out

def run(root:Path,outdir:Path):
    src,source_audit=verify_and_load(root)
    all_events=[]; deriv={}
    for tf,ms in TF_MS.items():
        deriv[tf]={}
        for sym in SYMBOLS:
            bars,inc=aggregate(src[sym],ms); segs=split_segments(bars,ms)
            ev=[]
            for seg in segs: ev.extend(events_for_segment(seg,sym,tf))
            all_events.extend(ev)
            deriv[tf][sym]={'complete_bars':len(bars),'incomplete_buckets_dropped':inc,'contiguous_segments':len(segs)}
    cells=defaultdict(list)
    for e in all_events: cells[e['cell']].append(e)
    temp={}; pitems=[]
    for cell in sorted(cells):
        base=metrics(cells[cell]); stress=metrics(cells[cell],'stress_net_bps'); boot=bootstrap(cells[cell])
        temp[cell]={'parent_discovery_mean_net_bps':PARENT_MEAN[cell],'base':base,'stress':stress,'bootstrap':boot,'by_year':year_metrics(cells[cell])}
        if boot['p_one_sided'] is not None:pitems.append((cell,boot['p_one_sided']))
    q=bh(pitems)
    for cell,d in temp.items():
        n=d['base']['n']; bm=d['base']['mean']; p=d['bootstrap']['p_one_sided']; qv=q.get(cell); pfv=d['base']['pf']; parent=PARENT_MEAN[cell]
        if n<MIN_N: cl='INSUFFICIENT_SAMPLE'
        elif parent>0 and bm is not None and bm>0 and pfv is not None and pfv>1 and p is not None and p<=P_MAX and qv is not None and qv<=Q_MAX:
            cl='REPLICATION_SUPPORTIVE'
        elif bm is not None and bm<0 and pfv is not None and pfv<1 and d['bootstrap']['upper95'] is not None and d['bootstrap']['upper95']<0:
            cl='REPLICATION_CONTRADICTS_STRONG'
        elif bm is not None and bm<0 and pfv is not None and pfv<1:
            cl='REPLICATION_CONTRADICTS_ECONOMIC'
        else: cl='REPLICATION_MIXED'
        d['bh_fdr_q']=qv; d['classification']=cl
        d['support_gate']={'n_ge_50':n>=MIN_N,'parent_mean_positive':parent>0,'mexc_mean_positive':bm is not None and bm>0,
                           'pf_gt_1':pfv is not None and pfv>1,'p_le_0_10':p is not None and p<=P_MAX,'q_le_0_10':qv is not None and qv<=Q_MAX}
    result={'experiment_id':EXPERIMENT_ID,'status':'REPLICATION_COMPLETE','source_audit':source_audit,'derived_data_audit':deriv,
            'event_count':len(all_events),'cells':temp,'classification_counts':dict(Counter(d['classification'] for d in temp.values())),
            'governance':{'2025_access':False,'2026_access':False,'live_trading':False,'exchange_mutation':False,'merge_to_main':False,'post_outcome_tuning':False}}
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/'EMA_CROSSOVER_INTERMEDIATE_MEXC_REP_001_RESULT_V0.1.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    fields=sorted({k for e in all_events for k in e})
    with (outdir/'EMA_CROSSOVER_INTERMEDIATE_MEXC_REP_001_EVENT_LEDGER_V0.1.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(sorted(all_events,key=lambda e:(e['entry_open_time'],e['cell'],e['symbol'])))
    print(json.dumps({'event_count':len(all_events),'classification_counts':result['classification_counts'],
                      'cells':{k:{'n':v['base']['n'],'mean':v['base']['mean'],'pf':v['base']['pf'],'p':v['bootstrap']['p_one_sided'],'q':v['bh_fdr_q'],'class':v['classification']} for k,v in temp.items()}},indent=2,sort_keys=True))

def selftest():
    xs=[100.0]*250; e=ema(xs,20); assert e[-1]==100.0
    bs=[Bar(i*FIFTEEN_MS,100,101,99,100,1) for i in range(8)]; o,inc=aggregate(bs,2*FIFTEEN_MS); assert len(o)==4 and inc==0
    print('SELF_TEST=PASS')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--artifact-root',type=Path);ap.add_argument('--output-dir',type=Path);ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    if a.self_test:selftest();return
    if not a.artifact_root or not a.output_dir: raise SystemExit('artifact-root and output-dir required')
    run(a.artifact_root,a.output_dir)
if __name__=='__main__': main()
