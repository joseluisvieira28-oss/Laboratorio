"""Public, credential-free metadata recovery. No automatic gate promotion."""
import concurrent.futures, datetime, hashlib, json, pathlib, re, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'forensic_v54'
MAX_BYTES = 4000000
SEEDS = {
 'numia_documentation': 'https://docs.numia.xyz/',
 'numia_partnership': 'https://medium.com/@numia.data/numia-partners-with-secret-network-to-bring-sql-access-to-on-chain-data-via-bigquery-680c89c748c8',
 'secretanalytics_indexer': 'https://secretanalytics.xyz/robots.txt',
 'kyve_pool_catalog': 'https://api.kyve.network/kyve/query/v1beta1/pools?pagination.limit=100',
 'kyve_kaon_catalog': 'https://api.kaon.kyve.network/kyve/query/v1beta1/pools?pagination.limit=100',
 'internet_archive_dataset_catalog': 'https://archive.org/advancedsearch.php?q=%22secret-4%22&output=json',
 'huggingface_dataset_catalog': 'https://huggingface.co/api/datasets?search=secretnetwork',
 'aws_open_data_catalog': 'https://raw.githubusercontent.com/awslabs/open-data-registry/main/datasets/aws-public-blockchain.yaml',
 'posthuman_explorer_metadata': 'https://explorer.posthuman.digital/secretnetwork/blocks/11880919',
 'stakecraft_snapshot_catalog': 'https://snapshots.stakecraft.com/',
}
REPOS = ['scrtlabs/SecretNetwork', 'SecretFoundation/docs', 'chainofsecrets/SecretNetwork',
         'notional-labs/ipfscync', 'notional-labs/ipfsync', 'forbole/bdjuno',
         'levackt/secretnetwork-node-status', 'Secret3dev/SecretNetwork']
for repo in REPOS:
 for route in ['releases?per_page=100', 'actions/artifacts?per_page=100']:
  SEEDS[repo.replace('/', '_') + '_' + route.split('?')[0].replace('/', '_')] = 'https://api.github.com/repos/' + repo + '/' + route

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self, *args, **kwargs):
  return None

def fetch(item):
 name, url = item
 row = {'id': name, 'url': url, 'method': 'GET', 'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  request = urllib.request.Request(url, headers={'User-Agent': 'CryptoLab-SCRT287-source-only-v54', 'Accept': 'application/json,text/plain,text/html'})
  try:
   response = urllib.request.build_opener(NoRedirect).open(request, timeout=20)
  except urllib.error.HTTPError as e:
   response = e
  with response:
   body = response.read(MAX_BYTES + 1)
   row.update(status=response.code, content_type=response.headers.get('Content-Type'), location=response.headers.get('Location'), truncated=len(body)>MAX_BYTES)
   body = body[:MAX_BYTES]
   row.update(sha256=hashlib.sha256(body).hexdigest(), bytes=len(body), raw='raw/' + name + '.bin')
   (OUT / row['raw']).write_bytes(body)
   try:
    data = json.loads(body)
   except (ValueError, UnicodeError):
    data = None
   if isinstance(data, dict):
    row['pagination_next'] = data.get('pagination', {}).get('next_key')
    if 'artifacts' in data:
     row['total_count'] = data.get('total_count')
     row['artifacts'] = [{k:a.get(k) for k in ['id','name','expired','created_at','expires_at','size_in_bytes']} for a in data['artifacts']]
     row['pagination_incomplete'] = data.get('total_count', 0) > len(data['artifacts'])
    if 'pools' in data:
     row['pool_names'] = [p.get('data', p).get('name') for p in data['pools']]
   if isinstance(data, list):
    row['releases'] = [{'tag':r.get('tag_name'),'published_at':r.get('published_at'), 'assets':[{k:a.get(k) for k in ['name','size','browser_download_url','digest']} for a in r.get('assets', [])]} for r in data if isinstance(r, dict)] if 'releases' in name else None
    row['pagination_incomplete'] = len(data) == 100
   text = body.decode('utf-8', 'replace')
   row['discovery_lines'] = [line[:1500] for line in text.splitlines() if re.search(r'secret-4|secretnetwork|snapshot|blockstore|\.torrent|ipfs|bigquery', line, re.I)][:30]
   row['classification'] = 'DISCOVERY_ONLY' if 200 <= row['status'] < 300 else 'ACCESS_BLOCKED_OR_ABSENT'
 except Exception as e:
  row.update(classification='ACCESS_BLOCKED', error=type(e).__name__ + ': ' + str(e))
 return row

def main():
 OUT.mkdir(exist_ok=True)
 (OUT / 'raw').mkdir(exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  rows = list(pool.map(fetch, SEEDS.items()))
 manifest = {'scope':'SOURCE_ONLY_NO_MARKET_DATA', 'candidate':'SCRT Proposal 287', 'chain_id':'secret-4',
  'voting_end':'2023-12-07T02:54:58.930543213Z', 'rows':rows, 'credentials_used':False,
  'canonical_H':None, 'canonical_T0':None, 'gate':'SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED',
  'forensic_exhaustion':False, 'rule':'Catalogs, snapshots and provider claims never certify H. Require validated H-1/H/H+1 headers, hashes, chain identity, adjacency and nanosecond boundary. Access failures and pagination limits remain incomplete.'}
 (OUT / 'receipt.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
 print(json.dumps({'requests':len(rows), 'statuses':[(r['id'],r.get('status'),r['classification']) for r in rows]}))

if __name__ == '__main__':
 main()
