"""Follow documented public metadata leads; do not access accounts or promote T0."""
import concurrent.futures,json,pathlib,re,urllib.parse
import forensic_scrt287_v54 as collector
ROOT=pathlib.Path(__file__).resolve().parent
collector.OUT=ROOT/'forensic_v55'
SEEDS={
 'numia_sql_docs':'https://docs.numia.xyz/sql/obsessiondb/whats-numia-sql',
 'numia_chain_coverage':'https://docs.numia.xyz/home/overview/chain-coverage',
 'numia_warehouse_docs':'https://docs.numia.xyz/home/products/data-warehouse',
 'numia_sitemap':'https://docs.numia.xyz/sitemap-index.xml',
 'numia_legacy_docs':'https://docs.numia.xyz/overview/supported-chains',
 'secretanalytics_metadata':'https://secretanalytics.xyz/sitemap.xml',
 'posthuman_frontend':'https://explorer.posthuman.digital/assets/index-2cf67c66.js',
 'bdjuno_redirect_release':'https://api.github.com/repositories/253669806/releases?per_page=100',
 'bdjuno_redirect_artifacts':'https://api.github.com/repositories/253669806/actions/artifacts?per_page=100',
 'ipfsync_tree':'https://api.github.com/repos/notional-labs/ipfsync/git/trees/HEAD?recursive=1',
 'secretlabs_release_page2':'https://api.github.com/repos/scrtlabs/SecretNetwork/releases?per_page=100&page=2',
 'secretlabs_release_page3':'https://api.github.com/repos/scrtlabs/SecretNetwork/releases?per_page=100&page=3',
 'secretlabs_release_page4':'https://api.github.com/repos/scrtlabs/SecretNetwork/releases?per_page=100&page=4',
 'archive_secret_network_data':'https://archive.org/advancedsearch.php?'+urllib.parse.urlencode({'q':'(title:("Secret Network") OR subject:(secretnetwork)) AND (mediatype:data OR mediatype:software)','output':'json','rows':100}),
 'huggingface_secret_network':'https://huggingface.co/api/datasets?search=secret-network',
 'blockchain_etl_cosmos':'https://api.github.com/repos/blockchain-etl/cosmos-etl/git/trees/HEAD?recursive=1',
 'chainofsecrets_tree':'https://api.github.com/repos/chainofsecrets/SecretNetwork/git/trees/HEAD?recursive=1',
 'secret_status_tree':'https://api.github.com/repos/levackt/secretnetwork-node-status/git/trees/HEAD?recursive=1',
}
def main():
 collector.OUT.mkdir(exist_ok=True);(collector.OUT/'raw').mkdir(exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  rows=list(pool.map(collector.fetch,SEEDS.items()))
 for r in rows:
  if r.get('raw') and 'tree' in r['id']:
   try:
    j=json.loads((collector.OUT/r['raw']).read_bytes())
    r['tree_sha']=j.get('sha');r['tree_truncated']=j.get('truncated')
    r['candidate_paths']=[x['path'] for x in j.get('tree',[]) if re.search(r'snapshot|archive|blockstore|dump|\.sql$|\.torrent$|telemetry|logs|secret',x['path'],re.I)][:100]
   except ValueError:pass
 receipt={'scope':'SOURCE_ONLY_NO_MARKET_DATA','candidate':'SCRT Proposal 287','rows':rows,'H':None,'T0':None,'gate':'SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED','forensic_exhaustion':False,'authenticated_access':False}
 (collector.OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 print(json.dumps([(r['id'],r.get('status'),r.get('pagination_incomplete'),r.get('candidate_paths')) for r in rows]))
if __name__=='__main__':main()
