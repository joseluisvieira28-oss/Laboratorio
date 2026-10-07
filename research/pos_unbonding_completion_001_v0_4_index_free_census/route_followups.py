import json, concurrent.futures, re, urllib.parse
from census import ROOT, FREEZE, save
from source_routes import metadata

def check(base,h):
 out={'base':base,'height':h,'requests':[]}
 for method in ('block','block_results'):
  rec,raw=metadata(base.rstrip('/')+'/'+method+'?height='+str(h),cap=16*1024*1024)
  result={'receipt':rec};out['requests'].append(result)
  if raw:
   try:
    obj=json.loads(raw);r=obj.get('result',{});result['rpc_error']=obj.get('error')
    if method=='block':
     hdr=r.get('block',{}).get('header',{});result['header']={k:hdr.get(k) for k in ('height','time','chain_id','app_hash')};result['block_hash']=r.get('block_id',{}).get('hash')
    else:result.update(height=r.get('height'),schema=list(r),tx_results_present='txs_results' in r,lifecycle_schema=any(k in r for k in ('end_block_events','finalize_block_events')))
   except Exception as e:result['error']=str(e)
 return out

def main():
 registry=json.loads((ROOT/'receipts'/'registry-prospective.json').read_text())
 tests=[('https://public-celestia-rpc.numia.xyz',h) for h in (1,2500000,3314015)]
 for name,h in [('kava',9500000),('injective',50000000),('sei',20000000),('akash',15000000)]:
  tests += [(s['address'],h) for s in registry['chains'][name].get('rpc',[]) if not any(x in s['address'] for x in ('go.getblock','lb.nodies','uquad'))]
 tests += [('https://injective-archive-rpc.polkachu.com',50000000),('https://sei-archive-rpc.polkachu.com',20000000),('https://akash-archive-rpc.polkachu.com',15000000)]
 out={'freeze':FREEZE,'counts_used':False,'substitute_selected':False,'tests':[]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for result in ex.map(lambda t:check(*t),tests):
   out['tests'].append(result);save(ROOT/'receipts'/'route-followups.json',out)
   print(json.dumps(result)[:1000],flush=True)
 # Public snapshot page metadata and HEAD only; never fetch current application state.
 rec,raw=metadata('https://quicksync.io/kava');out['quicksync_page']=rec
 if raw:
  text=raw.decode(); links=re.findall(r'https?[^\s"<>\\]+',text)
  targets=sorted(set(x.replace('&amp;','&') for x in links if 'storage' in x and 'kava' in x and any(t in x for t in ('archive','rocksdb'))))
  out['snapshot_headers']=[metadata(u,'HEAD')[0] for u in targets[:5]]
 save(ROOT/'receipts'/'route-followups.json',out)
if __name__=='__main__':main()
