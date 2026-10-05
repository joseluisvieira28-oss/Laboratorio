"""Frozen 1m screen. Outputs diagnostics, never fictitious executable fills."""
import collections, datetime as dt, hashlib, json, math, pathlib, random, statistics
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parent
def load(label):
    rows={}; conflicts=0; errors=[]
    for p in sorted((ROOT/'raw').glob(label+'_*.json')):
        rec=json.loads(p.read_text()); r=rec.get('response',{})
        if not r.get('success'): errors.append(p.name); continue
        d=r.get('data',{}); times=d.get('time',[])
        for i,t in enumerate(times):
            row={k:v[i] for k,v in d.items() if isinstance(v,list) and len(v)==len(times)}
            if t in rows and rows[t]!=row: conflicts+=1
            rows[t]=row
    return rows,conflicts,errors
def ci_by_day(trades):
    groups=collections.defaultdict(list)
    for t,p in trades: groups[t//86400].append(p)
    days=list(groups.values()); rng=random.Random(2801)
    if len(days)<30: return None
    means=[]
    for _ in range(2000):
        blocks=rng.choices(days,k=len(days)); means.append(sum(map(sum,blocks))/sum(map(len,blocks)))
    means.sort(); return [means[10],means[1989]]
def summary(trades):
    vals=[v for t,v in trades]
    return {'signals':len(vals),'active_days':len({t//86400 for t,v in trades}),'mean_bps':statistics.mean(vals) if vals else None,'ci99_day_block':ci_by_day(trades)}
def main():
    series={}; quality={}
    for label in ['last','index','fair']:
        series[label],c,e=load(label); quality[label]={'bars':len(series[label]),'conflicts':c,'failed_requests':e}
    last=series['last']; common=sorted(set(last)&set(series['index'])&set(series['fair']))
    days=sorted({t//86400 for t in common}); a=len(days)//2; b=a+len(days)//4
    segments={'Discovery':days[:a],'OOS':days[a:b],'Holdout':days[b:]}
    splits={n:{'days':len(ds),'start_day':ds[0] if ds else None,'end_day':ds[-1] if ds else None} for n,ds in segments.items()}
    funding=[]
    for p in (ROOT/'raw').glob('funding_*.json'):
        funding.extend(json.loads(p.read_text()).get('response',{}).get('data',{}).get('resultList',[]))
    funding={int(x['settleTime'])//1000:float(x['fundingRate']) for x in funding}
    def path_test(ts,ref,shift=0,delay=0,reverse=False):
        trades=[]; next_allowed=-1; excluded=collections.Counter()
        eligible=set(ts)
        for t in ts:
            if t<next_allowed: continue
            signal_t=t-shift
            if signal_t not in eligible or signal_t not in ref: continue
            p=float(last[signal_t]['close']); q=float(ref[signal_t]['close'])
            if p<=0 or q<=0: continue
            residual=(p/q-1)*10000
            if abs(residual)<20: continue
            entry=t+60*(1+delay); exit=entry+300
            if any(z not in eligible or float(last[z].get('vol',0))<=0 for z in range(t,exit+1,60)):
                excluded['gap_or_zero_volume_or_boundary']+=1; continue
            direction=(-1 if residual>0 else 1)*(-1 if reverse else 1)
            e=float(last[entry]['open']); x=float(last[exit]['open'])
            if e<=0 or x<=0: continue
            gross=direction*(x/e-1)*10000
            # Funding only as separate diagnostic; no claim missing dates imply zero.
            settled=sum(direction*rate*10000 for z,rate in funding.items() if entry<z<=exit)
            trades.append({'t':t,'gross':gross,'fee_only':gross-16,'stress_net':gross-20-settled,'funding':settled})
            next_allowed=exit
        return trades,dict(excluded)
    results={'quality':quality,'splits':splits,'common_bars':len(common),'funding':{'settlements':len(funding),'first':min(funding) if funding else None,'last':max(funding) if funding else None},'H2':{}}
    results['observed_start']=min(common) if common else None; results['observed_end']=max(common) if common else None
    results['coverage_within_observed_span']=len(common)/((max(common)-min(common))//60+1) if common else None
    for refname in ['index','fair']:
        ref=series[refname]; results['H2'][refname]={}
        for n,ds in segments.items():
            ts=[t for t in common if t//86400 in set(ds)]
            # Purge last five minutes of each split; eligibility prevents cross-boundary returns.
            magnitudes=[abs((float(last[t]['close'])/float(ref[t]['close'])-1)*10000) for t in ts if float(ref[t]['close'])>0 and float(last[t]['close'])>0 and float(last[t].get('vol',0))>0]
            trades,excluded=path_test(ts,ref)
            out={'eligible_magnitude_bars':len(magnitudes),'max_abs_residual_bps':max(magnitudes) if magnitudes else None,'above_16':sum(v>=16 for v in magnitudes),'above_20':sum(v>=20 for v in magnitudes),'fee_only':summary([(r['t'],r['fee_only']) for r in trades]),'stress_net_unverified_funding_coverage':summary([(r['t'],r['stress_net']) for r in trades]),'excluded':excluded}
            for label,kw in [('reverse',{'reverse':True}),('day_shift',{'shift':86400}),('extra_delay',{'delay':1})]:
                control,_=path_test(ts,ref,**kw); out[label]=summary([(r['t'],r['fee_only']) for r in control])
            out['regimes_utc_hours']={}
            regimes=collections.defaultdict(list)
            for r in trades:
                ny=dt.datetime.fromtimestamp(r['t']+60,dt.timezone.utc).astimezone(ZoneInfo('America/New_York')); minute=ny.hour*60+ny.minute
                label='weekend' if ny.weekday()>=5 else 'premarket' if 240<=minute<570 else 'cash_clock' if 570<=minute<960 else 'after_hours' if 960<=minute<1200 else 'overnight'
                regimes[label].append((r['t'],r['fee_only']))
                if ny.weekday()<5 and 555<=minute<585: regimes['open_window'].append((r['t'],r['fee_only']))
                if ny.weekday()<5 and 945<=minute<975: regimes['close_window'].append((r['t'],r['fee_only']))
            out['regimes_new_york_wall_clock_not_holiday_verified']={k:summary(v) for k,v in regimes.items()}
            # Hour bins avoid false session/holiday claims when calendar unavailable.
            for h in range(24):
                selected=[(r['t'],r['fee_only']) for r in trades if (r['t']//3600)%24==h]
                out['regimes_utc_hours'][str(h)]={'signals':len(selected),'mean_bps':statistics.mean(v for t,v in selected) if selected else None}
            results['H2'][refname][n]=out
    info=json.loads((ROOT/'raw/contract_detail.json').read_text()).get('response',{}).get('data',[])
    results['contract_census']=[{'symbol':x['symbol'],'name':x.get('fn'),'indexOrigin':x.get('indexOrigin')} for x in info if any(s in str(x).upper() for s in ['NVIDIA','NVDA'])]
    spots=json.loads((ROOT/'raw/spot_exchange_info.json').read_text()).get('response',{}).get('symbols',[])
    results['spot_census']=[x for x in spots if any(s in x.get('symbol','') for s in ['NVDA','NVIDIA'])]
    results['verdicts']={'H1':'BLOCKED: aligned Nasdaq/share and confirmed historical dependency/normalized token rail unavailable','H2':'BLOCKED: historical execution BBO/L2 and known-at-T publication timing unavailable; 1m diagnostic only','H3':'BLOCKED: token bars obtainable but total-return/share normalization, dated index dependency and executable costs missing','H4':'BLOCKED: session calendar/earnings timestamps and execution history unavailable; no event-specific outcomes selected','H5':'BLOCKED: no confirmed second interchangeable NVDA MEXC future','global':'BLOCKED'}
    for refname,outs in results['H2'].items():
        if all(o['max_abs_residual_bps'] is not None and o['max_abs_residual_bps']<16 for o in outs.values()):
            results['verdicts']['H2_'+refname+'_magnitude']='NO_EDGE'
        else:
            tests=[outs[n]['fee_only'] for n in ['OOS','Holdout']]
            if all(s['active_days']>=30 and s['ci99_day_block'] and s['ci99_day_block'][1]<0 for s in tests):
                results['verdicts']['H2_'+refname+'_fixed_1m_rule']='NO_EDGE'
            else: results['verdicts']['H2_'+refname+'_fixed_1m_rule']='BLOCKED: not an executable edge; magnitude/cost/source gates unresolved'
    (ROOT/'results.json').write_text(json.dumps(results,indent=2))
    manifest=[]
    for p in sorted((ROOT/'raw').glob('*.json')):
        manifest.append({'file':'raw/'+p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (ROOT/'evidence_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:results[k] for k in ['quality','common_bars','splits','funding','verdicts']},indent=2))
    for ref,outs in results['H2'].items():
        print(ref,json.dumps({n:{k:v for k,v in o.items() if k in ['max_abs_residual_bps','above_16','above_20','fee_only','reverse','day_shift','extra_delay']} for n,o in outs.items()},indent=2))
if __name__=='__main__': main()
