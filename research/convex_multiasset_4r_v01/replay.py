import csv, hashlib, io, json, math, os, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent/'receipts'; OUT.mkdir(exist_ok=True)
RAW=OUT/'raw'; RAW.mkdir(exist_ok=True)
parent=ROOT/'labs/btc-convex-trend-capture-001/h2_third_basket_validation_v0_1.py'
ns={'__file__':str(parent)}
# Load immutable Parent source helpers only; never run its old experiment.
exec(compile(parent.read_text().split('\nout={')[0],str(parent),'exec'),ns)
original_get=ns['get_bytes']; downloads=[]
def get_bytes(url):
    data=original_get(url)
    sha=hashlib.sha256(data).hexdigest()
    (RAW/sha).write_bytes(data)
    rec={'url':url,'sha256':sha,'bytes':len(data)}
    downloads.append(rec)
    if url.endswith('.zip'):
        checksum=original_get(url+'.CHECKSUM')
        (RAW/hashlib.sha256(checksum).hexdigest()).write_bytes(checksum)
        rec['checksum_text']=checksum.decode().strip()
        if checksum.decode().split()[0].lower()!=sha:
            raise RuntimeError('official checksum mismatch '+url)
    return data
ns['get_bytes']=get_bytes
SYMBOLS=['XRPUSDT','DOGEUSDT','ADAUSDT','LINKUSDT','AVAXUSDT']
F=.0008; LOSS=.04*(1-F)+2*F
TARGET=1+(4*LOSS+2*F)/(1-F)
HOUR=3600000; START=ns['START_MS']; END=ns['END_MS']

def barrier(b,entry,deadline):
    stop=entry*.96; target=entry*TARGET
    if b['open']<=stop:return b['open'],'GAP_STOP'
    if b['open']>=target:return target,'TARGET'
    if b['t']>=deadline:return b['open'],'TIMEOUT'
    if b['low']<=stop:return stop,'STOP'
    if b['high']>=target:return target,'TARGET'
    return None,None

def run(data,slip,risk):
    equity=500.; positions={}; pending=[]; trades=[]; peak=500.; dd=0.; skipped=0
    def marked(t,field):
        return equity+sum(p['qty']*(data[s]['by_t'][t][field]-p['entry']) for s,p in positions.items())
    def close(s,t,raw,reason):
        nonlocal equity
        p=positions.pop(s); price=raw*(1-slip); fee=p['qty']*price*F
        pnl=p['qty']*(price-p['entry'])-fee
        equity+=pnl
        trades.append(dict(symbol=s,entry_t=p['t'],exit_t=t,entry=p['entry'],exit=price,qty=p['qty'],reason=reason,net=pnl-p['fee']+p['funding'],funding=p['funding'],fees=fee+p['fee'],planned_risk=p['qty']*p['entry']*LOSS,slippage=p['qty']*(p['entry']-p['raw']+raw-price)))
    for t in range(START,END+1,HOUR):
        for s,p in positions.items():
            if t in data[s]['funding']:
                event=data[s]['funding'][t]; cf=-p['qty']*event['mark']*event['rate']
                equity+=cf; p['funding']+=cf
        # Carrying positions exit at open/intrabar before new entries; no capital
        # from intrabar exits is allowed to finance an earlier open entry.
        open_exits=[]; later_exits=[]
        for s,p in positions.items():
            b=data[s]['by_t'][t]; raw,reason=barrier(b,p['entry'],p['t']+1440*HOUR)
            if raw is not None:
                (open_exits if reason in ('GAP_STOP','TIMEOUT') or b['open']>=p['entry']*TARGET else later_exits).append((s,raw,reason))
        for s,raw,reason in open_exits:close(s,t,raw,reason)
        for s in pending:
            capital=marked(t,'open'); raw=data[s]['by_t'][t]['open']; price=raw*(1+slip)
            n=capital*risk/LOSS
            used=sum(p['qty']*p['entry'] for p in positions.values())
            usedrisk=sum(p['qty']*p['entry']*LOSS for p in positions.values())
            n=min(n,max(0.,capital*2*risk-usedrisk)/LOSS)
            if capital<=0 or n<=1e-9 or usedrisk+n*LOSS>capital*2*risk+1e-9 or used+n*(1+F)>capital:
                skipped+=1;continue
            qty=n/price; fee=n*F; equity-=fee
            positions[s]=dict(t=t,entry=price,raw=raw,qty=qty,fee=fee,funding=0.)
            b=data[s]['by_t'][t]; ex,reason=barrier(b,price,t+1440*HOUR)
            if ex is not None:later_exits.append((s,ex,reason))
        for s,raw,reason in later_exits:close(s,t,raw,reason)
        if t==END:
            for s in list(positions):close(s,t,data[s]['by_t'][t]['close'],'FORCED_END')
        mtm=marked(t,'close'); peak=max(peak,mtm); dd=min(dd,mtm/peak-1)
        pending=[s for s in SYMBOLS if s not in positions and t<END and data[s]['signals'].get(t,False)]
    wins=[x['net'] for x in trades if x['net']>0]; losses=[-x['net'] for x in trades if x['net']<0]
    streak=longest=0
    for tr in trades:
        streak=streak+1 if tr['net']<0 else 0; longest=max(longest,streak)
    return dict(risk=risk,slippage=slip,ending_equity=equity,net=equity-500,closed=len(trades),win_rate=len(wins)/len(trades) if trades else None,pf=sum(wins)/sum(losses) if losses else None,payoff=(sum(wins)/len(wins))/(sum(losses)/len(losses)) if wins and losses else None,drawdown=dd,longest_loss_streak=longest,net_without_top1=equity-500-max(wins,default=0),symbol_net={s:sum(x['net'] for x in trades if x['symbol']==s) for s in SYMBOLS},year_net={str(y):sum(x['net'] for x in trades if ns['year_from_ms'](x['exit_t'])==y) for y in range(2021,2026)},skipped=skipped,trades=trades)

def main():
    report={'experiment':'CONVEX-MULTIASSET-4R-HIST-001','checkout_sha':os.getenv('GITHUB_SHA'),'run_id':os.getenv('GITHUB_RUN_ID'),'family_oos':False,'source':{},'results':{},'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parent_code_sha256':hashlib.sha256(parent.read_bytes()).hexdigest()}
    data={}
    for s in SYMBOLS:
        try:
            bars,funding,manifest,mhash,meta=ns['load_symbol'](s)
            for b in bars:
                if not all(math.isfinite(b[k]) for k in ('open','high','low','close','volume')) or not 0<b['low']<=min(b['open'],b['close'])<=max(b['open'],b['close'])<=b['high'] or b['volume']<0:
                    raise RuntimeError('invalid OHLCV')
            times=[b['t'] for b in bars]
            if any(b-a!=HOUR for a,b in zip(times,times[1:])) or meta['warmup_hours_before_boundary']<400:raise RuntimeError('warmup/time gaps')
            ft=sorted(funding)
            if any(b-a>9*HOUR for a,b in zip(ft,ft[1:])):raise RuntimeError('funding gap >9h')
            signals,_=ns['build_signals'](bars,'PARENT')
            data[s]=dict(by_t={b['t']:b for b in bars},funding=funding,signals={b['t']:v for b,v in zip(bars,signals)})
            (OUT/(s+'_normalized.json')).write_text(json.dumps(dict(bars=bars,funding=funding)))
            report['source'][s]=dict(status='PASS',manifest=manifest,manifest_sha256=mhash,meta=meta)
        except Exception as e:
            report['source'][s]=dict(status='SOURCE_BLOCKED',error=repr(e))
        (OUT/'report.json').write_text(json.dumps(report,indent=2))
        (OUT/'downloads.json').write_text(json.dumps(downloads,indent=2))
        print(s,report['source'][s]['status'],report['source'][s].get('error',''),flush=True)
    if len(data)!=5:report['verdict']='SOURCE_BLOCKED'
    else:
        for risk in (.0025,.005,.01):
            for layer,slip in [('BASE',.0002),('STRESS',.0005)]:
                report['results'][f'{risk}_{layer}']=run(data,slip,risk)
        b=report['results']['0.0025_BASE']; s=report['results']['0.0025_STRESS']
        passed=b['net']>0 and s['net']>0 and (b['pf'] or 0)>1 and (s['pf'] or 0)>1 and (b['payoff'] or 0)>=4 and b['net_without_top1']>0 and sum(v>0 for v in b['symbol_net'].values())>=3
        report['verdict']='HISTORICAL_DIAGNOSTIC_SURVIVES' if passed else 'HISTORICAL_DIAGNOSTIC_FAIL'
    (OUT/'report.json').write_text(json.dumps(report,indent=2))
    (OUT/'custody.json').write_text(json.dumps({str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file()},indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('source','results')},indent=2))
    for key,value in report['results'].items():print(key,json.dumps({k:v for k,v in value.items() if k!='trades'}))

if __name__=='__main__':main()
