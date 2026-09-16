import hashlib, json, math, os, random, statistics, zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
FREEZE=HERE.parent/'BNB_LAUNCHPOOL_DEMAND_001_V2_OOS_2025_FREEZE_V0.1.json'
BIND=HERE/'BNB_LAUNCHPOOL_DEMAND_001_OOS_2025_EXECUTION_BINDING_V0.1.json'
SOURCE=HERE/'source_gate_v01'/'BNB_LAUNCHPOOL_DEMAND_001_OOS_2025_SOURCE_GATE_V0.1.json'
MARKET=HERE/'market_source_v01'/'BNB_LAUNCHPOOL_DEMAND_001_OOS_2025_MARKET_SOURCE_V0.1.json'
OUTDIR=HERE/'oos_result_v01'; OUT=OUTDIR/'BNB_LAUNCHPOOL_DEMAND_001_OOS_2025_RESULT_V0.1.json'; LEDGER=OUTDIR/'BNB_LAUNCHPOOL_DEMAND_001_OOS_2025_LEDGER_V0.1.json'

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()
def epoch_iso(s): return int(datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(timezone.utc).timestamp())
def parse_epoch(b):
    s=b.decode('ascii','strict').strip()
    if not s.isdigit(): return None
    x=int(s); sec=x/1_000_000.0 if x>10**14 else x/1_000.0 if x>10**11 else float(x)
    return int(round(sec))
def pf(v):
    pos=sum(x for x in v if x>0); neg=-sum(x for x in v if x<0)
    return math.inf if neg==0 and pos>0 else 0.0 if neg==0 else pos/neg
def q(vals,p):
    vals=sorted(vals); h=(len(vals)-1)*p; lo=math.floor(h); hi=math.ceil(h)
    return vals[lo] if lo==hi else vals[lo]*(hi-h)+vals[hi]*(h-lo)
def pfj(x): return '+Infinity' if math.isinf(x) else x

def main():
    OUTDIR.mkdir(parents=True,exist_ok=True)
    f=json.loads(FREEZE.read_text()); b=json.loads(BIND.read_text()); s=json.loads(SOURCE.read_text()); m=json.loads(MARKET.read_text())
    assert f['status']=='FROZEN_PRE_2025_SOURCE_AND_MARKET_OUTCOME_ACCESS'; assert b['status']=='FROZEN_POST_SOURCE_AUDIT_PRE_PRICE_OPEN'
    assert s['classification']=='SOURCE_DATA_PASS' and m['classification']=='MARKET_SOURCE_DATA_PASS'
    assert s['canonical_event_manifest_sha256']==b['source_gate']['canonical_event_manifest_sha256']
    assert m['archive_manifest_sha256']==b['market_source']['archive_manifest_sha256']
    assert m['selected_trade_paths']==8 and b['market_source']['selected_trade_paths']==8
    root=Path(os.environ.get('BLP_2025_MARKET_SOURCE_DIR','/tmp/blp_2025_market_source'))
    zips={p.name:p for p in root.rglob('BNBBTC-15m-2025-*.zip')}
    exp={x['archive']:x['sha256'] for x in m['archive_manifest']}
    if set(zips)!=set(exp): raise RuntimeError(f'ARCHIVE_SET_MISMATCH:{len(zips)}')
    for name,p in zips.items():
        if sha256_file(p)!=exp[name]: raise RuntimeError(f'ARCHIVE_SHA_MISMATCH:{name}')
        if '-2026-' in name: raise RuntimeError('FORBIDDEN_2026_ARCHIVE')
    required=set()
    for x in m['selected']:
        required.add(epoch_iso(x['entry_time_utc'])); required.add(epoch_iso(x['exit_time_utc']))
    if len(required)!=16: raise RuntimeError(f'EXPECTED_16_REQUIRED_ROWS_GOT_{len(required)}')
    opens={}; dup=[]
    for name in sorted(zips):
        with zipfile.ZipFile(zips[name]) as z:
            if z.testzip() is not None: raise RuntimeError(f'ZIP_CRC_FAILURE:{name}')
            mem=[x for x in z.namelist() if not x.endswith('/')]
            if len(mem)!=1: raise RuntimeError(f'ZIP_MEMBER_COUNT:{name}')
            with z.open(mem[0]) as fh:
                for line in fh:
                    if not line.strip(): continue
                    parts=line.split(b',',2)
                    if len(parts)<2: continue
                    ts=parse_epoch(parts[0])
                    if ts not in required: continue
                    op=float(parts[1].decode('ascii','strict'))
                    if not math.isfinite(op) or op<=0: raise RuntimeError(f'INVALID_OPEN:{ts}')
                    if ts in opens: dup.append(ts)
                    opens[ts]=op
    miss=sorted(required-set(opens))
    if miss or dup:
        result={'protocol_id':f['protocol_id'],'classification':'NON_SCIENTIFIC_BLOCKED_NO_TIER_DEMOTION','missing_rows':miss,'duplicate_rows':sorted(set(dup)),'live_trading_authorized':False}
        OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2)); return
    trades=[]
    for i,x in enumerate(m['selected'],1):
        et=epoch_iso(x['entry_time_utc']); xt=epoch_iso(x['exit_time_utc']); ent=opens[et]; ex=opens[xt]
        gross=10000*(ex/ent-1); base=gross-20.0; stress=gross-30.0
        trades.append({'trade_id':i,'project_numbers':x['project_numbers'],'symbols':x['symbols'],'signal_time_utc':x['signal_time_utc'],'entry_time_utc':x['entry_time_utc'],'exit_time_utc':x['exit_time_utc'],'entry_open_bnbbtc':ent,'exit_open_bnbbtc':ex,'gross_bps':gross,'base_net_bps':base,'stress_net_bps':stress})
    gross=[x['gross_bps'] for x in trades]; base=[x['base_net_bps'] for x in trades]; stress=[x['stress_net_bps'] for x in trades]; n=len(trades)
    rng=random.Random(160925); boot=[]
    for _ in range(5000): boot.append(statistics.fmean(base[rng.randrange(n)] for __ in range(n)))
    ci=[q(boot,0.025),q(boot,0.975)]
    pos=[x for x in base if x>0]; concentration=max(pos)/sum(pos) if pos else None
    base_mean=statistics.fmean(base); gross_mean=statistics.fmean(gross); base_pf=pf(base); stress_mean=statistics.fmean(stress); stress_pf=pf(stress)
    equity=1.0; peak=1.0; max_dd=0.0
    for r in base:
        equity*=max(0.0,1.0+r/10000.0); peak=max(peak,equity); max_dd=max(max_dd,1.0-equity/peak)
    cumulative=equity-1.0; fatal=(max_dd>0.50 and cumulative<0.05)
    gates={
      'source_provenance_clean_and_reproducible':True,
      'no_leakage_hindsight_or_post_outcome_selection':True,
      'minimum_resolved_trades':n>=8,
      'base_mean_net_bps_gt_zero':base_mean>0,
      'base_profit_factor_gte_one':base_pf>=1.0,
      'expected_sign_correct_long_bnbbtc':gross_mean>0,
      'max_single_trade_share_of_total_positive_base_net_lte_0_40':concentration is not None and concentration<=0.40,
      'unresolved_selected_execution_paths_zero':len(m['execution_path_failures'])==0,
      'source_rule_deviations_zero':True,
      'trading_rule_deviations_zero':True,
      'fatal_execution_or_risk_pathology_false':not fatal
    }
    if n<8: classification='INSUFFICIENT_OOS_SAMPLE_TIER3_REMAINS'
    elif all(gates.values()): classification='TIER_2_PROMOTED_CANDIDATE_QUASE_DIAMANTE_PATH2_PASS'
    elif base_mean<=0 or base_pf<1.0 or gross_mean<=0: classification='TIER_4_REJECTED_STONE_FOR_TESTED_2025_REPLICATION'
    else: classification='TIER_3_WATCHLIST_REMAINS'
    ledger={'protocol_id':f['protocol_id'],'archive_manifest_sha256':m['archive_manifest_sha256'],'trades':trades}
    lb=(json.dumps(ledger,indent=2,sort_keys=True)+'\n').encode(); LEDGER.write_bytes(lb); lsha=hashlib.sha256(lb).hexdigest()
    result={
      'protocol_id':f['protocol_id'],'parent_primary_verdict':'DISCOVERY_FAIL_NO_PROMOTION','classification':classification,'tier2_path2_pass':classification.startswith('TIER_2_'),
      'resolved_trades':n,'economics':{'gross_mean_bps':gross_mean,'base_mean_net_bps':base_mean,'base_median_net_bps':statistics.median(base),'base_profit_factor':pfj(base_pf),'base_win_rate':sum(x>0 for x in base)/n,'base_total_net_bps':sum(base),'stress_mean_net_bps':stress_mean,'stress_profit_factor':pfj(stress_pf),'stress_total_net_bps':sum(stress),'max_single_trade_positive_base_contribution_share':concentration},
      'bootstrap_base_mean_bps':{'replications':5000,'seed':160925,'ci95_lower':ci[0],'ci95_upper':ci[1],'median_bootstrap_mean':statistics.median(boot),'role':'REPORT_ONLY'},
      'risk':{'compounded_base_return':cumulative,'max_drawdown_compounded_base':max_dd,'v2_fatal_risk_rule_triggered':fatal},
      'promotion_gate_checks':gates,'failed_promotion_gates':[k for k,v in gates.items() if not v],
      'source_binding':{'canonical_event_manifest_sha256':s['canonical_event_manifest_sha256'],'market_archive_manifest_sha256':m['archive_manifest_sha256'],'market_source_run_id':b['market_source']['market_source_run_id'],'market_source_artifact_id':b['market_source']['market_source_artifact_id'],'market_source_artifact_zip_sha256':b['market_source']['market_source_artifact_zip_sha256']},
      'ledger_sha256':lsha,'access_2026_market':False,'live_trading_authorized':False,'post_outcome_rescue_allowed':False
    }
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'classification':classification,'resolved_trades':n,'economics':result['economics'],'bootstrap':result['bootstrap_base_mean_bps'],'risk':result['risk'],'failed_promotion_gates':result['failed_promotion_gates'],'ledger_sha256':lsha},indent=2))
if __name__=='__main__': main()
