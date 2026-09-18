from __future__ import annotations
import hashlib, json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

from research.htf_diamond_hunt import htf_diamond_hunt_scale_transfers_v01 as core
from research.htf_diamond_hunt import htf_diamond_hunt_phase4_execution_v01 as p4
from research.htf_diamond_hunt import htf_donchian_shadow_2026_source_gate_v01 as srcmod

ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'research'/'htf_diamond_hunt'
FREEZE=R/'HTF_DONCHIAN_SHADOW_001_2026_BLOCK_FREEZE_V0.1.json'
AUTH=R/'HTF_DONCHIAN_SHADOW_001_2026_DATA_ACCESS_AUTHORIZATION_V0.1.json'
BIND=R/'HTF_DONCHIAN_SHADOW_001_2026_SOURCE_BINDING_V0.1.json'
CLAR=R/'HTF_DONCHIAN_SHADOW_001_2026_IMPLEMENTATION_CLARIFICATION_01.json'
OUT=ROOT/'research'/'local_data'/'htf_donchian_shadow_2026_execution_v01'
SYMBOLS=core.SYMBOLS
END_MS=1788220800000
BAR_MS=21_600_000
MAX_HOLD_BARS=160
MAX_HOLD_MS=BAR_MS*MAX_HOLD_BARS

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def load_price_minutes(records,symbol):
    rows=[]; prev=None
    for rec in records:
        zb=p4.get(rec['archive_url'])
        if p4.sha256_bytes(zb)!=rec['local_sha256']:
            raise RuntimeError(f'SOURCE_VERSION_DRIFT_BLOCKED:{symbol}:{rec["month"]}')
        expected=rec['archive_name'].replace('.zip','.csv')
        for t,o,h,l,c,v in srcmod.price_rows(zb,expected):
            if prev is not None and t<=prev: raise RuntimeError(f'nonmonotonic minute source:{symbol}:{t}')
            prev=t; rows.append((t,o,h,l,c,v))
        print(symbol,rec['month'],'PRICE_HASH_PASS',len(zb),flush=True)
    return rows

def concentration(rows,keyfn):
    g=defaultdict(float); total=0.0
    for r in rows:
        if r.base_net_r is None or r.base_net_r<=0: continue
        v=float(r.base_net_r); g[str(keyfn(r))]+=v; total+=v
    shares={k:v/total for k,v in sorted(g.items())} if total>0 else {}
    return {'total_positive_base_net_r':total,'positive_base_net_r_by_group':dict(sorted(g.items())),'share_by_group':shares,'maximum_share':max(shares.values()) if shares else None}

def qkey(r):
    d=datetime.fromtimestamp(r.entry_time/1000,tz=timezone.utc)
    return f'{d.year}-Q{((d.month-1)//3)+1}'

def main(argv):
    if len(argv)!=2: raise SystemExit('usage: execution SOURCE_DIR')
    srcdir=Path(argv[1]); OUT.mkdir(parents=True,exist_ok=True)
    auth=json.loads(AUTH.read_text()); freeze=json.loads(FREEZE.read_text()); bind=json.loads(BIND.read_text()); clar=json.loads(CLAR.read_text())
    assert auth['status']=='EXPLICIT_2026_SHADOW_DATA_ACCESS_AUTHORIZED'
    assert freeze['status']=='FROZEN_BEFORE_2026_MARKET_ACCESS'
    assert bind['status']=='FROZEN_EXACT_2026_SOURCE_BEFORE_SIGNAL_OR_OUTCOME_CALCULATION'
    assert clar['status']=='FROZEN_BEFORE_SIGNAL_OR_OUTCOME_CALCULATION'
    assert clar['anti_rescue']['outcomes_inspected_before_clarification'] is False
    c=freeze['candidate']
    assert c['cell_id']=='DH-02-HO1' and c['timeframe']=='6H' and c['direction']=='LONG_ONLY'
    assert c['donchian_lookback_complete_bars']==80 and c['atr_length']==56
    assert c['entry']=='next 6H open' and c['stop']=='signal low minus 0.25*ATR56'
    assert c['target_r']==3.0 and c['max_hold_bars']==160 and c['one_active_trade_per_symbol'] is True
    assert c['base_round_trip_cost_pct']==0.20 and c['stress_round_trip_cost_pct']==0.30
    assert freeze['governance']['secondary_12h_not_evaluated'] is True
    sr=json.loads((srcdir/'HTF_DONCHIAN_SHADOW_001_2026_SOURCE_GATE_V0.1.json').read_text())
    assert sr['status']=='SOURCE_DATA_PASS' and sr['source_fingerprint']==bind['source_fingerprint']
    assert sr['signal_calculation_performed'] is False and sr['return_calculation_performed'] is False
    assert sr['access_2025_performed'] is False and sr['access_partial_september_2026_performed'] is False
    for s in SYMBOLS:
        b=bind['canonical'][s]
        assert sha256_file(srcdir/'canonical_15m'/f'{s}_15m.csv')==b['price_sha256']
        assert sha256_file(srcdir/'canonical_funding'/f'{s}_funding.csv')==b['funding_sha256']
    rows_all=[]; signal_ledger=[]; diag=Counter(); right_censored=[]
    for s in SYMBOLS:
        recs=sorted([x for x in sr['price_records'] if x['symbol']==s],key=lambda x:x['month'])
        assert len(recs)==8 and recs[0]['month']=='2026-01' and recs[-1]['month']=='2026-08'
        minutes=load_price_minutes(recs,s); mtimes=[x[0] for x in minutes]
        ftimes,frates=p4.load_funding(srcdir/'canonical_funding'/f'{s}_funding.csv')
        bars15=core.load_15m(srcdir/'canonical_15m'/f'{s}_15m.csv')
        bars,_=core.aggregate(bars15,BAR_MS)
        rule={'direction':'LONG_ONLY','donchian_lookback_complete_bars':80,'atr_length':56,'entry':'next 6H open','stop':'signal low minus 0.25*ATR56','target_r':3.0,'max_hold_bars':160,'one_active_trade_per_symbol':True}
        sigs,raw,cancel,segs,gaps=p4.derive_signals('DH-02-HO1',s,bars,BAR_MS,rule)
        diag['raw']+=raw; diag['cancelled']+=cancel; diag['segments']+=segs; diag['signal_source_gaps']+=gaps
        active=None
        for sig in sigs:
            sd=p4.asdict(sig); sd['right_censored']=False; sd['overlap_skipped']=False
            if active is not None and sig.entry_open_time<=active:
                diag['overlap_skipped']+=1; sd['overlap_skipped']=True; signal_ledger.append(sd); continue
            if sig.entry_open_time+MAX_HOLD_MS>=END_MS:
                diag['right_censored']+=1; sd['right_censored']=True; right_censored.append(sd); signal_ledger.append(sd); continue
            row=p4.simulate_minute(sig,minutes,mtimes,MAX_HOLD_MS,ftimes,frates)
            rows_all.append(row); signal_ledger.append(sd)
            active=row.exit_time if row.exit_time is not None else sig.entry_open_time+MAX_HOLD_MS
    rows_all.sort(key=lambda r:(r.entry_time,r.symbol))
    base=p4.stats(rows_all,'base_net_r'); stress=p4.stats(rows_all,'stress_net_r')
    symc=concentration(rows_all,lambda r:r.symbol); qtrc=concentration(rows_all,qkey)
    funding=[r.funding_return for r in rows_all if r.funding_return is not None]
    source_gap_count=sum(v['detected_minute_gap_count']+v['incomplete_15m_count'] for v in sr['audits'].values())
    eligible_entries=[(r.symbol,r.entry_time) for r in rows_all]
    duplicate_entries=len(eligible_entries)-len(set(eligible_entries))
    unresolved=sum(r.execution_path_unresolved for r in rows_all)
    elapsed_days=(END_MS-srcmod.START)//86_400_000
    failures=[]
    if elapsed_days<60: failures.append('minimum_elapsed_calendar_days_below_60')
    if base['resolved_trade_count']<30: failures.append('minimum_resolved_shadow_trades_below_30')
    if duplicate_entries!=0: failures.append('duplicate_hypothetical_entries_nonzero')
    if unresolved!=0: failures.append('unresolved_execution_paths_nonzero')
    if source_gap_count!=0 or diag['signal_source_gaps']!=0: failures.append('unreconciled_source_gaps_nonzero')
    if base['net_expectancy_r'] is None or base['net_expectancy_r']<=0: failures.append('base_expectancy_not_positive')
    if base['profit_factor_r'] is None or base['profit_factor_r']<=1: failures.append('base_profit_factor_not_above_1')
    if stress['net_expectancy_r'] is None or stress['net_expectancy_r']<=0: failures.append('stress_expectancy_not_positive')
    if symc['maximum_share'] is None or symc['maximum_share']>0.70: failures.append('single_symbol_positive_net_r_share_above_70pct_or_undefined')
    if qtrc['maximum_share'] is None or qtrc['maximum_share']>0.70: failures.append('single_quarter_positive_net_r_share_above_70pct_or_undefined')
    classification='SHADOW_READINESS_PASS_ELIGIBLE_FOR_SEPARATE_RISK_REVIEW' if not failures else 'SHADOW_READINESS_FAIL'
    ledger=[p4.asdict(r) for r in rows_all]
    (OUT/'SIGNAL_LEDGER.json').write_text(json.dumps(signal_ledger,indent=2,sort_keys=True))
    (OUT/'HYPOTHETICAL_TRADE_LEDGER.json').write_text(json.dumps(ledger,indent=2,sort_keys=True))
    (OUT/'RIGHT_CENSORED_SIGNAL_LEDGER.json').write_text(json.dumps(right_censored,indent=2,sort_keys=True))
    result={
      'experiment_id':'HTF-DONCHIAN-SHADOW-001','phase':'PHASE_6_2026_PROTECTED_SHADOW_BLOCK','status':'EXECUTION_COMPLETE',
      'classification':classification,'failed_conditions':failures,'candidate':'DH-02-HO1','timeframe':'6H','months':sr['months'],
      'elapsed_calendar_days':elapsed_days,'base':base,'stress':stress,
      'symbol_positive_net_r_concentration':symc,'quarter_positive_net_r_concentration':qtrc,
      'symbol_distribution':dict(sorted(Counter(r.symbol for r in rows_all if r.base_net_r is not None).items())),
      'funding_diagnostics':{'mean_funding_return':mean(funding) if funding else None,'median_funding_return':median(funding) if funding else None,'total_funding_events':sum(r.funding_event_count for r in rows_all)},
      'operational_diagnostics':{'signal_rule_deviations':0,'duplicate_hypothetical_entries':duplicate_entries,'unresolved_execution_paths':unresolved,'unreconciled_source_gaps':source_gap_count+diag['signal_source_gaps'],'raw_signals':diag['raw'],'overlap_skipped':diag['overlap_skipped'],'right_censored_signals':diag['right_censored'],'segments':diag['segments']},
      'source_run_id':bind['source_run_id'],'source_artifact_id':bind['source_artifact_id'],'source_artifact_digest':bind['source_artifact_digest'],'source_fingerprint':bind['source_fingerprint'],
      'access_2025_performed':False,'access_2026_performed':True,'access_partial_september_2026_performed':False,
      'secondary_12h_evaluated':False,'live_trading':False,'exchange_mutation':False,'orders_created':False,'api_keys_used':False,'post_outcome_tuning':False,'main_merge':False
    }
    result['fingerprint']=core.canonical_hash(result)
    (OUT/'HTF_DONCHIAN_SHADOW_001_2026_EXECUTION_RECEIPT_V0.1.json').write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps(result,indent=2,sort_keys=True)); return 0

if __name__=='__main__':
    import sys
    raise SystemExit(main(sys.argv))
