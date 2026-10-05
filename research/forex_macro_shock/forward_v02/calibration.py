"""Apply committed burn-in gates/formula only. No strategy PnL or activation."""
import argparse
import hashlib
import json
from datetime import datetime, timezone, timedelta
import time
from pathlib import Path

import collector as c
import model


def evaluate(store):
    integrity = store.verify()
    current_freeze = c.digest((c.ROOT/'PRE_OUTCOME_METHOD_FREEZE_V02.json').read_bytes())
    grids = []; seen = set(); errors = []
    for payload, in store.db.execute('SELECT payload FROM receipts ORDER BY seq'):
        row=json.loads(payload)
        if row['source']!='paired_grid':continue
        if row.get('freeze_sha256')!=current_freeze: errors.append('FREEZE_HASH_MISMATCH');continue
        raw=store.db.execute('SELECT body FROM raw WHERE hash=?',(row['raw_sha256'],)).fetchone()[0]
        g=json.loads(raw)
        tick=g['grid_ms']
        if not isinstance(tick,int) or tick%1000:errors.append('INVALID_GRID_ID');continue
        if tick in seen:errors.append('DUPLICATE_GRID_ID');continue
        seen.add(tick)
        if grids and tick<=grids[-1]['grid_ms']:errors.append('GRID_CLOCK_REVERSED')
        if tick>=int(c.SETUP_STOP*1000):errors.append('OUTSIDE_BURNIN_CUTOFF');continue
        dt=datetime.fromtimestamp(tick/1000,timezone.utc)
        # Eligibility is computed from the committed clock rules, not trusted labels.
        if dt.weekday()>=5 or not 10<=dt.hour<16:continue
        grids.append(g)
    days={}
    for g in grids:
        day=datetime.fromtimestamp(g['grid_ms']/1000,timezone.utc).date().isoformat()
        d=days.setdefault(day,{'recorded':0,'valid':0,'expected':21600,'longest_invalid_seconds':0,'_invalid_run':0})
        d['recorded']+=1
        if g['source_valid']:
            if 'basis_bps' not in g or 'mexc_spread_bps' not in g:errors.append('MISSING_VALID_GRID_MEASUREMENTS')
            d['valid']+=1;d['_invalid_run']=0
        else:
            d['_invalid_run']+=1;d['longest_invalid_seconds']=max(d['longest_invalid_seconds'],d['_invalid_run'])
    if days:
        first=datetime.fromisoformat(min(days)).date();last=datetime.fromisoformat(max(days)).date()
        while first<=last:
            if first.weekday()<5:
                days.setdefault(first.isoformat(),{'recorded':0,'valid':0,'expected':21600,'longest_invalid_seconds':0,'_invalid_run':0})
            first+=timedelta(days=1)
    for day,d in days.items():
        ticks=[g['grid_ms'] for g in grids if datetime.fromtimestamp(g['grid_ms']/1000,timezone.utc).date().isoformat()==day]
        start=int(datetime.fromisoformat(day+'T10:00:00+00:00').timestamp()*1000)
        end=start+21600*1000
        # Missing rows and edge windows are absent evidence, never reconstructed grids.
        gaps=[max(0,(b-a)//1000-1) for a,b in zip(ticks,ticks[1:])]
        gaps+=[(ticks[0]-start)//1000,(end-1000-ticks[-1])//1000] if ticks else [21600]
        d['max_missing_gap_seconds']=max(gaps,default=0)
        d['valid_coverage']=d['valid']/21600
        d.pop('_invalid_run')
    count=sum(d['valid'] for d in days.values())
    if len(days)<5:errors.append('FEWER_THAN_FIVE_DISTINCT_DAYS')
    if count<21600:errors.append('FEWER_THAN_21600_VALID_PAIRED_GRIDS')
    if any(d['valid_coverage']<.99 for d in days.values()):errors.append('DAILY_VALID_COVERAGE_BELOW_99_PERCENT')
    # No capture continuity can be inferred over missing eligible grids.
    if any(d['max_missing_gap_seconds']>5 for d in days.values()):errors.append('CAPTURE_CONTINUITY_UNPROVEN')
    if time.time()<c.SETUP_STOP:errors.append('BURNIN_WINDOW_NOT_CLOSED')
    if time.time()>=datetime(2026,10,26,tzinfo=timezone.utc).timestamp():errors.append('CALIBRATION_COMMIT_DEADLINE_NOT_PROVEN')
    # Reconnect qualification is a separate mandatory technical receipt, never
    # inferred from a small set of favourable valid grids.
    reconnect_unqualified=any(json.loads(x[0])['source'].endswith('_connection_failure') for x in store.db.execute('SELECT payload FROM receipts'))
    if reconnect_unqualified:errors.append('RECONNECT_QUALIFICATION_RECEIPT_REQUIRED')
    result={**integrity,'freeze_sha256':current_freeze,'valid_paired_grids':count,
            'distinct_days':len(days),'days':days,'outcomes_opened':0,'pnl_computed':False,
            'activation':False,'verdict':'OPERATIONALLY_BLOCKED','blockers':sorted(set(errors)),
            'calibration':None}
    if not errors:
        good=[g for g in grids if g['source_valid']]
        result['calibration']=model.calibrate([g['basis_bps'] for g in good],[g['mexc_spread_bps'] for g in good])
        result['calibration_source_gate']='PASS'
        result['blockers']=['Qualified event-runtime and committed activation receipt still required']
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--state',default=str(c.ROOT/'state/continuous.sqlite3'))
    p.add_argument('--report',default=str(c.ROOT/'evidence/CALIBRATION_GATE_V02_1.json'));a=p.parse_args()
    store=c.Store(a.state)
    try:
        result=evaluate(store);target=Path(a.report);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(result,indent=2));print(c.canonical(result))
    finally:store.db.close()


if __name__=='__main__':main()
