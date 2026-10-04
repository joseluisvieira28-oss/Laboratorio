"""Conforming source-only export. No external data or parent price responses."""
from __future__ import annotations
import argparse, concurrent.futures, csv, datetime as dt, gzip, hashlib, importlib.util, io, json, math, os
from collections import Counter, deque
from pathlib import Path

PARENT_SHA='7f135689afd9f51a758e2c98b5c8da9fe3c7f3eca15f40eced7fdb53b03d2eaf'
REFERENCE_SHA='6b85aaa5eb20b223a4e4b275960abf2eaf9f3852c0b8481fa1493257f7bdc737'
MANIFEST_SHA='59e16ce8ea41658c2ea0fc6f2489d4deafbdc676e008d0b93f95ee6e3864913d'
ANCHOR_SHA='be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3'
RR_ABS_TOL=1e-10
RR_REL_TOL=1e-12
H=(1000,5000,15000,60000)
R=(1000,5000,15000)
CELLS=(('R1_Y5',1000,5000),('R1_Y15',1000,15000),('R1_Y60',1000,60000),('R5_Y15',5000,15000),('R5_Y60',5000,60000),('R15_Y60',15000,60000))
FIELDS=['event_id','segment_id','anchor_date_utc','anchor_envelope_ns','anchor_payload_ms','side','direction','pre_depth5','zero_pre_depth']
for h in R: FIELDS += [f'r_{h}_{x}' for x in ('status','envelope_ns','payload_ms','lateness_ms','same_side_depth5','rr','class')]
FIELDS += ['timing_60000_status','timing_60000_envelope_ns']
class Fail(RuntimeError): pass
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def parent(path):
    if sha(path)!=PARENT_SHA: raise Fail('parent byte identity mismatch')
    spec=importlib.util.spec_from_file_location('frozen_parent',path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod
def source_extract(p,obj):
    # Exact frozen validation/float arithmetic; no midpoint constructed or returned.
    raw=obj.get('raw')
    if not isinstance(raw,dict) or raw.get('channel')!='l2Book': raise Fail('raw/channel')
    d=raw.get('data')
    if not isinstance(d,dict) or d.get('coin')!='BTC': raise Fail('data/coin')
    payload=d.get('time')
    if isinstance(payload,bool) or not isinstance(payload,int): raise Fail('payload integer')
    levels=d.get('levels')
    if not isinstance(levels,list) or len(levels)!=2: raise Fail('levels')
    px=[]; depths=[]
    for side in levels:
        if len(side)<5: raise Fail('top5 absent')
        prices=[]; sizes=[]
        for i,l in enumerate(side):
            if not isinstance(l,dict): raise Fail('level object')
            price=p.finite_num(l.get('px'),'px'); size=p.finite_num(l.get('sz'),'sz'); n=l.get('n')
            if price<=0 or size<0 or isinstance(n,bool) or not isinstance(n,int) or n<0: raise Fail('level validity')
            prices.append(price)
            if i<5: sizes.append(size)
        px.append(tuple(prices)); depths.append(sum(sizes))
    if not all(px[0][i]>px[0][i+1] for i in range(4)): raise Fail('bid order')
    if not all(px[1][i]<px[1][i+1] for i in range(4)): raise Fail('ask order')
    if px[0][0]>=px[1][0]: raise Fail('crossed book')
    return {'payload_ms':payload,'bid_best':px[0][0],'ask_best':px[1][0],'bid_prices_all':px[0],'ask_prices_all':px[1],'bid_depth5':depths[0],'ask_depth5':depths[1]}
def work(job):
    sid,rows,root,out,pp=job; p=parent(pp); root=Path(root); out=Path(out)
    final=out/f'parent_state_segment_{sid:02d}.csv.gz'; tmp=final.with_suffix('.partial')
    totals=Counter(); timing={h:Counter() for h in H}; cc={c:Counter() for c,_,_ in CELLS}
    daily={}; active={}; q={h:deque() for h in H}; ready={}; next_write=0; seq=0
    last_env=None; last_payload=None; prev=None
    with tmp.open('xb') as rawout, gzip.GzipFile(filename='',mode='wb',fileobj=rawout,mtime=0,compresslevel=1) as zipped, io.TextIOWrapper(zipped,encoding='utf-8',newline='') as text:
        writer=csv.DictWriter(text,fieldnames=FIELDS,lineterminator='\n'); writer.writeheader()
        def finalize(ev):
            nonlocal next_write
            pre=ev['pre']; row={'event_id':f'{sid:02d}:{ev["seq"]:09d}','segment_id':sid,'anchor_date_utc':ev['date'],'anchor_envelope_ns':ev['env'],'anchor_payload_ms':ev['payload'],'side':ev['side'],'direction':ev['direction'],'pre_depth5':repr(pre),'zero_pre_depth':int(pre<=0)}
            for h in R:
                state=ev['h'][h]; prefix=f'r_{h}_'
                row[prefix+'status']='ZERO_PRE_DEPTH_UNDEFINED' if pre<=0 else ('AVAILABLE' if state else 'MISSING_SOURCE_TIMING')
                for name in ('envelope_ns','payload_ms','lateness_ms','same_side_depth5','rr','class'): row[prefix+name]=''
                if state:
                    env,payload,depth=state
                    row[prefix+'envelope_ns']=env; row[prefix+'payload_ms']=payload
                    row[prefix+'lateness_ms']=repr((env-ev['env']-h*1000000)/1000000)
                    row[prefix+'same_side_depth5']=repr(depth)
                    if pre>0:
                        rr=depth/pre; group='WEAK' if depth<pre else 'STRONG'
                        if group != ('WEAK' if rr<1 else 'STRONG'): raise Fail('float class mismatch')
                        row[prefix+'rr']=repr(rr); row[prefix+'class']=group
            row['timing_60000_status']='AVAILABLE' if ev['h'][60000] else 'MISSING_SOURCE_TIMING'
            row['timing_60000_envelope_ns']=ev['h'][60000][0] if ev['h'][60000] else ''
            # Y states used only for historical cell eligibility, never parent price response.
            for cell,rh,yh in CELLS:
                c=cc[cell]; c['anchors_total']+=1
                if pre<=0: c['zero_pre_depth']+=1; continue
                r=ev['h'][rh]; y=ev['h'][yh]
                if r is None or y is None: c['timing_missing']+=1; continue
                rr=r[2]/pre; group='weak' if r[2]<pre else 'strong'
                c['valid']+=1; c[group+'_n']+=1; c[group+'_sum_rr']+=rr
                k=(ev['date'],cell,group); v=daily.setdefault(k,[0,0.0]); v[0]+=1; v[1]+=rr
            ready[ev['seq']]=row
            while next_write in ready:
                writer.writerow(ready.pop(next_write)); next_write+=1
        def resolve(eid,h,state,kind):
            ev=active[eid]
            if h in ev['h']: raise Fail('double horizon')
            ev['h'][h]=state; timing[h][kind]+=1
            if len(ev['h'])==4: finalize(ev); del active[eid]
        def consume(env,state):
            nonlocal prev,seq
            for h in H:
                while q[h] and q[h][0][0]<=env:
                    target,eid=q[h].popleft(); ev=active[eid]
                    if env-target<=p.MAX_LATENESS_NS:
                        depth=state['ask_depth5'] if ev['side']=='ASK' else state['bid_depth5']
                        resolve(eid,h,(env,state['payload_ms'],depth),'available')
                    else: resolve(eid,h,None,'missing_late')
            if prev is not None:
                totals['eligible_transitions']+=1
                a=state['ask_best']>prev['ask_best']; b=state['bid_best']<prev['bid_best']
                side=None
                if a and b: totals['ambiguous']+=1
                elif a:
                    if prev['ask_best'] in state['ask_prices_all']: raise Fail('prior ask present')
                    side='ASK'
                elif b:
                    if prev['bid_best'] in state['bid_prices_all']: raise Fail('prior bid present')
                    side='BID'
                else: totals['non_sweep']+=1
                if side:
                    totals['ask_sweeps' if side=='ASK' else 'bid_sweeps']+=1
                    active[seq]={'seq':seq,'env':env,'payload':state['payload_ms'],'date':p.anchor_date(env),'side':side,'direction':1 if side=='ASK' else -1,'pre':prev['ask_depth5' if side=='ASK' else 'bid_depth5'],'h':{}}
                    for h in H: q[h].append((env+h*1000000,seq))
                    seq+=1
            prev=state
        for index,r in enumerate(rows):
            path=root/r['key']; start,end=p.key_bounds_ns(r['key']); pending=b''; size=0; h256=hashlib.sha256(); md5=hashlib.md5(); dec=p.lz4.frame.LZ4FrameDecompressor()
            def line(data):
                nonlocal last_env,last_payload
                totals['records']+=1; obj=json.loads(data); env=p.parse_env_ns(obj['time']); state=source_extract(p,obj); payload=state['payload_ms']
                if not start<=env<end: raise Fail('envelope key boundary')
                if last_env is not None and env<last_env: raise Fail('envelope backwards')
                if payload*1000000>env: raise Fail('future payload')
                last_env=env
                if last_payload is not None and payload<last_payload: totals['stale']+=1; return
                if last_payload is not None and payload==last_payload: totals['equal']+=1
                last_payload=payload; totals['accepted']+=1; consume(env,state)
            with path.open('rb') as f:
                for chunk in iter(lambda:f.read(p.READ_CHUNK),b''):
                    size+=len(chunk); h256.update(chunk); md5.update(chunk); pending+=dec.decompress(chunk)
                    lines=pending.split(b'\n'); pending=lines.pop()
                    for data in lines:
                        if data.strip(): line(data)
            if pending.strip(): line(pending)
            if not dec.eof: raise Fail('incomplete lz4')
            if size!=int(r['actual_size']) or h256.hexdigest()!=r['sha256'] or md5.hexdigest()!=r['md5'] or r['md5']!=r['inventory_etag'].strip('"'): raise Fail('RAW byte mismatch')
            totals['objects']+=1
            if (index+1)%100==0: print(f'segment {sid}: {index+1}/{len(rows)} objects, {totals["records"]:,} records',flush=True)
        for h in H:
            while q[h]:
                _,eid=q[h].popleft(); resolve(eid,h,None,'missing_segment_end')
        if active or ready or next_write!=seq: raise Fail('unwritten events')
    if (totals['ask_sweeps'],totals['bid_sweeps'],totals['ambiguous'])!=p.EXPECTED_SEGMENT_EVENTS[sid]: raise Fail('segment identity')
    os.replace(tmp,final)
    result={'segment_id':sid,'file':str(final.resolve()),'sha256':sha(final),'size':final.stat().st_size,'rows':seq,'totals':dict(totals),'timing':{str(h):dict(v) for h,v in timing.items()},'cells':{c:dict(v) for c,v in cc.items()},'daily':[{'date':k[0],'cell':k[1],'group':k[2],'n':v[0],'sum_rr':v[1]} for k,v in sorted(daily.items())]}
    (out/f'segment_{sid:02d}_receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
def identity(p,results,reference):
    totals=Counter(); timing={h:Counter() for h in H}; cells={c:Counter() for c,_,_ in CELLS}
    for result in results:
        totals.update(result['totals'])
        for h in H: timing[h].update(result['timing'][str(h)])
        for c in cells: cells[c].update(result['cells'][c])
    guards={name:totals[name]==getattr(p,'EXPECTED_'+name.upper()) for name in ('objects','records','accepted','stale','equal','eligible_transitions','ask_sweeps','bid_sweeps','ambiguous')}
    guards['sweeps']=sum(x['rows'] for x in results)==p.EXPECTED_SWEEPS
    guards['segments']=len(results)==p.EXPECTED_SEGMENTS
    for h in H:
        for name,expected in (('available',p.EXPECTED_TIMING_AVAILABLE),('missing_late',p.EXPECTED_TIMING_MISSING_LATE),('missing_segment_end',p.EXPECTED_TIMING_MISSING_END)):
            guards[f'timing_{h}_{name}']=timing[h][name]==expected[h]
    reports=[]
    for expected in reference['cells']:
        c=expected['cell']; obs=cells[c]; report={'cell':c,**dict(obs)}
        for k in ('anchors_total','zero_pre_depth','timing_missing','valid','weak_n','strong_n'): guards[c+'_'+k]=obs[k]==expected[k]
        for group in ('weak','strong'):
            mean=obs[group+'_sum_rr']/obs[group+'_n']; exp=expected[group+'_event_mean_rr']
            guards[c+'_'+group+'_mean_rr']=math.isclose(mean,exp,rel_tol=RR_REL_TOL,abs_tol=RR_ABS_TOL)
            report[group+'_mean_rr']=mean; report[group+'_reference_mean_rr']=exp; report[group+'_abs_difference']=abs(mean-exp)
        reports.append(report)
    return guards,dict(totals),{str(h):dict(v) for h,v in timing.items()},reports
def main():
    a=argparse.ArgumentParser(); a.add_argument('--raw-root',required=True); a.add_argument('--parent-runner',required=True); a.add_argument('--reference',required=True); a.add_argument('--out-dir',required=True); a.add_argument('--workers',type=int,default=4); args=a.parse_args()
    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    receipt_path=out/'PARENT_STATE_MATERIALIZATION_RECEIPT_V0_2.json'
    try:
        p=parent(args.parent_runner); root=Path(args.raw_root)
        manifest=root/'L2_RESILIENCY_001_2024_BTC_RAW_SHA256_MANIFEST_V0_1.csv'; anchor=root/'_SWEEP_EVENT_PREFLIGHT_V0_1/L2_RESILIENCY_001_SWEEP_EVENT_ANCHORS_V0_1.csv'
        if sha(manifest)!=MANIFEST_SHA or sha(anchor)!=ANCHOR_SHA or sha(args.reference)!=REFERENCE_SHA: raise Fail('prerequisite byte identity')
        reference=json.loads(Path(args.reference).read_text()); rows=list(csv.DictReader(manifest.open(encoding='utf-8-sig')))
        if len(rows)!=8707 or len({r['key'] for r in rows})!=8707 or sum(int(r['actual_size']) for r in rows)!=p.EXPECTED_BYTES: raise Fail('source universe')
        segments=p.build_segments(rows)
        if len(segments)!=11: raise Fail('segment universe')
        jobs=[(i+1,r,str(root),str(out),args.parent_runner) for i,r in enumerate(segments)]
        results=[]
        with concurrent.futures.ProcessPoolExecutor(max_workers=min(4,max(1,args.workers))) as pool:
            for result in pool.map(work,jobs): results.append(result); print(f'segment {result["segment_id"]} identity complete',flush=True)
        guards,totals,timing,cells=identity(p,results,reference)
        receipt={'lab_id':'L2R-CROSSVENUE-001','classification':'PARENT_STATE_MATERIALIZATION_PASS' if all(guards.values()) else 'PARENT_STATE_IDENTITY_FAIL_CLOSED','parent_runner_sha256':PARENT_SHA,'exporter_sha256':sha(__file__),'manifest_sha256':MANIFEST_SHA,'anchor_sha256':ANCHOR_SHA,'historical_reference_sha256':REFERENCE_SHA,'rr_abs_tolerance':RR_ABS_TOL,'rr_rel_tolerance':RR_REL_TOL,'guards':guards,'totals':totals,'timing':timing,'cells':cells,'segments':[{k:v for k,v in x.items() if k!='daily'} for x in results],'rows':sum(x['rows'] for x in results),'firewalls':{'binance_read':False,'new_parent_price_responses':False,'protected_year_source_read':False,'exchange_mutation':False}}
        receipt_path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'classification':receipt['classification'],'failed_guards':[k for k,v in guards.items() if not v],'receipt':str(receipt_path)},indent=2),flush=True)
        return 0 if all(guards.values()) else 2
    except Exception as exc:
        failure={'lab_id':'L2R-CROSSVENUE-001','classification':'PARENT_STATE_TECHNICAL_BLOCKED','failure':str(exc),'binance_read':False,'protected_year_source_read':False}
        receipt_path.write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8'); print(json.dumps(failure),flush=True); return 2
if __name__=='__main__': raise SystemExit(main())
