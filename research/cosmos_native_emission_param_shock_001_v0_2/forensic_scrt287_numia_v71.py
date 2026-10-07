"""Follow only public documentary leads from V70; no account or SQL access."""
import concurrent.futures, datetime, json
import forensic_scrt287_v54 as acquisition
from forensic_scrt287_numia_v70 import ROOT
OUT = ROOT / 'forensic_numia_v71'
SEEDS = {
 'wayback_april2024': 'https://web.archive.org/web/20240417014429id_/https://docs.numia.xyz/overview/sql-access/chains/secret-network',
 'wayback_july2024': 'https://web.archive.org/web/20240718192156id_/https://docs.numia.xyz/overview/sql-access/chains/secret-network',
 'wayback_nov2024': 'https://web.archive.org/web/20241104003617id_/https://docs.numia.xyz/overview/sql-access/chains/secret-network',
 'wayback_jan2025': 'https://web.archive.org/web/20250115075315id_/https://docs.numia.xyz/overview/sql-access/chains/secret-network',
 'public_reports_tree': 'https://api.github.com/repos/numiadata/public-reports/git/trees/main?recursive=1',
 'numia_tools_tree': 'https://api.github.com/repos/numiadata/tools/git/trees/main?recursive=1',
 'numia_site_tree': 'https://api.github.com/repos/numiadata/site/git/trees/master?recursive=1',
 'numia_proxy_tree': 'https://api.github.com/repos/numiadata/numia-worker-proxy/git/trees/main?recursive=1',
 'neutron_schema_tree': 'https://api.github.com/repos/yodablocks/db-n-/git/trees/main?recursive=1',
 'historical_secret_doc': 'https://raw.githubusercontent.com/numiadata/numia-docs/4196600bd7f03c2e42fc7e5978db7d8b956a5103/docs/sql/querying-data/chains/secret-network.mdx',
 'google_timestamp_docs': 'https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/data-types',
 'google_sandbox_docs': 'https://docs.cloud.google.com/bigquery/docs/sandbox',
}
def main():
 if (OUT / 'receipt.json').exists():
  raise SystemExit('Preserve existing receipts; use a new version.')
 OUT.mkdir(exist_ok=True)
 (OUT / 'raw').mkdir(exist_ok=True)
 acquisition.OUT = OUT
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  rows = list(pool.map(acquisition.fetch, SEEDS.items()))
 (OUT / 'receipt.json').write_text(json.dumps({'scope':'SOURCE_ONLY_NO_MARKET_DATA', 'credentials_used':False,
  'authentication_attempted':False, 'sql_executed':False, 'rows':rows, 'canonical_H':None, 'canonical_T0':None,
  'gate':'SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED','forensic_phase':'OPEN_NOT_EXHAUSTED'},indent=2)+'\n',encoding='utf-8')
 print(json.dumps([(r['id'],r.get('status'),r['classification']) for r in rows]))
if __name__ == '__main__': main()
