#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json, math, os, re, zipfile
from collections import Counter, defaultdict, deque
from pathlib import Path

LAB_ID='L2R-EXEC-PASSIVE-001'
PARENT_LAB_ID='L2-RESILIENCY-001'
IMPLEMENTATION_VERSION='0.1.1'
YEAR=2025
EXPECTED_MANIFEST_SHA256='767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3'
EXPECTED_OBJECTS=8400
EXPECTED_BYTES=8975275014
HORIZONS_MS=(1000,5000,15000,60000)
CELLS=(('R1_Y5',1000,5000),('R1_Y15',1000,15000),('R1_Y60',1000,60000),('R5_Y15',5000,15000),('R5_Y60',5000,60000),('R15_Y60',15000,60000))
MAX_LATENESS_NS=1_100_000_000
READ_CHUNK=1024*1024
KEY_RE=re.compile(r'^market_data/(2025\d{4})/([0-9]|1[0-9]|2[0-3])/l2Book/BTC\.lz4$')
ISO_RE=re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?Z?$')
# Current official Hyperliquid base schedule snapshot (freeze date 2026-09-24), bps per fill.
MAKER_SCENARIOS_BPS=(0.0,0.4,0.8,1.2,1.5)
TAKER_SCENARIOS_BPS=(2.4,2.6,2.8,3.0,3.5,4.0,4.5)

class FailClosed(RuntimeError): pass

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*READ_CHUNK),b''): h.update(b)
    return h.hexdigest()

def parse_env_ns(s:str)->int:
    m=ISO_RE.fullmatch(s.strip())
    if not m: raise FailClosed(f'invalid envelope time {s}')
    base,frac=m.groups(); d=dt.datetime.strptime(base,'%Y-%m-%dT%H:%M:%S').replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp())*1_000_000_000+int(((frac or '')+'000000000')[:9])

def key_hour(key:str)->dt.datetime:
    m=KEY_RE.fullmatch(key)
    if not m: raise FailClosed(f'illegal key {key}')
    ymd,hs=m.groups(); d=dt.datetime.strptime(ymd+f'{int(hs):02d}','%Y%m%d%H').replace(tzinfo=dt.timezone.utc)
    return d

def key_bounds_ns(key:str):
    d=key_hour(key); s=int(d.timestamp())*1_000_000_000; return s,s+3_600_000_000_000

def finite(v,name):
    if isinstance(v,bool): raise FailClosed(f'boolean {name}')
    try: x=float(v)
    except Exception as e: raise FailClosed(f'non-numeric {name}') from e
    if not math.isfinite(x): raise FailClosed(f'non-finite {name}')
    return x

def extract_state(o):
    if not isinstance(o,dict) or 'raw' not in o or 'time' not in o: raise FailClosed('schema top-level')
    raw=o['raw']; data=raw.get('data') if isinstance(raw,dict) else None
    if not isinstance(data,dict) or raw.get('channel')!='l2Book' or data.get('coin')!='BTC': raise FailClosed('schema raw/data')
    p=data.get('time'); levels=data.get('levels')
    if isinstance(p,bool) or not isinstance(p,int): raise FailClosed('payload time')
    if not isinstance(levels,list) or len(levels)!=2: raise FailClosed('levels')
    bids,asks=levels
    if len(bids)<5 or len(asks)<5: raise FailClosed('top5')
    bp=[]; ap=[]; bsz=[]; asz=[]
    for side,pxs,szs in ((bids,bp,bsz),(asks,ap,asz)):
        for i,l in enumerate(side):
            if not isinstance(l,dict): raise FailClosed('level object')
            px=finite(l.get('px'),'px'); sz=finite(l.get('sz'),'sz')
            if px<=0 or sz<0: raise FailClosed('bad level')
            pxs.append(px)
            if i<5: szs.append(sz)
    if not all(bp[i]>bp[i+1] for i in range(4)): raise FailClosed('bid order')
    if not all(ap[i]<ap[i+1] for i in range(4)): raise FailClosed('ask order')
    if bp[0]>=ap[0]: raise FailClosed('crossed book')
    return {'payload_ms':p,'bid':bp[0],'ask':ap[0],'mid':(bp[0]+ap[0])/2,
            'bid_prices_all':tuple(bp),'ask_prices_all':tuple(ap),'bid_depth5':sum(bsz),'ask_depth5':sum(asz)}

def build_segments(rows):
    rows=sorted(rows,key=lambda r:key_hour(r['key'])); out=[]; cur=[]; prev=None
    for r in rows:
        h=key_hour(r['key'])
        if prev is None or h==prev+dt.timedelta(hours=1): cur.append(r)
        else: out.append(cur); cur=[r]
        prev=h
    if cur: out.append(cur)
    return out

def ret_mid(direction,r,y): return direction*10000.0*(y['mid']/r['mid']-1.0)
def ret_taker(direction,r,y):
    if direction>0: return 10000.0*(y['bid']/r['ask']-1.0)
    return -10000.0*(y['ask']/r['bid']-1.0)
def ret_maker_upper(direction,r,y):
    # Same directional-return convention as the parent: direction * (exit/entry - 1).
    # Deliberately optimistic upper bound: certain passive fill at touch on both legs,
    # no queue delay/adverse selection, exit fill exactly at Y-touch.
    if direction>0: return 10000.0*(y['ask']/r['bid']-1.0)
    return -10000.0*(y['bid']/r['ask']-1.0)
def spread_bps(st): return 10000.0*(st['ask']-st['bid'])/st['mid']

def process_segment(seg_id, rows, base:Path):
    last_env=None; last_payload=None; prev=None
    active={}; queues={h:deque() for h in HORIZONS_MS}; eid=0
    stats={c[0]:{'n':0,'sum_mid':0.0,'sum_taker':0.0,'sum_maker_upper':0.0,'sum_entry_spread':0.0,'sum_exit_spread':0.0} for c in CELLS}
    totals=Counter()
    def finalize(ev):
        for name,rh,yh in CELLS:
            r=ev['h'].get(rh); y=ev['h'].get(yh)
            if r is None or y is None or ev['pre_depth']<=0: continue
            depth=r['ask_depth5'] if ev['side']=='ASK' else r['bid_depth5']
            if depth>=ev['pre_depth']: continue
            s=stats[name]; s['n']+=1
            s['sum_mid']+=ret_mid(ev['direction'],r,y)
            s['sum_taker']+=ret_taker(ev['direction'],r,y)
            s['sum_maker_upper']+=ret_maker_upper(ev['direction'],r,y)
            s['sum_entry_spread']+=spread_bps(r); s['sum_exit_spread']+=spread_bps(y)
    def resolve(i,h,st):
        ev=active.get(i)
        if ev is None or h in ev['resolved']: return
        ev['resolved'].add(h); ev['h'][h]=st
        if len(ev['resolved'])==len(HORIZONS_MS): finalize(ev); del active[i]
    def resolve_due(env,st):
        for h in HORIZONS_MS:
            q=queues[h]
            while q and q[0][0]<=env:
                target,i=q.popleft(); resolve(i,h,st if env-target<=MAX_LATENESS_NS else None)
    def create(env,side,pre_depth):
        nonlocal eid
        i=eid; eid+=1; direction=1.0 if side=='ASK' else -1.0
        active[i]={'side':side,'direction':direction,'pre_depth':pre_depth,'h':{},'resolved':set()}
        for h in HORIZONS_MS: queues[h].append((env+h*1_000_000,i))
    def consume(env,st):
        nonlocal prev
        resolve_due(env,st)
        if prev is not None:
            aw=st['ask']>prev['ask']; bw=st['bid']<prev['bid']
            if aw and bw: totals['ambiguous']+=1
            elif aw:
                if any(p==prev['ask'] for p in st['ask_prices_all']): raise FailClosed('prior ask still present')
                totals['ask_sweeps']+=1; create(env,'ASK',prev['ask_depth5'])
            elif bw:
                if any(p==prev['bid'] for p in st['bid_prices_all']): raise FailClosed('prior bid still present')
                totals['bid_sweeps']+=1; create(env,'BID',prev['bid_depth5'])
        prev=st
    for row in rows:
        key=row['key']; path=base/'HL_L2R_2025_BTC_RAW_V0_1'/Path(*str(row['local_relpath']).replace('\\','/').split('/'))
        start,end=key_bounds_ns(key); dec=None; pending=b''
        import lz4.frame
        dec=lz4.frame.LZ4FrameDecompressor(); h=hashlib.sha256(); hm=hashlib.md5(); actual=0
        def proc(line):
            nonlocal last_env,last_payload
            o=json.loads(line); env=parse_env_ns(o['time'])
            if not(start<=env<end): raise FailClosed('envelope outside key hour')
            st=extract_state(o); p=st['payload_ms']
            if last_env is not None and env<last_env: raise FailClosed('envelope backwards')
            future=p*1_000_000>env; last_env=env
            if last_payload is not None and p<last_payload: totals['stale']+=1; return
            if not future: last_payload=p
            totals['accepted']+=1; consume(env,st)
        with path.open('rb') as f:
            while True:
                b=f.read(READ_CHUNK)
                if not b: break
                actual+=len(b); h.update(b); hm.update(b)
                out=dec.decompress(b)
                if not out: continue
                pending+=out; parts=pending.split(b'\n'); pending=parts.pop()
                for line in parts:
                    if line.strip(): proc(line)
        if pending.strip(): proc(pending)
        if not dec.eof: raise FailClosed(f'incomplete LZ4 {key}')
        if actual!=int(row['content_length']) or h.hexdigest().lower()!=row['sha256'].lower() or hm.hexdigest().lower()!=row['md5'].lower():
            raise FailClosed(f'byte/hash mismatch {key}')
        totals['objects']+=1
    for h in HORIZONS_MS:
        while queues[h]: _,i=queues[h].popleft(); resolve(i,h,None)
    if active: raise FailClosed('active events remain')
    return stats,totals

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',default=str(Path.home()/'Desktop'/'L2R_2025_BTC_VALIDATION_LOCAL')); args=ap.parse_args()
    base=Path(args.base).resolve(); ev=base/'_EVIDENCE_2025_VALIDATION_V0_1'; manifest=ev/'L2_RESILIENCY_001_2025_BTC_RAW_MANIFEST_V0_1.csv'
    if not manifest.exists(): raise SystemExit(f'FAIL-CLOSED manifest missing {manifest}')
    if sha256_file(manifest)!=EXPECTED_MANIFEST_SHA256: raise SystemExit('FAIL-CLOSED canonical manifest SHA mismatch')
    with manifest.open('r',encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    if len(rows)!=EXPECTED_OBJECTS or sum(int(r['content_length']) for r in rows)!=EXPECTED_BYTES: raise SystemExit('FAIL-CLOSED corpus identity mismatch')
    segs=build_segments(rows); print(f'CANONICAL SOURCE PASS | objects={len(rows)} segments={len(segs)}')
    merged={c[0]:Counter() for c in CELLS}; totals=Counter()
    for i,seg in enumerate(segs,1):
        st,tt=process_segment(i,seg,base); totals.update(tt)
        for cell,d in st.items(): merged[cell].update(d)
        print(f'segment {i} PASS | sweeps={tt["ask_sweeps"]+tt["bid_sweeps"]:,}')
    out=[]
    for name,_,_ in CELLS:
        s=merged[name]; n=int(s['n'])
        if n<=0: raise SystemExit(f'FAIL-CLOSED zero weak opportunities {name}')
        row={'cell':name,'weak_n':n,'mean_mid_response_bps':s['sum_mid']/n,
             'mean_taker_touch_gross_bps':s['sum_taker']/n,
             'mean_maker_touch_optimistic_gross_bps':s['sum_maker_upper']/n,
             'mean_entry_spread_bps':s['sum_entry_spread']/n,
             'mean_exit_spread_bps':s['sum_exit_spread']/n}
        for fee in MAKER_SCENARIOS_BPS: row[f'maker_upper_net_fee_{fee:.1f}_bps_per_fill']=row['mean_maker_touch_optimistic_gross_bps']-2*fee
        for fee in TAKER_SCENARIOS_BPS: row[f'taker_net_fee_{fee:.1f}_bps_per_fill']=row['mean_taker_touch_gross_bps']-2*fee
        out.append(row)
    evidence=base/'_EVIDENCE_L2R_EXEC_PASSIVE_V0_1'; evidence.mkdir(parents=True,exist_ok=True)
    csvp=evidence/'L2R_EXEC_PASSIVE_001_2025_UPPER_BOUND_CELL_SUMMARY_V0_1.csv'
    with csvp.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    base_maker=1.5; base_taker=4.5
    maker_base_vals=[r[f'maker_upper_net_fee_{base_maker:.1f}_bps_per_fill'] for r in out]
    positive_cells=sum(v>0 for v in maker_base_vals)
    by_r={str(rh):any(row['cell']==name and row[f'maker_upper_net_fee_{base_maker:.1f}_bps_per_fill']>0 for row in out for name,crh,_ in CELLS if crh==rh) for rh in (1000,5000,15000)}
    panel_mean=sum(maker_base_vals)/len(maker_base_vals)
    base_support={'panel_equal_weight_mean_positive':panel_mean>0,'at_least_4_of_6_cells_positive':positive_cells>=4,'each_R_has_positive_cell':all(by_r.values())}
    base_class='PASSIVE_STANDARD_BASE_UPPER_BOUND_SURVIVES' if all(base_support.values()) else 'PASSIVE_STANDARD_BASE_UPPER_BOUND_FAIL'
    verdict={
      'schema_version':'0.1','implementation_version':IMPLEMENTATION_VERSION,'lab_id':LAB_ID,'parent_lab_id':PARENT_LAB_ID,'year':YEAR,
      'purpose':'POST-VALIDATION DEVELOPMENT DIAGNOSTIC; NOT INDEPENDENT EVIDENCE',
      'source_manifest_sha256':EXPECTED_MANIFEST_SHA256,'classification':base_class,
      'standard_base_panel':{'equal_weight_mean_net_bps':panel_mean,'positive_cells':positive_cells,'positive_by_replenishment_horizon':by_r,'support_gate':base_support},
      'cells':out,
      'hyperliquid_fee_snapshot_bps_per_fill':{'base_maker':base_maker,'base_taker':base_taker,'maker_scenarios':MAKER_SCENARIOS_BPS,'taker_scenarios':TAKER_SCENARIOS_BPS},
      'interpretation':{
        'taker_base_all_cells_positive':all(r[f'taker_net_fee_{base_taker:.1f}_bps_per_fill']>0 for r in out),
        'maker_optimistic_base_all_cells_positive':all(r[f'maker_upper_net_fee_{base_maker:.1f}_bps_per_fill']>0 for r in out),
        'maker_optimistic_base_any_cell_positive':any(r[f'maker_upper_net_fee_{base_maker:.1f}_bps_per_fill']>0 for r in out),
        'rule':'Maker result is an intentionally optimistic upper bound, not a fill simulation. Failure at this bound closes the standard-base passive route. Survival only authorizes a separate queue/fill study.'
      },
      'firewalls':{'access_2026':False,'network':False,'live_trading':False,'exchange_mutation':False,'orders':False,'main_merge':False},
      'no_post_outcome_selection':'All six parent causal cells are reported; no cell is selected or promoted from 2025 outcomes.'
    }
    jp=evidence/'L2R_EXEC_PASSIVE_001_2025_UPPER_BOUND_RECEIPT_V0_1.json'; jp.write_text(json.dumps(verdict,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    z=base/'L2R_EXEC_PASSIVE_001_2025_UPPER_BOUND_EVIDENCE_V0_1.zip'
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as zz:
        zz.write(csvp,csvp.name); zz.write(jp,jp.name)
    print('\n=== EXECUTION UPPER-BOUND DIAGNOSTIC ===')
    for r in out:
        print(r['cell'],'n',r['weak_n'],'mid',r['mean_mid_response_bps'],'taker_gross',r['mean_taker_touch_gross_bps'],'maker_upper_gross',r['mean_maker_touch_optimistic_gross_bps'],'maker_base_net',r[f'maker_upper_net_fee_{base_maker:.1f}_bps_per_fill'])
    print('STANDARD BASE CLASSIFICATION:',base_class)
    print('PANEL equal-weight maker-upper net bps:',panel_mean,'positive_cells',f'{positive_cells}/6','positive_by_R',by_r)
    print('Evidence:',z); print('SHA256:',sha256_file(z)); print('NO 2026 / NO NETWORK / NO ORDERS')

if __name__=='__main__': main()
