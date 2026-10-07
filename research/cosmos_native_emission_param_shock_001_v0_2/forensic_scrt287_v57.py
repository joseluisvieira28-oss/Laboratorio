"""Inspect newly documented Secret3 recovery distribution; never run node scripts."""
import concurrent.futures,json,pathlib,urllib.request,urllib.error
import forensic_scrt287_v54 as c
c.OUT=pathlib.Path(__file__).resolve().parent/'forensic_v57'
SEEDS={
 'secret3_restore_source':'https://docs.scrt.network/restore.sh',
 'secret3_manual_docs':'https://docs.scrt.network/manual.md',
 'secret3_snapshot_index':'https://mainnet-secret-snapshot.secret3.dev/index.html',
 'secret3_snapshot_manifest':'https://mainnet-secret-snapshot.secret3.dev/manifest.json',
 'secret3_snapshot_status':'https://mainnet-secret-snapshot.secret3.dev/status.json',
 'secret3_snapshot_listing':'https://mainnet-secret-snapshot.secret3.dev/?list-type=2&max-keys=1000',
 'secret3_historical_header':'https://rpc.secret.mainnet.secret3.dev/block?height=11880919',
}
def main():
 c.OUT.mkdir(exist_ok=True);(c.OUT/'raw').mkdir(exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(c.fetch,SEEDS.items()))
 (c.OUT/'receipt.json').write_text(json.dumps({'scope':'SOURCE_ONLY_NO_MARKET_DATA','rows':rows,'H':None,'T0':None,'exhaustion':False,'scripts_executed':False},indent=2)+'\n',encoding='utf-8')
 print([(r['id'],r.get('status'),r.get('error')) for r in rows])
if __name__=='__main__':main()
