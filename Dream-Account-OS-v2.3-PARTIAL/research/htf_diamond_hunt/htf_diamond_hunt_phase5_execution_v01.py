from __future__ import annotations
import json, hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

from research.htf_diamond_hunt import htf_diamond_hunt_scale_transfers_v01 as core
from research.htf_diamond_hunt import htf_diamond_hunt_phase4_execution_v01 as p4
from research.htf_diamond_hunt import htf_diamond_hunt_phase5_source_gate_v01 as p5src

ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'research'/'htf_diamond_hunt'
FREEZE=R/'HTF_DIAMOND_HUNT_001_PHASE5_FORWARD_HOLDOUT_FREEZE_V0.1.json'
BIND=R/'HTF_DIAMOND_HUNT_001_PHASE5_SOURCE_BINDING_V0.1.json'
CLAR=R/'HTF_DIAMOND_HUNT_001_PHASE5_IMPLEMENTATION_CLARIFICATION_01.json'
OUT=ROOT/'research'/'local_data'/'htf_diamond_hunt_phase5_execution_v01'
SYMBOLS=core.SYMBOLS


def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def load_price_minutes(records,symbol):
    rows=[];prev=None
    for rec in records:
        zb=p4.get(rec['archive_url'])
        if p4.sha256_bytes(zb)!=rec['local_sha256']:
            raise RuntimeError(f'SOURCE_VERSION_DRIFT_BLOCKED:{symbol}:{rec["month"]}')
        expected=rec['archive_name'].replace('.zip','.csv')
        for t,o,h,l,c,v in p5src.price_rows(zb,expected):
            if prev is not None and t<=prev:raise RuntimeError(f'nonmonotonic minute source:{symbol}:{t}')
            prev=t;rows.append((t,o,h,l,c,v))
        print(symbol,rec['month'],'PRICE_HASH_PASS',len(zb),flush=True)
    return rows


def year_stats(rows):
    out={}
    for y in (2023,2024):
        vals=[r.base_net_r for r in rows if r.base_net_r is not None and datetime.fromtimestamp(r.entry_time/1000,tz=timezone.utc).year==y]
        out[str(y)]={'resolved_trade_count':len(vals),'base_expectancy_r':mean(vals) if vals else None,'total_base_net_r':sum(vals) if vals else None}
    return out


def concentration(rows,keyfn):
    g=defaultdict(float);total=0.0
    for r in rows:
        if r.base_net_r is None or r.base_net_r<=0:continue
        v=float(r.base_net_r);g[str(keyfn(r))]+=v;total+=v
    shares={k:v/total for k,v in sorted(g.items())} if total>0 else {}
    return {'total_positive_base_net_r':total,'positive_base_net_r_by_group':dict(sorted(g.items())),'share_by_group':shares,'maximum_share':max(shares.values()) if shares else None}


def qkey(r):
    d=datetime.fromtimestamp(r.entry_time/1000,tz=timezone.utc)
    return f'{d.year}-Q{((d.month-1)//3)+1}'


def classify(base,stress,boot,years,symc,qtrc):
    fails=[]
    if base['resolved_trade_count']<100:fails.append('resolved_trade_count_below_100')
    if base['net_expectancy_r'] is None or base['net_expectancy_r']<=0:fails.append('base_net_expectancy_not_positive')
    if base['profit_factor_r'] is None or base['profit_factor_r']<=1:fails.append('base_profit_factor_not_above_1')
    if boot['lower'] is None or boot['lower']<=0:fails.append('bootstrap_lower_95_not_positive')
    if stress['net_expectancy_r'] is None or stress['net_expectancy_r']<=0:fails.append('stress_expectancy_not_positive')
    for y in ('2023','2024'):
        if years[y]['base_expectancy_r'] is None or years[y]['base_expectancy_r']<=0:fails.append(f'calendar_year_{y}_expectancy_not_positive')
    if symc['maximum_share'] is None or symc['maximum_share']>0.70:fails.append('maximum_single_symbol_positive_net_r_share_above_70pct_or_undefined')
    if qtrc['maximum_share'] is None or qtrc['maximum_share']>0.70:fails.append('maximum_single_quarter_positive_net_r_share_above_70pct_or_undefined')
    cls='INSUFFICIENT_SAMPLE' if base['resolved_trade_count']<100 else ('EXACT_RULE_FORWARD_HOLDOUT_SURVIVES' if not fails else 'EXACT_RULE_FORWARD_HOLDOUT_FAIL')
    return cls,fails


def main(argv):
    if len(argv)!=2:raise SystemExit('usage: phase5 SOURCE_DIR')
    srcdir=Path(argv[1]);OUT.mkdir(parents=True,exist_ok=True)
    freeze=json.loads(FREEZE.read_text());bind=json.loads(BIND.read_text());clar=json.loads(CLAR.read_text())
    assert freeze['status']=='FROZEN_BEFORE_PHASE5_SOURCE_ACCESS_OR_OUTCOMES'
    assert [x['cell_id'] for x in freeze['cells']]==['DH-02-HO1','DH-03-HO1']
    assert freeze['dataset']['allowed_source_years']==[2023,2024] and freeze['dataset']['forbidden_source_years']==[2025,2026]
    assert freeze['execution_and_funding']=='IDENTICAL_TO_PHASE4'
    assert freeze['costs']=={'base_round_trip_pct':0.20,'stress_round_trip_pct':0.30}
    assert freeze['bootstrap']=={'repetitions':5000,'seed':230911,'unit':'UTC_ENTRY_DAY_BLOCK','confidence':0.95}
    assert bind['status']=='FROZEN_EXACT_PHASE5_SOURCE_BEFORE_ANY_HOLDOUT_OUTCOME'
    assert bind['artifact_id']==10438795414 and bind['artifact_digest']=='sha256:d84cc2f9117519568fa1a8d276217550da82ddffffc2df37c195a95787dda752'
    assert bind['source_fingerprint']=='d1a95d51d99eba0bd5f66e91d75ddcd175f7a84d954ba28a44c2dcd39ef4c5cb'
    assert bind['outcome_evaluation_performed'] is False and bind['access_2025_performed'] is False and bind['access_2026_performed'] is False
    assert clar['status']=='FROZEN_BEFORE_PHASE5_OUTCOMES' and clar['governance']['outcomes_inspected_before_this_clarification'] is False
    sr=json.loads((srcdir/'HTF_DIAMOND_HUNT_001_PHASE5_SOURCE_GATE_V0.1.json').read_text())
    assert sr['status']=='SOURCE_DATA_PASS' and sr['source_fingerprint']==bind['source_fingerprint']
    assert sr['signal_calculation_performed'] is False and sr['return_calculation_performed'] is False
    assert sr['access_2025_performed'] is False and sr['access_2026_performed'] is False
    for s in SYMBOLS:
        assert sha256_file(srcdir/'canonical_15m'/f'{s}_15m.csv')==bind['canonical_15m'][s]['sha256']
        assert sha256_file(srcdir/'canonical_funding'/f'{s}_funding.csv')==bind['canonical_funding'][s]['sha256']
    cellmap={x['cell_id']:x for x in freeze['cells']};results={cid:[] for cid in cellmap};diag={cid:Counter() for cid in cellmap}
    for s in SYMBOLS:
        recs=sorted([x for x in sr['price_records'] if x['symbol']==s],key=lambda x:x['month'])
        assert len(recs)==24 and recs[0]['month']=='2023-01' and recs[-1]['month']=='2024-12'
        minutes=load_price_minutes(recs,s);mtimes=[x[0] for x in minutes]
        ftimes,frates=p4.load_funding(srcdir/'canonical_funding'/f'{s}_funding.csv');bars15=core.load_15m(srcdir/'canonical_15m'/f'{s}_15m.csv')
        for cid,bar_ms in (('DH-02-HO1',21_600_000),('DH-03-HO1',43_200_000)):
            rule=cellmap[cid]['rule'];bars,_=core.aggregate(bars15,bar_ms);sigs,raw,cancel,segs,gaps=p4.derive_signals(cid,s,bars,bar_ms,rule)
            diag[cid]['raw']+=raw;diag[cid]['cancelled']+=cancel;diag[cid]['segments']+=segs;diag[cid]['gaps']+=gaps;active=None;mh=int(rule['max_hold_bars'])*bar_ms
            for sig in sigs:
                if active is not None and sig.entry_open_time<=active:diag[cid]['overlap']+=1;continue
                row=p4.simulate_minute(sig,minutes,mtimes,mh,ftimes,frates);results[cid].append(row);active=row.exit_time if row.exit_time is not None else sig.entry_open_time+mh
    rr={}
    for cid,rows in results.items():
        rows.sort(key=lambda r:(r.entry_time,r.symbol));base=p4.stats(rows,'base_net_r');stress=p4.stats(rows,'stress_net_r');boot=p4.bootstrap(rows);years=year_stats(rows);symc=concentration(rows,lambda r:r.symbol);qtrc=concentration(rows,qkey);cls,fails=classify(base,stress,boot,years,symc,qtrc);fv=[r.funding_return for r in rows if r.funding_return is not None]
        item={'cell_id':cid,'lineage':cellmap[cid]['lineage'],'classification':cls,'failed_conditions':fails,'base':base,'stress':stress,'bootstrap':boot,'calendar_years':years,'symbol_positive_net_r_concentration':symc,'quarter_positive_net_r_concentration':qtrc,'funding_diagnostics':{'mean_funding_return':mean(fv) if fv else None,'median_funding_return':median(fv) if fv else None,'total_funding_events':sum(r.funding_event_count for r in rows),'execution_path_unresolved_count':sum(r.execution_path_unresolved for r in rows)},'signal_diagnostics':dict(diag[cid]),'symbol_distribution':dict(sorted(Counter(r.symbol for r in rows if r.base_net_r is not None).items()))}
        rr[cid]=item;print(cid,json.dumps(item,sort_keys=True),flush=True);(OUT/f'{cid}_LEDGER.json').write_text(json.dumps([p4.asdict(r) for r in rows],indent=2,sort_keys=True))
    campaign='RESEARCH_GRADE_DIAMOND_CANDIDATE' if rr['DH-02-HO1']['classification']=='EXACT_RULE_FORWARD_HOLDOUT_SURVIVES' else 'NO_RESEARCH_GRADE_PROMOTION'
    out={'campaign_id':'HTF-DIAMOND-HUNT-001','phase':'PHASE_5_EXACT_RULE_FORWARD_HOLDOUT','status':'PHASE5_EXECUTION_BLOCK_COMPLETE','source_run_id':bind['source_run_id'],'source_artifact_id':bind['artifact_id'],'source_artifact_digest':bind['artifact_digest'],'source_fingerprint':bind['source_fingerprint'],'results':rr,'primary_candidate':'DH-02-HO1','secondary_family_cell':'DH-03-HO1','campaign_classification':campaign,'secondary_cannot_rescue_primary':True,'both_timeframes_reported':True,'post_outcome_tuning':False,'access_2025_performed':False,'access_2026_performed':False,'live_trading':False,'exchange_mutation':False,'merge_to_main':False}
    out['fingerprint']=core.canonical_hash(out);(OUT/'HTF_DIAMOND_HUNT_001_PHASE5_EXECUTION_RECEIPT_V0.1.json').write_text(json.dumps(out,indent=2,sort_keys=True));return 0

if __name__=='__main__':
    import sys
    raise SystemExit(main(sys.argv))
