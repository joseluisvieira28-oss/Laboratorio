from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

TRADE_CORE_FP='ab290487c693ad98cb20d1b87e2db2fcf11c97a54da303d7ff301e9d99dca9f8'
RISKS=[0.10,0.15,0.20,0.25,0.30]
PLANS={
 'STARTER':{'target_pct':10.0,'mdd_pct':6.0,'mdl_pct':3.0},
 'INTERMEDIATE':{'target_pct':12.0,'mdd_pct':5.0,'mdl_pct':3.0},
 'ADVANCED':{'target_pct':9.0,'mdd_pct':3.0,'mdl_pct':3.0},
}
EXEC=[0.20,0.30,0.50,0.75]
CARRY=[1.0,1.5,2.0]
GAP=[0.0,0.25,0.50,1.0]
PROFILES={
 'BASE':{'execution_round_trip_pct':0.20,'carry_multiplier':1.0,'stop_gap_extra_R':0.0},
 'STRESS':{'execution_round_trip_pct':0.30,'carry_multiplier':1.0,'stop_gap_extra_R':0.0},
 'SEVERE':{'execution_round_trip_pct':0.50,'carry_multiplier':1.5,'stop_gap_extra_R':0.50},
 'EXTREME':{'execution_round_trip_pct':0.75,'carry_multiplier':2.0,'stop_gap_extra_R':1.0},
}
REPS=20000
SEED=20260917


def canonical_hash(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def load_ledger(p:Path):
    d=json.loads(p.read_text())
    rows=sorted(d['records'],key=lambda r:(int(r['signal']['entry_open_time']),str(r['symbol'])))
    if len(rows)!=40: raise RuntimeError(f'LEDGER_COUNT:{len(rows)}')
    if canonical_hash(rows)!=TRADE_CORE_FP: raise RuntimeError('TRADE_CORE_FINGERPRINT_MISMATCH')
    if d.get('2026_accessed') is not False: raise RuntimeError('LEDGER_2026_FLAG')
    return rows


def is_stop(r): return 'STOP' in str(r['outcome']['exit_reason']).upper()


def trade_r(r,execution_pct,carry_mult,gap_r):
    s,o=r['signal'],r['outcome']
    hold_days=(int(o['exit_open_time'])-int(s['entry_open_time']))/86400000.0
    rf=float(s['initial_risk_fraction']); ex=execution_pct/100.0
    denom=rf+ex
    gross=float(o['gross_return_pct'])/100.0
    val=(gross-ex-0.00033*carry_mult*hold_days)/denom
    if is_stop(r): val-=gap_r
    return val


def metrics(vals):
    a=np.asarray(vals,float); gains=float(a[a>0].sum()); losses=float(-a[a<0].sum())
    return {'trade_count':int(a.size),'expectancy_R':float(a.mean()),'median_R':float(np.median(a)),'total_R':float(a.sum()),'win_rate':float((a>0).mean()),'profit_factor_R':None if losses<=0 else gains/losses,'positive_expectancy':bool(a.mean()>0)}


def historical_decision(rows,vals,risk_pct,plan):
    order=sorted(range(len(rows)),key=lambda i:(int(rows[i]['outcome']['exit_open_time']),str(rows[i]['symbol'])))
    eq=100.0; peak=100.0; maxdd=0.0
    target=100.0+PLANS[plan]['target_pct']; floor=100.0-PLANS[plan]['mdd_pct']
    decision='NO_DECISION_HISTORY'; decision_time=None; trades=0
    for i in order:
        eq*=1.0+(risk_pct/100.0)*vals[i]; trades+=1; peak=max(peak,eq); maxdd=max(maxdd,peak-eq)
        if eq<=floor: decision='STATIC_MDD_BREACH_BEFORE_TARGET'; decision_time=int(rows[i]['outcome']['exit_open_time']); break
        if eq>=target: decision='TARGET_BEFORE_STATIC_MDD'; decision_time=int(rows[i]['outcome']['exit_open_time']); break
    return {'plan':plan,'risk_pct_per_1R':risk_pct,'classification':decision,'decision_time_utc':None if decision_time is None else datetime.fromtimestamp(decision_time/1000,tz=timezone.utc).isoformat().replace('+00:00','Z'),'trades_to_decision':trades,'ending_equity':eq,'max_peak_to_trough_drawdown_units':maxdd}


def stage_a(rows):
    factors=[]; counts=defaultdict(int)
    for ex in EXEC:
      for cm in CARRY:
       for gap in GAP:
        vals=[trade_r(r,ex,cm,gap) for r in rows]; m=metrics(vals); decisions=[]
        for plan in PLANS:
          for risk in RISKS:
            d=historical_decision(rows,vals,risk,plan); decisions.append(d); counts[d['classification']]+=1
        factors.append({'execution_round_trip_pct':ex,'carry_multiplier':cm,'stop_gap_extra_R':gap,'trade_metrics':m,'decisions':decisions})
    return {'factor_combinations':len(factors),'decision_count':sum(len(x['decisions']) for x in factors),'classification_counts':dict(counts),'factors':factors}


def stage_b():
    rows=[]
    for risk in RISKS:
      for n in [2,3,4,6]:
       for lm in [1.0,1.5,2.0]:
        loss=n*risk*lm
        rows.append({'risk_pct_per_1R':risk,'simultaneous_positions':n,'loss_multiplier_R_per_position':lm,'nominal_loss_pct_initial':loss,'breaches_MDL_3pct':loss>=3.0,'breaches_ADVANCED_MDD_3pct':loss>=3.0,'breaches_INTERMEDIATE_MDD_5pct':loss>=5.0,'breaches_STARTER_MDD_6pct':loss>=6.0})
    return {'scenario_count':len(rows),'scenarios':rows}


def build_blocks(rows,vals):
    d=defaultdict(float)
    for r,v in zip(rows,vals):
      day=datetime.fromtimestamp(int(r['signal']['entry_open_time'])/1000,tz=timezone.utc).date().isoformat(); d[day]+=v
    days=sorted(d); return days,np.array([d[x] for x in days],dtype=float)


def pct(a,q): return float(np.percentile(a,q))


def mc_cell(blocks,sample_idx,risk_pct,plan):
    rr=(risk_pct/100.0)*blocks[sample_idx]; eq=100.0*np.cumprod(1.0+rr,axis=1)
    target=100.0+PLANS[plan]['target_pct']; floor=100.0-PLANS[plan]['mdd_pct']
    hit_t=eq>=target; hit_b=eq<=floor; any_t=hit_t.any(axis=1); any_b=hit_b.any(axis=1); n=eq.shape[1]
    first_t=np.where(any_t,np.argmax(hit_t,axis=1),n+1); first_b=np.where(any_b,np.argmax(hit_b,axis=1),n+1); tb=any_t&(first_t<first_b)
    peak=np.maximum.accumulate(np.concatenate([np.full((eq.shape[0],1),100.0),eq],axis=1),axis=1)[:,1:]
    dd_units=(peak-eq).max(axis=1); dd_peak=((peak-eq)/peak*100.0).max(axis=1); terminal=eq[:,-1]
    return {'plan':plan,'risk_pct_per_1R':risk_pct,'repetitions':int(eq.shape[0]),'target_reach_probability':float(any_t.mean()),'static_MDD_breach_probability':float(any_b.mean()),'target_before_static_MDD_probability':float(tb.mean()),'terminal_equity_percentiles':{'p05':pct(terminal,5),'p50':pct(terminal,50),'p95':pct(terminal,95)},'max_drawdown_units_percentiles':{'p50':pct(dd_units,50),'p90':pct(dd_units,90),'p95':pct(dd_units,95),'p99':pct(dd_units,99)},'max_drawdown_pct_peak_percentiles':{'p50':pct(dd_peak,50),'p90':pct(dd_peak,90),'p95':pct(dd_peak,95),'p99':pct(dd_peak,99)}}


def stage_c(rows):
    profile_blocks={}; days_ref=None
    for name,p in PROFILES.items():
      vals=[trade_r(r,p['execution_round_trip_pct'],p['carry_multiplier'],p['stop_gap_extra_R']) for r in rows]
      days,blocks=build_blocks(rows,vals)
      if days_ref is None: days_ref=days
      if days!=days_ref: raise RuntimeError('BLOCK_DAY_MISMATCH')
      profile_blocks[name]=blocks
    rng=np.random.default_rng(SEED); n=len(days_ref); sample_idx=rng.integers(0,n,size=(REPS,n),dtype=np.int32); results=[]
    for name,blocks in profile_blocks.items():
      for plan in PLANS:
       for risk in RISKS:
        x=mc_cell(blocks,sample_idx,risk,plan); x['profile']=name; results.append(x)
    return {'method':'UTC_ENTRY_DAY_BLOCK_BOOTSTRAP','seed':SEED,'repetitions':REPS,'distinct_entry_day_blocks':len(days_ref),'cell_count':len(results),'profiles':PROFILES,'cells':results}


def summarize(a,b,c):
    ps={}
    for name in PROFILES:
      cells=[x for x in c['cells'] if x['profile']==name]
      ps[name]={'target_before_MDD_probability_range':[min(x['target_before_static_MDD_probability'] for x in cells),max(x['target_before_static_MDD_probability'] for x in cells)],'MDD_breach_probability_range':[min(x['static_MDD_breach_probability'] for x in cells),max(x['static_MDD_breach_probability'] for x in cells)],'target_reach_probability_range':[min(x['target_reach_probability'] for x in cells),max(x['target_reach_probability'] for x in cells)]}
    profile_metrics={}
    for name,p in PROFILES.items():
      profile_metrics[name]=metrics([trade_r(r,p['execution_round_trip_pct'],p['carry_multiplier'],p['stop_gap_extra_R']) for r in ROWS])
    return {'stage_A_positive_expectancy_factor_combinations':sum(1 for f in a['factors'] if f['trade_metrics']['positive_expectancy']),'stage_A_total_factor_combinations':a['factor_combinations'],'stage_A_decision_classification_counts':a['classification_counts'],'profile_trade_metrics':profile_metrics,'stage_B_any_nominal_MDL_breach_scenarios':sum(x['breaches_MDL_3pct'] for x in b['scenarios']),'stage_B_total_scenarios':b['scenario_count'],'stage_C_profile_probability_ranges':ps}


def main():
    global ROWS
    ap=argparse.ArgumentParser(); ap.add_argument('ledger'); ap.add_argument('output'); args=ap.parse_args(); ROWS=load_ledger(Path(args.ledger))
    a=stage_a(ROWS); b=stage_b(); c=stage_c(ROWS); summary=summarize(a,b,c)
    severe_positive=summary['profile_trade_metrics']['SEVERE']['expectancy_R']>0
    status='BASE_STRESS_POSITIVE_SEVERE_SURVIVES' if severe_positive else 'BASE_STRESS_POSITIVE_SEVERE_GATE_FAIL_SMALL_SAMPLE'
    out={'document_id':'PROP_COMPAT_001G_TFG_KRAKEN_SEQUENCE_GAUNTLET_RECEIPT_V0.1','campaign_id':'PROP-COMPAT-001G','status':status,'setup_id':'TFG-DONCHIAN-1D-001','program_context':'KRAKEN_PROP','decisional_authority':False,'source':{'trade_core_fingerprint':TRADE_CORE_FP,'resolved_trade_count':len(ROWS),'year':2025,'historical_byte_identity_recovered':False,'access_2026':False},'stage_A':a,'stage_B':b,'stage_C':c,'summary':summary,'limitations':['Only 40 resolved trades / 30 UTC entry-day blocks are available; Monte Carlo uncertainty and temporal concentration are material.','Stages A and C are trade-ledger/sequence diagnostics and do not reconstruct proprietary Kraken intraday mark/bid/ask/depth or exact MDL.','This receipt cannot produce PROP_COMPAT_PASS, challenge purchase authorization or live-trading authorization.'],'governance':{'aggressive_research':True,'no_best_plan_selection':True,'no_best_risk_selection':True,'post_outcome_tuning':False,'setup_rules_changed':False,'challenge_purchase':False,'live_trading':False,'orders':False,'wallet_use':False,'exchange_mutation':False,'merge_to_main':False}}
    out['fingerprint']=canonical_hash(out); Path(args.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'summary':summary,'fingerprint':out['fingerprint']},indent=2,sort_keys=True))

if __name__=='__main__': main()
