#!/usr/bin/env python3
"""Frozen price-blind source planner and one-shot Binance Discovery runner."""
from __future__ import annotations
import argparse,csv,datetime as dt,gzip,hashlib,io,json,math,mmap,os,random,re,struct,urllib.request,zipfile
from collections import Counter,defaultdict
import subprocess
from pathlib import Path

LAB='L2R-CROSSVENUE-001'; BASE='https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT'
PARENT_SHA='7f135689afd9f51a758e2c98b5c8da9fe3c7f3eca15f40eced7fdb53b03d2eaf'
MANIFEST_SHA='59e16ce8ea41658c2ea0fc6f2489d4deafbdc676e008d0b93f95ee6e3864913d'
ANCHOR_SHA='be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3'
CELLS=(('R1_Y5',1000,5000),('R1_Y15',1000,15000),('R1_Y60',1000,60000),('R5_Y15',5000,15000),('R5_Y60',5000,60000),('R15_Y60',15000,60000))
H=(1000,5000,15000,60000); MIN_LATE_NS=2_000_000_000; REC=struct.Struct('<QI')
SHA_RE=re.compile(r'^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$')
class Blocked(RuntimeError): pass

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 return h.hexdigest()
def dates():
 d=dt.date(2024,1,1)
 while d.year==2024:
  yield d.isoformat(); d+=dt.timedelta(days=1)
def fetch(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'L2R-CROSSVENUE-001/0.1'}),timeout=120) as r: return r.read()
def download(url,p):
 p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+'.partial')
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'L2R-CROSSVENUE-001/0.1'}),timeout=180) as r,tmp.open('wb') as f:
  for b in iter(lambda:r.read(8*1024*1024),b''): f.write(b)
 os.replace(tmp,p)
def archive_name(d): return f'BTCUSDT-aggTrades-{d}.zip'
def csv_rows(z,d):
 name=f'BTCUSDT-aggTrades-{d}.csv'
 with zipfile.ZipFile(z) as zz:
  if name not in zz.namelist(): raise Blocked(f'official CSV absent: {d}')
  with zz.open(name) as raw:
   reader=csv.reader(io.TextIOWrapper(raw,encoding='utf-8',newline=''))
   first=True
   for row in reader:
    if not row: continue
    if first and row[0].lower().startswith('agg'): first=False; continue
    first=False
    if len(row)<8: raise Blocked(f'short aggregate row {d}')
    try: aid=int(row[0]); ts=int(row[5])
    except Exception as e: raise Blocked(f'invalid aggregate id/timestamp {d}') from e
    if aid<0 or ts<0: raise Blocked(f'negative aggregate id/timestamp {d}')
    yield row,aid,ts

def source_prepare(cache,receipt_path):
 cache=Path(cache); cache.mkdir(parents=True,exist_ok=True); items=[]; total=0; global_prev_id=-1; global_prev_ts=-1
 for di,d in enumerate(dates(),1):
  fn=archive_name(d); z=cache/fn; checksum=fetch(f'{BASE}/{fn}.CHECKSUM').decode('utf-8').strip(); m=SHA_RE.fullmatch(checksum)
  if not m or m.group(2).strip()!=fn: raise Blocked(f'checksum format/name failure {d}')
  exp=m.group(1).lower()
  if not z.exists(): download(f'{BASE}/{fn}',z)
  actual=sha(z)
  if actual!=exp: raise Blocked(f'archive SHA mismatch {d}')
  idx=cache/(d+'.idx'); tmp=idx.with_suffix('.idx.partial'); count=0; prev_id=-1; prev_ts=-1; first_ts=None; last_ts=None
  with tmp.open('wb') as out:
   for _,aid,ts in csv_rows(z,d):
    if aid<=prev_id or ts<prev_ts or aid<=global_prev_id or ts<global_prev_ts: raise Blocked(f'aggregate ID/timestamp ordering failure {d}')
    if ts<0: raise Blocked(f'invalid timestamp {d}')
    if count==0: first_ts=ts
    last_ts=ts; out.write(REC.pack(ts,count)); count+=1; prev_id=aid; prev_ts=ts; global_prev_id=aid; global_prev_ts=ts
  if count==0: raise Blocked(f'empty official archive {d}')
  os.replace(tmp,idx); total+=count
  items.append({'date':d,'zip':fn,'sha256':actual,'bytes':z.stat().st_size,'rows':count,'first_ts_ms':first_ts,'last_ts_ms':last_ts,'index_sha256':sha(idx),'index_bytes':idx.stat().st_size})
  print(f'SOURCE_DATE_PASS {di}/366 {d} rows={count}',flush=True)
 receipt={'lab_id':LAB,'classification':'BINANCE_2024_TIMESTAMP_ID_SOURCE_PASS','venue':'Binance spot','symbol':'BTCUSDT','days':len(items),'rows':total,'columns_used':['aggregate_trade_id','transact_time_ms'],'price_column_parsed':False,'quantity_column_parsed':False,'items':items,'firewalls':{'prices_opened':False,'returns_computed':False,'access_2025':False,'access_2026':False}}
 Path(receipt_path).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8'); print(f'SOURCE_RECEIPT {receipt_path}',flush=True)

def open_idx(path):
 path=str(path)
 if path in INDEX_CACHE:
  value=INDEX_CACHE.pop(path); INDEX_CACHE[path]=value; return value
 if len(INDEX_CACHE)>=4:
  _,old=INDEX_CACHE.popitem(last=False); old.close()
 with open(path,'rb') as f: value=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
 INDEX_CACHE[path]=value; return value
def clear_indexes():
 for value in INDEX_CACHE.values(): value.close()
 INDEX_CACHE.clear()
INDEX_CACHE={}
def idx_lookup(cache,target_ns):
 day=dt.datetime.fromtimestamp(target_ns//1_000_000_000,tz=dt.timezone.utc).date()
 if day.year!=2024: return None
 for offset in (0,1):
  cur=day+dt.timedelta(days=offset)
  if cur.year!=2024: return None
  p=Path(cache)/(cur.isoformat()+'.idx')
  if not p.exists(): raise Blocked(f'timestamp index missing {cur}')
  data=open_idx(str(p)); n=len(data)//REC.size; lo=0; hi=n
  while lo<hi:
   mid=(lo+hi)//2; ts,row=REC.unpack_from(data,mid*REC.size)
   if ts*1_000_000<target_ns: lo=mid+1
   else: hi=mid
  if lo<n:
   ts,row=REC.unpack_from(data,lo*REC.size); late=ts*1_000_000-target_ns
   if 0<=late<=MIN_LATE_NS: return (cur.isoformat(),row,ts,late)
  # Search the next UTC-day archive for a first at/after trade if still within tolerance.
 return None

def materialized_files(root,expected):
 receipt=json.loads(Path(expected).read_text())
 if receipt.get('classification')!='PARENT_STATE_MATERIALIZATION_PASS' or receipt.get('parent_runner_sha256')!=PARENT_SHA or not all(receipt['guards'].values()): raise Blocked('parent identity receipt is not PASS')
 files=[]
 for s in receipt['segments']:
  p=Path(s['file'])
  if not p.is_file() or sha(p)!=s['sha256'] or p.stat().st_size!=s['size']: raise Blocked(f'parent ledger identity mismatch segment {s["segment_id"]}')
  files.append(p)
 return receipt,files

def source_plan(cache,source_receipt,ledger_receipt,plan_dir,plan_receipt):
 cache=Path(cache); sr=json.loads(Path(source_receipt).read_text()); pr,ledgers=materialized_files(cache,ledger_receipt)
 if sr.get('classification')!='BINANCE_2024_TIMESTAMP_ID_SOURCE_PASS' or len(sr.get('items',[]))!=366: raise Blocked('full 366-day source gate absent')
 for item in sr['items']:
  z=cache/item['zip']; idx=cache/(item['date']+'.idx')
  if not z.is_file() or sha(z)!=item['sha256'] or not idx.is_file() or sha(idx)!=item['index_sha256']: raise Blocked('source/index bytes changed')
 out=Path(plan_dir); out.mkdir(parents=True,exist_ok=True)
 handles={}; writers={}; counters={c:Counter() for c,_,_ in CELLS}; quarter={c:defaultdict(Counter) for c,_,_ in CELLS}; daygroups=defaultdict(Counter)
 def writer(day):
  if day not in writers:
   p=out/(day+'.csv.gz'); raw=p.open('xb'); gz=gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=1); txt=io.TextIOWrapper(gz,encoding='utf-8',newline=''); w=csv.writer(txt,lineterminator='\n'); w.writerow(['event_id','date','direction']+[f'{c}_{x}' for c,_,_ in CELLS for x in ('group','r_date','r_row','r_ts_ms','y_date','y_row','y_ts_ms')]); handles[day]=(raw,gz,txt); writers[day]=w
  return writers[day]
 try:
  for ledger in ledgers:
   with gzip.open(ledger,'rt',encoding='utf-8',newline='') as f:
    for ev in csv.DictReader(f):
     day=ev['anchor_date_utc']; qtr=(int(day[5:7])-1)//3+1; pre=float(ev['pre_depth5'])
     selected={}
     for h in H:
      if h==60000: status=ev['timing_60000_status']; ns=ev['timing_60000_envelope_ns']
      else: status=ev[f'r_{h}_status']; ns=ev[f'r_{h}_envelope_ns']
      selected[h]=idx_lookup(cache,int(ns)) if status=='AVAILABLE' and ns else None
     row=[ev['event_id'],day,ev['direction']]
     for cell,rh,yh in CELLS:
      c=counters[cell]; qc=quarter[cell][qtr]; c['anchors']+=int(pre>0); qc['anchors']+=int(pre>0)
      rparent=ev[f'r_{rh}_status']=='AVAILABLE'; yparent=(ev['timing_60000_status']=='AVAILABLE' if yh==60000 else ev[f'r_{yh}_status']=='AVAILABLE')
      parentok=pre>0 and rparent and yparent
      c['parent_eligible']+=int(parentok); qc['parent_eligible']+=int(parentok)
      r=selected[rh] if parentok else None; y=selected[yh] if parentok else None
      c['r_target']+=int(parentok); c['y_target']+=int(parentok); qc['joint_den']+=int(parentok)
      c['r_pass']+=int(r is not None); c['y_pass']+=int(y is not None); qc['joint_pass']+=int(r is not None and y is not None)
      group=ev[f'r_{rh}_class'] if parentok else ''
      if group not in ('WEAK','STRONG'): group=''
      if r is not None and y is not None and y[2]*1_000_000<=r[2]*1_000_000: raise Blocked('external endpoint not strictly later than baseline')
      if group and r is not None and y is not None:
       c['group_'+group.lower()] +=1; qc['group_'+group.lower()]+=1
       daygroups[(day,cell)][group.lower()]+=1
      row.extend([group,r[0] if r else '',r[1] if r else '',r[2] if r else '',y[0] if y else '',y[1] if y else '',y[2] if y else ''])
     writer(day).writerow(row)
 finally:
  for raw,gz,txt in handles.values(): txt.close(); raw.close()
 paired={c:[] for c,_,_ in CELLS}; qpaired={c:Counter() for c,_,_ in CELLS}; globaldays=[]
 for c in paired:
  for day in sorted({d for d,cell in daygroups if cell==c}):
   z=daygroups[(day,c)]
   if z['weak']>=100 and z['strong']>=100: paired[c].append(day); qpaired[c][(int(day[5:7])-1)//3+1]+=1
 for day in sorted({d for d,_ in daygroups}):
  if all(day in paired[c] for c in paired): globaldays.append(day)
 gates={}
 for c,v in counters.items():
  gates[c+'_parent_coverage']=v['parent_eligible']/v['anchors']>=.99
  gates[c+'_r_coverage']=v['r_pass']/v['parent_eligible']>=.99
  gates[c+'_y_coverage']=v['y_pass']/v['parent_eligible']>=.99
  gates[c+'_joint_coverage']=(v['group_weak']+v['group_strong'])/v['parent_eligible']>=.98
  gates[c+'_weak_n']=v['group_weak']>=10000; gates[c+'_strong_n']=v['group_strong']>=10000
  gates[c+'_paired_days']=len(paired[c])>=300
  for q in range(1,5): gates[f'{c}_q{q}_paired_days']=qpaired[c][q]>=60
  for q in range(1,5):
   qv=quarter[c][q]; gates[f'{c}_q{q}_joint_coverage']=qv['joint_pass']/qv['joint_den']>=.98
 gates['global_paired_days']=len(globaldays)>=300
 result={'lab_id':LAB,'classification':'BINANCE_PRICE_BLIND_PLAN_PASS' if all(gates.values()) else 'BINANCE_PRICE_BLIND_PLAN_BLOCKED','source_receipt_sha256':sha(source_receipt),'parent_receipt_sha256':sha(ledger_receipt),'segments':[{'name':p.name,'sha256':sha(p),'size':p.stat().st_size} for p in sorted(out.glob('*.csv.gz'))],'gates':gates,'coverage':{c:dict(v) for c,v in counters.items()},'quarter':{c:{str(q):dict(v) for q,v in qs.items()} for c,qs in quarter.items()},'paired_days':{c:paired[c] for c in paired},'global_paired_days':globaldays,'firewalls':{'price_columns_parsed':False,'returns_computed':False,'access_2025':False,'access_2026':False}}
 Path(plan_receipt).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'classification':result['classification'],'failed_gates':[k for k,v in gates.items() if not v],'receipt':str(plan_receipt)},indent=2),flush=True)

def percentile(sorted_x,q):
 pos=(len(sorted_x)-1)*q; lo=math.floor(pos); hi=math.ceil(pos); return sorted_x[lo] if lo==hi else sorted_x[lo]*(hi-pos)+sorted_x[hi]*(pos-lo)

def load_lock(path,protocol,runner,exporter,plan_runner):
 lock=json.loads(Path(path).read_text())
 expected={'protocol_sha256':sha(protocol),'discovery_runner_sha256':sha(runner),'parent_exporter_sha256':sha(exporter),'price_blind_runner_sha256':sha(plan_runner),'parent_runner_sha256':PARENT_SHA,'manifest_sha256':MANIFEST_SHA,'anchor_sha256':ANCHOR_SHA}
 for k,v in expected.items():
  if lock.get(k)!=v: raise Blocked(f'implementation lock mismatch: {k}')
 return lock

def issue_authority(source_receipt,parent_receipt,plan_receipt,plan_dir,protocol,runner,exporter,lockfile,authority,marker,outdir):
 sr=json.loads(Path(source_receipt).read_text()); pr,pfiles=materialized_files(Path(parent_receipt).parent, parent_receipt); plan=json.loads(Path(plan_receipt).read_text())
 lock=load_lock(lockfile,protocol,runner,exporter,runner)
 if sr.get('classification')!='BINANCE_2024_TIMESTAMP_ID_SOURCE_PASS' or plan.get('classification')!='BINANCE_PRICE_BLIND_PLAN_PASS' or not all(plan['gates'].values()): raise Blocked('pre-outcome gates not all PASS')
 for item in plan['segments']:
  p=Path(plan_dir)/item['name']
  if not p.is_file() or sha(p)!=item['sha256']: raise Blocked('lookup plan changed before authority')
 manifest={'lab_id':LAB,'classification':'ONE_SHOT_DISCOVERY_AUTHORITY_ISSUED_PRE_OUTCOME','implementation_lock_sha256':sha(lockfile),'source_receipt_sha256':sha(source_receipt),'parent_receipt_sha256':sha(parent_receipt),'parent_segment_sha256':{p.name:sha(p) for p in pfiles},'plan_receipt_sha256':sha(plan_receipt),'plan_files':plan['segments'],'protocol_sha256':sha(protocol),'runner_sha256':sha(runner),'marker_path':str(Path(marker).resolve()),'output_dir':str(Path(outdir).resolve()),'scope':'2024 Binance spot BTCUSDT aggTrades only; one execution','firewalls':{'prices_opened_at_issue':False,'access_2025':False,'access_2026':False,'trading':False,'exchange_mutation':False}}
 target=Path(authority); target.parent.mkdir(parents=True,exist_ok=True); fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 with os.fdopen(fd,'w',encoding='utf-8',newline='') as f: json.dump(manifest,f,indent=2); f.write(chr(10))
 print(json.dumps({'classification':manifest['classification'],'authority':str(target),'authority_sha256':sha(target),'runner_sha256':manifest['runner_sha256']},indent=2))

def outcome(cache,source_receipt,parent_receipt,plan_receipt,plan_dir,protocol,runner,exporter,lockfile,authority,authority_commit,marker,outdir):
 cache=Path(cache); out=Path(outdir); marker=Path(marker); out.mkdir(parents=True,exist_ok=True)
 auth=json.loads(Path(authority).read_text()); plan=json.loads(Path(plan_receipt).read_text()); sr=json.loads(Path(source_receipt).read_text()); pr,ledger=materialized_files(Path(parent_receipt).parent,parent_receipt)
 lock=load_lock(lockfile,protocol,runner,exporter,runner)
 if auth.get('classification')!='ONE_SHOT_DISCOVERY_AUTHORITY_ISSUED_PRE_OUTCOME' or auth['runner_sha256']!=sha(runner) or sha(protocol)!=auth['protocol_sha256'] or sha(lockfile)!=auth['implementation_lock_sha256']: raise Blocked('authority/runner/protocol binding mismatch')
 if plan['classification']!='BINANCE_PRICE_BLIND_PLAN_PASS' or sha(plan_receipt)!=auth['plan_receipt_sha256'] or sha(source_receipt)!=auth['source_receipt_sha256'] or sha(parent_receipt)!=auth['parent_receipt_sha256']: raise Blocked('pre-outcome receipt identity mismatch')
 # Require the committed authority bytes to exist at the supplied immutable commit.
 if marker.resolve()!=Path(auth['marker_path']).resolve() or out.resolve()!=Path(auth['output_dir']).resolve(): raise Blocked('one-shot paths do not match authority')
 repo=Path(runner).resolve().parents[2]; rel=Path(authority).resolve().relative_to(repo).as_posix()
 committed=subprocess.check_output(['git','show',f'{authority_commit}:{rel}'],cwd=repo).decode('utf-8')
 if hashlib.sha256(committed.encode()).hexdigest()!=sha(authority): raise Blocked('authority bytes are not present in claimed commit')
 for p in ledger:
  if sha(p)!=next(x['sha256'] for x in pr['segments'] if x['segment_id']==int(p.stem.split('_')[-1])): raise Blocked('parent ledger changed')
 for it in sr['items']:
  z=cache/it['zip']; idx=cache/(it['date']+'.idx')
  if not z.is_file() or sha(z)!=it['sha256'] or not idx.is_file() or sha(idx)!=it['index_sha256']: raise Blocked(f'source bytes changed {it["date"]}')
 for item in plan['segments']:
  p=Path(plan_dir)/item['name']
  if not p.is_file() or sha(p)!=item['sha256']: raise Blocked('lookup plan changed')
 # Irreversible one-shot consumption occurs before the first price field is read.
 marker.parent.mkdir(parents=True,exist_ok=True); fd=os.open(marker,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump({'authority_sha256':sha(authority),'authority_commit':authority_commit,'consumed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'CONSUMED'},f); f.write(chr(10))
 print('ONE_SHOT_AUTHORITY_CONSUMED; first Binance price read follows.',flush=True)
 daily={}; planned_counts=Counter(); event_rows=0
 try:
  for seg in plan['segments']:
   pp=Path(plan_dir)/seg['name']
   with gzip.open(pp,'rt',encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
   wanted=defaultdict(set)
   for x in rows:
    for c,_,_ in CELLS:
     for side in ('r','y'):
      day=x[f'{c}_{side}_date']; row=x[f'{c}_{side}_row']
      if day and row!='': wanted[day].add(int(row))
     for c,_,_ in CELLS:
      if x[f'{c}_group']: planned_counts[(x['date'],c,x[f'{c}_group'].lower())]+=1
   prices={}
   for day,needed in wanted.items():
    z=cache/archive_name(day); item=next(i for i in sr['items'] if i['date']==day)
    if sha(z)!=item['sha256']: raise Blocked(f'price archive SHA changed {day}')
    found=set(); dname=f'BTCUSDT-aggTrades-{day}.csv'
    with zipfile.ZipFile(z) as zz, zz.open(dname) as raw:
     reader=csv.reader(io.TextIOWrapper(raw,encoding='utf-8',newline='')); first=True; data_ix=0
     for row in reader:
      if not row: continue
      if first and row[0].lower().startswith('agg'): first=False; continue
      first=False
      if data_ix in needed:
       price=float(row[1])
       if not math.isfinite(price) or price<=0: raise Blocked('invalid selected Binance price')
       prices[(day,data_ix)]=price; found.add(data_ix)
      data_ix+=1
    if found!=needed: raise Blocked(f'selected trade rows absent {day}')
   for x in rows:
    day=x['date']; daydata=daily.setdefault(day,{c:{'weak_sum':0.0,'weak_n':0,'strong_sum':0.0,'strong_n':0} for c,_,_ in CELLS})
    for c,_,_ in CELLS:
     group=x[f'{c}_group']; rd=x[f'{c}_r_date']; rr=x[f'{c}_r_row']; yd=x[f'{c}_y_date']; yr=x[f'{c}_y_row']
     if not group: continue
     if group not in ('WEAK','STRONG') or (rd,int(rr)) not in prices or (yd,int(yr)) not in prices: raise Blocked('planned price key missing')
     p_r=prices[(rd,int(rr))]; p_y=prices[(yd,int(yr))]; response=int(x['direction'])*10000.0*(p_y/p_r-1.0)
     if not math.isfinite(response): raise Blocked('non-finite signed response')
     g=group.lower(); daydata[c][g+'_sum']+=response; daydata[c][g+'_n']+=1
    event_rows+=1
   print(f'OUTCOME_DAY_PASS {day} events={len(rows)}',flush=True)
  for day,values in daily.items():
   for c,_,_ in CELLS:
    for group in ('weak','strong'):
     if values[c][group+'_n']!=planned_counts[(day,c,group)]: raise Blocked('outcome group count differs from pre-outcome plan')
  eligible={c:{} for c,_,_ in CELLS}
  for day,celldata in daily.items():
   for c,_,_ in CELLS:
    v=celldata[c]
    if v['weak_n']>=100 and v['strong_n']>=100: eligible[c][day]=v['weak_sum']/v['weak_n']-v['strong_sum']/v['strong_n']
  global_daily={d:sum(eligible[c][d] for c,_,_ in CELLS)/len(CELLS) for d in sorted(set.intersection(*(set(eligible[c]) for c,_,_ in CELLS)))}
  def bootstrap(vals,seed):
   rng=random.Random(seed); n=len(vals); means=[]
   for _ in range(10000): means.append(sum(vals[rng.randrange(n)] for _ in range(n))/n)
   means.sort(); return percentile(means,.025),percentile(means,.975)
  cellout=[]
  for c,rh,yh in CELLS:
   vals=[eligible[c][d] for d in sorted(eligible[c])]; ci=bootstrap(vals,20260919)
   cellout.append({'cell':c,'R_ms':rh,'Y_ms':yh,'eligible_days':len(vals),'daily_contrast_mean_bps':sum(vals)/len(vals),'bootstrap_ci95_bps':ci,'positive':sum(vals)/len(vals)>0})
  gvals=list(global_daily.values()); gci=bootstrap(gvals,20260919); geffect=sum(gvals)/len(gvals)
  byR={str(r):any(x['positive'] for x in cellout if x['R_ms']==r) for r in (1000,5000,15000)}
  gates={'global_effect_positive':geffect>0,'global_ci_lower_positive':gci[0]>0,'at_least_4_cells_positive':sum(x['positive'] for x in cellout)>=4,'each_R_family_positive':all(byR.values())}
  verdict='DISCOVERY_MECHANISM_SUPPORTED' if all(gates.values()) else 'DISCOVERY_FAIL_NO_SUPPORT'
  result={'lab_id':LAB,'classification':verdict,'label':'NEW_MECHANISM_PREVIOUSLY_EXPOSED_PARENT_SOURCE','authority_sha256':sha(authority),'authority_commit':authority_commit,'runner_sha256':sha(runner),'protocol_sha256':sha(protocol),'parent_receipt_sha256':sha(parent_receipt),'source_receipt_sha256':sha(source_receipt),'price_blind_plan_receipt_sha256':sha(plan_receipt),'consumed_marker_sha256':sha(marker),'events_processed':event_rows,'cell_results':cellout,'global':{'eligible_days':len(gvals),'effect_bps':geffect,'bootstrap_ci95_bps':gci,'positive_cells':sum(x['positive'] for x in cellout),'positive_by_R':byR},'support_gates':gates,'firewalls':{'calendar_2024_only':True,'access_2025':False,'access_2026':False,'pnl':False,'fees':False,'trading':False,'exchange_mutation':False,'post_outcome_tuning':False}}
  (out/'DISCOVERY_2024_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'classification':verdict,'global':result['global'],'gates':gates},indent=2),flush=True)
 except Exception as e:
  fail={'lab_id':LAB,'classification':'ONE_SHOT_TECHNICAL_BLOCKED_NO_RETRY','error':str(e),'authority_sha256':sha(authority),'consumed_marker_sha256':sha(marker),'prices_may_have_been_opened':True,'post_outcome_tuning':False}
  (out/'DISCOVERY_2024_RECEIPT.json').write_text(json.dumps(fail,indent=2)+'\n',encoding='utf-8'); print(json.dumps(fail),flush=True); raise

def main():
 ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='phase',required=True)
 s=sub.add_parser('source'); s.add_argument('--cache',required=True); s.add_argument('--receipt',required=True)
 p=sub.add_parser('plan'); p.add_argument('--cache',required=True); p.add_argument('--source-receipt',required=True); p.add_argument('--parent-receipt',required=True); p.add_argument('--plan-dir',required=True); p.add_argument('--receipt',required=True)
 i=sub.add_parser('issue-authority'); i.add_argument('--source-receipt',required=True); i.add_argument('--parent-receipt',required=True); i.add_argument('--plan-receipt',required=True); i.add_argument('--plan-dir',required=True); i.add_argument('--protocol',required=True); i.add_argument('--runner',required=True); i.add_argument('--exporter',required=True); i.add_argument('--implementation-lock',required=True); i.add_argument('--authority',required=True); i.add_argument('--marker',required=True); i.add_argument('--outdir',required=True)
 o=sub.add_parser('outcome'); o.add_argument('--cache',required=True); o.add_argument('--source-receipt',required=True); o.add_argument('--parent-receipt',required=True); o.add_argument('--plan-receipt',required=True); o.add_argument('--plan-dir',required=True); o.add_argument('--protocol',required=True); o.add_argument('--runner',required=True); o.add_argument('--exporter',required=True); o.add_argument('--implementation-lock',required=True); o.add_argument('--authority',required=True); o.add_argument('--authority-commit',required=True); o.add_argument('--marker',required=True); o.add_argument('--outdir',required=True)
 a=ap.parse_args()
 try:
  if a.phase=='source': source_prepare(a.cache,a.receipt)
  elif a.phase=='plan': source_plan(a.cache,a.source_receipt,a.parent_receipt,a.plan_dir,a.receipt)
  elif a.phase=='issue-authority': issue_authority(a.source_receipt,a.parent_receipt,a.plan_receipt,a.plan_dir,a.protocol,a.runner,a.exporter,a.implementation_lock,a.authority,a.marker,a.outdir)
  elif a.phase=='outcome': outcome(a.cache,a.source_receipt,a.parent_receipt,a.plan_receipt,a.plan_dir,a.protocol,a.runner,a.exporter,a.implementation_lock,a.authority,a.authority_commit,a.marker,a.outdir)
 except Exception as exc:
  target=Path(a.receipt) if a.phase=='source' else Path(a.receipt) if a.phase=='plan' else Path(a.outdir)/'DISCOVERY_2024_RECEIPT.json' if a.phase=='outcome' else None
  if target:
   target.parent.mkdir(parents=True,exist_ok=True)
   state={'lab_id':LAB,'classification':'BINANCE_SOURCE_PREFLIGHT_BLOCKED' if a.phase=='source' else 'BINANCE_PRICE_BLIND_PLAN_BLOCKED' if a.phase=='plan' else 'ONE_SHOT_TECHNICAL_BLOCKED_NO_RETRY' if a.phase=='outcome' else 'AUTHORITY_ISSUANCE_BLOCKED','failure':str(exc),'firewalls':{'price_values_parsed':False,'access_2025':False,'access_2026':False,'trading':False}}
   target.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
  raise
if __name__=='__main__': main()
