import json,hashlib,urllib.request,urllib.error,pathlib,concurrent.futures,datetime
P=pathlib.Path(__file__).resolve().parent; R=P/'receipts'
if (P/'historical_version_inventory.json').exists(): raise SystemExit('Existing inventory preserved; use a new run directory')
def get(name,url):
 rec={'name':name,'url':url,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Laboratorio-Coreum-Replay-V07'}),timeout=30) as r: b=r.read();rec['http_status']=r.status
  (R/(name+'.raw')).write_bytes(b);rec.update(status='RETRIEVED',sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),file='receipts/'+name+'.raw')
  try:o=json.loads(b)
  except:o=None
  return rec,o
 except Exception as e:rec.update(status='FAILED',error=str(e));return rec,None
T=json.loads((R/'official_tags.raw').read_bytes()); releases=json.loads((R/'official_releases.raw').read_bytes()); tags={x['name']:x['commit']['sha'] for x in T}; recs=[]; inv=[]
for tag in ['v1.0.0','v2.0.0','v2.0.1','v2.0.2','v3.0.0','v3.0.1','v3.0.2','v3.0.3']:
 sha=tags[tag]; rec,tree=get('tree_'+tag,'https://api.github.com/repos/CoreumFoundation/coreum/git/trees/'+sha+'?recursive=1');recs.append(rec)
 paths=[x['path'] for x in (tree or {}).get('tree',[]) if x['path']=='go.mod' or x['path']=='genesis/coreum-mainnet-1.json' or (x['path'].startswith('app/upgrade') and x['path'].endswith('.go')) or x['path']=='build/coreum/upgrades.go']
 jobs=[('history_'+tag+'_'+hashlib.sha256(p.encode()).hexdigest()[:10],'https://raw.githubusercontent.com/CoreumFoundation/coreum/'+sha+'/'+p,p) for p in paths]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for (name,url,p),(r,o) in zip(jobs,pool.map(lambda j:get(j[0],j[1]),jobs)):r.update(tag=tag,path=p,commit=sha);recs.append(r)
 rel=next((x for x in releases if x['tag_name']==tag),{})
 inv.append({'tag':tag,'source_commit':sha,'published_at':rel.get('published_at'),'assets':[{k:a.get(k) for k in ['name','size','digest','browser_download_url']} for a in rel.get('assets',[])],'activation_height_verified':False})
 for a in rel.get('assets',[]):
  if a['name']=='checksums.txt':r,o=get('checksums_'+tag,a['browser_download_url']);recs.append(r)
A='https://archive.rpc.mainnet-1.tx.org';plans=[]
for name in ['v1','v2','v2patch1','v3','v3patch1','v3patch2']:
 data=(bytes([10,len(name)])+name.encode()).hex();url=A+'/abci_query?path=%22/cosmos.upgrade.v1beta1.Query/AppliedPlan%22&data=0x'+data+'&height=15000000&prove=false'
 r,o=get('applied_'+name,url);recs.append(r);res=(((o or {}).get('result') or {}).get('response') or {})
 plans.append({'name':name,'response':res,'trusted_for_replay':False,'reason':'Source A state query is a discovery hint; requires independent execution/state verification'})
(P/'historical_version_inventory.json').write_text(json.dumps({'versions':inv,'applied_plan_hints':plans,'sequence_complete':False,'records':recs},indent=2))
print(json.dumps({'versions':[(x['tag'],x['source_commit']) for x in inv],'plan_hints':plans,'failures':[r for r in recs if r['status']!='RETRIEVED']},indent=2))
