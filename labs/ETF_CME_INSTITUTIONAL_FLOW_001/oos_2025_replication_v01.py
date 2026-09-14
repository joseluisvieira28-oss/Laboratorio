#!/usr/bin/env python3
import csv, io, json, math, os, re, sys, zipfile
from datetime import datetime, timedelta

SOURCE_DIR=os.environ.get('SOURCE_DIR','source_gate')
OUT=os.environ.get('OUT_DIR','artifacts/etf_cme_oos_2025_replication_v01')
os.makedirs(OUT,exist_ok=True)
PROTOCOL=json.load(open('labs/ETF_CME_INSTITUTIONAL_FLOW_001/oos_2025_protocol_v01.json'))
GATE=json.load(open(os.path.join(SOURCE_DIR,'source_data_gate_receipt.json')))
if GATE.get('status')!='SOURCE_DATA_GATE_PASS': raise SystemExit('source gate not PASS')
if GATE.get('year_2026_accessed') is not False: raise SystemExit('2026 contamination in source gate')

# CFTC rows including one 2024 prior-state observation.
cftc_path=os.path.join(SOURCE_DIR,'cftc_133741_2024prior_2025.csv')
rows=list(csv.DictReader(open(cftc_path,encoding='utf-8-sig')))
parsed=[]
for r in rows:
    d=datetime.fromisoformat(r['report_date_as_yyyy_mm_dd'].replace('Z','+00:00')).date()
    oi=float(r['open_interest_all']); nl=float(r['noncomm_positions_long_all']); ns=float(r['noncomm_positions_short_all'])
    parsed.append((d,oi,nl,ns))
parsed.sort()

# BTC 2025 daily opens from exact source-gate bytes.
btc={}
for month in range(1,13):
    ym=f'2025-{month:02d}'
    zp=os.path.join(SOURCE_DIR,f'BTCUSDT-1d-{ym}.zip')
    with zipfile.ZipFile(zp) as z:
        name=z.namelist()[0]
        for row in csv.reader(io.StringIO(z.read(name).decode('utf-8'))):
            if not row: continue
            ts=int(row[0]); sec=ts/1_000_000 if ts>10**14 else ts/1000
            d=datetime.utcfromtimestamp(sec).date()
            if d.year!=2025: raise SystemExit(f'protected period BTC row {d}')
            btc[d]=float(row[1])

obs=[]
prev=None
for d,oi,nl,ns in parsed:
    net=nl-ns
    if prev is None:
        prev=(d,net); continue
    if d.year!=2025:
        prev=(d,net); continue
    signal=(net-prev[1])/oi
    entry=d+timedelta(days=8)
    exitd=entry+timedelta(days=7)
    # Exclude BEFORE outcome lookup if any part would require 2026.
    if entry.year!=2025 or exitd.year!=2025:
        prev=(d,net); continue
    if entry not in btc or exitd not in btc: raise SystemExit(f'missing BTC price {entry} or {exitd}')
    fwd=btc[exitd]/btc[entry]-1.0
    pos=1 if signal>0 else (-1 if signal<0 else 0)
    gross=pos*fwd
    base=gross-0.001 if pos else 0.0
    stress=gross-0.002 if pos else 0.0
    obs.append({'as_of':d,'signal':signal,'entry':entry,'exit':exitd,'forward_return':fwd,'position':pos,'gross':gross,'base_net':base,'stress_net':stress})
    prev=(d,net)

n=len(obs)
if n<40: raise SystemExit(f'insufficient evaluable weeks: {n}')

# OLS y = alpha + beta*x with Newey-West HAC lag 2, pure stdlib.
x=[o['signal'] for o in obs]; y=[o['forward_return'] for o in obs]
sx=sum(x); sy=sum(y); sxx=sum(v*v for v in x); sxy=sum(a*b for a,b in zip(x,y))
det=n*sxx-sx*sx
alpha=(sxx*sy-sx*sxy)/det
beta=(n*sxy-sx*sy)/det
res=[yy-alpha-beta*xx for xx,yy in zip(x,y)]
# inv(X'X)
inv=[[sxx/det,-sx/det],[-sx/det,n/det]]
S=[[0.0,0.0],[0.0,0.0]]
X=[[1.0,v] for v in x]
for t in range(n):
    e2=res[t]*res[t]
    for i in range(2):
        for j in range(2): S[i][j]+=X[t][i]*X[t][j]*e2
L=2
for lag in range(1,L+1):
    w=1-lag/(L+1)
    for t in range(lag,n):
        c=res[t]*res[t-lag]
        for i in range(2):
            for j in range(2):
                S[i][j]+=w*c*(X[t][i]*X[t-lag][j]+X[t-lag][i]*X[t][j])
T=[[sum(inv[i][k]*S[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
C=[[sum(T[i][k]*inv[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
se_beta=math.sqrt(max(C[1][1],0.0)); z=beta/se_beta if se_beta>0 else float('inf')
p_one=0.5*math.erfc(z/math.sqrt(2))

def pf(vals):
    pos=sum(v for v in vals if v>0); neg=-sum(v for v in vals if v<0)
    return float('inf') if neg==0 and pos>0 else (pos/neg if neg>0 else 0.0)

gross=[o['gross'] for o in obs]; base=[o['base_net'] for o in obs]; stress=[o['stress_net'] for o in obs]
positive_gross=[max(v,0.0) for v in gross]; total_pos=sum(positive_gross)
max_trade_share=(max(positive_gross)/total_pos) if total_pos>0 else 1.0
criteria={
 'minimum_40_evaluable_weeks':n>=40,
 'base_net_mean_positive':sum(base)/n>0,
 'base_profit_factor_gte_1':pf(base)>=1.0,
 'max_single_trade_share_positive_gross_pnl_le_0_40':max_trade_share<=0.40,
 'clean_provenance':True,
 'no_leakage':True,
 'no_fatal_execution_or_data_pathology':True
}
path2=all(criteria.values())
classification='OOS_PATH2_PASS' if path2 else 'OOS_PATH2_FAIL'
if not path2 and n>=40 and ((sum(base)/n)<=0 or pf(base)<1.0): classification='OOS_PATH2_FAIL_NEGATIVE_ECONOMICS'
receipt={
 'lab':'ETF-CME-INSTFLOW-001','replication_id':'ETF-CME-INSTFLOW-001-OOS-2025-V0.1','stage':'INDEPENDENT_2025_OOS_ONE_SHOT','classification':classification,'path2_pass':path2,
 'source_gate_run_id':34814938876,'source_gate_cftc_sha256':GATE['cftc']['raw_sha256'],'source_gate_btc_combined_archive_sha256':GATE['btc']['combined_archive_sha256'],
 'evaluable_weeks':n,'beta':beta,'hac_lag_weeks':2,'hac_se_beta':se_beta,'one_sided_hac_p_diagnostic':p_one,
 'base_cost_bps':10,'base_net_mean':sum(base)/n,'base_profit_factor':pf(base),'stress_cost_bps':20,'stress_net_mean':sum(stress)/n,'stress_profit_factor':pf(stress),
 'max_single_trade_share_positive_gross_pnl':max_trade_share,'criteria':criteria,
 'first_as_of':obs[0]['as_of'].isoformat(),'last_as_of':obs[-1]['as_of'].isoformat(),'first_entry':obs[0]['entry'].isoformat(),'last_exit':obs[-1]['exit'].isoformat(),
 'year_2025_accessed':True,'year_2026_accessed':False,'live_trading':False,'exchange_mutation':False,'post_outcome_tuning':False
}
json.dump(receipt,open(os.path.join(OUT,'oos_2025_closeout.json'),'w'),indent=2,sort_keys=True)
with open(os.path.join(OUT,'oos_2025_observations.csv'),'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['as_of','signal','entry','exit','forward_return','position','gross','base_net','stress_net']); w.writeheader()
    for o in obs: w.writerow({k:(v.isoformat() if hasattr(v,'isoformat') else v) for k,v in o.items()})
print(json.dumps(receipt,indent=2,sort_keys=True))
