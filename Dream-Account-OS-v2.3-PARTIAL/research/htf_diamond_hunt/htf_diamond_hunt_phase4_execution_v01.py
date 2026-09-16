from __future__ import annotations

import bisect, csv, hashlib, io, json, sys, time, urllib.request, zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from random import Random
from statistics import mean, median
from typing import Any

from research.htf_diamond_hunt import htf_diamond_hunt_scale_transfers_v01 as core
from research.htf_diamond_hunt import htf_diamond_hunt_phase3_source_gate_v01 as p3src

ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'research'/'htf_diamond_hunt'
FREEZE=R/'HTF_DIAMOND_HUNT_001_PHASE4_FUNDING_EXECUTION_FREEZE_V0.1.json'
P3BIND=R/'HTF_DIAMOND_HUNT_001_PHASE3_SOURCE_BINDING_V0.1.json'
FUND_BIND=R/'HTF_DIAMOND_HUNT_001_PHASE4_FUNDING_SOURCE_BINDING_V0.1.json'
OUT=ROOT/'research'/'local_data'/'htf_diamond_hunt_phase4_execution_v01'
SYMBOLS=core.SYMBOLS
MIN_MS=60_000
BASE_COST=0.002
STRESS_COST=0.003
REPS=5000
SEED=230911
UA='HTF-DIAMOND-HUNT-001 Phase4 frozen execution/1.0'

@dataclass(frozen=True)
class ExecRow:
    cell_id:str
    symbol:str
    signal_open_time:int
    entry_time:int
    exit_time:int|None
    entry_price:float
    exit_price:float|None
    stop:float
    target:float
    initial_risk_fraction:float
    exit_reason:str
    price_gross_return:float|None
    funding_return:float|None
    funding_event_count:int
    economic_gross_return:float|None
    base_net_r:float|None
    stress_net_r:float|None
    execution_path_unresolved:bool


def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def get(url:str,retries:int=4)->bytes:
    last=None
    for k in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA})
            with urllib.request.urlopen(req,timeout=120) as r:
                if r.status!=200:raise RuntimeError(f'HTTP {r.status}')
                return r.read()
        except Exception as e:
            last=e
            if k+1<retries:time.sleep(2**k)
    raise RuntimeError(f'download failed {url}: {last}')

def load_funding(path:Path):
    times=[]; rates=[]
    with path.open(newline='') as f:
        r=csv.DictReader(f)
        assert tuple(r.fieldnames or ())==('funding_time_ms','funding_rate')
        prev=None
        for x in r:
            t=int(x['funding_time_ms']); rate=float(x['funding_rate'])
            if prev is not None:assert t>prev
            assert isfinite(rate); prev=t; times.append(t);rates.append(rate)
    return times,rates

def load_price_minutes(records:list[dict[str,Any]],symbol:str):
    rows=[]; prev=None
    for rec in records:
        zb=get(rec['archive_url'])
        if sha256_bytes(zb)!=rec['local_sha256']:raise RuntimeError(f'SOURCE_VERSION_DRIFT_BLOCKED:{symbol}:{rec["month"]}')
        expected=rec['archive_name'].replace('.zip','.csv')
        for t,o,h,l,c,v in p3src.iter_zip_rows(zb,expected):
            if prev is not None and t<=prev:raise RuntimeError(f'nonmonotonic minute source:{symbol}:{t}')
            prev=t; rows.append((t,o,h,l,c,v))
        print(symbol,rec['month'],'PRICE_HASH_PASS',len(zb),flush=True)
    return rows

def funding_cashflow(times,rates,entry_t,exit_t):
    lo=bisect.bisect_right(times,entry_t); hi=bisect.bisect_left(times,exit_t)
    selected=rates[lo:hi]
    return -sum(selected),len(selected)

def simulate_minute(sig:core.Signal, minutes, mtimes, max_hold_ms:int, ftimes,frates)->ExecRow:
    i=bisect.bisect_left(mtimes,sig.entry_open_time)
    if i>=len(minutes) or minutes[i][0]!=sig.entry_open_time:
        return ExecRow(sig.cell_id,sig.symbol,sig.signal_open_time,sig.entry_open_time,None,sig.entry,None,sig.stop,sig.target,sig.initial_risk_fraction,'EXECUTION_PATH_UNRESOLVED_ENTRY',None,None,0,None,None,None,True)
    entry_open=minutes[i][1]
    if abs(entry_open-sig.entry)>max(1e-10,abs(sig.entry)*1e-10):
        raise RuntimeError(f'entry price mismatch:{sig.symbol}:{sig.entry_open_time}:{entry_open}:{sig.entry}')
    deadline=sig.entry_open_time+max_hold_ms
    j=i
    prev_t=None
    while j<len(minutes):
        t,o,hi,lo,c,v=minutes[j]
        if t>deadline:break
        if prev_t is not None and t!=prev_t+MIN_MS:
            return ExecRow(sig.cell_id,sig.symbol,sig.signal_open_time,sig.entry_open_time,None,sig.entry,None,sig.stop,sig.target,sig.initial_risk_fraction,'EXECUTION_PATH_UNRESOLVED_GAP',None,None,0,None,None,None,True)
        prev_t=t
        if t==deadline:
            px=o; reason='TIME_EXIT_EXACT_MINUTE_OPEN'; exit_t=t
            break
        if o<=sig.stop:
            px=o;reason='STOP_GAP_MINUTE_OPEN';exit_t=t;break
        if o>=sig.target:
            px=sig.target;reason='TARGET_GAP_CAPPED_AT_TARGET';exit_t=t;break
        sh=lo<=sig.stop; th=hi>=sig.target
        if sh and th:
            px=sig.stop;reason='STOP_WINS_SAME_MINUTE_AMBIGUITY';exit_t=t;break
        if sh:
            px=sig.stop;reason='STOP';exit_t=t;break
        if th:
            px=sig.target;reason='TARGET';exit_t=t;break
        j+=1
    else:
        return ExecRow(sig.cell_id,sig.symbol,sig.signal_open_time,sig.entry_open_time,None,sig.entry,None,sig.stop,sig.target,sig.initial_risk_fraction,'EXECUTION_PATH_UNRESOLVED_END',None,None,0,None,None,None,True)
    if 'exit_t' not in locals():
        return ExecRow(sig.cell_id,sig.symbol,sig.signal_open_time,sig.entry_open_time,None,sig.entry,None,sig.stop,sig.target,sig.initial_risk_fraction,'EXECUTION_PATH_UNRESOLVED_DEADLINE',None,None,0,None,None,None,True)
    price_gross=(px-sig.entry)/sig.entry
    funding,nfund=funding_cashflow(ftimes,frates,sig.entry_open_time,exit_t)
    econ=price_gross+funding
    base=(econ-BASE_COST)/(sig.initial_risk_fraction+BASE_COST)
    stress=(econ-STRESS_COST)/(sig.initial_risk_fraction+STRESS_COST)
    return ExecRow(sig.cell_id,sig.symbol,sig.signal_open_time,sig.entry_open_time,exit_t,sig.entry,px,sig.stop,sig.target,sig.initial_risk_fraction,reason,price_gross,funding,nfund,econ,base,stress,False)

def derive_signals(cell_id,symbol,bars,bar_ms,rule):
    all_sigs=[]; raw=cancel=gaps=segments=0
    segs,gaps=core.split_segments(bars,bar_ms);segments=len(segs)
    for seg in segs:
        sigs,r,c=core.derive_donchian(cell_id,symbol,seg,rule);all_sigs.extend(sigs);raw+=r;cancel+=c
    all_sigs.sort(key=lambda s:(s.entry_open_time,s.fingerprint))
    return all_sigs,raw,cancel,segments,gaps

def stats(rows:list[ExecRow],attr:str):
    vals=[float(getattr(r,attr)) for r in rows if getattr(r,attr) is not None]
    gains=sum(x for x in vals if x>0); losses=-sum(x for x in vals if x<0)
    return {'resolved_trade_count':len(vals),'selected_trade_count':len(rows),'unresolved_trade_count':len(rows)-len(vals),'net_expectancy_r':mean(vals) if vals else None,'median_net_r':median(vals) if vals else None,'win_rate':sum(x>0 for x in vals)/len(vals) if vals else None,'profit_factor_r':gains/losses if losses>0 else None}
def percentile(vals,p):
    pos=(len(vals)-1)*p;lo=int(pos);hi=min(lo+1,len(vals)-1);f=pos-lo
    return vals[lo]*(1-f)+vals[hi]*f
def bootstrap(rows):
    g=defaultdict(list)
    for r in rows:
        if r.base_net_r is None:continue
        day=datetime.fromtimestamp(r.entry_time/1000,tz=timezone.utc).date().isoformat();g[day].append(r.base_net_r)
    days=sorted(g); point=[v for d in days for v in g[d]]
    if not point:return {'sample_days':0,'lower':None,'point_estimate':None,'upper':None}
    rng=Random(SEED);draw=[]
    for _ in range(REPS):
        s=[]
        for _ in days:s.extend(g[days[rng.randrange(len(days))]])
        draw.append(mean(s))
    draw.sort();return {'method':'UTC_ENTRY_DAY_BLOCK_BOOTSTRAP','repetitions':REPS,'seed':SEED,'sample_days':len(days),'lower':percentile(draw,.025),'point_estimate':mean(point),'upper':percentile(draw,.975)}
def classify(base,stress,boot):
    if base['resolved_trade_count']<100:return 'INSUFFICIENT_SAMPLE',['resolved_trade_count_below_100']
    fails=[]
    if base['net_expectancy_r'] is None or base['net_expectancy_r']<=0:fails.append('base_net_expectancy_not_positive')
    if base['profit_factor_r'] is None or base['profit_factor_r']<=1:fails.append('base_profit_factor_not_above_1')
    if boot['lower'] is None or boot['lower']<=0:fails.append('bootstrap_lower_95_not_positive')
    if stress['net_expectancy_r'] is None or stress['net_expectancy_r']<=0:fails.append('stress_expectancy_not_positive')
    return ('FUNDING_EXECUTION_SURVIVES' if not fails else 'FUNDING_EXECUTION_FAIL'),fails

def main(argv):
    if len(argv)!=3:raise SystemExit('usage: phase4 PRICE_SOURCE_DIR FUNDING_SOURCE_DIR')
    price_dir=Path(argv[1]);fund_dir=Path(argv[2]);OUT.mkdir(parents=True,exist_ok=True)
    freeze=json.loads(FREEZE.read_text());pbind=json.loads(P3BIND.read_text());fbind=json.loads(FUND_BIND.read_text())
    assert freeze['status']=='FROZEN_BEFORE_PHASE4_SOURCE_ACCESS_OR_OUTCOMES'
    assert [x['cell_id'] for x in freeze['cells']]==['DH-02-FX1','DH-03-FX1']
    assert fbind['status']=='FROZEN_EXACT_PHASE4_FUNDING_SOURCE_BEFORE_ANY_EXECUTION_OUTCOME'
    prec=json.loads((price_dir/'HTF_DIAMOND_HUNT_001_PHASE3_SOURCE_GATE_V0.1.json').read_text())
    frec=json.loads((fund_dir/'HTF_DIAMOND_HUNT_001_PHASE4_FUNDING_SOURCE_GATE_V0.1.json').read_text())
    assert prec['status']=='SOURCE_DATA_PASS' and prec['source_fingerprint']==pbind['source_fingerprint']
    assert frec['status']=='SOURCE_DATA_PASS' and frec['source_fingerprint']==fbind['source_fingerprint']
    for s in SYMBOLS:
        assert sha256_file(price_dir/'canonical_15m'/f'{s}_15m.csv')==pbind['canonical_15m'][s]['sha256']
        assert sha256_file(fund_dir/'canonical_funding'/f'{s}_funding.csv')==fbind['canonical_funding'][s]['sha256']
    cellmap={x['cell_id']:x for x in freeze['cells']}; results={cid:[] for cid in cellmap}; diagnostics={cid:Counter() for cid in cellmap}
    price_records=prec['records']
    for symbol in SYMBOLS:
        recs=sorted([x for x in price_records if x['symbol']==symbol],key=lambda x:x['month'])
        minutes=load_price_minutes(recs,symbol); mtimes=[x[0] for x in minutes]
        ftimes,frates=load_funding(fund_dir/'canonical_funding'/f'{symbol}_funding.csv')
        bars15=core.load_15m(price_dir/'canonical_15m'/f'{symbol}_15m.csv')
        for cid,bar_ms in (('DH-02-FX1',21_600_000),('DH-03-FX1',43_200_000)):
            rule=cellmap[cid]['rule'];bars,_=core.aggregate(bars15,bar_ms); sigs,raw,cancel,segs,gaps=derive_signals(cid,symbol,bars,bar_ms,rule)
            diagnostics[cid]['raw']+=raw;diagnostics[cid]['cancelled']+=cancel;diagnostics[cid]['segments']+=segs;diagnostics[cid]['gaps']+=gaps
            active_until=None;max_hold_ms=int(rule['max_hold_bars'])*bar_ms
            for sig in sigs:
                if active_until is not None and sig.entry_open_time<=active_until:
                    diagnostics[cid]['overlap']+=1;continue
                row=simulate_minute(sig,minutes,mtimes,max_hold_ms,ftimes,frates);results[cid].append(row)
                if row.exit_time is not None:active_until=row.exit_time
                else:active_until=sig.entry_open_time+max_hold_ms
    receipt_results={}
    for cid,rows in results.items():
        rows.sort(key=lambda r:(r.entry_time,r.symbol));base=stats(rows,'base_net_r');stress=stats(rows,'stress_net_r');boot=bootstrap(rows);cls,fails=classify(base,stress,boot)
        funding_vals=[r.funding_return for r in rows if r.funding_return is not None]
        rr={'cell_id':cid,'lineage':cellmap[cid]['lineage'],'classification':cls,'failed_conditions':fails,'base':base,'stress':stress,'bootstrap':boot,'funding_diagnostics':{'mean_funding_return':mean(funding_vals) if funding_vals else None,'median_funding_return':median(funding_vals) if funding_vals else None,'total_funding_events':sum(r.funding_event_count for r in rows),'execution_path_unresolved_count':sum(r.execution_path_unresolved for r in rows)},'signal_diagnostics':dict(diagnostics[cid]),'symbol_distribution':dict(sorted(Counter(r.symbol for r in rows if r.base_net_r is not None).items()))}
        receipt_results[cid]=rr;print(cid,json.dumps(rr,sort_keys=True),flush=True)
        (OUT/f'{cid}_LEDGER.json').write_text(json.dumps([asdict(r) for r in rows],indent=2,sort_keys=True))
    receipt={'campaign_id':'HTF-DIAMOND-HUNT-001','phase':'PHASE_4_FUNDING_ADJUSTED_MINUTE_PATH_VALIDATION','status':'PHASE4_EXECUTION_BLOCK_COMPLETE','price_source_artifact_id':pbind['artifact_id'],'price_source_fingerprint':pbind['source_fingerprint'],'funding_source_artifact_id':fbind['artifact_id'],'funding_source_fingerprint':fbind['source_fingerprint'],'results':receipt_results,'both_timeframes_reported':True,'post_outcome_tuning':False,'access_2023_performed':False,'access_2024_performed':False,'access_2025_performed':False,'access_2026_performed':False,'live_trading':False,'exchange_mutation':False}
    receipt['fingerprint']=core.canonical_hash(receipt);(OUT/'HTF_DIAMOND_HUNT_001_PHASE4_EXECUTION_RECEIPT_V0.1.json').write_text(json.dumps(receipt,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main(sys.argv))
