from __future__ import annotations
import hashlib, json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

from research.htf_diamond_hunt import htf_diamond_hunt_scale_transfers_v01 as core
from research.htf_diamond_hunt import htf_diamond_hunt_phase4_execution_v01 as p4
from research.htf_diamond_hunt import htf_dh03_2025_source_gate_v01 as src

ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'research'/'htf_diamond_hunt'
FREEZE=R/'HTF_DH03_12H_2025_ONE_SHOT_OOS_FREEZE_V0.1.json'
BIND=R/'HTF_DH03_12H_2025_SOURCE_BINDING_V0.1.json'
OUT=ROOT/'research'/'local_data'/'htf_dh03_2025_oos_v01'
SYMBOLS=core.SYMBOLS
BAR_MS=43_200_000

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def load_price_minutes(records,symbol):
    rows=[];prev=None
    for rec in records:
        zb=p4.get(rec['archive_url'])
        if p4.sha256_bytes(zb)!=rec['local_sha256']:
            raise RuntimeError(f'SOURCE_VERSION_DRIFT_BLOCKED:{symbol}:{rec["month"]}')
        expected=rec['archive_name'].replace('.zip','.csv')
        for t,o,h,l,c,v in src.price_rows(zb,expected):
            if prev is not None and t<=prev:
                raise RuntimeError(f'nonmonotonic minute source:{symbol}:{t}')
            prev=t;rows.append((t,o,h,l,c,v))
        print(symbol,rec['month'],'PRICE_HASH_PASS',len(zb),flush=True)
    return rows

def half_stats(rows):
    groups={'H1':[],'H2':[]}
    for r in rows:
        if r.base_net_r is None: continue
        d=datetime.fromtimestamp(r.entry_time/1000,tz=timezone.utc)
        groups['H1' if d.month<=6 else 'H2'].append(r.base_net_r)
    return {k:{
        'resolved_trade_count':len(v),
        'base_expectancy_r':mean(v) if v else None,
        'total_base_net_r':sum(v) if v else None
    } for k,v in groups.items()}

def concentration(rows,keyfn):
    g=defaultdict(float);total=0.0
    for r in rows:
        if r.base_net_r is None or r.base_net_r<=0: continue
        v=float(r.base_net_r);g[str(keyfn(r))]+=v;total+=v
    shares={k:v/total for k,v in sorted(g.items())} if total>0 else {}
    return {
        'total_positive_base_net_r':total,
        'positive_base_net_r_by_group':dict(sorted(g.items())),
        'share_by_group':shares,
        'maximum_share':max(shares.values()) if shares else None
    }

def qkey(r):
    d=datetime.fromtimestamp(r.entry_time/1000,tz=timezone.utc)
    return f'{d.year}-Q{((d.month-1)//3)+1}'

def classify(base,stress,boot,halves,symc,qtrc,unresolved):
    fails=[]
    if base['resolved_trade_count']<60: fails.append('resolved_trade_count_below_60')
    if base['net_expectancy_r'] is None or base['net_expectancy_r']<=0: fails.append('base_net_expectancy_not_positive')
    if base['profit_factor_r'] is None or base['profit_factor_r']<=1: fails.append('base_profit_factor_not_above_1')
    if boot['lower'] is None or boot['lower']<=0: fails.append('bootstrap_lower_95_not_positive')
    if stress['net_expectancy_r'] is None or stress['net_expectancy_r']<=0: fails.append('stress_expectancy_not_positive')
    for h in ('H1','H2'):
        if halves[h]['base_expectancy_r'] is None or halves[h]['base_expectancy_r']<=0:
            fails.append(f'{h.lower()}_2025_expectancy_not_positive')
    if symc['maximum_share'] is None or symc['maximum_share']>0.70:
        fails.append('maximum_single_symbol_positive_net_r_share_above_70pct_or_undefined')
    if qtrc['maximum_share'] is None or qtrc['maximum_share']>0.70:
        fails.append('maximum_single_quarter_positive_net_r_share_above_70pct_or_undefined')
    if unresolved!=0: fails.append('unresolved_execution_paths_nonzero')
    if base['resolved_trade_count']<60:
        cls='INDEPENDENT_2025_OOS_INSUFFICIENT_SAMPLE'
    else:
        cls='INDEPENDENT_2025_OOS_SURVIVES__RESEARCH_GRADE_DH03_CANDIDATE' if not fails else 'INDEPENDENT_2025_OOS_FAIL'
    return cls,fails

def main(argv):
    if len(argv)!=2: raise SystemExit('usage: htf_dh03_2025_oos_v01.py SOURCE_DIR')
    srcdir=Path(argv[1]);OUT.mkdir(parents=True,exist_ok=True)
    freeze=json.loads(FREEZE.read_text())
    bind=json.loads(BIND.read_text())
    assert freeze['status']=='FROZEN_BEFORE_ANY_EXACT_DH03_2025_SOURCE_OR_OUTCOME_ACCESS'
    assert freeze['dataset']['allowed_source_years']==[2025]
    assert freeze['dataset']['forbidden_source_years']==[2026]
    assert freeze['rule']['timeframe']=='12H_UTC'
    assert freeze['rule']['donchian_lookback_complete_bars']==40
    assert freeze['rule']['atr_length']==28
    assert freeze['rule']['target_r']==3.0
    assert freeze['rule']['max_hold_bars']==80
    assert freeze['costs']=={'base_round_trip_pct':0.20,'stress_round_trip_pct':0.30}
    assert freeze['bootstrap']=={'repetitions':5000,'seed':230911,'unit':'UTC_ENTRY_DAY_BLOCK','confidence':0.95}
    assert bind['status']=='FROZEN_EXACT_2025_SOURCE_BEFORE_ANY_OOS_OUTCOME'
    assert bind['outcome_evaluation_performed'] is False
    assert bind['access_2026_performed'] is False

    sr=json.loads((srcdir/'HTF_DH03_12H_2025_SOURCE_GATE_V0.1.json').read_text())
    assert sr['status']=='SOURCE_DATA_PASS'
    assert sr['source_fingerprint']==bind['source_fingerprint']
    assert sr['signal_calculation_performed'] is False
    assert sr['return_calculation_performed'] is False
    assert sr['outcome_evaluation_performed'] is False
    assert sr['access_2026_performed'] is False

    for s in SYMBOLS:
        assert sha256_file(srcdir/'canonical_15m'/f'{s}_15m.csv')==bind['canonical_15m'][s]['sha256']
        assert sha256_file(srcdir/'canonical_funding'/f'{s}_funding.csv')==bind['canonical_funding'][s]['sha256']

    rule={
        'direction':'LONG_ONLY',
        'donchian_lookback_complete_bars':40,
        'atr_length':28,
        'entry':'next 12H open',
        'stop':'signal low minus 0.25*ATR28',
        'target_r':3.0,
        'max_hold_bars':80,
        'one_active_trade_per_symbol':True
    }
    rows=[];diag=Counter()
    for s in SYMBOLS:
        recs=sorted([x for x in sr['price_records'] if x['symbol']==s],key=lambda x:x['month'])
        assert len(recs)==12 and recs[0]['month']=='2025-01' and recs[-1]['month']=='2025-12'
        minutes=load_price_minutes(recs,s)
        mtimes=[x[0] for x in minutes]
        ftimes,frates=p4.load_funding(srcdir/'canonical_funding'/f'{s}_funding.csv')
        bars15=core.load_15m(srcdir/'canonical_15m'/f'{s}_15m.csv')
        bars,_=core.aggregate(bars15,BAR_MS)
        sigs,raw,cancel,segs,gaps=p4.derive_signals('DH-03-2025-OOS',s,bars,BAR_MS,rule)
        diag['raw']+=raw;diag['cancelled']+=cancel;diag['segments']+=segs;diag['gaps']+=gaps
        active=None;mh=80*BAR_MS
        for sig in sigs:
            if active is not None and sig.entry_open_time<=active:
                diag['overlap']+=1;continue
            row=p4.simulate_minute(sig,minutes,mtimes,mh,ftimes,frates)
            rows.append(row)
            active=row.exit_time if row.exit_time is not None else sig.entry_open_time+mh

    rows.sort(key=lambda r:(r.entry_time,r.symbol))
    base=p4.stats(rows,'base_net_r')
    stress=p4.stats(rows,'stress_net_r')
    boot=p4.bootstrap(rows)
    halves=half_stats(rows)
    symc=concentration(rows,lambda r:r.symbol)
    qtrc=concentration(rows,qkey)
    unresolved=sum(r.execution_path_unresolved for r in rows)
    cls,fails=classify(base,stress,boot,halves,symc,qtrc,unresolved)
    fv=[r.funding_return for r in rows if r.funding_return is not None]
    result={
        'experiment_id':'HTF-DH03-12H-2025-ONE-SHOT-OOS-V0.1',
        'classification':cls,
        'failed_conditions':fails,
        'base':base,
        'stress':stress,
        'bootstrap':boot,
        'calendar_halves':halves,
        'symbol_positive_net_r_concentration':symc,
        'quarter_positive_net_r_concentration':qtrc,
        'funding_diagnostics':{
            'mean_funding_return':mean(fv) if fv else None,
            'median_funding_return':median(fv) if fv else None,
            'total_funding_events':sum(r.funding_event_count for r in rows),
            'execution_path_unresolved_count':unresolved
        },
        'signal_diagnostics':dict(diag),
        'symbol_distribution':dict(sorted(Counter(r.symbol for r in rows if r.base_net_r is not None).items())),
        'source_run_id':bind['source_run_id'],
        'source_artifact_id':bind['artifact_id'],
        'source_artifact_digest':bind['artifact_digest'],
        'source_fingerprint':bind['source_fingerprint'],
        'access_2026_performed':False,
        'live_trading':False,
        'orders':False,
        'exchange_mutation':False,
        'post_outcome_tuning':False
    }
    (OUT/'HTF_DH03_12H_2025_OOS_LEDGER_V0.1.json').write_text(json.dumps([p4.asdict(r) for r in rows],indent=2,sort_keys=True))
    (OUT/'HTF_DH03_12H_2025_OOS_RESULT_V0.1.json').write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__':
    import sys
    raise SystemExit(main(sys.argv))
