from __future__ import annotations
import csv, hashlib, io, json, sys, time, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research'/'local_data'/'prop_compat_001b_kraken'
UA='PROP-COMPAT-001B Kraken ambiguity envelope/1.0'
SYMBOLS=['BTCUSDT','ETHUSDT','SOLUSDT','BNBUSDT','XRPUSDT','DOGEUSDT']; SYM={s:i for i,s in enumerate(SYMBOLS)}
START_MS=1672531200000; END_MS=1735689600000; MIN_MS=60000; N=(END_MS-START_MS)//MIN_MS

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()
def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def get(url,retries=4):
    last=None
    for k in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA})
            with urllib.request.urlopen(req,timeout=120) as r: return r.read()
        except Exception as e:
            last=e
            if k+1<retries: time.sleep(2**k)
    raise RuntimeError(f'download failed:{url}:{last}')
def parse_price_zip(zb,expected):
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        with z.open(expected) as fh:
            for row in csv.reader(io.TextIOWrapper(fh)):
                if not row: continue
                try: t=int(row[0])
                except: continue
                yield t,float(row[1]),float(row[2]),float(row[3]),float(row[4])

def load_sources(srcdir):
    gate=json.loads((srcdir/'HTF_DIAMOND_HUNT_001_PHASE5_SOURCE_GATE_V0.1.json').read_text())
    assert gate['status']=='SOURCE_DATA_PASS'
    assert gate['source_fingerprint']=='d1a95d51d99eba0bd5f66e91d75ddcd175f7a84d954ba28a44c2dcd39ef4c5cb'
    op=np.full((6,N),np.nan); hi=np.full((6,N),np.nan); lo=np.full((6,N),np.nan); cl=np.full((6,N),np.nan)
    count=0
    for rec in sorted(gate['price_records'],key=lambda x:(x['symbol'],x['month'])):
        si=SYM[rec['symbol']]; zb=get(rec['archive_url'])
        if sha256_bytes(zb)!=rec['local_sha256']: raise RuntimeError(f'HASH_DRIFT:{rec["symbol"]}:{rec["month"]}')
        n=0
        for t,o,h,l,c in parse_price_zip(zb,rec['archive_name'].replace('.zip','.csv')):
            if START_MS<=t<END_MS:
                j=(t-START_MS)//MIN_MS; op[si,j]=o; hi[si,j]=h; lo[si,j]=l; cl[si,j]=c; n+=1
        if n!=rec['row_count']: raise RuntimeError(f'ROWCOUNT:{rec["symbol"]}:{rec["month"]}:{n}:{rec["row_count"]}')
        count+=1; print('PRICE_HASH_PASS',rec['symbol'],rec['month'],flush=True)
    if count!=144 or np.isnan(cl).any(): raise RuntimeError('SOURCE_INCOMPLETE')
    return op,hi,lo,cl,count

def load_ledger(execdir):
    p=execdir/'DH-03-HO1_LEDGER.json'
    if sha256_file(p)!='ec4e5dbc8d95a73d4eb9db55f4e1c0f264dba7eb724cbb7424f2c034a3a7eebd': raise RuntimeError('LEDGER_HASH_MISMATCH')
    rows=[r for r in json.loads(p.read_text()) if not r['execution_path_unresolved']]
    if len(rows)!=146: raise RuntimeError(f'resolved {len(rows)}')
    return sorted(rows,key=lambda r:(r['entry_time'],r['symbol']))

def scenarios():
    plans={'STARTER':(10.,6.),'INTERMEDIATE':(12.,5.),'ADVANCED':(9.,3.)}; risks=[.10,.15,.20,.25,.30]; execs={'BASE':(.001,.001),'STRESS':(.0015,.0015)}; out=[]
    for plan,(target,mdd) in plans.items():
      for risk in risks:
       for ex,(en,xx) in execs.items():
        out.append(dict(plan=plan,target=100+target,mdd_floor=100-mdd,risk=risk/100,exec=ex,en=en,xx=xx,carry='LEGAL',phase=-1))
        for phase in range(240): out.append(dict(plan=plan,target=100+target,mdd_floor=100-mdd,risk=risk/100,exec=ex,en=en,xx=xx,carry='SUPPORT',phase=phase))
    return out

def simulate(rows,op,hi,lo,cl):
    sc=scenarios(); M=len(sc); bal=np.full(M,100.); daily=np.full(M,97.); decided=np.zeros(M,bool); passed=np.zeros(M,bool); breached=np.zeros(M,bool); ambig=np.zeros(M,bool)
    decision=np.full(M,-1,np.int64); reason=np.array(['']*M,dtype=object); risk=np.array([x['risk'] for x in sc]); target=np.array([x['target'] for x in sc]); mdd=np.array([x['mdd_floor'] for x in sc]); en=np.array([x['en'] for x in sc]); xx=np.array([x['xx'] for x in sc]); legal=np.array([x['carry']=='LEGAL' for x in sc]); phase=np.array([x['phase'] for x in sc],dtype=np.int16)
    qty=np.zeros((6,M)); entpx=np.zeros(6); active=[None]*6; entries=defaultdict(list); exits=defaultdict(list)
    for r in rows: entries[(r['entry_time']-START_MS)//MIN_MS].append(r); exits[(r['exit_time']-START_MS)//MIN_MS].append(r)
    first=min(entries); maxdd=np.zeros(M); maxlow=np.zeros(M); maxdaily=np.zeros(M); maxnot=np.zeros(M); maxtotal=np.zeros(M); maxconc=np.zeros(M,np.int16); everlow=np.zeros(M,bool)
    def equity(prices):
        pnl=np.zeros(M)
        for si in range(6):
            if active[si] is not None: pnl += qty[si]*(prices[si]-entpx[si])
        return bal+pnl
    for j in range(first,N):
        live=~decided
        if not live.any(): break
        mod=j%1440; pxopen=op[:,j]; current=np.zeros(M)
        for si in range(6):
            if active[si] is not None: current += np.abs(qty[si])*pxopen[si]
        mask=live & legal & (mod==0)
        if mask.any(): bal[mask]-=current[mask]*.00033
        mask=live & (~legal) & (phase==(mod%240))
        if mask.any(): bal[mask]-=current[mask]*.000055
        if mod==30: daily[live]=bal[live]-3.
        for r in sorted(exits.get(j,[]),key=lambda x:x['symbol']):
            si=SYM[r['symbol']]; mask=live & (qty[si]!=0)
            if mask.any():
                ep=float(r['exit_price']); bal[mask]+=qty[si,mask]*(ep-entpx[si]); bal[mask]-=np.abs(qty[si,mask])*ep*xx[mask]; qty[si,mask]=0
            active[si]=None; entpx[si]=0
        for r in sorted(entries.get(j,[]),key=lambda x:x['symbol']):
            si=SYM[r['symbol']]; eq=equity(pxopen); mask=live; amt=eq[mask]*risk[mask]; notion=amt/float(r['initial_risk_fraction']); qty[si,mask]=notion/float(r['entry_price']); bal[mask]-=notion*en[mask]; entpx[si]=float(r['entry_price']); active[si]=r; maxnot[mask]=np.maximum(maxnot[mask],notion)
        total=np.zeros(M); conc=np.zeros(M,np.int16)
        for si in range(6): total += np.abs(qty[si])*pxopen[si]; conc += (qty[si]!=0).astype(np.int16)
        maxtotal=np.maximum(maxtotal,total); maxconc=np.maximum(maxconc,conc)
        eqc=equity(cl[:,j]); eqh=equity(hi[:,j]); eql=equity(lo[:,j]); maxdd=np.maximum(maxdd,100-eqc); maxlow=np.maximum(maxlow,100-eql); maxdaily=np.maximum(maxdaily,daily-eqc); everlow |= live & ((eql<=mdd)|(eql<=daily))
        tmask=live & (eqc>=target)
        if tmask.any():
            safe=tmask & (~everlow); passed[safe]=1; decided[safe]=1; decision[safe]=j; reason[safe]='TARGET_CLOSE_ROBUST_TO_LOW_BOUND'
            unc=tmask & everlow; ambig[unc]=1; decided[unc]=1; decision[unc]=j; reason[unc]='TARGET_REACHED_BUT_INTRAMINUTE_BREACH_BOUND_CROSSED'
        live=~decided; bmask=live & ((eqc<=mdd)|(eqc<=daily))
        if bmask.any():
            possible=eqh>=target; obvious=bmask & (~possible); breached[obvious]=1; decided[obvious]=1; decision[obvious]=j; reason[obvious]=np.where(eqc[obvious]<=mdd[obvious],'MDD_CLOSE_BREACH','MDL_CLOSE_BREACH')
            unc=bmask & possible; ambig[unc]=1; decided[unc]=1; decision[unc]=j; reason[unc]='BREACH_CLOSE_WITH_SAME_MINUTE_TARGET_UPPER_BOUND'
    out=[]
    for k,x in enumerate(sc):
        label='ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED' if passed[k] else ('OBVIOUS_PROXY_BREACH' if breached[k] else ('AMBIGUITY_MATERIAL' if ambig[k] else 'PROXY_INSUFFICIENT_HISTORY_NO_DECISION'))
        out.append({**x,'classification':label,'decision_time_utc':None if decision[k]<0 else datetime.fromtimestamp((START_MS+int(decision[k])*MIN_MS)/1000,tz=timezone.utc).isoformat().replace('+00:00','Z'),'reason':str(reason[k]),'ending_balance':float(bal[k]),'max_close_drawdown_pct_initial':float(maxdd[k]),'max_low_bound_drawdown_pct_initial':float(maxlow[k]),'max_daily_close_breach_margin_pct_initial':float(maxdaily[k]),'max_single_position_notional_multiple_initial':float(maxnot[k]/100),'max_total_open_notional_multiple_initial':float(maxtotal[k]/100),'max_concurrent_positions':int(maxconc[k])})
    return out

def summarize(results,archives):
    groups=defaultdict(list)
    for r in results: groups[(r['plan'],r['risk'],r['exec'])].append(r)
    cells=[]
    for key,rs in sorted(groups.items()):
        l=[r for r in rs if r['carry']=='LEGAL'][0]; s=[r for r in rs if r['carry']=='SUPPORT']; counts=defaultdict(int)
        for r in s: counts[r['classification']]+=1
        if l['classification']=='ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED' and counts['ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED']==240: cell='ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED'
        elif l['classification']=='OBVIOUS_PROXY_BREACH' and counts['OBVIOUS_PROXY_BREACH']==240: cell='OBVIOUS_PROXY_BREACH'
        elif l['classification']=='PROXY_INSUFFICIENT_HISTORY_NO_DECISION' or counts['PROXY_INSUFFICIENT_HISTORY_NO_DECISION']>0: cell='PROXY_INSUFFICIENT'
        else: cell='AMBIGUITY_MATERIAL'
        cells.append({'plan':key[0],'risk_pct_per_1R':round(key[1]*100,2),'execution_case':key[2],'cell_classification':cell,'legal_daily':{k:l[k] for k in ['classification','decision_time_utc','reason','ending_balance','max_close_drawdown_pct_initial','max_low_bound_drawdown_pct_initial','max_total_open_notional_multiple_initial','max_concurrent_positions']},'support_4h_phase_counts':dict(counts),'support_4h_decision_time_range_utc':[min((r['decision_time_utc'] for r in s if r['decision_time_utc']),default=None),max((r['decision_time_utc'] for r in s if r['decision_time_utc']),default=None)]})
    cc=defaultdict(int)
    for c in cells: cc[c['cell_classification']]+=1
    return {'campaign_id':'PROP-COMPAT-001B','status':'KRAKEN_PROP_AMBIGUITY_ENVELOPE_COMPLETE','setup_id':'DH-03-HO1','decisional_authority':False,'official_phase3_risk_grid_run':False,'source_validation':{'binance_1m_archives_downloaded_and_hash_validated':archives,'access_2025':False,'access_2026':False},'base_cells':30,'support_phase_paths':7200,'cell_classification_counts':dict(cc),'cells':cells,'governance':{'no_best_plan_selection':True,'no_best_risk_selection':True,'post_outcome_tuning':False,'challenge_purchase':False,'live_trading':False,'merge_to_main':False}}

def main(argv):
    if len(argv)!=3: raise SystemExit('usage: runner SOURCE_ARTIFACT_DIR EXECUTION_ARTIFACT_DIR')
    src=Path(argv[1]); ex=Path(argv[2]); OUT.mkdir(parents=True,exist_ok=True); rows=load_ledger(ex); op,hi,lo,cl,archives=load_sources(src); receipt=summarize(simulate(rows,op,hi,lo,cl),archives); raw=json.dumps(receipt,sort_keys=True,separators=(',',':')).encode(); receipt['fingerprint']=hashlib.sha256(raw).hexdigest(); (OUT/'PROP_COMPAT_001B_KRAKEN_PROP_AMBIGUITY_ENVELOPE_RECEIPT_V0.1.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)); print(json.dumps({k:receipt[k] for k in ['status','cell_classification_counts','fingerprint']},sort_keys=True),flush=True); return 0
if __name__=='__main__': raise SystemExit(main(sys.argv))
