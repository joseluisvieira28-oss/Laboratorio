"""Bounded independent state, snapshot and prospective substitute qualification probes."""
import concurrent.futures, json, urllib.request, urllib.parse, urllib.error, pathlib, shutil
from census import ROOT, FREEZE, CHAINS, RPC, save, digest

def metadata(url,method='GET',cap=2000000):
 rec={'url':url,'method':method}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,method=method,headers={'User-Agent':'UnbondingV04/1.0'}),timeout=20) as r:
   rec.update(http=r.status,final_url=r.url,content_length=r.headers.get('Content-Length'),content_type=r.headers.get('Content-Type'))
   if method=='GET':
    raw=r.read(cap+1)
    if len(raw)>cap:raise ValueError('metadata exceeds cap')
    rec.update(sha256=digest(raw));return rec,raw
  return rec,None
 except urllib.error.HTTPError as e:
  raw=e.read(4096);rec.update(http=e.code,error=raw.decode(errors='replace'),sha256=digest(raw))
 except Exception as e:rec['error']=str(e)
 return rec,None

def state(chain,provider):
 rpc=RPC(chain,provider);h=CHAINS[chain]['anchor'];out={'chain':chain,'provider':provider,'height':h,'freeze':FREEZE,'proof_verified':False,'range_completeness':False,'queries':[]}
 # subspace disabled: production SDKs can query current store while echoing requested height.
 for path,data,prove in [('/store/staking/key','0x41',True),('/cosmos.staking.v1beta1.Query/Pool','0x',False)]:
  q={'path':json.dumps(path),'data':data,'height':str(h),'prove':str(prove).lower()}
  try:
   result,rec=rpc.get('abci_query',q);response=result['response']
   out['queries'].append({'path':path,'code':response.get('code'),'log':response.get('log'),'height':response.get('height'),'proof_ops':response.get('proofOps') or response.get('proof_ops'),'key':response.get('key'),'value':response.get('value')})
  except Exception as e:out['queries'].append({'path':path,'error':str(e)})
 out['receipts']=rpc.receipts;save(ROOT/'receipts'/f'state-{chain}-{provider}.json',out)
 return {'chain':chain,'provider':provider,'queries':[{k:v for k,v in q.items() if k not in ('value','proof_ops')} for q in out['queries']]}

def registry_and_substitutes():
 out={'freeze':FREEZE,'source_only':True,'substitute_selected':False,'census_use_authorized':False,'chains':{}}
 for name in ('cosmoshub','osmosis','kava','celestia','dydx','injective','sei','akash'):
  rec,raw=metadata(f'https://raw.githubusercontent.com/cosmos/chain-registry/master/{name}/chain.json')
  row={'registry_receipt':rec,'qualification':'PENDING_MECHANISM_AND_TWO_PATHS'};out['chains'][name]=row
  if not raw:continue
  obj=json.loads(raw);row.update(chain_id=obj.get('chain_id'),codebase=obj.get('codebase'),genesis=obj.get('codebase',{}).get('genesis'),rpc=obj.get('apis',{}).get('rpc'))
  if name not in ('injective','sei','akash'):continue
  # Headers only. No event census on unqualified substitutes.
  candidates=(obj.get('apis',{}).get('rpc') or [])[:8]
  row['historical_path_tests']=[]
  height={'injective':50000000,'sei':20000000,'akash':15000000}[name]
  for src in candidates:
   url=src['address'].rstrip('/')+'/blockchain?'+urllib.parse.urlencode({'minHeight':height,'maxHeight':height})
   receipt,body=metadata(url)
   test={'provider':src.get('provider'),'height':height,'receipt':receipt};row['historical_path_tests'].append(test)
   if body:
    try:
     j=json.loads(body);test['rpc_error']=j.get('error');metas=j.get('result',{}).get('block_metas') or []
     test['headers']=[{'height':m['header']['height'],'time':m['header']['time'],'chain_id':m['header']['chain_id'],'hash':m['block_id']['hash']} for m in metas]
    except Exception as e:test['error']=str(e)
 save(ROOT/'receipts'/'registry-prospective.json',out);return out

def snapshots():
 urls=['https://download.nodies.org/download/latest/snapshot/de/kava/mainnet/archive','https://download.nodies.org/download/latest/snapshot/use/kava/mainnet/archive','https://quicksync.io','https://polkachu.com/archive_snapshots','https://docs.nodies.app','https://docs.kava.io/docs/nodes-and-validators/node-setup-guide/','https://docs.kava.io/docs/faq/historic-data/']
 out={'freeze':FREEZE,'payloads_downloaded':False,'proof_verified':False,'restoration_executed':False,'disk_free_bytes':shutil.disk_usage(ROOT).free,'tools':{t:shutil.which(t) for t in ('docker','go','wsl','rocksdb_dump')},'routes':[]}
 for url in urls:
  rec,raw=metadata(url,'HEAD' if 'download.nodies' in url else 'GET');out['routes'].append(rec)
  if raw:
   dest=ROOT/'receipts'/('metadata-'+digest(url.encode())[:12]+'.txt');dest.write_bytes(raw);rec['saved_metadata']=dest.name
 save(ROOT/'receipts'/'snapshot-routes.json',out);return out

def main():
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
  jobs=[ex.submit(state,c,s) for c,v in CHAINS.items() for s in v['sources']]
  jobs += [ex.submit(registry_and_substitutes),ex.submit(snapshots)]
  for f in concurrent.futures.as_completed(jobs):
   try:result=f.result();print(json.dumps(result)[:4000],flush=True)
   except Exception as e:print(type(e).__name__+': '+str(e),flush=True)
if __name__=='__main__':main()
