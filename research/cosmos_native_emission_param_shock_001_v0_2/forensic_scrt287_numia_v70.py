"""Unauthenticated Numia discovery only; never execute SQL or promote the gate."""
import concurrent.futures, datetime, hashlib, json, os, pathlib, subprocess, urllib.parse
from forensic_scrt287_v54 import fetch
import forensic_scrt287_v54 as acquisition

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'forensic_numia_v70'
PIN = '8e67930bee1d99acf933cc4a000b90258b352f68'
FIRST = 'e5d7d16f7f580ef6621196a4ba56d73972bbb825'
SEEDS = {
 'schema_current': f'https://raw.githubusercontent.com/numiadata/numia-docs/{PIN}/data/secret-table.json',
 'schema_first': f'https://raw.githubusercontent.com/numiadata/numia-docs/{FIRST}/data/secret-table.json',
 'metadata_generator': f'https://raw.githubusercontent.com/numiadata/numia-docs/{PIN}/scripts/src/cmd/tables-metadata.ts',
 'sql_getting_started': f'https://raw.githubusercontent.com/numiadata/numia-docs/{PIN}/docs/sql/overview/getting-started.mdx',
 'secret_doc': f'https://raw.githubusercontent.com/numiadata/numia-docs/{PIN}/docs/sql/querying-data/chains/secret.mdx',
 'numia_repo_metadata': 'https://api.github.com/repos/numiadata/numia-docs',
 'numia_forks': 'https://api.github.com/repos/numiadata/numia-docs/forks?per_page=100',
 'numia_org_repos': 'https://api.github.com/orgs/numiadata/repos?per_page=100',
 'secret_schema_commits': 'https://api.github.com/repos/numiadata/numia-docs/commits?path=data/secret-table.json&per_page=100',
 'legacy_using_commits': 'https://api.github.com/repos/numiadata/numia-docs/commits?path=using-numia/chains/secret&per_page=100',
 'legacy_overview_commits': 'https://api.github.com/repos/numiadata/numia-docs/commits?path=overview/sql-access/chains/secret&per_page=100',
 'partnership': 'https://medium.com/@numia.data/numia-partners-with-secret-network-to-bring-sql-access-to-on-chain-data-via-bigquery-680c89c748c8',
 'foundation_report': 'https://scrt.network/wp-content/uploads/2024/04/SNF-Quarterly-Report-Q1-2024.pdf',
 'wayback_docs_secret': 'https://web.archive.org/cdx/search/cdx?url=docs.numia.xyz/*secret*&output=json&filter=statuscode:200&collapse=urlkey',
 'wayback_legacy_using': 'https://web.archive.org/cdx/search/cdx?url=docs.numia.xyz/using-numia/chains/secret*&output=json&collapse=timestamp:6',
 'wayback_legacy_overview': 'https://web.archive.org/cdx/search/cdx?url=docs.numia.xyz/overview/sql-access/chains/secret*&output=json&collapse=timestamp:6',
 'legacy_using_live': 'https://docs.numia.xyz/using-numia/chains/secret',
 'legacy_overview_live': 'https://docs.numia.xyz/overview/sql-access/chains/secret',
 'github_secret_repos': 'https://api.github.com/search/repositories?q=numia+secret&per_page=100',
 'github_bigquery_repos': 'https://api.github.com/search/repositories?q=numia+bigquery&per_page=100',
 'github_code_exact': 'https://api.github.com/search/code?q=' + urllib.parse.quote('"numia-data.secret.secret_blocks"'),
 'grepapp_exact': 'https://grep.app/api/search?q=numia-data.secret.secret_blocks',
 'grepapp_legacy': 'https://grep.app/api/search?q=immaculate-355716.secret',
 'grepapp_secret_blocks': 'https://grep.app/api/search?q=secret_blocks&filter[lang][0]=SQL',
}
for project in ['numia-data', 'immaculate-355716']:
 base = f'https://bigquery.googleapis.com/bigquery/v2/projects/{project}/datasets/secret'
 SEEDS[project + '_dataset'] = base
 SEEDS[project + '_tables'] = base + '/tables?maxResults=100'
 SEEDS[project + '_blocks_metadata'] = base + '/tables/secret_blocks'
 SEEDS[project + '_blocks_rows'] = base + '/tables/secret_blocks/data?maxResults=1'
 SEEDS[project + '_events_metadata'] = base + '/tables/secret_block_events'

def main():
 if (OUT / 'receipt.json').exists():
  raise SystemExit('Receipt exists; preserve it. Use a new version for a new acquisition.')
 OUT.mkdir(exist_ok=True)
 (OUT / 'raw').mkdir(exist_ok=True)
 acquisition.OUT = OUT
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  rows = list(pool.map(fetch, SEEDS.items()))
 receipt = {'scope': 'SOURCE_ONLY_NO_MARKET_DATA', 'credentials_used': False,
  'authentication_attempted': False, 'sql_executed': False, 'base_commit': os.environ.get('GITHUB_SHA') or subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT).decode().strip(),
  'requested_baseline': '29ff9fadfaa62f520f1403f605637e3847f1e971', 'numia_docs_pin': PIN,
  'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'rows': rows,
  'canonical_H': None, 'canonical_T0': None, 'certified_sources': '11/12',
  'gate': 'SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED', 'forensic_phase': 'OPEN_NOT_EXHAUSTED'}
 (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
 print(json.dumps([(r['id'],r.get('status'),r['classification']) for r in rows]))

if __name__ == '__main__':
 main()
