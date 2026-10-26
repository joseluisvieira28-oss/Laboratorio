#!/usr/bin/env python3
"""Frozen descriptive economics/power audit for uploaded 2022-23 Fusion CSV.
No network, no market orders, no outcome tuning, no holdout access.
Expected SHA-256 pins the already-observed CSV; 'power' is planning-only.
"""
import argparse, csv, hashlib, json, math
from datetime import date, timedelta
from pathlib import Path

EXPECTED_SHA='38b042c4d439f8ddf2f6bc5665b24608345a765dddbc00b2f0d4f767729ad8d3'
COSTS=(4.,7.,10.,12.,14.,16.,20.,30.)  # Descriptive fixed-cost sensitivity, not a pick list
ALPHA_TWO_SIDED_Z=1.959963984540054
POWER80_Z=.8416212335729143

class AuditError(ValueError):pass

def load(path):
    raw=path.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA:raise AuditError('CSV_SHA256_MISMATCH: refuse changed sample')
    rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    if len(rows)!=730:raise AuditError('EXPECTED_730_DAYS')
    out=[]
    for i,r in enumerate(rows):
        exp=(date(2022,1,1)+timedelta(days=i)).isoformat()
        if r['date']!=exp:raise AuditError('CALENDAR_OR_ORDER_MISMATCH:'+exp)
        a=int(r['avax20']);b=int(r['btc20']);g=float(r['gross_bps'])
        if a not in (-1,0,1) or b not in (-1,0,1) or not math.isfinite(g):
            raise AuditError('NONFINITE_OR_INVALID_STATE:'+exp)
        masks=(bool(a),bool(a and a==b),bool(a and a==-b))
        if tuple(r[x] for x in ('baseline_trade','fusion_trade','opposite_context_trade'))!=tuple(str(m) for m in masks):
            raise AuditError('MASK_MISMATCH:'+exp)
        if sum(masks[1:]) != int(masks[0]) and b!=0:raise AuditError('PARTITION_MISMATCH:'+exp)
        out.append({'date':exp,'year':int(exp[:4]),'side':a,'gross':g,'base':masks[0], 'fusion':masks[1],'excluded':masks[2]})
    return digest,out

def stats(rows,flag,cost):
    pnl=[(r['gross']-cost) if r[flag] else 0. for r in rows]
    n=sum(r[flag] for r in rows)
    return {'trades':n,'sum_bps':round(sum(pnl),5), 'calendar_mean_bps':round(sum(pnl)/len(rows),6),
            'trade_mean_bps':round(sum(pnl)/n,6) if n else None}

def nw_long_run_sd(values,L=30):
    n=len(values)
    mean=sum(values)/n; z=[v-mean for v in values]
    gamma0=sum(t*t for t in z)/n
    long=gamma0
    for lag in range(1,min(L,n-1)+1):
        gamma=sum(z[i]*z[i-lag] for i in range(lag,n))/n
        long+=2*(1-lag/(L+1))*gamma
    return math.sqrt(max(0.,long))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--csv',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=Path('FUSION_ECONOMIC_POWER_V05.json'))
    args=ap.parse_args()
    digest,rows=load(args.csv)
    fused=[r for r in rows if r['fusion']]
    gross_mean=sum(r['gross'] for r in fused)/len(fused)
    annual={}
    for yr in (2022,2023):
        rs=[r for r in rows if r['year']==yr]
        ff=[r for r in rs if r['fusion']]
        annual[str(yr)]={'fused_trades':len(ff), 'fused_gross_mean_per_trade_bps':round(sum(r['gross'] for r in ff)/len(ff),6),
                         'BASE14':stats(rs,'fusion',14),'STRESS20':stats(rs,'fusion',20),
                         'incremental_BASE14_bps_per_day':round(stats(rs,'fusion',14)['calendar_mean_bps']-stats(rs,'base',14)['calendar_mean_bps'],6)}
    fee_cases={}
    for name,fee in [('maker_maker_fee_only',4.),('maker_taker_fee_only',7.),('taker_taker_fee_only',10.)]:
        fee_cases[name]={'roundtrip_fee_bps':fee,'max_other_cost_bps_to_zero':round(gross_mean-fee,6),
                         'caveat':'Contemporary Binance regular USDT rates, not historic 2022-23 nor MEXC; fill path unproven'}
    sensitivity={str(int(c)):stats(rows,'fusion',c) for c in COSTS}
    y_fusion20=[r['gross']-20 if r['fusion'] else 0. for r in rows]
    within_sd={str(year):nw_long_run_sd([y_fusion20[i] for i,r in enumerate(rows) if r['year']==year],30) for year in (2022,2023)}
    sigma_pooled=nw_long_run_sd(y_fusion20,30)
    sigma_worst=max(sigma_pooled,*within_sd.values())
    z=ALPHA_TWO_SIDED_Z+POWER80_Z
    target=[2.,5.]
    power={'model':'Gaussian HAC approximate 2-sided alpha 5%, 80% power; lag 30; nonconfirmatory planning based on exposed outcomes',
          'sigma_LRV_bps_per_sqrt_day':{'pooled':round(sigma_pooled,4),'by_year':{k:round(v,4) for k,v in within_sd.items()},'worst_case':round(sigma_worst,4)},
          'target_positive_net_bps_per_calendar_day':{str(int(d)):{'required_calendar_days_pooled':math.ceil((z*sigma_pooled/d)**2),
                                                                     'required_calendar_days_worst':math.ceil((z*sigma_worst/d)**2)} for d in target},
          'detectable_positive_net_bps_day_if_365_days_worst':round(z*sigma_worst/math.sqrt(365),4),
          'detectable_positive_net_bps_day_if_730_days_worst':round(z*sigma_worst/math.sqrt(730),4),
          'limitations':'2022-23 pooled/annual data already exposed, high regime drift and tails; parametric planning is not prospective evidence, power gate not passed'}
    report={'identity':'AVAX20_BTC20_V05_COST_BOUND_POWER_PLANNING_2022_2023',
            'status':'DESCRIPTIVE_COST_AUDIT_ONLY_NOT_LIVE_READY',
            'input_sha256':digest,'dates':['2022-01-01','2023-12-31'], 'protected_holdouts_touched':False,
            'positive_gross_ceiling_roundtrip_bps':round(gross_mean,6),
            'gross_no_cost':stats(rows,'fusion',0),'annual':annual,
            'contemporary_regular_binance_USDT_fee_geometry':fee_cases,
            'cost_sensitivity_fixed_bps_roundtrip':sensitivity,
            'power_planning':power,
            'funding':'01:00-to-02:00 UTC interval ordinarily crosses no 00/08/16 or 00/04/08/12/16/20 settlement; historical symbol exception and realized account funding not independently audited',
            'execution':'OHLC open prices not executable quotes; spread, slippage, fill probability, queue, latency, funding/capacity not measured',
            'final':'NO INDEPENDENT ECONOMIC EDGE; STRESS20 NEGATIVE; FAIL_CLOSED'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(args.output),'gross_ceiling':report['positive_gross_ceiling_roundtrip_bps'], 'annual':annual,
                      'power':power},indent=2))

if __name__=='__main__':main()
