#!/usr/bin/env python3
"""REACTIVE-SHOCK-SCALP-005 R1: execute *existing* immutable Sept 2026 14-event freeze.

No private endpoints, trading, 2025 OOS, or 2026 holdout. Bybit historical
BBO is a proxy; never call this executable MEXC PnL.
"""
from __future__ import annotations
import hashlib, json, random, statistics, sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# Imported frozen discovery scorer; do not change signal/return arithmetic.
from research.microstructure_scalping import reactive_shock_scalp_005_v01 as frozen

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'REACTIVE_SHOCK_SCALP_005_REPLICATION_R1_MANIFEST.json'
RECEIPTS=HERE/'receipts'
OUTPUT=RECEIPTS/'reactive_shock_r1_economic_receipt.json'
SEED=20260926
N_BOOT=5000

def quality_manifest(raw):
    es=raw['events']; prior=set(raw['prior_mve_dates'])
    assert raw['event_count']==len(es)==14
    assert len(prior)==8 and len({x['date'] for x in es})==14
    assert sum(x['type']=='CPI' for x in es)==7 and sum(x['type']=='NFP' for x in es)==7
    assert all(x['date'] not in prior and date.fromisoformat(x['date']).year==2023 for x in es)
    assert all(x['release_time_et']=='08:30 AM' and x['release_timezone']=='America/New_York' for x in es)
    assert raw['guards']['prior_mve_events_excluded'] and not raw['guards']['oos_2025_opened']
    assert not raw['guards']['holdout_2026_opened']
    return sorted(es,key=lambda e:e['date'])

def bootstrap_ci(vals):
    if not vals:return None
    rng=random.Random(SEED)
    means=sorted(sum(rng.choices(vals,k=len(vals)))/len(vals) for _ in range(N_BOOT))
    return [means[int(.025*N_BOOT)],means[int(.975*N_BOOT)]]

def strict_gate(rows):
    v=[x for x in rows if x['status']=='RESOLVED']
    cp=[x['stress10_bps'] for x in v if x['type']=='CPI']
    nf=[x['stress10_bps'] for x in v if x['type']=='NFP']
    allv=[x['stress10_bps'] for x in v]
    lo=bootstrap_ci(allv)
    bits={
      'n_ge_12':len(allv)>=12,
      'cpi_n_ge_6':len(cp)>=6,
      'nfp_n_ge_6':len(nf)>=6,
      'pooled_mean_gt_0':bool(allv and statistics.fmean(allv)>0),
      'pooled_median_gt_0':bool(allv and statistics.median(allv)>0),
      'cpi_mean_gt_0':bool(cp and statistics.fmean(cp)>0),
      'nfp_mean_gt_0':bool(nf and statistics.fmean(nf)>0),
      'at_least_8_positive':sum(x>0 for x in allv)>=8,
      'bootstrap_ci_lower_gt_0':bool(lo and lo[0]>0),
    }
    return {
      'decision':'REPLICATION_SURVIVES' if all(bits.values()) else 'REPLICATION_FAILS_STRICT_GATE',
      'gates':bits,'resolved':len(v),'CPI':len(cp),'NFP':len(nf),
      'mean_stress10_bps':statistics.fmean(allv) if allv else None,
      'median_stress10_bps':statistics.median(allv) if allv else None,
      'mean_cpi_stress10_bps':statistics.fmean(cp) if cp else None,
      'mean_nfp_stress10_bps':statistics.fmean(nf) if nf else None,
      'bootstrap_ci95_stress10_bps':lo,
      'positive_stress10_events':sum(x>0 for x in allv),
    }

def main():
    manifest=SOURCE.read_bytes()
    raw=json.loads(manifest)
    events=quality_manifest(raw)
    RECEIPTS.mkdir(parents=True,exist_ok=True)
    work=Path('/tmp/reactive_shock_r1');work.mkdir(parents=True,exist_ok=True)
    out={'lab_id':'REACTIVE-SHOCK-SCALP-005', 'phase':'FROZEN_DISCOVERY_REPLICATION_R1',
         'freeze':'REACTIVE_SHOCK_SCALP_005_REPLICATION_R1_FREEZE_V0_1.md',
         'manifest_sha256':hashlib.sha256(manifest).hexdigest(),
         'original_selection_dates_excluded':raw['prior_mve_dates'],
         'venue_market_source':'Bybit BTCUSDT historical trade and order book',
         'economic_cost_proxy':'MEXC 16bps taker+taker, plus 10bps frozen stress',
         'outcome_attribution':'BYBIT_HISTORICAL_PROXY_NOT_MEXC_EXECUTABLE',
         'live_orders':False,'private_api':False,'oos_2025_opened':False,'holdout_2026_opened':False,
         'rows':[], 'source_receipts':[]}
    for e in events:
        day=e['date']
        print('SOURCE_ONLY',day,e['type'],flush=True)
        t0=int(datetime.fromisoformat(day+'T08:30:00').replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc).timestamp()*1000)
        l2p=work/(day+'_l2.zip');trp=work/(day+'_trades.csv.gz')
        rec={'date':day,'type':e['type'],'status':'SOURCE_BLOCKED'}
        provenance={'date':day}
        try:
            l2bytes=frozen.fetch(frozen.BYBIT_L2.format(date=day),l2p)
            tbytes=frozen.fetch(frozen.BYBIT_TRADES.format(date=day),trp)
            provenance={'date':day,'l2_bytes':l2bytes,'trade_bytes':tbytes,
                        'l2_sha256':hashlib.sha256(l2p.read_bytes()).hexdigest(),
                        'trade_sha256':hashlib.sha256(trp.read_bytes()).hexdigest()}
            pre,states=frozen.load_event_l2(l2p,t0)
            trades=frozen.load_event_trades(trp,t0)
            provenance.update({'l2_states':len(states),'trades_0_5s':len(trades),
                               'pre_bbo_timestamp':pre[0]})
            s=frozen.eval_variant({'date':day,'type':e['type'],'t0_ms':t0},pre,states,trades,'FLOWPRICE_W2')
            if s and s['horizons'].get('60000'):
                z=s['horizons']['60000']
                rec.update(status='RESOLVED', direction=s['direction'], entry_ts=s['entry_ms'],
                           taker_gross_bps=z['taker_gross_bps'],
                           fee_only_bps=z['taker_gross_bps']-16,
                           stress10_bps=z['taker_gross_bps']-26,
                           stress20_bps=z['taker_gross_bps']-36)
            else: rec.update(status='NO_SIGNAL_OR_OUTCOME')
        except Exception as exc:
            rec.update(status='SOURCE_BLOCKED',error=type(exc).__name__+': '+str(exc)[:300])
            print('SOURCE_BLOCKED',day,str(exc)[:140],flush=True)
        finally:
            for f in (l2p,trp):
                if f.exists():f.unlink()
        out['rows'].append(rec)
        out['source_receipts'].append(provenance)
        # Atomic checkpoint for audit if runner is interrupted; not a completed verdict.
        OUTPUT.write_text(json.dumps({**out,'progress':'INCOMPLETE_NOT_ADJUDICATED'},indent=2),encoding='utf-8')
        print('EVENT',json.dumps(rec,sort_keys=True),flush=True)
    if any(x['status']=='SOURCE_BLOCKED' for x in out['rows']):
        out['status']='SOURCE_BLOCKED'
        out['gate']={'decision':'NOT_ADJUDICATED_MISSING_SOURCE'}
    else:
        out['status']='REPLAY_COMPLETE'
        out['gate']=strict_gate(out['rows'])
    out['progress']='FINAL'
    OUTPUT.write_text(json.dumps(out,indent=2,sort_keys=True),encoding='utf-8')
    print('FINAL_SUMMARY',json.dumps({'status':out['status'],'gate':out['gate'],'rows':out['rows']},sort_keys=True),flush=True)
    return 0 if out['status']=='REPLAY_COMPLETE' else 3

if __name__=='__main__':sys.exit(main())