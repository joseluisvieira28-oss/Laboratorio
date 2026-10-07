"""Targeted public follow-up to V54/V55 documented metadata."""
import json,concurrent.futures,pathlib
import forensic_scrt287_v54 as c
c.OUT=pathlib.Path(__file__).resolve().parent/'forensic_v56'
SEEDS={
 'numia_cosmos_schema':'https://docs.numia.xyz/sql/obsessiondb/ecosystems/cosmos-sdk',
 'numia_sql_access':'https://docs.numia.xyz/sql/obsessiondb/getting-started',
 'numia_migration':'https://docs.numia.xyz/sql/migrating-bigquery-to-obsessiondb',
 'secret_status_source':'https://raw.githubusercontent.com/levackt/secretnetwork-node-status/master/README.md',
 'notional_ipfsync_readme':'https://raw.githubusercontent.com/notional-labs/ipfsync/2956af3/README.md',
 'notional_ipfs_documentation':'https://raw.githubusercontent.com/notional-labs/notional/9b5165e255e142711bb04c64ac75c3234bc573cb/infrastructure/ipfsync/README.md',
 'hf_secretnetwork_retry':'https://huggingface.co/api/datasets?search=secretnetwork',
 'stakecraft_retry':'https://snapshots.stakecraft.com/',
}
def main():
 c.OUT.mkdir(exist_ok=True);(c.OUT/'raw').mkdir(exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(c.fetch,SEEDS.items()))
 (c.OUT/'receipt.json').write_text(json.dumps({'scope':'SOURCE_ONLY_NO_MARKET_DATA','rows':rows,'H':None,'T0':None,'exhaustion':False},indent=2)+'\n',encoding='utf-8')
 print([(r['id'],r.get('status'),r.get('error')) for r in rows])
if __name__=='__main__':main()
