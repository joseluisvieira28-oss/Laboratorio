import csv
import hashlib
import io
import json
import math
import random
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROTO=HERE/'FROZEN_PROTOCOL_V01.json'
OUTDIR=HERE/'discovery_evidence'
OUT=OUTDIR/'CBLL_DISCOVERY_RESULT_V01.json'
DV='https://data.binance.vision'
CB='https://api.exchange.coinbase.com'
UA={'User-Agent':'Mozilla/5.0 CBLL-USDT-5M-Z3-001/1.0'}
ASSETS={'BTC':('BTC-USDT','BTCUSDT'),'ETH':('ETH-USDT','ETHUSDT')}
START=datetime(2022,1,1,tzinfo=timezone.utc)
END=datetime(2024,1,1,tzinfo=timezone.utc)
BAR=300
ROLL=2016
ZTH=3.0

GUARDS={'year_2024_opened':False,'year_2025_opened':False,'year_2026_opened':False,'live_trading':False,'exchange_mutation':False,'orders':False}

class DataFailure(RuntimeError): pass
class SourceBlocked(RuntimeError): pass

def get(url,attempts=6,allow_404=False):
    last=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=40) as r:return r.read()
        except urllib.error.HTTPError as e:
            if allow_404 and e.code==404:return None
            last=e
            if e.code not in (429,500,502,503,504):break
        except Exception as e:last=e
        time.sleep(min(8,0.5*(2**i)))
    raise SourceBlocked(f'GET_FAILED:{url}:{type(last).__name__}:{last}')

def month_iter(start,end):
    y,m=start.year,start.month
    while (y,m)<(end.year,end.month):
        yield f'{y:04d}-{m:02d}'
        m+=1
        if m==13:y+=1;m=1

def parse_checksum(raw,name):
    parts=raw.decode('utf-8','replace').strip().split()
    if not parts:raise DataFailure(f'EMPTY_CHECKSUM:{name}')
    dg=parts[0].lower()
    if len(dg)!=64 or any(c not in '0123456789abcdef' for c in dg):raise DataFailure(f'BAD_CHECKSUM:{name}')
    return dg

def load_binance(symbol):
    bars={}; receipts=[]
    for ym in month_iter(START,END):
        p=f'data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{ym}.zip'
        cb=get(f'{DV}/{p}.CHECKSUM',allow_404=True)
        if cb is None:raise DataFailure(f'BINANCE_CHECKSUM_MISSING:{p}')
        official=parse_checksum(cb,p.rsplit('/',1)[-1]); z=get(f'{DV}/{p}')
        actual=hashlib.sha256(z).hexdigest()
        if actual!=official:raise DataFailure(f'BINANCE_SHA_MISMATCH:{p}')
        receipts.append({'path':p,'sha256':actual})
        with zipfile.ZipFile(io.BytesIO(z)) as zz:
            bad=zz.testzip()
            if bad:raise DataFailure(f'BINANCE_ZIP_CRC:{bad}')
            names=[n for n in zz.namelist() if not n.endswith('/')]
            if len(names)!=1:raise DataFailure(f'BINANCE_MEMBER_COUNT:{p}')
            with zz.open(names[0]) as f:
                w=io.TextIOWrapper(f,encoding='utf-8-sig',errors='replace',newline='')
                for row in csv.reader(w):
                    if not row:continue
                    if str(row[0]).lower() in {'open_time','opentime'}:continue
                    if len(row)<6:raise DataFailure(f'BINANCE_ROW_SHORT:{p}')
                    n=int(row[0]); sec=n/1_000_000 if n>10**14 else n/1000 if n>10**11 else n
                    ts=int(sec)
                    if ts<int(START.timestamp()) or ts>=int(END.timestamp()):continue
                    bars[ts]=(float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]))
    return bars,receipts

def iso(dt):return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

def load_coinbase(product):
    bars={}; cursor=START; calls=0
    # 299 bars per request leaves room for endpoint edge semantics.
    step=timedelta(seconds=BAR*299)
    while cursor<END:
        stop=min(END,cursor+step)
        q=urllib.parse.urlencode({'granularity':BAR,'start':iso(cursor),'end':iso(stop)})
        raw=get(f'{CB}/products/{product}/candles?{q}')
        calls+=1
        try:d=json.loads(raw)
        except Exception as e:raise DataFailure(f'COINBASE_JSON:{product}:{e}')
        if isinstance(d,dict) and d.get('message'):raise SourceBlocked(f'COINBASE_MESSAGE:{product}:{d}')
        if not isinstance(d,list):raise DataFailure(f'COINBASE_NOT_LIST:{product}')
        for row in d:
            if not isinstance(row,list) or len(row)<6:raise DataFailure(f'COINBASE_ROW_SHAPE:{product}:{row}')
            ts=int(row[0])
            if ts<int(START.timestamp()) or ts>=int(END.timestamp()):continue
            # Coinbase schema: time, low, high, open, close, volume
            bars[ts]=(float(row[3]),float(row[2]),float(row[1]),float(row[4]),float(row[5]))
        cursor=stop
        time.sleep(0.12)
    return bars,{'product':product,'calls':calls,'endpoint':f'{CB}/products/{product}/candles','granularity_seconds':BAR}

def expected_timestamps():
    a=int(START.timestamp());b=int(END.timestamp())
    return list(range(a,b,BAR))

def compute_signals(cb,bn):
    tslist=expected_timestamps(); divs={}; sync=0
    for ts in tslist:
        if ts in cb and ts in bn:
            co,_,_,cc,_=cb[ts];bo,_,_,bc,_=bn[ts]
            if co>0 and bo>0:
                divs[ts]=(cc/co-1.0)-(bc/bo-1.0);sync+=1
    signals=[]
    # Contiguous prior-window requirement closes missing-bar ambiguity.
    for i in range(ROLL,len(tslist)-1):
        ts=tslist[i]
        if ts not in divs:continue
        prior_ts=tslist[i-ROLL:i]
        if any(x not in divs for x in prior_ts):continue
        vals=[divs[x] for x in prior_ts]
        sd=statistics.stdev(vals)
        if not math.isfinite(sd) or sd<=0:continue
        mu=statistics.fmean(vals);z=(divs[ts]-mu)/sd
        if z>=ZTH:signals.append({'signal_ts':ts,'z':z,'divergence':divs[ts]})
    return signals,sync,len(tslist)

def simulate(asset,signals,bn,cost):
    trades=[];busy_until=-1
    for s in signals:
        entry_ts=s['signal_ts']+BAR
        if entry_ts<=busy_until or entry_ts not in bn:continue
        entry=bn[entry_ts][0]
        if entry<=0:continue
        stop=entry*0.99;target=entry*1.02
        exit_px=None;exit_ts=None;why=None
        for k in range(12):
            ts=entry_ts+k*BAR
            if ts not in bn:exit_px=None;break
            o,h,l,c,_=bn[ts]
            if o<=stop:exit_px=o;exit_ts=ts;why='GAP_STOP';break
            if o>=target:exit_px=target;exit_ts=ts;why='GAP_TARGET_CAPPED';break
            if l<=stop and h>=target:exit_px=stop;exit_ts=ts;why='SAME_BAR_STOP_FIRST';break
            if l<=stop:exit_px=stop;exit_ts=ts;why='STOP';break
            if h>=target:exit_px=target;exit_ts=ts;why='TARGET';break
            if k==11:exit_px=c;exit_ts=ts;why='TIME';break
        if exit_px is None:continue
        gross=exit_px/entry-1.0;net=gross-cost;net_r=net/0.01
        trades.append({'asset':asset,'signal_ts':s['signal_ts'],'entry_ts':entry_ts,'exit_ts':exit_ts,'signal_z':s['z'],'divergence':s['divergence'],'entry':entry,'exit':exit_px,'exit_reason':why,'gross_return':gross,'net_return':net,'net_R':net_r})
        busy_until=exit_ts
    return trades

def pf(vals):
    gp=sum(x for x in vals if x>0);gl=-sum(x for x in vals if x<0)
    if gl==0:return float('inf') if gp>0 else 0.0
    return gp/gl

def metrics(trades):
    vals=[x['net_R'] for x in trades]
    return {'n':len(vals),'mean_net_R':statistics.fmean(vals) if vals else None,'profit_factor':pf(vals) if vals else None,'win_rate':sum(x>0 for x in vals)/len(vals) if vals else None,'sum_net_R':sum(vals)}

def bootstrap_daily(trades):
    byday=defaultdict(float)
    for t in trades:
        d=datetime.fromtimestamp(t['entry_ts'],tz=timezone.utc).date().isoformat();byday[d]+=t['net_R']
    days=[];d=START.date();end=END.date()
    while d<end:
        days.append(byday.get(d.isoformat(),0.0));d+=timedelta(days=1)
    rng=random.Random(20260916);means=[];n=len(days)
    for _ in range(10000):means.append(sum(days[rng.randrange(n)] for __ in range(n))/n)
    means.sort();lo=means[int(0.025*(len(means)-1))];hi=means[int(0.975*(len(means)-1))]
    return {'days':n,'mean_daily_portfolio_R':statistics.fmean(days),'bootstrap_95_lower':lo,'bootstrap_95_upper':hi}

def concentration(trades):
    pos=defaultdict(float)
    for t in trades:
        if t['net_R']>0:
            m=datetime.fromtimestamp(t['entry_ts'],tz=timezone.utc).strftime('%Y-%m');pos[m]+=t['net_R']
    total=sum(pos.values())
    return max(pos.values())/total if total>0 and pos else 1.0

def leave_one_min_mean(trades):
    vals=[t['net_R'] for t in trades];n=len(vals)
    if n<=1:return None
    s=sum(vals);return min((s-x)/(n-1) for x in vals)

def main():
    p=json.loads(PROTO.read_text())
    assert p['status']=='FROZEN_PRE_OUTCOME';assert p['signal']['threshold']==3.0;assert p['universe']['timeframe_minutes']==5
    assert p['data']['no_2024_access_before_discovery_classification'] is True
    assert p['data']['no_2025_access'] is True and p['data']['no_2026_access'] is True
    source={'binance':{},'coinbase':{}};data={};source_failures=[]
    try:
        for asset,(cp,bs) in ASSETS.items():
            bn,br=load_binance(bs);cb,cr=load_coinbase(cp)
            data[asset]=(cb,bn);source['binance'][asset]=br;source['coinbase'][asset]=cr
    except SourceBlocked as e:
        OUTDIR.mkdir(parents=True,exist_ok=True);doc={'classification':'SOURCE_ACCESS_BLOCKED','reason':str(e),'guards':GUARDS};OUT.write_text(json.dumps(doc,indent=2)+'\n');print(json.dumps(doc,indent=2));return
    except Exception as e:
        OUTDIR.mkdir(parents=True,exist_ok=True);doc={'classification':'DATA_FAILURE','reason':f'{type(e).__name__}:{e}','guards':GUARDS};OUT.write_text(json.dumps(doc,indent=2)+'\n');print(json.dumps(doc,indent=2));return
    all_base=[];all_stress=[];coverage={};signal_counts={}
    for asset,(cb,bn) in data.items():
        sig,sync,expected=compute_signals(cb,bn);coverage[asset]={'coinbase_bars':len(cb),'binance_bars':len(bn),'synchronized_bars':sync,'expected_bars':expected,'sync_fraction':sync/expected};signal_counts[asset]=len(sig)
        if sync/expected<0.995:source_failures.append(f'{asset}:SYNC_COVERAGE_LT_99.5PCT')
        all_base.extend(simulate(asset,sig,bn,p['strategy']['base_round_trip_cost_fraction']))
        all_stress.extend(simulate(asset,sig,bn,p['strategy']['stress_round_trip_cost_fraction']))
    all_base=sorted(all_base,key=lambda x:(x['entry_ts'],x['asset']))
    all_stress=sorted(all_stress,key=lambda x:(x['entry_ts'],x['asset']))
    if source_failures:
        classification='DATA_FAILURE';reason=';'.join(source_failures)
    elif len(all_base)<p['discovery']['sample_floor_resolved_trades']:
        classification='INSUFFICIENT_SAMPLE';reason='resolved trades below frozen floor'
    else:
        bm=metrics(all_base);sm=metrics(all_stress);boot=bootstrap_daily(all_base)
        byyear={str(y):metrics([t for t in all_base if datetime.fromtimestamp(t['entry_ts'],tz=timezone.utc).year==y]) for y in (2022,2023)}
        byasset={a:metrics([t for t in all_base if t['asset']==a]) for a in ASSETS}
        conc=concentration(all_base);loo=leave_one_min_mean(all_base)
        gates={
            'resolved_trades_gte':bm['n']>=100,
            'base_mean_net_R_gt':bm['mean_net_R']>0,
            'base_profit_factor_gt':bm['profit_factor']>1.10,
            'bootstrap_95_lower_mean_daily_portfolio_R_gt':boot['bootstrap_95_lower']>0,
            'stress_mean_net_R_gt':sm['mean_net_R']>0,
            'stress_profit_factor_gt':sm['profit_factor']>1.0,
            'calendar_year_2022_mean_net_R_gt':byyear['2022']['mean_net_R'] is not None and byyear['2022']['mean_net_R']>0,
            'calendar_year_2023_mean_net_R_gt':byyear['2023']['mean_net_R'] is not None and byyear['2023']['mean_net_R']>0,
            'btc_only_mean_net_R_gt':byasset['BTC']['mean_net_R'] is not None and byasset['BTC']['mean_net_R']>0,
            'eth_only_mean_net_R_gt':byasset['ETH']['mean_net_R'] is not None and byasset['ETH']['mean_net_R']>0,
            'max_positive_month_share_lte':conc<=0.25,
            'minimum_leave_one_trade_out_mean_net_R_gt':loo is not None and loo>0,
            'source_integrity_failures_eq':True,
            'execution_unresolved_eq':True,
        }
        classification='DISCOVERY_SURVIVES' if all(gates.values()) else 'DISCOVERY_NO_EDGE';reason='all frozen promotion gates passed' if classification=='DISCOVERY_SURVIVES' else 'one or more frozen promotion gates failed'
    bm=metrics(all_base);sm=metrics(all_stress);boot=bootstrap_daily(all_base) if all_base else None
    byyear={str(y):metrics([t for t in all_base if datetime.fromtimestamp(t['entry_ts'],tz=timezone.utc).year==y]) for y in (2022,2023)}
    byasset={a:metrics([t for t in all_base if t['asset']==a]) for a in ASSETS}
    conc=concentration(all_base) if all_base else None;loo=leave_one_min_mean(all_base) if all_base else None
    gates=None
    if classification in {'DISCOVERY_SURVIVES','DISCOVERY_NO_EDGE'}:
        gates={
            'resolved_trades_gte':bm['n']>=100,'base_mean_net_R_gt':bm['mean_net_R']>0,'base_profit_factor_gt':bm['profit_factor']>1.10,
            'bootstrap_95_lower_mean_daily_portfolio_R_gt':boot['bootstrap_95_lower']>0,'stress_mean_net_R_gt':sm['mean_net_R']>0,'stress_profit_factor_gt':sm['profit_factor']>1.0,
            'calendar_year_2022_mean_net_R_gt':byyear['2022']['mean_net_R'] is not None and byyear['2022']['mean_net_R']>0,
            'calendar_year_2023_mean_net_R_gt':byyear['2023']['mean_net_R'] is not None and byyear['2023']['mean_net_R']>0,
            'btc_only_mean_net_R_gt':byasset['BTC']['mean_net_R'] is not None and byasset['BTC']['mean_net_R']>0,
            'eth_only_mean_net_R_gt':byasset['ETH']['mean_net_R'] is not None and byasset['ETH']['mean_net_R']>0,
            'max_positive_month_share_lte':conc<=0.25,'minimum_leave_one_trade_out_mean_net_R_gt':loo is not None and loo>0,
            'source_integrity_failures_eq':len(source_failures)==0,'execution_unresolved_eq':True}
    doc={'lab_id':p['lab_id'],'mve_id':p['mve_id'],'classification':classification,'reason':reason,'coverage':coverage,'signal_counts':signal_counts,'base_metrics':bm,'stress_metrics':sm,'bootstrap_daily':boot,'by_year':byyear,'by_asset':byasset,'max_positive_month_share':conc,'minimum_leave_one_trade_out_mean_net_R':loo,'promotion_gates':gates,'source_failures':source_failures,'guards':GUARDS,'source_receipts':source,'trades_base':all_base}
    OUTDIR.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(doc,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:doc[k] for k in ['classification','reason','coverage','signal_counts','base_metrics','stress_metrics','bootstrap_daily','by_year','by_asset','max_positive_month_share','minimum_leave_one_trade_out_mean_net_R','promotion_gates','guards']},indent=2,sort_keys=True,allow_nan=False))

if __name__=='__main__':main()
