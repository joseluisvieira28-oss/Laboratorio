#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,datetime as dt,gzip,hashlib,io,json,math,statistics,sys,zipfile
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'options_spotperp_v0_1'
sys.path.insert(0,str(PARENT))
import discovery_runner_v01 as v01
import regime_discovery_runner_v02 as v02

LAB_ID='OPTIONS-SPOTPERP-002'
VERSION='CONFIRMATION-2025-V0.1'
AUTHORITY_COMMIT='6f47b388b2c7e0a19df41200472e50caed4f58a6'
START=dt.date(2025,1,1); LAST_SIGNAL=dt.date(2025,12,29); END=dt.date(2025,12,31)
BASE_COST=10.0; STRESS_COST=20.0; MIN_ENTERED=80


def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def med(xs): return float(statistics.median(xs))

def load_manifest(root:Path):
    p=root/'confirmation_source_manifest.json'; r=root/'confirmation_source_audit_report.json'
    if not p.exists() or not r.exists(): raise RuntimeError('SOURCE_OR_DATA_BLOCKED: confirmation source receipts missing')
    m=json.loads(p.read_text()); a=json.loads(r.read_text())
    if m.get('status')!='SOURCE_AUDIT_PASS' or a.get('status')!='SOURCE_AUDIT_PASS': raise RuntimeError('SOURCE_OR_DATA_BLOCKED: source gate not PASS')
    if m.get('authority_commit')!=AUTHORITY_COMMIT: raise RuntimeError('SOURCE_OR_DATA_BLOCKED: authority mismatch')
    if m.get('confirmation_2025_authorized') is not True or m.get('confirmation_2025_accessed') is not True: raise RuntimeError('SOURCE_OR_DATA_BLOCKED: 2025 authorization receipt missing')
    if m.get('year_2026_accessed') is not False: raise RuntimeError('SOURCE_OR_DATA_BLOCKED: 2026 flag')
    for k in ('skew_values_computed','signals_computed','forward_returns_computed','pnl_computed'):
        if m.get(k) is not False: raise RuntimeError(f'SOURCE_OR_DATA_BLOCKED: premature outcome flag {k}')
    return m

def build_signal(root:Path,m):
    inst=defaultdict(lambda:defaultdict(list)); side={}
    for e in m['raw_pages']:
        p=root/'raw'/e['page']
        if not p.exists() or sha(p)!=e['sha256']: raise RuntimeError('SOURCE_OR_DATA_BLOCKED: raw integrity')
        obj=json.loads(gzip.decompress(p.read_bytes()).decode()); rows=obj.get('result',{}).get('trades')
        if not isinstance(rows,list): raise RuntimeError('SOURCE_OR_DATA_BLOCKED: invalid raw payload')
        for row in rows:
            t=dt.datetime.fromtimestamp(int(row['timestamp'])/1000,tz=dt.timezone.utc); d=t.date()
            if d<START or d>END: raise RuntimeError('SOURCE_OR_DATA_BLOCKED: Deribit row outside 2025')
            expiry,strike,s=v01.parse_instrument(str(row['instrument_name']))
            iv=float(row['iv']); idx=float(row['index_price'])
            if not(math.isfinite(iv) and iv>0 and math.isfinite(idx) and idx>0): continue
            dte=(expiry-d).days
            if not(30<=dte<=120): continue
            mm=strike/idx
            if not((s=='C' and 1.05<=mm<=1.20) or (s=='P' and 0.80<=mm<=0.95)): continue
            inst[d][str(row['instrument_name'])].append(iv); side[str(row['instrument_name'])]=s
    sig={}
    for d,names in inst.items():
        c=[];p=[]
        for name,vals in names.items(): (c if side[name]=='C' else p).append(med(vals))
        if len(c)>=5 and len(p)>=5: sig[d]=med(c)-med(p)
    return sig

def load_btc(root:Path,m):
    out={}; entries=m.get('btc_price_raw_archives',[])
    if len(entries)!=13: raise RuntimeError('SOURCE_OR_DATA_BLOCKED: expected 13 BTC archives')
    for e in entries:
        p=root/'raw_binance_btcusdt_1d'/e['file']
        if not p.exists() or sha(p)!=e['sha256']: raise RuntimeError('SOURCE_OR_DATA_BLOCKED: BTC integrity')
        with zipfile.ZipFile(p) as zf:
            members=[x for x in zf.namelist() if not x.endswith('/')]
            if len(members)!=1: raise RuntimeError('SOURCE_OR_DATA_BLOCKED: BTC zip members')
            with zf.open(members[0]) as fh:
                for row in csv.reader(io.TextIOWrapper(fh,encoding='utf-8')):
                    if not row: continue
                    d=dt.datetime.fromtimestamp(int(row[0])/1000,tz=dt.timezone.utc).date()
                    if d.year>=2026: raise RuntimeError('SOURCE_OR_DATA_BLOCKED: 2026 BTC row')
                    op=float(row[1])
                    if not(math.isfinite(op) and op>0): raise RuntimeError('SOURCE_OR_DATA_BLOCKED: invalid BTC open')
                    out[d]=op
    return out

def metrics(rows,cost):
    entered=[r for r in rows if r['position']!=0]; vals=[r['gross_bps']-cost for r in entered]
    pos=sum(x for x in vals if x>0); neg=-sum(x for x in vals if x<0); pf=pos/neg if neg>0 else (float('inf') if pos>0 else 0.0)
    qs={}
    positive_gross={}
    for q in range(1,5):
        rr=[r for r in entered if ((r['signal_date'].month-1)//3+1)==q]; vv=[r['gross_bps']-cost for r in rr]; gg=sum(r['gross_bps'] for r in rr)
        qs[str(q)]={'n':len(rr),'net_mean_bps':sum(vv)/len(vv) if vv else None,'gross_pnl_bps':gg,'net_pnl_bps':sum(vv)}; positive_gross[str(q)]=max(0.0,gg)
    tot=sum(positive_gross.values()); share=max(positive_gross.values())/tot if tot>0 else 1.0
    cum=math.exp(sum(v/10000 for v in vals))-1 if vals else 0.0
    wealth=peak=1.0;mdd=0.0
    for v in vals:
        wealth*=math.exp(v/10000);peak=max(peak,wealth);mdd=min(mdd,wealth/peak-1)
    return {'entered_trades':len(entered),'net_mean_bps_per_trade':sum(vals)/len(vals) if vals else None,'profit_factor':pf,'cumulative_net_return':cum,'max_drawdown':mdd,'quarters':qs,'single_quarter_max_share_positive_gross_pnl':share}

def run(root:Path,out:Path):
    m=load_manifest(root); sig=build_signal(root,m); btc=load_btc(root,m); rows=[]
    for d in sorted(sig):
        if d<START or d>LAST_SIGNAL: continue
        reg=v02.regime_for_day(d,btc)
        if reg is None or reg[0]!='UP_LOW': continue
        e=d+dt.timedelta(days=1); x=d+dt.timedelta(days=2)
        if e.year>=2026 or x.year>=2026: raise RuntimeError('SOURCE_OR_DATA_BLOCKED: attempted 2026 outcome')
        if e not in btc or x not in btc: raise RuntimeError(f'SOURCE_OR_DATA_BLOCKED: missing BTC outcome {d}')
        f=math.log(btc[x]/btc[e]); s=sig[d]; pos=1 if s>0 else (-1 if s<0 else 0)
        rows.append({'signal_date':d,'skew':s,'forward_log_return':f,'position':pos,'gross_bps':pos*f*10000,'momentum_30d':reg[1],'realized_vol_30d':reg[2]})
    entered=[r for r in rows if r['position']!=0]; base=metrics(rows,BASE_COST); stress=metrics(rows,STRESS_COST)
    reg=v01.ols_hac7([r['skew'] for r in rows],[r['forward_log_return'] for r in rows]) if len(rows)>=20 else None
    qual=[q for q,v in base['quarters'].items() if v['n']>=15]
    nonneg=sum(1 for q in qual if base['quarters'][q]['net_mean_bps'] is not None and base['quarters'][q]['net_mean_bps']>=0)
    gates={
        'A_entered_ge_80':len(entered)>=MIN_ENTERED,
        'B_beta_positive':bool(reg and reg['beta']>0),
        'C_net_mean_10bps_positive':base['net_mean_bps_per_trade'] is not None and base['net_mean_bps_per_trade']>0,
        'D_profit_factor_10bps_gt_1':base['profit_factor']>1.0,
        'E_at_least_2_qualifying_quarters_nonnegative':nonneg>=2,
        'F_no_single_quarter_gt_75pct_positive_gross_pnl':base['single_quarter_max_share_positive_gross_pnl']<=0.75,
        'G_2026_not_accessed':True,
    }
    if len(entered)<MIN_ENTERED: cls='INSUFFICIENT_SAMPLE'; rc=5
    elif all(gates.values()): cls='OOS_REPLICATED'; rc=0
    else: cls='OOS_FAILED'; rc=3
    result={'lab_id':LAB_ID,'version':VERSION,'authority_commit':AUTHORITY_COMMIT,'candidate_regime':'UP_LOW','classification':cls,'oos_window':{'start':START.isoformat(),'last_evaluable_signal':LAST_SIGNAL.isoformat(),'end':END.isoformat()},'regime_observations':len(rows),'regression':reg,'base_10bps':base,'stress_20bps':stress,'qualifying_quarters_n_ge_15':qual,'qualifying_quarters_nonnegative':nonneg,'gates':gates,'confirmation_2025_accessed':True,'year_2026_accessed':False,'live_trading_authorized':False,'exchange_mutation_authorized':False,'tier1_automatic':False}
    out.mkdir(parents=True,exist_ok=True); (out/'OPTIONS_SPOTPERP_002_CONFIRMATION_2025_CLOSEOUT_V01.json').write_text(json.dumps(v01.sanitize_json(result),indent=2,sort_keys=True),encoding='utf-8')
    with (out/'OPTIONS_SPOTPERP_002_CONFIRMATION_2025_LEDGER_V01.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['signal_date','skew','momentum_30d','realized_vol_30d','forward_log_return','position','gross_bps']);
        for r in rows:w.writerow([r['signal_date'].isoformat(),r['skew'],r['momentum_30d'],r['realized_vol_30d'],r['forward_log_return'],r['position'],r['gross_bps']])
    print(cls);print('ENTERED=',len(entered));print('2025 OOS ONLY / 2026 LOCKED / NO LIVE TRADING');return rc

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();raise SystemExit(run(Path(a.source_root),Path(a.output)))
