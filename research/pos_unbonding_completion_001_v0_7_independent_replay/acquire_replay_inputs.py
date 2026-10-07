import json, hashlib, urllib.request, urllib.error, concurrent.futures, pathlib, datetime, shutil, subprocess
P=pathlib.Path(__file__).resolve().parent
if (P/'acquisition_receipt.json').exists(): raise SystemExit('Existing run preserved; copy scripts into a new run directory before reacquisition')
RAW=P/'receipts'; RAW.mkdir(exist_ok=True)
FREEZE='8bc913d321e5063480f33a67b705193269aac603'
def get(name,url):
    rec={'name':name,'url':url,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'freeze_commit':FREEZE}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Laboratorio-Coreum-Replay-V07','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=25) as r:
            b=r.read(); rec['http_status']=r.status
        path=RAW/(name+'.raw'); path.write_bytes(b)
        rec.update(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),file=path.relative_to(P).as_posix(),status='RETRIEVED')
        try: obj=json.loads(b)
        except Exception: obj=None
        return rec,obj
    except Exception as e:
        rec.update(status='TRANSPORT_FAILED',error=str(e))
        if isinstance(e,urllib.error.HTTPError):
            b=e.read(); (RAW/(name+'.error')).write_bytes(b); rec['error_sha256']=hashlib.sha256(b).hexdigest(); rec['http_status']=e.code
        return rec,None
jobs=[('official_head','https://api.github.com/repos/CoreumFoundation/coreum/commits/master'),('official_releases','https://api.github.com/repos/CoreumFoundation/coreum/releases?per_page=100'),('official_tags','https://api.github.com/repos/CoreumFoundation/coreum/tags?per_page=100')]
A='https://archive.rpc.mainnet-1.tx.org'
for h in [1,2,5000000,5000001,10000000,10000001,15000000,15000001]: jobs.append(('block_'+str(h),A+'/block?height='+str(h)))
for h in [1,5000000,10000000,15000000]:
    jobs.append(('commit_'+str(h),A+'/commit?height='+str(h)))
    jobs.append(('validators_'+str(h),A+'/validators?height='+str(h)+'&per_page=100&page=1'))
records=[]; objects={}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for rec,obj in pool.map(lambda j:get(*j),jobs): records.append(rec); objects[rec['name']]=obj
head=(objects.get('official_head') or {}).get('sha')
if head:
    rec,tree=get('official_tree','https://api.github.com/repos/CoreumFoundation/coreum/git/trees/'+head+'?recursive=1'); records.append(rec)
    paths=[x['path'] for x in (tree or {}).get('tree',[]) if 'genesis' in x['path'].lower() or 'upgrade' in x['path'].lower()]
    (P/'official_candidate_paths.json').write_text(json.dumps({'revision':head,'paths':paths},indent=2))
    for p in paths:
        if ('mainnet' in p and p.endswith('.json')) or (p.endswith('.go') and ('upgrade' in p or 'network' in p)):
            rec,obj=get('source_'+hashlib.sha256(p.encode()).hexdigest()[:12],'https://raw.githubusercontent.com/CoreumFoundation/coreum/'+head+'/'+p); rec['source_path']=p; records.append(rec)
            if obj and isinstance(obj,dict) and obj.get('chain_id')=='coreum-mainnet-1':
                (P/'genesis_pin.json').write_text(json.dumps({'revision':head,'path':p,**rec,'chain_id':obj['chain_id'],'initial_height':obj.get('initial_height'),'genesis_time':obj.get('genesis_time'),'validator_count':len(obj.get('validators',[]))},indent=2))
anchors=[]
for h in [1,5000000,10000000,15000000]:
    o=objects.get('block_'+str(h)) or {}; r=o.get('result') or {}; hd=(r.get('block') or {}).get('header') or {}
    nxt=(((objects.get('block_'+str(h+1)) or {}).get('result') or {}).get('block') or {}).get('header') or {}
    anchors.append({'height':h,'chain_id':hd.get('chain_id'),'time':hd.get('time'),'reported_block_hash':(r.get('block_id') or {}).get('hash'),'header_app_hash':hd.get('app_hash'),'post_height_commit_expected_in_next_header':nxt.get('app_hash'),'error':o.get('error'),'independently_validated':False})
(P/'transport_anchors.json').write_text(json.dumps(anchors,indent=2))
(P/'acquisition_receipt.json').write_text(json.dumps({'freeze_commit':FREEZE,'records':records,'environment':{'platform':'Windows','go':shutil.which('go'),'docker':shutil.which('docker'),'wsl':shutil.which('wsl')},'local_replay_executed':False,'block_results_requested':False,'census_executed':False},indent=2))
print(json.dumps({'records':len(records),'failed':[(r['name'],r.get('http_status'),r.get('error')) for r in records if r['status']!='RETRIEVED'],'head':head,'anchors':anchors},indent=2))
