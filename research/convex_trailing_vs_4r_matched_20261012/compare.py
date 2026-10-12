#!/usr/bin/env python3
"""2026-10-12: controlled historical compare; NEVER live orders; previously seen family data."""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'research/convex_firstbasket_4r_hist_20261012'
sys.path.insert(0,str(SRC))
import replay as baseline

OUT=Path(__file__).resolve().parent/'receipts'
OUT.mkdir(exist_ok=True)
RAW=OUT/'raw'
RAW.mkdir(exist_ok=True)
# Keep the original source helper and fixed-4R economic engine byte-for-byte unchanged.
baseline.OUT=OUT
baseline.RAW=RAW
baseline.ns['get_bytes']=baseline.get_bytes
HOUR=baseline.HOUR
START=baseline.START
END=baseline.END
SYMBOLS=tuple(baseline.SYMBOLS)
F=baseline.F
LOSS=baseline.LOSS
ACT=.05
TRAIL=.12
STOP=.04
EXPECTED_MANIFEST={
 'ETHUSDT':'67442d3abd255de1fab33507ebc83eb00d6905a6f50ab46e011498ce715d508b',
 'SOLUSDT':'04bfcdaa8ef0f6f05619f4b351cb7924900b75a74da9c588efc318c273f723d4',
 'BNBUSDT':'c8b8c13265109e9acfc84b28f6b1b7a4383167685beb0722939236e0519a5452',
}
CONTROL_EXPECTED={
 '0.0025_BASE':(532.591965,459),
 '0.0025_STRESS':(515.952360,462),
}

def next_active_stop(peak,close,entry,initial_stop):
    """Parent Pine V5: high peak observed by close; +5% threshold NOT sticky."""
    return max(initial_stop,peak*(1-TRAIL)) if (close-entry)/entry>=ACT else initial_stop

def trailing_bar_exit(bar,active_stop,entry_hour,deadline):
    """Use only active stop from PREVIOUS close; 60d timer at current OPEN."""
    if bar['open']<=active_stop:
        return bar['open'],'GAP_STOP',True
    if deadline is not None and bar['t']>=deadline:
        return bar['open'],'TIMEOUT',True
    if bar['low']<=active_stop:
        return active_stop,'STOP',False
    return None,None,False

def run_trailing(data,slip,risk,horizon_hours=1440):
    equity=500.
    positions={}
    pending=[]
    trades=[]
    peak_equity=500.
    max_dd=0.
    skipped=0
    def marked(t,field):
        return equity+sum(p['qty']*(data[s]['by_t'][t][field]-p['entry']) for s,p in positions.items())
    def close(s,t,raw,reason):
        nonlocal equity
        p=positions.pop(s)
        price=raw*(1-slip)
        fee=p['qty']*price*F
        pnl=p['qty']*(price-p['entry'])-fee
        equity+=pnl
        trades.append(dict(
            symbol=s,entry_t=p['t'],exit_t=t,entry=p['entry'],exit=price,
            qty=p['qty'],reason=reason,net=pnl-p['fee']+p['funding'],
            funding=p['funding'],fees=fee+p['fee'],
            planned_risk=p['qty']*p['entry']*LOSS,
            slippage=p['qty']*(p['entry']-p['raw']+raw-price),
            peak_at_exit=p['peak'],active_stop_before_exit=p['active_stop']
        ))
    for t in range(START,END+1,HOUR):
        for s,p in positions.items():
            if t in data[s]['funding']:
                event=data[s]['funding'][t]
                cf=-p['qty']*event['mark']*event['rate']
                equity+=cf
                p['funding']+=cf

        open_exits=[]
        later_exits=[]
        for s,p in positions.items():
            b=data[s]['by_t'][t]
            raw,reason,is_open=trailing_bar_exit(
                b,p['active_stop'],p['t'],None if horizon_hours is None else p['t']+horizon_hours*HOUR)
            if raw is not None:
                (open_exits if is_open else later_exits).append((s,raw,reason))
        for s,raw,reason in open_exits:
            close(s,t,raw,reason)

        for s in pending:
            capital=marked(t,'open')
            raw=data[s]['by_t'][t]['open']
            price=raw*(1+slip)
            n=capital*risk/LOSS
            used=sum(p['qty']*p['entry'] for p in positions.values())
            usedrisk=sum(p['qty']*p['entry']*LOSS for p in positions.values())
            n=min(n,max(0.,capital*2*risk-usedrisk)/LOSS)
            if capital<=0 or n<=1e-9 or usedrisk+n*LOSS>capital*2*risk+1e-9 or used+n*(1+F)>capital:
                skipped+=1
                continue
            qty=n/price
            fee=n*F
            equity-=fee
            positions[s]=dict(t=t,entry=price,raw=raw,qty=qty,fee=fee,funding=0.,
                              peak=price,initial_stop=price*(1-STOP),active_stop=price*(1-STOP))
            b=data[s]['by_t'][t]
            raw_exit,reason,_=trailing_bar_exit(
                b,positions[s]['active_stop'],t,None if horizon_hours is None else t+horizon_hours*HOUR)
            if raw_exit is not None:
                later_exits.append((s,raw_exit,reason))

        for s,raw,reason in later_exits:
            close(s,t,raw,reason)

        if t==END:
            for s in list(positions):
                close(s,t,data[s]['by_t'][t]['close'],'FORCED_END')
        else:
            for s,p in positions.items():
                b=data[s]['by_t'][t]
                p['peak']=max(p['peak'],b['high'])
                p['active_stop']=next_active_stop(p['peak'],b['close'],p['entry'],p['initial_stop'])
        mtm=marked(t,'close')
        peak_equity=max(peak_equity,mtm)
        max_dd=min(max_dd,mtm/peak_equity-1.)
        pending=[s for s in SYMBOLS if s not in positions and t<END and data[s]['signals'].get(t,False)]
    wins=[x['net'] for x in trades if x['net']>0]
    losses=[-x['net'] for x in trades if x['net']<0]
    streak=longest=0
    for tr in trades:
        streak=streak+1 if tr['net']<0 else 0
        longest=max(longest,streak)
    return dict(risk=risk,slippage=slip,horizon_hours=horizon_hours,
                ending_equity=equity,net=equity-500,closed=len(trades),
                win_rate=len(wins)/len(trades) if trades else None,
                pf=sum(wins)/sum(losses) if losses else None,
                payoff=(sum(wins)/len(wins))/(sum(losses)/len(losses)) if wins and losses else None,
                drawdown=max_dd,longest_loss_streak=longest,
                net_without_top1=equity-500-max(wins,default=0),
                symbol_net={s:sum(x['net'] for x in trades if x['symbol']==s) for s in SYMBOLS},
                year_net={str(y):sum(x['net'] for x in trades if baseline.ns['year_from_ms'](x['exit_t'])==y) for y in range(2021,2026)},
                skipped=skipped,trades=trades)

def summary(res):
    ts=res['trades']
    wins=sorted((x['net'] for x in ts if x['net']>0),reverse=True)
    return dict(ending_equity=res['ending_equity'],net=res['net'],
        net_pct=100*res['net']/500,
        closed=res['closed'],win_pct=100*res['win_rate'] if res['win_rate'] is not None else None,
        pf=res['pf'],payoff=res['payoff'],
        drawdown_pct=100*res['drawdown'],
        max_losing_streak=res['longest_loss_streak'],skipped=res['skipped'],
        fees=sum(x['fees'] for x in ts),
        funding=sum(x['funding'] for x in ts),
        slippage=sum(x['slippage'] for x in ts),
        net_without_top1=res['net']-sum(wins[:1]),
        net_without_top3=res['net']-sum(wins[:3]),
        symbol_net=res['symbol_net'],year_net=res['year_net'],
        exit_counts={reason:sum(x['reason']==reason for x in ts) for reason in sorted({x['reason'] for x in ts})},
        symbol_trades={s:sum(x['symbol']==s for x in ts) for s in SYMBOLS}
    )

def main():
    assert SYMBOLS==('ETHUSDT','SOLUSDT','BNBUSDT')
    assert F==.0008 and START==baseline.ns['START_MS'] and END==baseline.ns['END_MS']
    report={
      'experiment':'CONVEX-TRAILING-VS-4R-MATCHED-HIST-001',
      'family_oos':False,'basis':'RESEARCH_ONLY_2021_2025_ALREADY_EXPOSED',
      'run_id':os.getenv('GITHUB_RUN_ID'),
      'checkout_sha':os.getenv('GITHUB_SHA'),
      'freeze_sha':'b4b713bf6240caef28d973a7925b3166379ded09',
      'control_module_sha256':hashlib.sha256((SRC/'replay.py').read_bytes()).hexdigest(),
      'trailing_module_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'source':{},'results':{},'summary':{},
      'verdict':'SOURCE_BLOCKED'
    }
    data={}
    for s in SYMBOLS:
        try:
            bars,funding,manifest,mhash,meta=baseline.ns['load_symbol'](s)
            if mhash!=EXPECTED_MANIFEST[s]:
                raise RuntimeError(f'SOURCE_DRIFT_BLOCKED manifest {s}: {mhash} != {EXPECTED_MANIFEST[s]}')
            for b in bars:
                if not all(math.isfinite(b[k]) for k in ('open','high','low','close','volume')) or not 0<b['low']<=min(b['open'],b['close'])<=max(b['open'],b['close'])<=b['high'] or b['volume']<0:
                    raise RuntimeError('bad OHLCV')
            times=[b['t'] for b in bars]
            if any(y-x!=HOUR for x,y in zip(times,times[1:])) or meta['warmup_hours_before_boundary']<400:
                raise RuntimeError('bar continuity/warmup')
            fund_times=sorted(funding)
            if any(y-x>9*HOUR for x,y in zip(fund_times,fund_times[1:])):
                raise RuntimeError('funding gap')
            signals,_=baseline.ns['build_signals'](bars,'PARENT')
            data[s]=dict(by_t={b['t']:b for b in bars},funding=funding,
                         signals={b['t']:v for b,v in zip(bars,signals)})
            (OUT/(s+'_normalized.json')).write_text(json.dumps(dict(bars=bars,funding=funding)))
            report['source'][s]=dict(status='PASS',manifest_sha256=mhash,meta=meta,manifest=manifest)
        except Exception as e:
            report['source'][s]=dict(status='SOURCE_BLOCKED',error=repr(e))
        (OUT/'report.json').write_text(json.dumps(report,indent=2))
        (OUT/'downloads.json').write_text(json.dumps(baseline.downloads,indent=2))
        print('SOURCE',s,report['source'][s]['status'],report['source'][s].get('error',''),flush=True)

    if len(data)!=3:
        report['verdict']='SOURCE_BLOCKED'
    else:
        # Both algorithms encounter exactly the same loaded bars/funding and frozen shared-account model.
        for risk in (.0025,.005,.01):
            for label,slip in [('BASE',.0002),('STRESS',.0005)]:
                suffix=f'{risk}_{label}'
                control=baseline.run(data,slip,risk)
                report['results']['4R_60D_'+suffix]=control
                report['results']['TRAIL_60D_'+suffix]=run_trailing(data,slip,risk,1440)
                report['results']['TRAIL_PARENT_NO_TIMER_'+suffix]=run_trailing(data,slip,risk,None)
        for k,v in report['results'].items():
            report['summary'][k]=summary(v)
        for key,(expected,expected_count) in CONTROL_EXPECTED.items():
            observed=report['results']['4R_60D_'+key]
            if abs(observed['ending_equity']-expected)>.02 or observed['closed']!=expected_count:
                report['verdict']='CONTROL_PARITY_BLOCKED'
                report['control_parity_issue']=dict(key=key,expected=expected,observed=observed['ending_equity'],expected_count=expected_count,observed_count=observed['closed'])
                break
        else:
            cp=[report['summary']['4R_60D_0.0025_'+layer] for layer in ('BASE','STRESS')]
            tp=[report['summary']['TRAIL_60D_0.0025_'+layer] for layer in ('BASE','STRESS')]
            trail_superior=all(t['net']>c['net'] and t['pf']>c['pf'] and t['net']>0 and t['pf']>1 and t['net_without_top1']>0 for c,t in zip(cp,tp))
            fixed_superior=all(c['net']>t['net'] and c['pf']>t['pf'] and c['net']>0 and c['pf']>1 and c['net_without_top1']>0 for c,t in zip(cp,tp))
            report['verdict']='TRAILING_OUTPERFORMS_4R' if trail_superior else '4R_OUTPERFORMS_TRAILING' if fixed_superior else 'MIXED_OR_BOTH_FAIL'
    (OUT/'report.json').write_text(json.dumps(report,indent=2))
    (OUT/'custody.json').write_text(json.dumps({
        str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in OUT.rglob('*') if p.is_file() and p.name!='custody.json'
    },indent=2))
    print('VERDICT',report['verdict'],flush=True)
    for k,v in report['summary'].items():
        print('SUMMARY',k,json.dumps(v),flush=True)
    if report['verdict'] in ('SOURCE_BLOCKED','CONTROL_PARITY_BLOCKED'):
        raise RuntimeError('Fail closed: '+report['verdict'])

if __name__=='__main__':main()
