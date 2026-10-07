"""V0.4 source-only engine. No market APIs, indexes, accounts or latest queries."""
import argparse, base64, concurrent.futures, hashlib, json, pathlib, time
import urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
FREEZE = 'aeb1fe6bb2e730d2424d7d96929d8522a7dfe3af'
ENGINE_REVISION = 'v04-r2-authz-strict-protobuf'
LAST_COMPLETION_HEIGHT = {'ATOM':23763458,'OSMO':26771085,'KAVA':13333699,'TIA':3314015,'DYDX':33826953}
START, END = '2023-01-01T00:00:00Z', '2025-01-01T00:00:00Z'
CHAINS = {
 'ATOM': {'id':'cosmoshub-4','genesis':5200791,'anchor':20000000,'upper':24000000,'sources':{'citizenweb3':'https://rpc.cosmoshub-4-archive.citizenweb3.com','cryptocrew':'https://rpc.cosmoshub-main.ccvalidators.com'}},
 'OSMO': {'id':'osmosis-1','genesis':1,'anchor':15000000,'upper':27000000,'sources':{'foundation':'https://rpc.archive.osmosis.zone','validatus':'https://rpc.archive.osmosis.validatus.com'}},
 'KAVA': {'id':'kava_2222-10','genesis':1,'anchor':9500000,'upper':14000000,'sources':{'kavalabs':'https://rpc.data.kava.io','chainstack':'https://rpc.data.kava.chainstacklabs.com'}},
 'TIA': {'id':'celestia','genesis':1,'anchor':2500000,'upper':3400000,'sources':{'kjnodes':'http://136.243.94.113:26667','numia':'https://public-celestia-rpc.numia.xyz'}},
 'DYDX': {'id':'dydx-mainnet-1','genesis':1,'anchor':15000000,'upper':35000000,'sources':{'kingnodes':'https://dydx-ops-archive-rpc.kingnodes.com','polkachu':'https://dydx-dao-archive-rpc.polkachu.com'}}
}

def digest(raw): return hashlib.sha256(raw).hexdigest()
def save(path,obj):
 path=pathlib.Path(path); path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8'); tmp.replace(path)
def timestamp(s): return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()

class RPC:
 def __init__(self, chain, provider):
  self.chain,self.provider=chain,provider; self.base=CHAINS[chain]['sources'][provider]
  self.receipts=[]; self.last=0
 def get(self,method,params):
  assert method in ('blockchain','block','block_results','abci_query')
  assert 'height' in params or ('minHeight' in params and 'maxHeight' in params)
  if self.provider=='kavalabs': time.sleep(max(0,3.1-(time.monotonic()-self.last)))
  url=self.base+'/'+method+'?'+urllib.parse.urlencode(params)
  rec={'method':method,'params':params,'provider':self.provider,'url':url}; start=time.monotonic()
  try:
   self.last=time.monotonic()
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UnbondingV04/1.0'}),timeout=15) as r:
    raw=r.read(32*1024*1024+1); rec['http']=r.status
   if len(raw)>32*1024*1024: raise ValueError('response size cap')
   rec.update(sha256=digest(raw),bytes=len(raw)); obj=json.loads(raw)
   if obj.get('error'): raise ValueError(json.dumps(obj['error']))
   return obj['result'], rec
  except urllib.error.HTTPError as e:
   raw=e.read(4096); rec.update(http=e.code,error_body=raw.decode(errors='replace'),sha256=digest(raw)); raise
  except Exception as e: rec['error']=type(e).__name__+': '+str(e); raise
  finally: rec['seconds']=time.monotonic()-start; self.receipts.append(rec)
 def header(self,h):
  obj,rec=self.get('blockchain',{'minHeight':h,'maxHeight':h})
  # Do not retain last_height (current state); only requested historical header.
  metas=obj.get('block_metas') or []
  if len(metas)!=1: raise ValueError('missing or multiple requested headers')
  m=metas[0]; head=m['header']
  if int(head['height'])!=h or head['chain_id']!=CHAINS[self.chain]['id']: raise ValueError('height/chain mismatch')
  return {'height':h,'time':head['time'],'hash':m['block_id']['hash'],'app_hash':head['app_hash'],'app_version':head.get('version',{}).get('app')}

def lower_bound(rpc,lo,hi,target):
 t=timestamp(target); a=rpc.header(lo); b=rpc.header(hi)
 if timestamp(a['time'])>=t: return {'first':a,'previous':None,'genesis_boundary':True}
 if timestamp(b['time'])<t: raise ValueError('upper bracket before target; explicit new historical bracket required')
 while hi-lo>1:
  mid=(lo+hi)//2; m=rpc.header(mid)
  if timestamp(m['time'])<t: lo=mid
  else: hi=mid
 return {'first':rpc.header(hi),'previous':rpc.header(lo),'genesis_boundary':False}

def bounds(chain,provider):
 rpc=RPC(chain,provider); spec=CHAINS[chain]; result={'chain':chain,'provider':provider,'freeze':FREEZE}
 try:
  result['start']=lower_bound(rpc,spec['genesis'],spec['anchor'],START)
  result['exclusive_end']=lower_bound(rpc,spec['anchor'],spec['upper'],END)
  result['status']='BOUNDARIES_PROVEN_NOT_CENSUS'
 except Exception as e: result.update(status='BOUNDARY_BLOCKED',error=str(e))
 result['receipts']=rpc.receipts; save(ROOT/'receipts'/f'bounds-{chain}-{provider}.json',result)
 return {k:v for k,v in result.items() if k!='receipts'}

def fields(buf):
 def var(i):
  value=0
  for shift in range(0,70,7):
   if i>=len(buf): raise ValueError('truncated varint')
   b=buf[i]; i+=1; value|=(b&127)<<shift
   if b<128:return value,i
  raise ValueError('oversize varint')
 i=0
 while i<len(buf):
  key,i=var(i); n,w=key>>3,key&7
  if n==0: raise ValueError('zero protobuf field')
  if w==0:v,i=var(i)
  elif w in (1,2,5):
   if w==2:size,i=var(i)
   else:size=8 if w==1 else 4
   if i+size>len(buf):raise ValueError('truncated protobuf field')
   v=buf[i:i+size];i+=size
  else:raise ValueError('unsupported wire type')
  yield n,w,v
def first(buf,n,default=None):return next((v for k,w,v in fields(buf) if k==n),default)
def textf(buf,n):
 v=first(buf,n);return v.decode('utf-8') if isinstance(v,bytes) else v
def messages(raw):
 body=first(raw,1)
 if not isinstance(body,bytes):raise ValueError('TxRaw body absent')
 out=[]
 def walk(anybuf,indices,depth=0):
  if depth>8:raise ValueError('nested message depth cap')
  typ=textf(anybuf,1)
  if typ=='/cosmos.authz.v1beta1.MsgExec':
   value=first(anybuf,2,b'')
   for j,child in enumerate(v for n,w,v in fields(value) if n==2 and w==2):walk(child,indices+[j],depth+1)
   return
  if typ not in ('/cosmos.staking.v1beta1.MsgUndelegate','/cosmos.staking.v1beta1.MsgCancelUnbondingDelegation'):return
  value=first(anybuf,2,b''); coin=first(value,3,b'')
  msg={'message_index':indices[0],'message_path':indices,'type':typ,'delegator':textf(value,1),'validator':textf(value,2),'amount':textf(coin,2),'denom':textf(coin,1)}
  if not all(msg[k] for k in ('delegator','validator','amount','denom')):raise ValueError('missing staking fields')
  if not msg['amount'].isdigit():raise ValueError('invalid amount')
  if 'Cancel' in typ:msg['creation_height']=first(value,4,0)
  out.append(msg)
 for idx,anybuf in enumerate(v for n,w,v in fields(body) if n==1 and w==2):walk(anybuf,[idx])
 return out
def attrs(e):
 out={}
 for a in e.get('attributes',[]):
  k,v=a['key'],a['value']
  # Legacy ABCI base64 is decoded only when both are canonical base64.
  try:
   kb=base64.b64decode(k,validate=True).decode();vb=base64.b64decode(v,validate=True).decode()
   if kb in ('amount','validator','delegator','completion_time','creation_height','unbonding_id'):k,v=kb,vb
  except Exception:pass
  out.setdefault(k,[]).append(v)
 return out

def scan(chain,provider,lo,hi,out,max_seconds=240):
 """Coverage checkpoint: only contiguous successful block+results; failures never empty rows."""
 if hi<lo or hi-lo>=10000:raise ValueError('shard max 10000 blocks')
 if lo<CHAINS[chain]['genesis'] or hi>LAST_COMPLETION_HEIGHT[chain]:raise ValueError('shard outside frozen historical height bounds')
 path=pathlib.Path(out); rpc=RPC(chain,provider); started=time.monotonic()
 manifest={'freeze':FREEZE,'engine_revision':ENGINE_REVISION,'chain':chain,'provider':provider,'lo':lo,'hi':hi,'rows':[],'attempts':[],'complete':False,'ledger_certified':False}
 if path.exists():
  manifest=json.loads(path.read_text(encoding='utf-8'))
  if any(manifest.get(k)!=v for k,v in [('freeze',FREEZE),('engine_revision',ENGINE_REVISION),('chain',chain),('provider',provider),('lo',lo),('hi',hi)]):raise ValueError('checkpoint identity or decoder revision mismatch; old receipt preserved, new scan required')
 next_h=lo+len(manifest['rows'])
 for h in range(next_h,hi+1):
  if time.monotonic()-started>max_seconds:break
  offset=len(rpc.receipts)
  try:
   bo,br=rpc.get('block',{'height':h});head=bo['block']['header']
   if int(head['height'])!=h or head['chain_id']!=CHAINS[chain]['id']:raise ValueError('block mismatch')
   if timestamp(head['time'])>=timestamp(END):raise ValueError('out-of-window payload; stop')
   ro,rr=rpc.get('block_results',{'height':h})
   if int(ro['height'])!=h:raise ValueError('results height mismatch')
   txs=bo['block'].get('data',{}).get('txs') or []; results=ro.get('txs_results') or []
   if len(txs)!=len(results):raise ValueError('tx/result cardinality mismatch')
   row={'height':h,'time':head['time'],'block_hash':bo['block_id']['hash'],'app_hash':head['app_hash'],'block_digest':br['sha256'],'results_digest':rr['sha256'],'staking':[],'lifecycle':[]}
   for i,(tx,tr) in enumerate(zip(txs,results)):
    raw=base64.b64decode(tx,validate=True); msg=messages(raw)
    if 'code' not in tr:raise ValueError('missing explicit execution code')
    if int(tr['code'])==0 and msg:row['staking'].append({'tx_index':i,'tx_hash':digest(raw).upper(),'messages':msg,'events':[{'type':e['type'],'attrs':attrs(e)} for e in tr.get('events',[]) if e['type'] in ('unbond','complete_unbonding','cancel_unbonding_delegation')]})
   for phase in ('begin_block_events','end_block_events','finalize_block_events'):
    for ei,e in enumerate(ro.get(phase) or []):
     if e.get('type') in ('complete_unbonding','slash','unbond','cancel_unbonding_delegation'):row['lifecycle'].append({'phase':phase,'event_index':ei,'type':e['type'],'attrs':attrs(e)})
   manifest['rows'].append(row)
  except Exception as e:
   manifest['last_error']={'height':h,'error':str(e)}
   manifest['attempts'].extend(rpc.receipts[offset:]);save(path,manifest);break
  manifest['attempts'].extend(rpc.receipts[offset:]);save(path,manifest)
 manifest['complete']=len(manifest['rows'])==hi-lo+1
 manifest['elapsed_seconds_this_run']=time.monotonic()-started
 manifest['rows_per_second_this_run']=(len(manifest['rows'])-(next_h-lo))/max(.001,manifest['elapsed_seconds_this_run'])
 save(path,manifest)
 return {'chain':chain,'provider':provider,'complete':manifest['complete'],'covered':len(manifest['rows']),'error':manifest.get('last_error'),'seconds':manifest['elapsed_seconds_this_run']}

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['bounds','scan']);p.add_argument('--chain',choices=list(CHAINS));p.add_argument('--provider');p.add_argument('--lo',type=int);p.add_argument('--hi',type=int);p.add_argument('--out');p.add_argument('--seconds',type=int,default=240);a=p.parse_args()
 if a.mode=='bounds':
  jobs=[(c,s) for c,v in CHAINS.items() for s in v['sources'] if not a.chain or c==a.chain]
  with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
   for x in ex.map(lambda t:bounds(*t),jobs):print(json.dumps(x),flush=True)
 else:print(json.dumps(scan(a.chain,a.provider,a.lo,a.hi,a.out,a.seconds)))
if __name__=='__main__':main()
