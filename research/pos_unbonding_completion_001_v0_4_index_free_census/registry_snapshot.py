import concurrent.futures,json,hashlib
from census import ROOT,FREEZE,save
from source_routes import metadata
COMMIT='7cec0f5c2fbef9ac8658f916ed239dd0b6c0119e'
def candidate(row):
 rec,raw=metadata(f'https://raw.githubusercontent.com/cosmos/chain-registry/{COMMIT}/{row["path"]}')
 out={**row,'receipt':rec,'qualification':'NOT_CERTIFIED_SOURCE_ONLY'}
 if raw:
  sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest();out['git_blob_verified']=sha==row['blob_sha']
  j=json.loads(raw);out.update(chain_id=j.get('chain_id'),status=j.get('status'),network_type=j.get('network_type'),codebase=j.get('codebase'),staking=j.get('staking'),apis=j.get('apis'))
 return out
def main():
 rows=json.loads((ROOT/'receipts'/'historical-registry-universe-paths.json').read_text())['candidates']
 out={'freeze':FREEZE,'registry_commit':COMMIT,'candidate_count':len(rows),'selection_by_counts_or_outcomes':False,'candidates':[]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for result in ex.map(candidate,rows):out['candidates'].append(result);save(ROOT/'receipts'/'historical-registry-universe.json',out)
 print(json.dumps({'count':len(rows),'verified':sum(x.get('git_blob_verified',False) for x in out['candidates'])}))
if __name__=='__main__':main()
