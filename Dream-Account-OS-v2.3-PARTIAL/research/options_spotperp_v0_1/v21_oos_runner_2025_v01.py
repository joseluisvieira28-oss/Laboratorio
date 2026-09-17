#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,datetime as dt,gzip,hashlib,io,json,math,statistics,zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import discovery_runner_v01 as parent
import risk_scaling_v21_runner as v21

LAB_ID='OPTIONS-SPOTPERP-001';VERSION='V2.1-OOS-2025-V0.1'
AUTHORITY_COMMIT='bc7d397f7d6d896a0ef3fc25b93e4678e64f8ae2'
START=dt.date(2025,1,1);LAST_SIGNAL=dt.date(2025,12,29);END=dt.date(2025,12,31)
BASE_COST=10.0;STRESS_COST=20.0;MIN_ENTERED=50


def sha(p:Path)->str:
    h=hashlib.sha256();
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()

def med(xs):return float(statistics.median(xs))
def ts_ms(v:int)->int:
    if 1_000_000_000_000<=v<10_000_000_000_000:return v
    if 1_000_000_000_000_000<=v<10_000_000_000_000_000:return v//1000
    raise RuntimeError(f'OOS_BLOCKED_SOURCE_PROVENANCE: unexpected Binance timestamp {v}')

def load_manifest(root:Path):
    mp=root/'v21_oos_source_manifest.json';rp=root/'v21_oos_source_audit_report.json'
    if not mp.exists() or not rp.exists():raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: source receipts missing')
    m=json.loads(mp.read_text());r=json.loads(rp.read_text())
    if m.get('status')!='SOURCE_AUDIT_PASS' or r.get('status')!='SOURCE_AUDIT_PASS':raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: source gate not PASS')
    if m.get('authority_commit')!=AUTHORITY_COMMIT:raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: authority mismatch')
    if m.get('oos_2025_authorized') is not True or m.get('oos_2025_accessed') is not True:raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: 2025 source receipt missing')
    if m.get('year_2026_accessed') is not False:raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: 2026 source flag')
    for k in ('skew_values_computed','signals_computed','forward_returns_computed','pnl_computed'):
        if m.get(k) is not False:raise RuntimeError(f'OOS_BLOCKED_SOURCE_PROVENANCE: premature outcome flag {k}')
    return m,r

def build_signal(root:Path,m):
    inst=defaultdict(lambda:defaultdict(list));side={}
    for e in m['raw_pages']:
        p=root/'raw'/e['page']
        if not p.exists() or sha(p)!=e['sha256']:raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: Deribit integrity')
        obj=json.loads(gzip.decompress(p.read_bytes()).decode());rows=obj.get('result',{}).get('trades')
        if not isinstance(rows,list):raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: invalid Deribit payload')
        for row in rows:
            d=dt.datetime.fromtimestamp(int(row['timestamp'])/1000,tz=dt.timezone.utc).date()
            if d<START or d>END:raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: Deribit outside 2025')
            try:expiry,strike,s=parent.parse_instrument(str(row['instrument_name']));iv=float(row['iv']);idx=float(row['index_price'])
            except Exception:continue
            if not(math.isfinite(iv) and iv>0 and math.isfinite(idx) and idx>0):continue
            dte=(expiry-d).days;mm=strike/idx
            if not(30<=dte<=120):continue
            if not((s=='C' and 1.05<=mm<=1.20) or (s=='P' and 0.80<=mm<=0.95)):continue
            name=str(row['instrument_name']);inst[d][name].append(iv);side[name]=s
    sig={}
    for d,names in inst.items():
        calls=[];puts=[]
        for name,vals in names.items():(calls if side[name]=='C' else puts).append(med(vals))
        if len(calls)>=5 and len(puts)>=5:sig[d]=med(calls)-med(puts)
    return sig

def load_btc(root:Path,m):
    out={};entries=m.get('btc_price_raw_archives',[])
    if len(entries)!=57:raise RuntimeError(f'OOS_BLOCKED_SOURCE_PROVENANCE: expected 57 BTC archives got {len(entries)}')
    for e in entries:
        p=root/'raw_binance_btcusdt_1d'/e['file']
        if not p.exists() or sha(p)!=e['sha256']:raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: BTC integrity')
        with zipfile.ZipFile(p) as zf:
            members=[x for x in zf.namelist() if not x.endswith('/')]
            if len(members)!=1:raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: BTC zip members')
            with zf.open(members[0]) as fh:
                for row in csv.reader(io.TextIOWrapper(fh,encoding='utf-8')):
                    if not row:continue
                    d=dt.datetime.fromtimestamp(ts_ms(int(row[0]))/1000,tz=dt.timezone.utc).date()
                    if d.year>=2026:raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: attempted 2026 BTC')
                    op=float(row[1]);cl=float(row[4])
                    if not all(math.isfinite(x) and x>0 for x in (op,cl)):raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: invalid BTC OHLC')
                    if d in out:raise RuntimeError(f'OOS_BLOCKED_SOURCE_PROVENANCE: duplicate BTC day {d}')
                    out[d]={'open':op,'close':cl}
    return out

def maxdd(net):
    wealth=peak=1.0;mdd=0.0
    for x in net:
        wealth*=math.exp(x/10000);peak=max(peak,wealth);mdd=min(mdd,wealth/peak-1)
    return mdd

def metrics(rows,cost):
    entered=[r for r in rows if r['position']!=0 and r['weight']>0]
    gross=[r['unscaled_gross_bps']*r['weight'] for r in entered];net=[g-cost*r['weight'] for g,r in zip(gross,entered)]
    pos=sum(x for x in net if x>0);neg=-sum(x for x in net if x<0);pf=pos/neg if neg>0 else (float('inf') if pos>0 else 0.0)
    qs={};positive={}
    for q in range(1,5):
        rr=[r for r in entered if ((r['signal_date'].month-1)//3+1)==q];gg=[r['unscaled_gross_bps']*r['weight'] for r in rr];nn=[g-cost*r['weight'] for g,r in zip(gg,rr)]
        qs[str(q)]={'n':len(rr),'mean_weight':sum(r['weight'] for r in rr)/len(rr) if rr else None,'gross_pnl_bps':sum(gg),'net_pnl_bps':sum(nn),'net_mean_bps':sum(nn)/len(nn) if nn else None};positive[str(q)]=max(0.0,sum(gg))
    total_pos=sum(positive.values());share=max(positive.values())/total_pos if total_pos>0 else 1.0;tw=sum(r['weight'] for r in entered)
    return {'entered_scaled_trades':len(entered),'average_executed_notional':tw/len(entered) if entered else 0.0,'total_executed_notional_units':tw,'long_count':sum(r['position']>0 for r in entered),'short_count':sum(r['position']<0 for r in entered),'gross_mean_bps_per_parent_opportunity':sum(gross)/len(gross) if gross else None,'net_mean_bps_per_parent_opportunity':sum(net)/len(net) if net else None,'profit_factor':pf,'cumulative_net_return':math.exp(sum(x/10000 for x in net))-1 if net else 0.0,'max_drawdown':maxdd(net),'win_rate':sum(x>0 for x in net)/len(net) if net else None,'quarters':qs,'single_quarter_max_share_positive_gross_pnl':share}
def sanitize(x:Any)->Any:
    if isinstance(x,float) and not math.isfinite(x):return None
    if isinstance(x,dict):return {k:sanitize(v) for k,v in x.items()}
    if isinstance(x,list):return [sanitize(v) for v in x]
    return x

def run(root:Path,out:Path):
    m,audit=load_manifest(root);sig=build_signal(root,m);btc=load_btc(root,m)
    # Exact V2.1 causal state: RV20 and expanding median begin at the original 2021-04 start and continue through 2025.
    rv=v21.rv20_series(btc);weights=v21.causal_weights(rv)
    rows=[];unresolved=[]
    for d in sorted(sig):
        if d<START:continue
        if d>LAST_SIGNAL:
            unresolved.append({'signal_date':d.isoformat(),'reason':'t+1/t+2 would require protected 2026 data' if d>=dt.date(2025,12,30) else 'outside evaluable window'});continue
        e=d+dt.timedelta(days=1);x=d+dt.timedelta(days=2)
        if e.year>=2026 or x.year>=2026:raise RuntimeError('OOS_BLOCKED_SOURCE_PROVENANCE: attempted protected 2026 outcome')
        if e not in btc or x not in btc:raise RuntimeError(f'OOS_BLOCKED_SOURCE_PROVENANCE: missing BTC outcome {d}')
        skew=sig[d];pos=1 if skew>0 else (-1 if skew<0 else 0);fwd=math.log(btc[x]['open']/btc[e]['open']);w=float(weights.get(d,0.0))
        rows.append({'signal_date':d,'skew':skew,'position':pos,'forward_log_return':fwd,'unscaled_gross_bps':pos*fwd*10000,'rv20':rv.get(d),'weight':w})
    base=metrics(rows,BASE_COST);stress=metrics(rows,STRESS_COST)
    nonneg=sum(1 for v in base['quarters'].values() if v['n']>0 and v['net_mean_bps'] is not None and v['net_mean_bps']>=0)
    gates={'A_provenance_leakage_source_pass':True,'B_entered_scaled_trades_ge_50':base['entered_scaled_trades']>=MIN_ENTERED,'C_average_executed_notional_ge_0_40':base['average_executed_notional']>=0.40,'D_base10_net_mean_positive':base['net_mean_bps_per_parent_opportunity'] is not None and base['net_mean_bps_per_parent_opportunity']>0,'E_base10_pf_gt_1':base['profit_factor']>1,'F_base10_cumulative_net_positive':base['cumulative_net_return']>0,'G_at_least_2_of_4_quarters_nonnegative':nonneg>=2,'H_no_single_quarter_gt_60pct_positive_gross':base['single_quarter_max_share_positive_gross_pnl']<=0.60,'I_exact_v21_identity_unchanged':True}
    if not gates['A_provenance_leakage_source_pass']:cls='OOS_BLOCKED_SOURCE_PROVENANCE';rc=4
    elif not gates['B_entered_scaled_trades_ge_50']:cls='INSUFFICIENT_OOS_SAMPLE';rc=5
    elif all(gates.values()):cls='TIER_2_PROMOTED_CANDIDATE__QUASE_DIAMANTE__HIGH_RISK_FRAGILITY';rc=0
    elif (not gates['D_base10_net_mean_positive']) or (not gates['E_base10_pf_gt_1']) or (not gates['F_base10_cumulative_net_positive']) or (not gates['G_at_least_2_of_4_quarters_nonnegative']):cls='TIER_4_REJECTED_EXACT_V21';rc=3
    else:cls='TIER_3_HIGH_OOS_MIXED_NOT_PROMOTED';rc=6
    result={'lab_id':LAB_ID,'version':VERSION,'authority_commit':AUTHORITY_COMMIT,'classification':cls,'oos_window':{'start':START.isoformat(),'last_evaluable_signal':LAST_SIGNAL.isoformat(),'end':END.isoformat()},'valid_signal_days_2025':len(sig),'evaluated_parent_opportunities':len(rows),'unresolved_signals':unresolved,'base_10bps':base,'stress_20bps':stress,'nonnegative_quarters':nonneg,'gates':gates,'source_audit_status':audit.get('status'),'oos_2025_accessed':True,'year_2026_accessed':False,'live_trading_authorized':False,'exchange_mutation_authorized':False,'main_merge_authorized':False,'notes':['Historical V1/V2 verdicts remain immutable.','Stress20 is fragility diagnostic under Promotion Policy V3.','No post-outcome rescue or second 2025 shot authorized.']}
    out.mkdir(parents=True,exist_ok=True);(out/'OPTIONS_SPOTPERP_001_V21_2025_OOS_CLOSEOUT_V01.json').write_text(json.dumps(sanitize(result),indent=2,sort_keys=True))
    with (out/'OPTIONS_SPOTPERP_001_V21_2025_OOS_LEDGER_V01.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['signal_date','skew','position','forward_log_return','unscaled_gross_bps','rv20','weight']);
        for r in rows:w.writerow([r['signal_date'].isoformat(),r['skew'],r['position'],r['forward_log_return'],r['unscaled_gross_bps'],r['rv20'],r['weight']])
    print(cls);print('ENTERED=',base['entered_scaled_trades']);print('NET10=',base['net_mean_bps_per_parent_opportunity']);print('PF10=',base['profit_factor']);print('2025 OOS OPENED ONCE / 2026 LOCKED / NO LIVE TRADING');return rc

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();raise SystemExit(run(Path(a.source_root),Path(a.output)))