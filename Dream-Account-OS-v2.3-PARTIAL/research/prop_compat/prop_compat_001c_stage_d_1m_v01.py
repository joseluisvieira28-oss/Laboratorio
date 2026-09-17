from __future__ import annotations
import hashlib, json, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from research.prop_compat import prop_compat_001b_kraken_proxy_runner_v01 as v1

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research'/'local_data'/'prop_compat_001c_stage_d'
START_MS=v1.START_MS; END_MS=v1.END_MS; MIN_MS=v1.MIN_MS; N=v1.N; SYM=v1.SYM
PLANS={'STARTER':(10.0,6.0),'INTERMEDIATE':(12.0,5.0),'ADVANCED':(9.0,3.0)}
RISKS=[.10,.15,.20,.25,.30]
PROFILES={
 'SEVERE':{'rt':.50,'carry_mult':1.5,'gap_r':.50},
 'EXTREME':{'rt':.75,'carry_mult':2.0,'gap_r':1.00},
}

def iso(j):
    return datetime.fromtimestamp((START_MS+int(j)*MIN_MS)/1000,tz=timezone.utc).isoformat().replace('+00:00','Z')

def scenarios():
    out=[]
    for plan,(target,mdd) in PLANS.items():
      for risk_pct in RISKS:
       for profile,p in PROFILES.items():
        half=(p['rt']/100.0)/2.0
        base=dict(plan=plan,target=100+target,mdd_floor=100-mdd,risk=risk_pct/100.0,profile=profile,en=half,xx=half,carry_mult=p['carry_mult'],gap_r=p['gap_r'])
        out.append({**base,'carry':'LEGAL','phase':-1})
        for phase in range(240): out.append({**base,'carry':'SUPPORT','phase':phase})
    return out

def is_stop(r): return 'STOP' in str(r['exit_reason']).upper()

def simulate(rows,op,hi,lo,cl):
    sc=scenarios(); M=len(sc)
    bal=np.full(M,100.0); daily=np.full(M,97.0); decided=np.zeros(M,bool); passed=np.zeros(M,bool); breached=np.zeros(M,bool); ambig=np.zeros(M,bool)
    decision=np.full(M,-1,np.int64); reason=np.array(['']*M,dtype=object)
    risk=np.array([x['risk'] for x in sc]); target=np.array([x['target'] for x in sc]); mdd=np.array([x['mdd_floor'] for x in sc]); en=np.array([x['en'] for x in sc]); xx=np.array([x['xx'] for x in sc]); cm=np.array([x['carry_mult'] for x in sc]); gap=np.array([x['gap_r'] for x in sc]); legal=np.array([x['carry']=='LEGAL' for x in sc]); phase=np.array([x['phase'] for x in sc],dtype=np.int16)
    qty=np.zeros((6,M)); entpx=np.zeros(6); active=[None]*6
    entries=defaultdict(list); exits=defaultdict(list)
    for r in rows:
        entries[(r['entry_time']-START_MS)//MIN_MS].append(r); exits[(r['exit_time']-START_MS)//MIN_MS].append(r)
    first=min(entries)
    max_close_dd=np.zeros(M); max_low_dd=np.zeros(M); max_daily_margin=np.zeros(M); max_total_notional=np.zeros(M); max_conc=np.zeros(M,np.int16)
    ever_low=np.zeros(M,bool); ever_high=np.zeros(M,bool); first_high=np.full(M,-1,np.int64); first_low=np.full(M,-1,np.int64)
    total_exec_cost=np.zeros(M); total_carry=np.zeros(M); total_gap=np.zeros(M)
    def equity(prices):
        pnl=np.zeros(M)
        for si in range(6):
            if active[si] is not None: pnl += qty[si]*(prices[si]-entpx[si])
        return bal+pnl
    def freeze(mask):
        if mask.any(): qty[:,mask]=0.0
    for j in range(first,N):
        live=~decided
        if not live.any(): break
        mod=j%1440; pxopen=op[:,j]
        current=np.zeros(M)
        for si in range(6):
            if active[si] is not None: current += np.abs(qty[si])*pxopen[si]
        mask=live & legal & (mod==0)
        if mask.any():
            debit=current[mask]*0.00033*cm[mask]; bal[mask]-=debit; total_carry[mask]+=debit
        mask=live & (~legal) & (phase==(mod%240))
        if mask.any():
            debit=current[mask]*0.000055*cm[mask]; bal[mask]-=debit; total_carry[mask]+=debit
        if mod==30: daily[live]=bal[live]-3.0
        for r in sorted(exits.get(j,[]),key=lambda x:x['symbol']):
            si=SYM[r['symbol']]; mask=live & (qty[si]!=0)
            if mask.any():
                ep=float(r['exit_price']); q=np.abs(qty[si,mask]); pnl=qty[si,mask]*(ep-entpx[si]); fee=q*ep*xx[mask]
                bal[mask]+=pnl; bal[mask]-=fee; total_exec_cost[mask]+=fee
                if is_stop(r):
                    extra=q*float(r['entry_price'])*float(r['initial_risk_fraction'])*gap[mask]
                    bal[mask]-=extra; total_gap[mask]+=extra
                qty[si,mask]=0.0
            active[si]=None; entpx[si]=0.0
        for r in sorted(entries.get(j,[]),key=lambda x:x['symbol']):
            si=SYM[r['symbol']]; eq=equity(pxopen); mask=live; amt=eq[mask]*risk[mask]; notion=amt/float(r['initial_risk_fraction']); qty[si,mask]=notion/float(r['entry_price']); fee=notion*en[mask]; bal[mask]-=fee; total_exec_cost[mask]+=fee; entpx[si]=float(r['entry_price']); active[si]=r
        total=np.zeros(M); conc=np.zeros(M,np.int16)
        for si in range(6): total+=np.abs(qty[si])*pxopen[si]; conc+=(qty[si]!=0).astype(np.int16)
        max_total_notional[live]=np.maximum(max_total_notional[live],total[live]); max_conc[live]=np.maximum(max_conc[live],conc[live])
        eqc=equity(cl[:,j]); eqh=equity(hi[:,j]); eql=equity(lo[:,j])
        max_close_dd[live]=np.maximum(max_close_dd[live],100-eqc[live]); max_low_dd[live]=np.maximum(max_low_dd[live],100-eql[live]); max_daily_margin[live]=np.maximum(max_daily_margin[live],daily[live]-eqc[live])
        low=live & ((eql<=mdd)|(eql<=daily)); new=low & (~ever_low); first_low[new]=j; ever_low|=low
        high=live & (eqh>=target); new=high & (~ever_high); first_high[new]=j; ever_high|=high
        tmask=live & (eqc>=target)
        if tmask.any():
            safe=tmask & (~ever_low); passed[safe]=1; decided[safe]=1; decision[safe]=j; reason[safe]='TARGET_CLOSE_ROBUST_TO_LOW_BOUND'; freeze(safe)
            unc=tmask & ever_low; ambig[unc]=1; decided[unc]=1; decision[unc]=j; reason[unc]='TARGET_CLOSE_AFTER_INTRAMINUTE_BREACH_LOWER_BOUND'; freeze(unc)
        live=~decided; bmask=live & ((eqc<=mdd)|(eqc<=daily))
        if bmask.any():
            unc=bmask & ever_high; ambig[unc]=1; decided[unc]=1; decision[unc]=j; reason[unc]='BREACH_CLOSE_AFTER_TARGET_INTRAMINUTE_UPPER_BOUND'; freeze(unc)
            ob=bmask & (~ever_high); breached[ob]=1; decided[ob]=1; decision[ob]=j; reason[ob]=np.where(eqc[ob]<=mdd[ob],'MDD_CLOSE_BREACH','MDL_CLOSE_BREACH'); freeze(ob)
    out=[]
    for k,x in enumerate(sc):
        if passed[k]: label='ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED'
        elif breached[k]: label='OBVIOUS_PROXY_BREACH'
        elif ambig[k] or ever_high[k]: label='AMBIGUITY_MATERIAL'
        else: label='PROXY_INSUFFICIENT_HISTORY_NO_DECISION'
        out.append({**x,'classification':label,'decision_time_utc':None if decision[k]<0 else iso(decision[k]),'reason':str(reason[k]),'ending_balance':float(bal[k]),'max_close_drawdown_pct_initial':float(max_close_dd[k]),'max_low_bound_drawdown_pct_initial':float(max_low_dd[k]),'max_daily_close_breach_margin_pct_initial':float(max_daily_margin[k]),'max_total_open_notional_multiple_initial':float(max_total_notional[k]/100.0),'max_concurrent_positions':int(max_conc[k]),'total_execution_cost_units':float(total_exec_cost[k]),'total_carry_cost_units':float(total_carry[k]),'total_gap_surcharge_units':float(total_gap[k]),'target_upper_bound_possible':bool(ever_high[k]),'first_target_upper_bound_time_utc':None if first_high[k]<0 else iso(first_high[k]),'breach_lower_bound_possible':bool(ever_low[k]),'first_breach_lower_bound_time_utc':None if first_low[k]<0 else iso(first_low[k])})
    return out

def summarize(results,archives):
    groups=defaultdict(list)
    for r in results: groups[(r['plan'],r['risk'],r['profile'])].append(r)
    cells=[]; cc=defaultdict(int)
    for key,rs in sorted(groups.items()):
        legal=[r for r in rs if r['carry']=='LEGAL'][0]; support=[r for r in rs if r['carry']=='SUPPORT']; counts=defaultdict(int)
        for r in support: counts[r['classification']]+=1
        if legal['classification']=='ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED' and counts['ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED']==240: cell='ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED'
        elif legal['classification']=='OBVIOUS_PROXY_BREACH' and counts['OBVIOUS_PROXY_BREACH']==240: cell='OBVIOUS_PROXY_BREACH'
        elif legal['classification']=='PROXY_INSUFFICIENT_HISTORY_NO_DECISION' or counts['PROXY_INSUFFICIENT_HISTORY_NO_DECISION']>0: cell='PROXY_INSUFFICIENT'
        else: cell='AMBIGUITY_MATERIAL'
        cc[cell]+=1
        cells.append({'plan':key[0],'risk_pct_per_1R':round(key[1]*100,2),'profile':key[2],'cell_classification':cell,'legal_daily':{k:legal[k] for k in ['classification','decision_time_utc','reason','ending_balance','max_close_drawdown_pct_initial','max_low_bound_drawdown_pct_initial','max_daily_close_breach_margin_pct_initial','max_total_open_notional_multiple_initial','max_concurrent_positions','total_execution_cost_units','total_carry_cost_units','total_gap_surcharge_units']},'support_4h_phase_counts':dict(counts),'support_4h_decision_time_range_utc':[min((r['decision_time_utc'] for r in support if r['decision_time_utc']),default=None),max((r['decision_time_utc'] for r in support if r['decision_time_utc']),default=None)]})
    return {'document_id':'PROP_COMPAT_001C_DH03_KRAKEN_STAGE_D_1M_RECEIPT_V0.1','campaign_id':'PROP-COMPAT-001C','status':'STAGE_D_1M_SEVERE_EXTREME_COMPLETE','setup_id':'DH-03-HO1','decisional_authority':False,'source_validation':{'binance_1m_archives_downloaded_and_hash_validated':archives,'access_2025':False,'access_2026':False},'profiles':PROFILES,'base_cells':30,'support_phase_paths':7200,'cell_classification_counts':dict(cc),'cells':cells,'governance':{'aggressive_research':True,'no_best_plan_selection':True,'no_best_risk_selection':True,'post_outcome_tuning':False,'challenge_purchase':False,'live_trading':False,'merge_to_main':False}}

def main(argv):
    if len(argv)!=3: raise SystemExit('usage: stage_d SOURCE_ARTIFACT_DIR EXECUTION_ARTIFACT_DIR')
    src=Path(argv[1]); ex=Path(argv[2]); OUT.mkdir(parents=True,exist_ok=True)
    rows=v1.load_ledger(ex); op,hi,lo,cl,archives=v1.load_sources(src); receipt=summarize(simulate(rows,op,hi,lo,cl),archives); raw=json.dumps(receipt,sort_keys=True,separators=(',',':')).encode(); receipt['fingerprint']=hashlib.sha256(raw).hexdigest(); p=OUT/'PROP_COMPAT_001C_DH03_KRAKEN_STAGE_D_1M_RECEIPT_V0.1.json'; p.write_text(json.dumps(receipt,indent=2,sort_keys=True)); print(json.dumps({'status':receipt['status'],'cell_classification_counts':receipt['cell_classification_counts'],'fingerprint':receipt['fingerprint']},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main(sys.argv))
