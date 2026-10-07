"""Pin candidate historical production release source. Height applicability remains unverified."""
import concurrent.futures,json,re
from source_routes import metadata
from census import ROOT,FREEZE,save

SPECS={
 'ATOM':('cosmos/gaia',['v8.0.1','v9.0.2','v10.0.1','v11.0.0','v12.0.0','v13.0.0','v14.1.0','v15.2.0','v16.0.0','v17.0.0','v18.0.0','v19.0.0','v20.0.0','v21.0.0']),
 'OSMO':('osmosis-labs/osmosis',['v13.1.2','v14.0.0','v15.0.0','v16.1.1','v17.0.0','v18.0.0','v19.0.0','v20.0.0','v21.0.0','v22.0.0','v23.0.0','v24.0.0','v25.0.0','v26.0.0','v27.0.0']),
 'KAVA':('kava-labs/kava',['v0.19.2','v0.21.1','v0.23.3','v0.24.3','v0.25.0','v0.26.2']),
 'TIA':('celestiaorg/celestia-app',['v1.0.0','v1.3.0','v1.8.0','v2.0.0','v3.0.0']),
 'DYDX':('dydxprotocol/v4-chain',['protocol/v1.0.0','protocol/v2.0.0','protocol/v3.0.0','protocol/v4.0.0','protocol/v5.0.0','protocol/v6.0.0','protocol/v7.0.0']),
 'INJ':('InjectiveLabs/injective-core',['v1.10.0','v1.11.0','v1.12.0','v1.13.0']),
 'SEI':('sei-protocol/sei-chain',['v1.0.0','v2.0.0','v3.0.0','v5.9.0'])}

def pin(chain,repo,tag):
 path='protocol/go.mod' if chain=='DYDX' else 'go.mod'
 rec,raw=metadata(f'https://raw.githubusercontent.com/{repo}/{tag}/{path}')
 out={'chain':chain,'app_repo':repo,'tag':tag,'go_mod_receipt':rec,'height_applicability_certified':False}
 if not raw:return out
 s=raw.decode();out['sdk_module_lines']=[x.strip() for x in s.splitlines() if any(k in x for k in ('cosmos-sdk','cometbft','tendermint'))]
 rec,raw=metadata(f'https://api.github.com/repos/{repo}/commits/{tag}')
 out['commit_receipt']=rec
 if raw:out['app_commit']=json.loads(raw).get('sha')
 # Resolve SDK replacement, including forked SDKs, from go.mod rather than label.
 matches=re.findall(r'github.com/cosmos/cosmos-sdk\s+([v][^\s]+)',s)
 replacement=re.search(r'github.com/cosmos/cosmos-sdk\s*=>\s*github.com/([^\s]+)\s+(v[^\s]+)',s)
 if replacement:sdk_repo,sdk_tag=replacement.groups()
 elif matches:sdk_repo,sdk_tag='cosmos/cosmos-sdk',matches[0]
 else:return out
 out.update(sdk_repo=sdk_repo,sdk_tag=sdk_tag)
 # Pseudo versions carry immutable commit suffix; otherwise use named release with digest.
 sdkref=sdk_tag.rsplit('-',1)[-1] if re.search(r'-\d{14}-[a-f0-9]{12}$',sdk_tag) else sdk_tag
 out['sdk_source_ref']=sdkref;out['source_files']=[]
 for filename in ('x/staking/types/keys.go','x/staking/keeper/delegation.go','store/iavl/store.go'):
  rec,raw=metadata(f'https://raw.githubusercontent.com/{sdk_repo}/{sdkref}/{filename}')
  row={'path':filename,'receipt':rec};out['source_files'].append(row)
  if raw:
   text=raw.decode();row['relevant_source_lines']=[{'line':i,'text':line.strip()} for i,line in enumerate(text.splitlines(),1) if any(k in line for k in ('UnbondingQueueKey','FormatTimeBytes','GetUnbondingDelegationTimeKey','Query subspace','case "subspace"','QuerySubspace','prefix :=','Iterator','ctx.BlockTime','UnbondingOnHoldRefCount','UnbondingID'))][:60]
 return out

def main():
 jobs=[(c,r,t) for c,(r,tags) in SPECS.items() for t in tags]
 out={'freeze':FREEZE,'production_height_map_complete':False,'pins':[]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for row in ex.map(lambda x:pin(*x),jobs):
   out['pins'].append(row);save(ROOT/'receipts'/'version-pins.json',out);print(row['chain'],row['tag'],row.get('sdk_repo'),row.get('sdk_tag'),flush=True)
if __name__=='__main__':main()
