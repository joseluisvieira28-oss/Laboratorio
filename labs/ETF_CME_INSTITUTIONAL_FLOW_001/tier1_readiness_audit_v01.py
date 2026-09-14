#!/usr/bin/env python3
import csv, json, math, os, statistics

IN='oos_input/oos_2025_observations.csv'
OUT='artifacts/etf_cme_tier1_readiness_v01'
os.makedirs(OUT, exist_ok=True)
rows=[]
with open(IN,newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f):
        rows.append({k:(float(v) if k in {'signal','forward_return','position','gross','base_net','stress_net'} else v) for k,v in r.items()})
if len(rows)!=50:
    raise SystemExit(f'expected 50 rows, got {len(rows)}')

def pf(vals):
    pos=sum(v for v in vals if v>0)
    neg=-sum(v for v in vals if v<0)
    return float('inf') if neg==0 else pos/neg

def max_dd(vals):
    c=0.0; peak=0.0; m=0.0
    for v in vals:
        c+=v; peak=max(peak,c); m=min(m,c-peak)
    return m

gross=[r['gross'] for r in rows]
base=[r['base_net'] for r in rows]
stress=[r['stress_net'] for r in rows]
pos_gross=[v for v in gross if v>0]
base_mean=statistics.fmean(base)
stress_mean=statistics.fmean(stress)
base_pf=pf(base); stress_pf=pf(stress)
share=max(pos_gross)/sum(pos_gross)
cum=sum(base); dd=max_dd(base)
loo=[statistics.fmean(base[:i]+base[i+1:]) for i in range(len(base))]
blocks=[]
for i in range(0,50,10):
    vals=base[i:i+10]
    blocks.append({'block':i//10+1,'start_as_of':rows[i]['as_of'],'end_as_of':rows[i+9]['as_of'],'mean_base_net':statistics.fmean(vals),'sum_base_net':sum(vals),'positive_mean':statistics.fmean(vals)>0})
pos_blocks=sum(b['positive_mean'] for b in blocks)
break_even=statistics.fmean(gross)*10000
criteria={
 'expected_50_observations':len(rows)==50,
 'base_net_mean_gt_0':base_mean>0,
 'base_pf_gte_1':base_pf>=1,
 'stress20_net_mean_gte_0':stress_mean>=0,
 'stress20_pf_gte_1':stress_pf>=1,
 'max_single_trade_positive_gross_share_lte_0_40':share<=0.40,
 'additive_cumulative_base_net_gte_0_05':cum>=0.05,
 'max_additive_drawdown_abs_lt_0_50':abs(dd)<0.50,
 'leave_one_trade_out_min_base_net_mean_gt_0':min(loo)>0,
 'positive_10_trade_blocks_gte_3':pos_blocks>=3,
 'break_even_roundtrip_cost_bps_gte_20':break_even>=20.0,
}
classification='READINESS_PASS' if all(criteria.values()) else 'READINESS_FAIL'
receipt={
 'lab':'ETF-CME-INSTFLOW-001','study_id':'ETF-CME-INSTFLOW-001-TIER1-READINESS-V0.1','stage':'POST_OOS_EXECUTION_RISK_DIAGNOSTIC_ONLY',
 'classification':classification,'tier_before':'TIER 2 — PROMOTED CANDIDATE — FRAGILE','tier_after':'UNCHANGED',
 'observations':len(rows),'base_net_mean':base_mean,'base_profit_factor':base_pf,'stress20_net_mean':stress_mean,'stress20_profit_factor':stress_pf,
 'max_single_trade_share_positive_gross_pnl':share,'additive_cumulative_base_net':cum,'max_additive_drawdown':dd,
 'leave_one_out_min_base_net_mean':min(loo),'positive_10_trade_blocks':pos_blocks,'blocks':blocks,
 'break_even_roundtrip_cost_bps':break_even,'criteria':criteria,
 'tier1_promotion_from_this_study':False,'new_market_outcomes_accessed':False,'year_2026_accessed':False,
 'live_trading':False,'exchange_mutation':False,'post_outcome_optimization':False,
 'scientific_note':'READINESS_PASS only supports deciding whether a future independent holdout is worth spending; it is not Tier 1 evidence by itself.'
}
with open(os.path.join(OUT,'tier1_readiness_receipt.json'),'w',encoding='utf-8') as f: json.dump(receipt,f,indent=2,sort_keys=True)
print(json.dumps(receipt,indent=2,sort_keys=True))
