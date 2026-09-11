from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib, json, random
from pathlib import Path
from statistics import mean
import sys
from research.phase_b_h04_binance_daily_manifest_v01 import EXPECTED_ARCHIVE_COUNT, FREEZE_FINGERPRINT, build_h04_manifest_receipt, expected_h04_daily_objects
from research.phase_b_h04_binance_offline_adapter_v01 import TIMEFRAME_MS, TIMESTAMP_UNIT_AMENDMENT_FINGERPRINT, adapt_h04_binance_daily_archive_bytes
from research.phase_b_h04_research_evaluator_v01 import evaluate_h04_universe, reprice_fixed
from research.phase_b_h04_stage_classifier_v01 import classify, decision_as_dict
from research.phase_b_research_evaluator_v01 import day_block_bootstrap_expectancy
from research.phase_b_signal_formation_v01 import CostAssumptions, ResearchParameters

HYPOTHESIS_ID="H04_POSITIVE_TAKER_FLOW_PERSISTENCE"
EXPECTED_AUTHORIZATION_FINGERPRINT="c091bdf34287dd5286fd8a55301cd6984907c5b3b431a92e140ceb7fd6e0b7ab"
EXPECTED_MANIFEST_FINGERPRINT="b4485d5d0acffe0e6d1607a300cc41fec11b59373a160e5271afd61a4e89719f"
EXPECTED_TIMESTAMP_UNIT_AMENDMENT_FINGERPRINT="efb5007ac77ff3d87e08f0be9012aba9deaff825557fbc489f802e3948d7602d"
DEFAULT_AUTHORIZATION_PATH=Path(__file__).with_name("PHASE_B_H04_BINANCE_DATA_ACCESS_AUTHORIZATION_V0.1.json")
TIMESTAMP_UNIT_AMENDMENT_PATH=Path(__file__).with_name("PHASE_B_H04_BINANCE_TIMESTAMP_UNIT_ADAPTER_AMENDMENT_V0.1.json")
BASE_COSTS=CostAssumptions(name="BASE_SENSITIVITY",fee_pct_each_side=0.05,spread_pct=0.05,slippage_pct_each_side=0.025)
STRESS_COSTS=CostAssumptions(name="STRESS",fee_pct_each_side=0.05,spread_pct=0.10,slippage_pct_each_side=0.05)
PARAMETERS=ResearchParameters()

def _hash(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def _write(path,body):
    body=dict(body); body['fingerprint']=_hash(body); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(body,indent=2,sort_keys=True)+'\n'); return body
def _load_auth(path):
    raw=json.loads(path.read_text()); supplied=raw.get('fingerprint'); unsigned=dict(raw); unsigned.pop('fingerprint',None)
    if supplied!=EXPECTED_AUTHORIZATION_FINGERPRINT or _hash(unsigned)!=supplied: raise PermissionError('H04 authorization fingerprint mismatch')
    if raw.get('status')!='AUTHORIZED_H04_BINANCE_DISCOVERY_ACQUISITION_AND_OFFLINE_EVALUATION_ONLY': raise PermissionError('H04 authorization status mismatch')
    if raw.get('required_bindings',{}).get('h04_prospective_freeze_fingerprint')!=FREEZE_FINGERPRINT: raise PermissionError('H04 freeze binding mismatch')
    if raw.get('required_bindings',{}).get('manifest_fingerprint')!=EXPECTED_MANIFEST_FINGERPRINT: raise PermissionError('manifest binding mismatch')
    for k in ('mexc_2025_09_through_2025_12_authorized','holdout_2026_authorized','exchange_mutation_authorized','live_trading_authorized','main_merge_authorized','render_deploy_authorized'):
        if raw.get(k) is not False: raise PermissionError(f'guard drift {k}')
    return raw

def _load_timestamp_unit_amendment(path=TIMESTAMP_UNIT_AMENDMENT_PATH):
    raw=json.loads(path.read_text()); supplied=raw.get('fingerprint'); unsigned=dict(raw); unsigned.pop('fingerprint',None)
    if supplied!=EXPECTED_TIMESTAMP_UNIT_AMENDMENT_FINGERPRINT or _hash(unsigned)!=supplied: raise PermissionError('H04 timestamp-unit amendment fingerprint mismatch')
    if TIMESTAMP_UNIT_AMENDMENT_FINGERPRINT!=EXPECTED_TIMESTAMP_UNIT_AMENDMENT_FINGERPRINT: raise PermissionError('H04 adapter amendment binding mismatch')
    if raw.get('status')!='FROZEN_PRE_OUTCOME_FORMAT_NORMALIZATION': raise PermissionError('H04 timestamp-unit amendment status mismatch')
    trigger=raw.get('trigger') or {}
    if trigger.get('outcomes_evaluated') is not False or trigger.get('classification_produced') is not False: raise PermissionError('H04 amendment was not frozen pre-outcome')
    norm=raw.get('normalization') or {}
    for key in ('market_values_changed','flow_fields_changed','geometry_changed','management_changed','costs_changed','decision_policy_changed'):
        if norm.get(key) is not False: raise PermissionError(f'H04 amendment scientific drift: {key}')
    rerun=raw.get('rerun_policy') or {}
    if rerun.get('same_frozen_h04_rules') is not True or rerun.get('same_authorized_binance_window') is not True or rerun.get('same_symbols') is not True or rerun.get('no_parameter_edits') is not True: raise PermissionError('H04 amendment rerun-policy drift')
    if rerun.get('mexc_2025_09_through_2025_12_locked') is not True or rerun.get('holdout_2026_locked') is not True: raise PermissionError('H04 protected-data lock drift')
    return raw

def _mechanism_bootstrap(base_records,bars_by_symbol,reps=5000,seed=230911,confidence=.95):
    flow={s:{b.candle.open_time:b.flow_imbalance for b in bars} for s,bars in bars_by_symbol.items()}
    byday={}
    for r in base_records:
        day=datetime.fromtimestamp(r.signal.entry_open_time/1000,tz=timezone.utc).date().isoformat()
        persistent=flow[r.symbol][r.signal.breakout_open_time]>0 and flow[r.symbol][r.signal.retest_open_time]>0
        byday.setdefault(day,[]).append((persistent,bool(r.outcome.tp1_reached)))
    days=sorted(byday)
    def diff(rows):
        p=[y for f,y in rows if f]; n=[y for f,y in rows if not f]
        return None if not p or not n else mean(p)-mean(n)
    point=diff([x for d in days for x in byday[d]])
    rng=random.Random(seed); draws=[]
    for _ in range(reps):
        sample=[]
        for _ in range(len(days)): sample.extend(byday[rng.choice(days)])
        v=diff(sample)
        if v is not None: draws.append(v)
    draws.sort(); a=(1-confidence)/2
    def q(qv):
        if not draws:return None
        pos=qv*(len(draws)-1); lo=int(pos); hi=min(lo+1,len(draws)-1); f=pos-lo; return draws[lo]*(1-f)+draws[hi]*f
    return {'method':'UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP_OF_TP1_RATE_DIFFERENCE','repetitions':reps,'valid_repetitions':len(draws),'sample_days':len(days),'seed':seed,'confidence':confidence,'point_estimate':point,'lower':q(a),'upper':q(1-a)}

def run_h04(raw_root:Path, output_path:Path, authorization_path:Path=DEFAULT_AUTHORIZATION_PATH):
    auth=_load_auth(authorization_path); amendment=_load_timestamp_unit_amendment(); manifest=build_h04_manifest_receipt()
    if manifest['fingerprint']!=EXPECTED_MANIFEST_FINGERPRINT: raise PermissionError('manifest fingerprint drift')
    objs=expected_h04_daily_objects(); missing=[]
    for it in objs:
        d=raw_root/it['symbol']; a=d/it['archive_filename']; c=d/(it['archive_filename']+'.CHECKSUM')
        if not a.is_file():missing.append(str(a))
        if not c.is_file():missing.append(str(c))
    if missing: return _write(output_path,{'document_type':'PHASE_B_H04_BINANCE_DISCOVERY_RECEIPT','version':'0.1','status':'H04_DISCOVERY_NOT_RUN_INTAKE_INCOMPLETE','missing_file_count':len(missing),'first_missing':missing[0],'mexc_validation_2025_accessed':False,'holdout_2026_accessed':False})
    bars={s:[] for s in auth['symbols']}; sha={}; integrity={'archives_expected':EXPECTED_ARCHIVE_COUNT,'archives_passed':0,'checksum_verified':0,'source_rows':0,'detected_internal_gap_count':0,'missing_candles_including_day_boundaries':0,'source_close_time_anomaly_count':0}
    for it in objs:
        d=raw_root/it['symbol']; ap=d/it['archive_filename']; cp=d/(it['archive_filename']+'.CHECKSUM'); raw=ap.read_bytes(); chk=cp.read_text()
        ad=adapt_h04_binance_daily_archive_bytes(symbol=it['symbol'],day=it['date_utc'],archive_filename=it['archive_filename'],archive_bytes=raw,checksum_text=chk)
        if not ad.status.startswith('PASS_BINANCE_DAILY'): raise RuntimeError(f"integrity block {it['symbol']} {it['date_utc']} {ad.status} {ad.reasons}")
        day_start=int(datetime.strptime(it['date_utc'],'%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp()*1000); day_end=day_start+86400000
        lead=(ad.bars[0].candle.open_time-day_start)//TIMEFRAME_MS; trail=(day_end-TIMEFRAME_MS-ad.bars[-1].candle.open_time)//TIMEFRAME_MS; total=int(lead+ad.missing_candle_count+trail)
        if lead<0 or trail<0 or ad.row_count+total!=96: raise RuntimeError('day coverage block')
        integrity['archives_passed']+=1; integrity['checksum_verified']+=1; integrity['source_rows']+=ad.row_count; integrity['detected_internal_gap_count']+=ad.detected_gap_count; integrity['missing_candles_including_day_boundaries']+=total; integrity['source_close_time_anomaly_count']+=ad.source_close_time_anomaly_count
        bars[it['symbol']].extend(ad.bars); sha[f"{it['symbol']}/{it['archive_filename']}"] = ad.archive_sha256
    archive_set=_hash(sha)
    records,metrics,base_records,mechanism,diagnostics=evaluate_h04_universe(bars,PARAMETERS,BASE_COSTS)
    bootstrap=asdict(day_block_bootstrap_expectancy(records,repetitions=5000,seed=230911,confidence=0.95))
    stress=reprice_fixed(records,STRESS_COSTS,min_net_rr=2.0); mech_boot=_mechanism_bootstrap(base_records,bars)
    decision=classify(metrics,stress,bootstrap,mechanism,mech_boot,minimum=100)
    body={'document_type':'PHASE_B_H04_BINANCE_DISCOVERY_RECEIPT','version':'0.1','status':'H04_DISCOVERY_COMPLETE','hypothesis_id':HYPOTHESIS_ID,'source':'OFFICIAL_BINANCE_PUBLIC_DATA_ONLY','market_type':'SPOT','timeframe':'15m','window_start_utc_inclusive':'2023-02-01T00:00:00.000Z','window_end_utc_exclusive':'2025-09-01T00:00:00.000Z','symbols':auth['symbols'],'authorization_fingerprint':auth['fingerprint'],'h04_freeze_fingerprint':FREEZE_FINGERPRINT,'manifest_fingerprint':manifest['fingerprint'],'timestamp_unit_adapter_amendment_fingerprint':amendment['fingerprint'],'archive_set_fingerprint':archive_set,'integrity':integrity,'base_metrics':asdict(metrics),'mechanism_metrics':asdict(mechanism),'mechanism_bootstrap':mech_boot,'bootstrap':bootstrap,'fixed_cohort_stress':asdict(stress),'decision':decision_as_dict(decision),'diagnostics':diagnostics,'mexc_validation_2025_09_through_2025_12_accessed':False,'holdout_2026_accessed':False,'exchange_mutation_performed':False,'live_trading_performed':False}
    return _write(output_path,body)

def main(argv=None):
    a=list(sys.argv[1:] if argv is None else argv); root=Path(a[0]); out=Path(a[1]); authp=Path(a[2]) if len(a)>2 else DEFAULT_AUTHORIZATION_PATH
    try:r=run_h04(root,out,authp)
    except Exception as e: print(f'H04_DISCOVERY_FATAL: {type(e).__name__}: {e}'); return 2
    print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r.get('status')=='H04_DISCOVERY_COMPLETE' else 3
if __name__=='__main__': raise SystemExit(main())
