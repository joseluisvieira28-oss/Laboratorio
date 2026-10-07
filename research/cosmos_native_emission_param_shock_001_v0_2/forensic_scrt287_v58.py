"""Read public Secret3 documentation and snapshot metadata only."""
import concurrent.futures,json,pathlib
import forensic_scrt287_v54 as c
c.OUT=pathlib.Path(__file__).resolve().parent/'forensic_v58'
SEEDS={
 'secret3_snapshot_latest':'https://mainnet-secret-snapshot.secret3.dev/latest.json',
 'secret3_snapshot_checksum':'https://mainnet-secret-snapshot.secret3.dev/latest.sha256',
 'secret3_home_docs':'https://docs.scrt.network/',
 'secret3_operator_home':'https://docs.scrt.network/operators/home/',
 'secret3_sitemap':'https://docs.scrt.network/sitemap.xml',
}
def main():
 c.OUT.mkdir(exist_ok=True);(c.OUT/'raw').mkdir(exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:rows=list(p.map(c.fetch,SEEDS.items()))
 (c.OUT/'receipt.json').write_text(json.dumps({'scope':'SOURCE_ONLY_NO_MARKET_DATA','rows':rows,'H':None,'T0':None,'exhaustion':False},indent=2)+'\n',encoding='utf-8')
 print([(r['id'],r.get('status')) for r in rows])
if __name__=='__main__':main()
