#!/usr/bin/env python3
"""CED-1D-V1 V3 boundary-week re-adjudication for the three frozen Momentum survivors.

Research-only. Uses only 2021-2024 raw Discovery ledger. 2025/2026 are not opened.
The only prospective change versus the historical closeout is the already-frozen
boundary-week policy: split-edge partial-week trades remain in the immutable ledger
but are excluded from inference metrics.
"""
from __future__ import annotations
import argparse, array, csv, hashlib, json, math, random
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

EXPECTED = {
    "event_ledger.csv": "03af682447bb94de8b04ded7ceb0026c2cd2589c53a9d0979bd22f1e6d289ff4",
    "results_raw.csv": "3daad67d6d2864e64470ed068ec452642a1a70ef8be2ef37250c137efd1e0790",
    "primary_atomic_registry.json": "707fdc763372a8c735a0afe32e7984c672bc2a9dbd73f49a3656ed77b4c3410d",
    "run_manifest.json": "c0a90d04e9bc10a4ea19b4ddbc49f4a001c6e84397ca6cdc6648cbdcfe3b1822",
}
CONTRACT_SHA = "4a6ee27a8b6fd66dcc89e3d2b4211d3f5d5c8020c151f8908f081108803acfb4"
RAW_ARTIFACT_SHA = "361412b71864bc216d73ec4457f60affccbaba39c5f1c5e8e0a1377c9ca68d9c"
HISTORICAL_CLOSEOUT_SHA = "8b30a95606a0949a912fa8d1475e63c9431263c7568bf0b2d3df4f8373c47416"
TARGETS = ("CED1D-0031", "CED1D-0241", "CED1D-0251")
START = date(2021,1,1); END = date(2024,12,31)
INF_START = date(2021,1,4); INF_END = date(2024,12,30)
YEARS=(2021,2022,2023,2024)

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()

def mean(xs): return math.fsum(xs)/len(xs) if xs else None
def week(d): return d-timedelta(days=d.weekday())
def parse_day(s):
    d=date.fromisoformat(s)
    if not START <= d <= END: raise RuntimeError(f"FIREWALL_DATE_OUTSIDE_DISCOVERY:{s}")
    return d
def canonical(o): return json.dumps(o,sort_keys=True,separators=(',',':'),allow_nan=False)
def full_inference_event(e): return INF_START <= e['day'] < INF_END

def load_cells(run_dir: Path):
    with (run_dir/'results_raw.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=820: raise RuntimeError('EXPECTED_820_RESULTS')
    return {r['test_id']:json.loads(r['config_json']) for r in rows}

def load_events(run_dir: Path,cells):
    events={k:[] for k in cells}; counts={k:Counter() for k in cells}; seen=set(); prev_exit={}
    with (run_dir/'event_ledger.csv').open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f)
        for row in r:
            tid=row['test_id']; c=cells[tid]; sd=parse_day(row['signal_day'])
            ed=parse_day(row['entry_day']) if row['entry_day'] else None
            xd=parse_day(row['exit_day']) if row['exit_day'] else None
            if (tid,sd) in seen: raise RuntimeError('DUPLICATE_SIGNAL_ROW')
            seen.add((tid,sd)); status=row['status']; counts[tid][status]+=1
            if ed is not None and ed != sd+timedelta(days=1): raise RuntimeError('ENTRY_CAUSALITY_FAILURE')
            if xd is not None and xd != ed+timedelta(days=int(c['horizon'])): raise RuntimeError('HORIZON_MISMATCH')
            if status!='TRADE': continue
            if tid in prev_exit and ed < prev_exit[tid]: raise RuntimeError('OVERLAPPING_EXECUTED_EVENTS')
            prev_exit[tid]=xd
            signed=float(row['signed_return']); gross=signed*10000
            events[tid].append({'day':ed,'signal_day':sd,'exit_day':xd,'gross':gross,'symbol':c['symbol']})
    return events,counts

def sample_gate(events,rules):
    ds={e['day'] for e in events}; months={(d.year,d.month) for d in ds}
    m={'events':len(events),'active_days':len(ds),'active_week_clusters':len({week(d) for d in ds}), 'active_months':len(months)}
    failures=[k for k,v in m.items() if v < rules['min_'+k]]
    annual={y:sum(yy==y for yy,mm in months) for y in YEARS}
    failures += [f'months_in_{y}' for y in YEARS if annual[y] < rules['min_months_per_calendar_year']]
    m.update({f'months_{y}':annual[y] for y in YEARS})
    m['minimum_floor_ratio']=min(m[k]/rules['min_'+k] for k in ('events','active_days','active_week_clusters','active_months'))
    m['sample_pass']=not failures; m['failed_gates']='|'.join(failures); return m

def temporal(events,base):
    groups={k:defaultdict(list) for k in ('year','month','quarter','day')}
    for e in events:
        d=e['day']; v=e['gross']-base
        for kind,key in [('year',str(d.year)),('month',d.strftime('%Y-%m')),('quarter',f'{d.year}-Q{(d.month-1)//3+1}'),('day',d.isoformat())]: groups[kind][key].append(v)
    return groups

def concentration(events,base,caps):
    values=[abs(e['gross']-base) for e in events]; total=math.fsum(values)
    if not total: return {'absolute_pnl_denominator':total,'day_share':None,'month_share':None,'top5_share':None,'concentration_ratio':None}
    days=defaultdict(list); months=defaultdict(list)
    for e,v in zip(events,values): days[e['day'].isoformat()].append(v); months[e['day'].strftime('%Y-%m')].append(v)
    day_share=max(math.fsum(v) for v in days.values())/total
    month_share=max(math.fsum(v) for v in months.values())/total
    top5=math.fsum(sorted(values,reverse=True)[:5])/total
    ratio=max(day_share/caps['max_single_day_share_absolute_pnl'],month_share/caps['max_single_month_share_absolute_pnl'],top5/caps['max_top5_event_share_absolute_pnl'])
    return {'absolute_pnl_denominator':total,'day_share':day_share,'month_share':month_share,'top5_share':top5,'concentration_ratio':ratio}

def neighbors(tid,cells):
    selected=cells[tid]; fixed={'symbol','family','direction','state'}
    pool={k:v for k,v in cells.items() if all(v.get(f)==selected.get(f) for f in fixed)}; result=set()
    for axis in selected.keys()-fixed:
        if not isinstance(selected[axis],(int,float)): continue
        vals=sorted({v[axis] for v in pool.values()}); i=vals.index(selected[axis])
        adjacent=vals[max(0,i-1):i]+vals[i+1:i+2]
        for key,cand in pool.items():
            if cand[axis] in adjacent and all(cand[k]==selected[k] for k in selected if k!=axis): result.add(key)
    return sorted(result)

def ascending_score(value,thresholds): return 0 if value is None else sum(value>=t for t in thresholds)

def score_components(m,contract):
    g,co=m['gate'],m['concentration']['concentration_ratio']; net=m['mean']; gross=m['gross_mean']
    economic=0 if net is None or net<=0 else 1+sum(net>=t for t in (2,4,6,10))
    low=0 if co is None or co>1 else (5 if co<=.5 else 4 if co<=.7 else 3 if co<=.8 else 2 if co<=.9 else 1)
    cost=0 if gross is None or gross<=0 else 1+sum(gross>t for t in (6,10,14,20))
    comp={'economic_magnitude':economic,
          'temporal_repeatability':ascending_score(m['positive_month_fraction'],(.4,.5,.6,.7,.8)),
          'parameter_stability':ascending_score(m['neighbor_fraction'],(.25,.4,.55,.7,.85)) if m['neighbor_count']>=2 else 0,
          'sample_sufficiency':ascending_score(g['minimum_floor_ratio'],(1,1.25,1.5,2,3)),
          'cross_context_consistency':0,'mechanism':0,'low_concentration':low,
          'implementation_realism':1,'cost_robustness':cost}
    weights=contract['scout_score']['weights']
    score=math.fsum(weights[k]*v/5 for k,v in comp.items())
    veto=[]
    if not g['sample_pass'] or co is None: veto.append('insufficient_sample')
    if co is not None and co>1: veto.append('single_episode_dependence')
    return comp,score,veto

def route(score,veto):
    if 'insufficient_sample' in veto:return 'INSUFFICIENT_SAMPLE'
    if veto or score<40:return 'ARCHIVE'
    return 'WATCH' if score<55 else 'SCOUT_SURVIVOR' if score<70 else 'SHORTLIST_ELIGIBLE'

class WeekPlan:
    def __init__(self,reps,seed):
        first=INF_START; self.weeks=[]
        while first < INF_END: self.weeks.append(first); first += timedelta(days=7)
        rng=random.Random(seed); n=len(self.weeks)
        self.draws=[array.array('H',(rng.randrange(n) for _ in range(n))) for _ in range(reps)]

def percentile(a,p):
    pos=(len(a)-1)*p; lo=math.floor(pos); hi=math.ceil(pos)
    return a[lo]+(a[hi]-a[lo])*(pos-lo)

def bootstrap(events,base,plan):
    idx={w:i for i,w in enumerate(plan.weeks)}; bins=[[] for _ in plan.weeks]
    for e in events: bins[idx[week(e['day'])]].append(e['gross']-base)
    sums=[math.fsum(b) for b in bins]; counts=[len(b) for b in bins]
    obs=mean([e['gross']-base for e in events]); estimates=[]; exceed=invalid=0
    for draw in plan.draws:
        count=sum(counts[i] for i in draw)
        if not count: invalid+=1; continue
        est=math.fsum(sums[i] for i in draw)/count
        estimates.append(est); exceed += (est-obs+2)>=obs
    if invalid/len(plan.draws)>.01: return {'status':'INFERENCE_BLOCKED_INVALID_RESAMPLES'}
    estimates.sort()
    return {'status':'PASS','p_raw':(1+exceed)/(len(plan.draws)+1),
            'ci_low':percentile(estimates,.025),'ci_high':percentile(estimates,.975),
            'resamples':len(plan.draws),'invalid_zero_count':invalid}

def bh(pvalues):
    ids=sorted(pvalues,key=lambda k:(1 if pvalues[k] is None else pvalues[k],k))
    ans={}; previous=1.; n=len(ids)
    for rank in range(n,0,-1):
        key=ids[rank-1]; p=pvalues[key]
        previous=min(previous,(1 if p is None else p)*n/rank)
        ans[key]=previous if p is not None else None
    return ans

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-dir',required=True); ap.add_argument('--contract',required=True); ap.add_argument('--output',required=True)
    a=ap.parse_args(); rd=Path(a.run_dir); contract_path=Path(a.contract); out=Path(a.output)
    for name,expected in EXPECTED.items():
        actual=sha(rd/name)
        if actual!=expected: raise RuntimeError(f'HASH_MISMATCH:{name}:{actual}')
    if sha(contract_path)!=CONTRACT_SHA: raise RuntimeError('CONTRACT_HASH_MISMATCH')
    manifest=json.loads((rd/'run_manifest.json').read_text())
    if manifest['confirmation_2025_accessed'] or manifest['access_2026_plus']: raise RuntimeError('PROTECTED_DATA_ALREADY_ACCESSED')
    contract=json.loads(contract_path.read_text()); cells=load_cells(rd)
    events,counts=load_events(rd,cells)
    inference={k:[e for e in v if full_inference_event(e)] for k,v in events.items()}
    base=contract['costs']['scout_bands']['BASE']; metrics={}
    for tid,es in inference.items():
        groups=temporal(es,base); months=groups['month']
        years={str(y):mean(groups['year'].get(str(y),[])) for y in YEARS}
        annual=list(years.values()); nets=[e['gross']-base for e in es]
        co=concentration(es,base,contract['stability'])
        metrics[tid]={'gate':sample_gate(es,contract['sample_rules']['scout']),
                      'groups':groups,'years':years,'mean':mean(nets),
                      'gross_mean':mean([e['gross'] for e in es]),
                      'concentration':co,
                      'minimum_temporal_net':min(annual) if all(v is not None for v in annual) else None,
                      'positive_month_fraction':sum(math.fsum(v)>0 for v in months.values())/len(months) if months else None,
                      'positive_quarters':sum(math.fsum(v)>0 for v in groups['quarter'].values()),
                      'lomo_all_positive':all(mean([e['gross']-base for e in es if e['day'].strftime('%Y-%m')!=month])>0 for month in months) if len(months)>1 else None}
    for tid,m in metrics.items():
        adj=neighbors(tid,cells)
        good=[k for k in adj if metrics[k]['gate']['sample_pass'] and metrics[k]['mean'] is not None
              and metrics[k]['mean']>0 and m['mean'] is not None and metrics[k]['mean']>=.5*m['mean']]
        m.update(neighbors=adj,neighbor_count=len(adj),neighbor_fraction=len(good)/len(adj) if adj else None,qualifying_neighbors=good)
    plan=WeekPlan(contract['statistics']['bootstrap_resamples'],contract['statistics']['seed']); boots={}
    for tid,c in cells.items():
        if c['family']!='A_MOMENTUM':continue
        m=metrics[tid]; ratio=m['concentration']['concentration_ratio']
        boots[tid]=bootstrap(inference[tid],base,plan) if m['gate']['sample_pass'] and ratio is not None and ratio<=1 else {'status':'INSUFFICIENT_SAMPLE','p_raw':None,'ci_low':None,'ci_high':None}
    q=bh({tid:boots[tid].get('p_raw') for tid in boots}); targets={}
    for tid in TARGETS:
        m=metrics[tid]; comp,score,veto=score_components(m,contract)
        stability={'positive_month_gate':m['positive_month_fraction']>=2/3,
                   'quarter_gate':m['positive_quarters']>=3,
                   'neighbor_gate':m['neighbor_fraction']>=.75 if m['neighbor_fraction'] is not None else False,
                   'concentration_gate':m['concentration']['concentration_ratio']<=1,
                   'mean_above_2':m['mean']>2,
                   'stress14_mean_at_least_zero':m['gross_mean']>=14,
                   'leave_one_month_out_all_positive':m['lomo_all_positive']}
        targets[tid]={'config':cells[tid],
                      'ledger_trade_count':len(events[tid]),
                      'inference_trade_count':len(inference[tid]),
                      'boundary_week_ledger_only_count':len(events[tid])-len(inference[tid]),
                      'base10_mean_bps':m['mean'],
                      'stress14_mean_bps':m['gross_mean']-14,
                      'severe20_mean_bps':m['gross_mean']-20,
                      'year_base10_mean_bps':m['years'],
                      'sample_gate':m['gate'],
                      'positive_active_month_fraction':m['positive_month_fraction'],
                      'positive_quarters':m['positive_quarters'],
                      'neighbor_ids':m['neighbors'],
                      'qualifying_neighbor_ids':m['qualifying_neighbors'],
                      'neighbor_fraction':m['neighbor_fraction'],
                      'concentration':m['concentration'],
                      'bootstrap':boots[tid],
                      'bh_q':q[tid],
                      'score_components':comp,
                      'scout_score':score,
                      'hard_vetoes':veto,
                      'routing_state':route(score,veto),
                      'stability_gates':stability}
    result={'document_id':'CED_1D_V3_BOUNDARY_WEEK_READJUDICATION_RECEIPT_V0.1',
            'status':'HISTORICAL_VERDICT_PRESERVED__V3_BOUNDARY_WEEK_READJUDICATION_COMPLETE',
            'source':{'raw_discovery_artifact_sha256':RAW_ARTIFACT_SHA,
                      'historical_closeout_sha256':HISTORICAL_CLOSEOUT_SHA,
                      'contract_sha256':CONTRACT_SHA,
                      'member_sha256':EXPECTED,
                      'confirmation_2025_accessed':False,
                      'access_2026_plus':False},
            'boundary_policy':{'signal_completion_week_anchor_equivalent_date':'entry_day = signal_day + 1 day',
                               'inference_start_inclusive':INF_START.isoformat(),
                               'inference_end_exclusive':INF_END.isoformat(),
                               'partial_week_rows_remain_in_ledger':True},
            'targets':targets,
            'summary':{'SCOUT_SURVIVOR':[tid for tid,v in targets.items() if v['routing_state']=='SCOUT_SURVIVOR'],
                       'WATCH':[tid for tid,v in targets.items() if v['routing_state']=='WATCH'],
                       'SHORTLIST_ELIGIBLE':[tid for tid,v in targets.items() if v['routing_state']=='SHORTLIST_ELIGIBLE'],
                       '2025_confirmation_opened':False,
                       'candidate_emitted':False,
                       'promoted_emitted':False},
            'governance':{'post_outcome_tuning':False,'new_cells_admitted':False,'costs_changed':False,
                          '2025_accessed':False,'2026_accessed':False,'live_trading':False,'orders':False,'merge_to_main':False}}
    payload=canonical(result).encode()
    result['fingerprint']=hashlib.sha256(payload).hexdigest()
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
